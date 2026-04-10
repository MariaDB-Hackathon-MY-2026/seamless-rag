"""
TOON v3 Encoder — full implementation per TOON v3 normative specification.

Handles primitives, objects, arrays (inline, tabular, nested, mixed),
delimiter options, key folding, and all quoting/escaping rules.
"""
from __future__ import annotations

import math
import re
from typing import Any

# ============================================================
#  Constants
# ============================================================

_UNQUOTED_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_NUMERIC_RE = re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$")
_LEADING_ZERO_RE = re.compile(r"^0\d+$")
_IDENT_SEGMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_KEYWORDS = frozenset({"true", "false", "null"})

# ============================================================
#  Escape / quoting helpers
# ============================================================


def _escape_string(value: str) -> str:
    """Apply TOON v3 Section 7.1 escape sequences."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )


def _is_safe_unquoted_key(key: str) -> bool:
    """Section 7.3: key may be unquoted if it matches identifier pattern."""
    return bool(key) and bool(_UNQUOTED_KEY_RE.match(key))


def _encode_key(key: str) -> str:
    """Encode an object/tabular field key per Section 7.3."""
    if _is_safe_unquoted_key(key):
        return key
    return '"' + _escape_string(key) + '"'


def _needs_quoting(value: str, delimiter: str) -> bool:
    """Section 7.2: determine if a string value must be quoted."""
    if not value:
        return True  # empty string
    # Leading/trailing whitespace (Unicode-aware)
    if value[0] != value[0].lstrip() or value[-1] != value[-1].rstrip():
        return True
    if value in _KEYWORDS:
        return True  # looks like literal
    if _NUMERIC_RE.match(value) or _LEADING_ZERO_RE.match(value):
        return True  # looks like number
    # Structural chars, control chars, delimiter
    for ch in value:
        if ch in (":", '"', "\\", "[", "]", "{", "}",
                   "\n", "\r", "\t"):
            return True
        if ch == delimiter:
            return True
        # Control characters (< 0x20) and non-space Unicode whitespace
        if ord(ch) < 0x20 or (ch != " " and ch.isspace()):
            return True
    # Leading hyphen
    return value[0] == "-"


def _encode_string_value(value: str, delimiter: str) -> str:
    """Encode a string value, quoting and escaping if needed."""
    if _needs_quoting(value, delimiter):
        return '"' + _escape_string(value) + '"'
    return value


# ============================================================
#  Number canonicalization (Section 2)
# ============================================================


def _encode_number(value: int | float) -> str:
    """Canonical number encoding per Section 2."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return "null"
        if value == 0.0:
            return "0"  # handles -0.0
        # Check if it's a whole number
        if value == int(value) and abs(value) < 1e20:
            return str(int(value))
        # Use repr for full precision, then strip trailing zeros
        s = repr(value)
        # repr may use scientific notation for very small/large floats
        if "e" in s or "E" in s:
            s = f"{value:.20f}".rstrip("0").rstrip(".")
            if "." not in s:
                return s
            return s
        return s
    # int
    return str(value)


# ============================================================
#  Primitive encoding
# ============================================================


def encode_value(value: object) -> str:
    """Encode a single primitive value according to TOON v3 rules.

    Handles: None->null, bool->true/false, int/float->canonical number,
    str->quoted if needed per Section 7.2.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _encode_number(value)
    if isinstance(value, str):
        return _encode_string_value(value, ",")
    raise TypeError(f"Cannot encode {type(value).__name__} as TOON primitive")


# ============================================================
#  Internal value encoding with delimiter context
# ============================================================


def _encode_primitive(value: Any, delimiter: str) -> str:
    """Encode a primitive with delimiter-aware quoting."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return _encode_number(value)
    if isinstance(value, str):
        return _encode_string_value(value, delimiter)
    raise TypeError(f"Cannot encode {type(value).__name__} as TOON primitive")


