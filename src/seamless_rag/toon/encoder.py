"""
TOON v3 Tabular Encoder — stub implementation.

This file is the primary target for Claude Code TDD iteration.
All tests in tests/unit/test_toon_encoder.py should drive development here.

TODO: Implement encode_tabular(), encode_value(), encode_object(), encode()
"""


def encode_tabular(data: list[dict], key: str | None = None) -> str:
    """Encode a list of uniform dicts as TOON v3 tabular format.

    Args:
        data: List of dicts with identical keys and primitive values.
        key: Optional key prefix for the tabular array.

    Returns:
        TOON v3 tabular string.
    """
    raise NotImplementedError("TOON tabular encoder not yet implemented")


def encode_value(value: object) -> str:
    """Encode a single primitive value according to TOON v3 rules.

    Handles: None→null, bool→true/false, int/float→canonical number,
    str→quoted if needed per Section 7.2.
    """
    raise NotImplementedError("TOON value encoder not yet implemented")


def encode_object(data: dict) -> str:
    """Encode a flat dict as TOON v3 object format.

    Args:
        data: Dict with string keys and primitive values.

    Returns:
        TOON v3 object string (key: value pairs).
    """
    raise NotImplementedError("TOON object encoder not yet implemented")


def encode(data: object, options: dict | None = None) -> str:
    """Generic TOON v3 encoder — dispatches to appropriate format.

    Args:
        data: Any JSON-compatible Python value.
        options: Optional encoding options (delimiter, indent, etc.)

    Returns:
        TOON v3 encoded string.
    """
    raise NotImplementedError("TOON generic encoder not yet implemented")
