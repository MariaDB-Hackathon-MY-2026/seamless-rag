"""
Unit tests for TOON v3 tabular encoder.

Tests cover:
- Tabular encoding (primary use case for SQL results)
- Value quoting rules (TOON v3 spec Section 7.2)
- Number canonicalization (Section 2)
- Escape sequences (Section 7.1)
- Field name quoting (Section 7.3)
- Edge cases (NULL, booleans, Unicode, special chars)
"""
import json
import math

import pytest

from seamless_rag.toon.encoder import encode_tabular, encode_value, encode_object


class TestEncodeTabular:
    """Test tabular array encoding — the primary TOON use case for SQL results."""

    def test_single_row(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["single_row"]
        assert encode_tabular(data) == expected

    def test_multi_row(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["multi_row"]
        assert encode_tabular(data) == expected

    def test_empty_array(self):
        assert encode_tabular([]) == "[0,]:"

    def test_preserves_field_order(self):
        """Field order comes from first dict's key order."""
        data = [{"z": 1, "a": 2, "m": 3}]
        result = encode_tabular(data)
        assert result.startswith("[1,]{z,a,m}:")

    def test_header_format(self):
        """Header must be [N,]{fields}: with comma in brackets for tabular."""
        data = [{"x": 1}, {"x": 2}, {"x": 3}]
        result = encode_tabular(data)
        assert result.startswith("[3,]{x}:")

    def test_row_indentation(self):
        """Rows must be indented by 2 spaces."""
        data = [{"a": 1}]
        lines = encode_tabular(data).split("\n")
        assert len(lines) == 2
        assert lines[1].startswith("  ")

    def test_no_trailing_newline(self):
        """TOON spec: no trailing newline."""
        data = [{"a": 1}]
        result = encode_tabular(data)
        assert not result.endswith("\n")


class TestValueQuoting:
    """Test TOON v3 value quoting rules (Section 7.2)."""

    def test_null(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["with_null"]
        assert encode_tabular(data) == expected

    def test_booleans(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["with_bool"]
        assert encode_tabular(data) == expected

    def test_comma_in_value_quoted(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["needs_quoting_comma"]
        assert encode_tabular(data) == expected

    def test_colon_in_value_quoted(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["needs_quoting_colon"]
        assert encode_tabular(data) == expected

    def test_empty_string_quoted(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["empty_string"]
        assert encode_tabular(data) == expected

    def test_numeric_string_quoted(self, toon_tabular_cases):
        """Strings that look like numbers must be quoted."""
        data, expected = toon_tabular_cases["string_looks_like_number"]
        assert encode_tabular(data) == expected

    def test_bool_string_quoted(self, toon_tabular_cases):
        """Strings 'true'/'false' must be quoted."""
        data, expected = toon_tabular_cases["string_looks_like_bool"]
        assert encode_tabular(data) == expected

    def test_null_string_quoted(self, toon_tabular_cases):
        """String 'null' must be quoted."""
        data, expected = toon_tabular_cases["string_looks_like_null"]
        assert encode_tabular(data) == expected

    def test_unicode_unquoted(self, toon_tabular_cases):
        """Unicode text without special chars is safe unquoted."""
        data, expected = toon_tabular_cases["unicode"]
        assert encode_tabular(data) == expected

    def test_leading_space_quoted(self):
        data = [{"id": 1, "val": " hello"}]
        result = encode_tabular(data)
        assert '" hello"' in result

    def test_trailing_space_quoted(self):
        data = [{"id": 1, "val": "hello "}]
        result = encode_tabular(data)
        assert '"hello "' in result

    def test_hyphen_start_quoted(self):
        """Values starting with - must be quoted."""
        data = [{"id": 1, "val": "-note"}]
        result = encode_tabular(data)
        assert '"-note"' in result

    def test_brackets_quoted(self):
        data = [{"id": 1, "val": "[1,2]"}]
        result = encode_tabular(data)
        assert '"[1,2]"' in result

    def test_braces_quoted(self):
        data = [{"id": 1, "val": "{a:1}"}]
        result = encode_tabular(data)
        assert '"{a:1}"' in result


class TestEscapeSequences:
    """Test TOON v3 escape sequences (Section 7.1)."""

    def test_newline_escaped(self, toon_tabular_cases):
        data, expected = toon_tabular_cases["newline_in_value"]
        assert encode_tabular(data) == expected

    def test_backslash_escaped(self):
        data = [{"id": 1, "path": "C:\\Users"}]
        result = encode_tabular(data)
        assert '"C:\\\\Users"' in result

    def test_double_quote_escaped(self):
        data = [{"id": 1, "val": 'He said "hi"'}]
        result = encode_tabular(data)
        assert '"He said \\"hi\\""' in result

    def test_tab_escaped(self):
        data = [{"id": 1, "val": "a\tb"}]
        result = encode_tabular(data)
        assert '"a\\tb"' in result

    def test_carriage_return_escaped(self):
        data = [{"id": 1, "val": "a\rb"}]
        result = encode_tabular(data)
        assert '"a\\rb"' in result


class TestNumberCanonicalization:
    """Test TOON v3 number encoding (Section 2)."""

    def test_integer(self):
        data = [{"val": 42}]
        assert "42" in encode_tabular(data)

    def test_negative_integer(self):
        data = [{"val": -7}]
        assert "-7" in encode_tabular(data)

    def test_float_strips_trailing_zeros(self):
        data = [{"val": 1.5}]
        result = encode_tabular(data)
        assert "1.5" in result
        assert "1.50" not in result

    def test_float_whole_becomes_integer(self):
        """1.0 -> 1"""
        data = [{"val": 1.0}]
        lines = encode_tabular(data).split("\n")
        # The value should be "1" not "1.0"
        assert lines[1].strip() == "1"

    def test_negative_zero_becomes_zero(self):
        """-0.0 -> 0"""
        data = [{"val": -0.0}]
        lines = encode_tabular(data).split("\n")
        assert lines[1].strip() == "0"

    def test_no_scientific_notation(self):
        """Large numbers must not use scientific notation."""
        data = [{"val": 1000000}]
        result = encode_tabular(data)
        assert "1000000" in result
        assert "e" not in result.lower()

    def test_nan_becomes_null(self):
        data = [{"val": float("nan")}]
        result = encode_tabular(data)
        assert "null" in result

    def test_infinity_becomes_null(self):
        data = [{"val": float("inf")}]
        result = encode_tabular(data)
        assert "null" in result

    def test_neg_infinity_becomes_null(self):
        data = [{"val": float("-inf")}]
        result = encode_tabular(data)
        assert "null" in result


class TestFieldNameQuoting:
    """Test TOON v3 key encoding (Section 7.3)."""

    def test_simple_name_unquoted(self):
        data = [{"user_name": "Ada"}]
        result = encode_tabular(data)
        assert "{user_name}" in result

    def test_dotted_name_unquoted(self):
        """Dots are valid in unquoted keys."""
        data = [{"user.name": "Ada"}]
        result = encode_tabular(data)
        assert "{user.name}" in result

    def test_hyphen_name_quoted(self):
        data = [{"order-id": 1}]
        result = encode_tabular(data)
        assert '{"order-id"}' in result

    def test_space_name_quoted(self):
        data = [{"full name": "Ada"}]
        result = encode_tabular(data)
        assert '{"full name"}' in result

    def test_digit_start_quoted(self):
        data = [{"123abc": "val"}]
        result = encode_tabular(data)
        assert '{"123abc"}' in result

    def test_empty_key_quoted(self):
        data = [{"": "val"}]
        result = encode_tabular(data)
        assert '{""}' in result


class TestTokenEfficiency:
    """Verify TOON is actually more compact than JSON for tabular data."""

    def test_toon_shorter_than_json(self, sample_search_results):
        toon = encode_tabular(sample_search_results)
        json_str = json.dumps(sample_search_results)
        assert len(toon) < len(json_str), (
            f"TOON ({len(toon)} chars) should be shorter than JSON ({len(json_str)} chars)"
        )

    def test_toon_shorter_than_json_compact(self, sample_search_results):
        toon = encode_tabular(sample_search_results)
        json_compact = json.dumps(sample_search_results, separators=(",", ":"))
        # For 3+ rows of tabular data, TOON should be more compact
        assert len(toon) < len(json_compact), (
            f"TOON ({len(toon)} chars) should be shorter than compact JSON ({len(json_compact)} chars)"
        )

    def test_savings_above_30_percent(self, sample_search_results):
        """TOON should save at least 30% vs JSON for tabular data."""
        toon = encode_tabular(sample_search_results)
        json_str = json.dumps(sample_search_results)
        savings = (len(json_str) - len(toon)) / len(json_str) * 100
        assert savings >= 30, f"Token savings {savings:.1f}% is below 30% target"