def _is_primitive(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


# ============================================================
#  Array classification helpers
# ============================================================


def _all_primitives(arr: list) -> bool:
    return all(_is_primitive(v) for v in arr)


def _all_arrays(arr: list) -> bool:
    return all(isinstance(v, list) for v in arr)


def _is_tabular(arr: list) -> bool:
    """Check if array qualifies for tabular format (Section 9.3)."""
    if not arr:
        return False
    if not all(isinstance(v, dict) for v in arr):
        return False
    keys = set(arr[0].keys())
    for row in arr[1:]:
        if set(row.keys()) != keys:
            return False
    # All values must be primitives
    for row in arr:
        for v in row.values():
            if not _is_primitive(v):
                return False
    return True


# ============================================================
#  Delimiter header helpers
# ============================================================


def _delim_in_bracket(delimiter: str) -> str:
    """Return delimiter suffix for bracket notation. Comma is omitted."""
    if delimiter == ",":
        return ""
    return delimiter


# ============================================================
#  Tabular encoder
# ============================================================


def encode_tabular(
    data: list[dict],
    key: str | None = None,
    *,
    delimiter: str = ",",
    indent: int = 2,
    depth: int = 0,
) -> str:
    """Encode a list of uniform dicts as TOON v3 tabular format.

    Public convenience API — always includes delimiter in bracket header.
    Format: [N,]{field1,field2}: (comma always shown).
    """
    return _encode_tabular_core(
        data, key, delimiter=delimiter, indent=indent, depth=depth,
        always_show_delim=True,
    )


def _encode_tabular_core(
    data: list[dict],
    key: str | None,
    *,
    delimiter: str = ",",
    indent: int = 2,
    depth: int = 0,
    always_show_delim: bool = False,
) -> str:
    """Internal tabular encoder.

    Args:
        always_show_delim: If True, always include delimiter in bracket
            (encode_tabular public API). If False, follow spec convention
            where comma is omitted (used by encode()).
    """
    prefix = " " * (indent * depth)
    n = len(data)
    dsuf = delimiter if always_show_delim else _delim_in_bracket(delimiter)

    if n == 0:
        if key is not None:
            return f"{prefix}{_encode_key(key)}[0{dsuf}]:"
        return f"{prefix}[0{dsuf}]:"

    fields = list(data[0].keys())
    field_header = delimiter.join(_encode_key(f) for f in fields)
    header_key = _encode_key(key) if key is not None else ""

    header = f"{header_key}[{n}{dsuf}]{{{field_header}}}:"

    lines = [f"{prefix}{header}"]
    row_prefix = " " * (indent * (depth + 1))
    for row in data:
        values = []
        for f in fields:
            values.append(_encode_primitive(row[f], delimiter))
        lines.append(f"{row_prefix}{delimiter.join(values)}")

    return "\n".join(lines)


# ============================================================
#  Object encoder
# ============================================================


def encode_object(data: dict) -> str:
    """Encode a flat dict as TOON v3 object format.

    Args:
        data: Dict with string keys and primitive values.

    Returns:
        TOON v3 object string (key: value pairs).
    """
    return _encode_object_lines(data, delimiter=",", indent=2, depth=0)


def _encode_object_lines(
    data: dict,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> str:
    """Encode an object (dict) producing multi-line output."""
    if not data:
        return ""

    lines: list[str] = []

    for k, v in data.items():
        # Key folding (safe mode)
        if key_folding == "safe" and isinstance(v, dict) and len(v) == 1:
            folded = _try_fold(
                k, v, delimiter=delimiter, indent=indent, depth=depth,
                flatten_depth=flatten_depth, parent_keys=parent_keys or set(data.keys()),
                key_folding=key_folding,
            )
            if folded is not None:
                lines.append(folded)
                continue

        encoded = _encode_value_in_object(
            k, v, delimiter=delimiter, indent=indent, depth=depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )
        lines.append(encoded)

    return "\n".join(lines)


def _try_fold(
    key: str,
    value: dict,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    flatten_depth: int | float,
    parent_keys: set[str],
    key_folding: str,
    segments: list[str] | None = None,
) -> str | None:
    """Try to fold a single-key object chain into dotted path."""
    if segments is None:
        segments = [key]

    if not _IDENT_SEGMENT_RE.match(key):
        return None

    inner_key = next(iter(value))
    inner_val = value[inner_key]

    if not _IDENT_SEGMENT_RE.match(inner_key):
        return None

    new_segments = segments + [inner_key]

    if len(new_segments) > flatten_depth:
        return None

    # Check collision with parent sibling keys:
    # exact match OR any sibling starts with folded_key + "."
    folded_key = ".".join(new_segments)
    if folded_key in parent_keys:
        return None
    prefix_check = folded_key + "."
    if any(sk.startswith(prefix_check) for sk in parent_keys):
        return None

    # If inner_val is a single-key dict, recurse deeper
    if isinstance(inner_val, dict) and len(inner_val) == 1:
        deeper = _try_fold(
            inner_key, inner_val,
            delimiter=delimiter, indent=indent, depth=depth,
            flatten_depth=flatten_depth, parent_keys=parent_keys,
            key_folding=key_folding,
            segments=new_segments,
        )
        if deeper is not None:
            return deeper

    # Fold terminates here — encode the final value with the folded key
    prefix = " " * (indent * depth)
    # Consume fold budget: remaining depth for sub-encoding
    consumed = len(new_segments) - 1
    remaining_depth = flatten_depth - consumed if flatten_depth != float("inf") else float("inf")

    if isinstance(inner_val, dict):
        if not inner_val:
            return f"{prefix}{folded_key}:"
        sub = _encode_object_lines(
            inner_val, delimiter=delimiter, indent=indent, depth=depth + 1,
            key_folding=key_folding, flatten_depth=remaining_depth,
            parent_keys=parent_keys,
        )
        return f"{prefix}{folded_key}:\n{sub}"

    if isinstance(inner_val, list):
        return _encode_array_field(
            folded_key, inner_val,
            delimiter=delimiter, indent=indent, depth=depth,
            key_folding=key_folding, flatten_depth=remaining_depth,
            parent_keys=parent_keys,
        )

    ev = _encode_primitive(inner_val, delimiter)
    return f"{prefix}{folded_key}: {ev}"


def _encode_value_in_object(
    key: str,
    value: Any,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> str:
    """Encode a single key-value pair within an object."""
    prefix = " " * (indent * depth)
    ek = _encode_key(key)

    if isinstance(value, list):
        return _encode_array_field(
            key, value, delimiter=delimiter, indent=indent, depth=depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )

    if isinstance(value, dict):
        if not value:
            return f"{prefix}{ek}:"
        # Disable folding in sub-tree if a sibling key creates ambiguity
        sub_folding = key_folding
        if key_folding == "safe" and parent_keys:
            key_prefix = key + "."
            if any(sk.startswith(key_prefix) for sk in parent_keys):
                sub_folding = "off"
        sub = _encode_object_lines(
            value, delimiter=delimiter, indent=indent, depth=depth + 1,
            key_folding=sub_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )
        return f"{prefix}{ek}:\n{sub}"

    ev = _encode_primitive(value, delimiter)
    return f"{prefix}{ek}: {ev}"


# ============================================================
#  Array encoding
# ============================================================


def _encode_array_field(
    key: str | None,
    arr: list,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> str:
    """Encode an array as a field value (or root-level)."""
    prefix = " " * (indent * depth)
    ek = _encode_key(key) if key is not None else ""
    dsuf = _delim_in_bracket(delimiter)
    n = len(arr)

    # Empty array
    if n == 0:
        return f"{prefix}{ek}[0{dsuf}]:"

    # All primitives → inline
    if _all_primitives(arr):
        vals = delimiter.join(_encode_primitive(v, delimiter) for v in arr)
        return f"{prefix}{ek}[{n}{dsuf}]: {vals}"

    # Tabular (uniform object array with primitive values)
    if _is_tabular(arr):
        return _encode_tabular_core(
            arr, key, delimiter=delimiter, indent=indent, depth=depth,
            always_show_delim=False,
        )

    # All arrays → array of arrays
    if _all_arrays(arr):
        header = f"{prefix}{ek}[{n}{dsuf}]:"
        lines = [header]
        item_prefix = " " * (indent * (depth + 1))
        for sub_arr in arr:
            sn = len(sub_arr)
            if sn == 0:
                lines.append(f"{item_prefix}- [{sn}{dsuf}]:")
            else:
                vals = delimiter.join(_encode_primitive(v, delimiter) for v in sub_arr)
                lines.append(f"{item_prefix}- [{sn}{dsuf}]: {vals}")
        return "\n".join(lines)

    # Mixed / non-uniform → list format
    return _encode_mixed_array(
        key, arr, delimiter=delimiter, indent=indent, depth=depth,
        key_folding=key_folding, flatten_depth=flatten_depth,
        parent_keys=parent_keys,
    )


def _encode_mixed_array(
    key: str | None,
    arr: list,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> str:
    """Encode a mixed/non-uniform array in list format (Section 9.4)."""
    prefix = " " * (indent * depth)
    ek = _encode_key(key) if key is not None else ""
    dsuf = _delim_in_bracket(delimiter)
    n = len(arr)

    header = f"{prefix}{ek}[{n}{dsuf}]:"
    lines = [header]
    item_prefix = " " * (indent * (depth + 1))

    for item in arr:
        if _is_primitive(item):
            ev = _encode_primitive(item, delimiter)
            lines.append(f"{item_prefix}- {ev}")
        elif isinstance(item, list):
            # Nested array in list item
            arr_str = _encode_array_field(
                None, item, delimiter=delimiter, indent=indent, depth=depth + 1,
                key_folding=key_folding, flatten_depth=flatten_depth,
                parent_keys=parent_keys,
            )
            # Replace the prefix with "- " marker
            stripped = arr_str.lstrip()
            lines.append(f"{item_prefix}- {stripped}")
        elif isinstance(item, dict):
            _encode_list_item_object(
                item, lines, item_prefix,
                delimiter=delimiter, indent=indent, depth=depth + 1,
                key_folding=key_folding, flatten_depth=flatten_depth,
                parent_keys=parent_keys,
            )
        else:
            ev = _encode_primitive(item, delimiter)
            lines.append(f"{item_prefix}- {ev}")

    return "\n".join(lines)


def _encode_list_item_object(
    obj: dict,
    lines: list[str],
    item_prefix: str,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> None:
    """Encode a dict as a list item (- key: val / continuation lines).

    The "- " marker occupies `indent` chars, so continuation fields
    align with the content after "- " (i.e. depth + 1).
    """
    if not obj:
        lines.append(f"{item_prefix}-")
        return

    keys = list(obj.keys())
    first_key = keys[0]
    first_val = obj[first_key]

    # First field gets the "- " prefix
    first_line = _encode_first_list_field(
        first_key, first_val, item_prefix,
        delimiter=delimiter, indent=indent, depth=depth,
        key_folding=key_folding, flatten_depth=flatten_depth,
        parent_keys=parent_keys,
    )
    lines.extend(first_line)

    # Continuation fields align with content after "- " → depth + 1
    cont_depth = depth + 1
    for k in keys[1:]:
        v = obj[k]
        encoded = _encode_value_in_object(
            k, v, delimiter=delimiter, indent=indent, depth=cont_depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )
        lines.append(encoded)


def _encode_first_list_field(
    key: str,
    value: Any,
    item_prefix: str,
    *,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> list[str]:
    """Encode the first field of a list-item object with '- ' prefix.

    Sub-content (array rows, nested object fields) is indented at
    depth + 2: one level for the list item, one for the "- " offset.
    """
    ek = _encode_key(key)
    dsuf = _delim_in_bracket(delimiter)
    # Sub-content depth: accounts for item indent + "- " offset
    sub_depth = depth + 2

    if isinstance(value, list):
        n = len(value)
        if n == 0:
            return [f"{item_prefix}- {ek}[0{dsuf}]:"]
        if _all_primitives(value):
            vals = delimiter.join(_encode_primitive(v, delimiter) for v in value)
            return [f"{item_prefix}- {ek}[{n}{dsuf}]: {vals}"]
        if _is_tabular(value):
            # Tabular inside list item
            fields = list(value[0].keys())
            field_header = delimiter.join(_encode_key(f) for f in fields)
            header = f"{item_prefix}- {ek}[{n}{dsuf}]{{{field_header}}}:"
            result = [header]
            row_prefix = " " * (indent * sub_depth)
            for row in value:
                vals = delimiter.join(
                    _encode_primitive(row[f], delimiter) for f in fields
                )
                result.append(f"{row_prefix}{vals}")
            return result
        if _all_arrays(value):
            header = f"{item_prefix}- {ek}[{n}{dsuf}]:"
            result = [header]
            sub_prefix = " " * (indent * sub_depth)
            for sub_arr in value:
                sn = len(sub_arr)
                if sn == 0:
                    result.append(f"{sub_prefix}- [{sn}{dsuf}]:")
                else:
                    vals = delimiter.join(_encode_primitive(v, delimiter) for v in sub_arr)
                    result.append(f"{sub_prefix}- [{sn}{dsuf}]: {vals}")
            return result
        # Mixed nested array — encode at sub_depth - 1 because
        # _encode_mixed_array adds its own +1 for items
        mixed = _encode_mixed_array(
            key, value, delimiter=delimiter, indent=indent,
            depth=depth + 1,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )
        mixed_lines = mixed.split("\n")
        # Replace first line prefix with "- "
        first = mixed_lines[0].lstrip()
        result = [f"{item_prefix}- {first}"]
        result.extend(mixed_lines[1:])
        return result

    if isinstance(value, dict):
        if not value:
            return [f"{item_prefix}- {ek}:"]
        sub = _encode_object_lines(
            value, delimiter=delimiter, indent=indent, depth=sub_depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )
        return [f"{item_prefix}- {ek}:", *sub.split("\n")]

    ev = _encode_primitive(value, delimiter)
    return [f"{item_prefix}- {ek}: {ev}"]


# ============================================================
#  Generic encoder
# ============================================================


def encode(data: object, options: dict | None = None) -> str:
    """Generic TOON v3 encoder — dispatches to appropriate format.

    Args:
        data: Any JSON-compatible Python value.
        options: Optional encoding options (delimiter, indent, keyFolding, flattenDepth)

    Returns:
        TOON v3 encoded string.
    """
    opts = options or {}
    delimiter = opts.get("delimiter", ",")
    indent_size = opts.get("indent", 2)
    key_folding = opts.get("keyFolding", "off")
    flatten_depth = opts.get("flattenDepth", float("inf"))

    return _encode_any(
        data,
        key=None,
        delimiter=delimiter,
        indent=indent_size,
        depth=0,
        key_folding=key_folding,
        flatten_depth=flatten_depth,
        parent_keys=None,
    )


def _encode_any(
    value: Any,
    *,
    key: str | None,
    delimiter: str,
    indent: int,
    depth: int,
    key_folding: str = "off",
    flatten_depth: int | float = float("inf"),
    parent_keys: set[str] | None = None,
) -> str:
    """Core dispatch: encode any JSON value."""
    # Primitive at root
    if _is_primitive(value):
        if key is not None:
            prefix = " " * (indent * depth)
            ek = _encode_key(key)
            ev = _encode_primitive(value, delimiter)
            return f"{prefix}{ek}: {ev}"
        return _encode_primitive(value, delimiter)

    # Array
    if isinstance(value, list):
        return _encode_array_field(
            key, value,
            delimiter=delimiter, indent=indent, depth=depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=parent_keys,
        )

    # Object
    if isinstance(value, dict):
        if key is not None:
            prefix = " " * (indent * depth)
            ek = _encode_key(key)
            if not value:
                return f"{prefix}{ek}:"
            sub = _encode_object_lines(
                value, delimiter=delimiter, indent=indent, depth=depth + 1,
                key_folding=key_folding, flatten_depth=flatten_depth,
                parent_keys=parent_keys,
            )
            return f"{prefix}{ek}:\n{sub}"
        return _encode_object_lines(
            value, delimiter=delimiter, indent=indent, depth=depth,
            key_folding=key_folding, flatten_depth=flatten_depth,
            parent_keys=set(value.keys()) if value else None,
        )

    raise TypeError(f"Cannot encode {type(value).__name__}")
