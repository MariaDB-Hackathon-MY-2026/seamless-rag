"""
Property-based tests for TOON encoder using Hypothesis.

These tests generate random inputs to discover edge cases that
example-based tests miss. Critical for TOON because the format
has subtle quoting/escaping rules.
"""
import json
import math
import re

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from seamless_rag.toon.encoder import encode_tabular, encode_value

# ============================================================
#  Custom Strategies
# ============================================================

# TOON-safe primitive values
toon_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**53), max_value=2**53),
    st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False),
    st.text(
        alphabet=st.characters(
            blacklist_categories=("Cs",),  # no surrogates
            blacklist_characters=("\x00",),
        ),
        min_size=0,
        max_size=200,
    ),
)

# Valid TOON field names (SQL column names)
toon_field_names = st.from_regex(r"[a-z_][a-z0-9_]{0,15}", fullmatch=True)


@st.composite
def toon_tabular_array(draw):
    """Generate a list of dicts with identical keys (SQL result set shape)."""
    keys = draw(st.lists(toon_field_names, min_size=1, max_size=8, unique=True))
    n_rows = draw(st.integers(min_value=1, max_value=20))
    rows = []
    for _ in range(n_rows):
        row = {k: draw(toon_primitives) for k in keys}
        rows.append(row)
    return rows


# ============================================================
#  Properties
# ============================================================

@pytest.mark.props
class TestTabularProperties:
    """Property-based tests for tabular encoding."""

    @given(rows=toon_tabular_array())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_encode_never_crashes(self, rows):
        """Encoder must handle any valid tabular input without exceptions."""
        result = encode_tabular(rows)
        assert isinstance(result, str)

    @given(rows=toon_tabular_array())
    @settings(max_examples=200)
    def test_deterministic(self, rows):
        """Same input always produces identical output."""
        assert encode_tabular(rows) == encode_tabular(rows)

    @given(rows=toon_tabular_array())
    @settings(max_examples=200)
    def test_no_trailing_newline(self, rows):
        """Output must not end with newline (TOON spec)."""
        result = encode_tabular(rows)
        if result:  # empty array produces minimal output
            assert not result.endswith("\n")

    @given(rows=toon_tabular_array())
    @settings(max_examples=200)
    def test_no_trailing_whitespace_per_line(self, rows):
        """No trailing spaces on any line (TOON spec Section 12)."""
        result = encode_tabular(rows)
        for i, line in enumerate(result.split("\n")):
            assert line == line.rstrip(), f"Line {i} has trailing whitespace: {line!r}"

    @given(rows=toon_tabular_array())
    @settings(max_examples=200)
    def test_header_count_matches_rows(self, rows):
        """Header [N,] count must match actual number of rows."""
        result = encode_tabular(rows)
        # Extract N from [N,]{...}:
        match = re.match(r"\[(\d+),\]", result)
        assert match, f"Could not parse header from: {result[:50]}"
        assert int(match.group(1)) == len(rows)

    @given(rows=toon_tabular_array())
    @settings(max_examples=200)
    def test_row_count_matches(self, rows):
        """Number of data lines must match number of input rows."""
        result = encode_tabular(rows)
        lines = result.split("\n")
        data_lines = [l for l in lines[1:] if l.strip()]  # skip header
        assert len(data_lines) == len(rows)

    @given(rows=toon_tabular_array())
    @settings(max_examples=100)
    def test_shorter_than_json_for_many_rows(self, rows):
        """For 5+ rows with 3+ fields, TOON tabular should be shorter than compact JSON.

        TOON's header overhead amortizes over rows, so very small tables
        (2 rows, 1 field, short values) may not benefit. The real value
        is in database query results which typically have many rows.

        Note: TOON spec requires no scientific notation for floats, so
        extreme floats (1e+50) expand to many digits. This is a spec
        compliance tradeoff — skip inputs with extreme floats.
        """
        if len(rows) < 5 or len(rows[0]) < 3:
            return  # small tables may not benefit from TOON header overhead
        # Skip if any float would expand to >20 digits (scientific notation edge case)
        for row in rows:
            for v in row.values():
                if isinstance(v, float) and v != 0.0 and (abs(v) > 1e15 or 0 < abs(v) < 1e-10):
                    return
        result = encode_tabular(rows)
        json_str = json.dumps(rows, separators=(",", ":"))
        assert len(result) <= len(json_str), (
            f"TOON ({len(result)}) not shorter than JSON ({len(json_str)}) "
            f"for {len(rows)} rows x {len(rows[0])} fields"
        )


@pytest.mark.props
class TestPrimitiveProperties:
    """Property-based tests for individual value encoding."""

    @given(val=st.text(min_size=0, max_size=100))
    @settings(max_examples=300)
    def test_string_encode_never_crashes(self, val):
        """String encoding must handle any Unicode input."""
        result = encode_value(val)
        assert isinstance(result, str)

    @given(val=st.integers(min_value=-(2**53), max_value=2**53))
    def test_integer_no_scientific_notation(self, val):
        """Encoded integers must not contain 'e' or 'E'."""
        result = encode_value(val)
        assert "e" not in result.lower(), f"Scientific notation in: {result}"

    @given(val=st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False))
    def test_float_no_scientific_notation(self, val):
        """Encoded floats must not contain scientific notation."""
        result = encode_value(val)
        if result != "null":  # NaN/Inf become null
            assert "e" not in result.lower(), f"Scientific notation in: {result}"

    @given(val=st.floats(allow_nan=True, allow_infinity=True))
    def test_nan_inf_become_null(self, val):
        """NaN and Infinity must encode as null."""
        if math.isnan(val) or math.isinf(val):
            assert encode_value(val) == "null"

    @given(val=st.sampled_from(["true", "false", "null", "True", "FALSE"]))
    def test_keyword_strings_quoted(self, val):
        """Strings matching TOON keywords must be quoted."""
        result = encode_value(val)
        if val in ("true", "false", "null"):
            assert result.startswith('"') and result.endswith('"'), (
                f"Keyword string {val!r} not quoted: {result}"
            )
