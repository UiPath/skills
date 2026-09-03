"""Facts out of TypeScript source by masked-depth scanning.

Same posture as turtle.py: mask comments and strings to preserve offsets, then match braces by
depth. What this reads is narrow on purpose -- the interface fields a contract declares, and the
(entity, field) pairs an edit writes. A shape it does not recognise is reported as unresolved, so
absence never reads as "this job writes nothing".
"""

from __future__ import annotations

import re


def _matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _interface_body(src: str, name: str) -> str | None:
    match = re.search(rf"\binterface\s+{re.escape(name)}\s*\{{", src)
    if not match:
        return None
    open_idx = match.end() - 1
    close_idx = _matching_brace(src, open_idx)
    return None if close_idx < 0 else src[open_idx + 1 : close_idx]


def interface_fields(src: str, name: str) -> list[str] | None:
    """Top-level field names of `interface <name> { ... }`, optional markers stripped."""
    body = _interface_body(src, name)
    if body is None:
        return None
    fields, depth = [], 0
    for line in body.splitlines():
        if depth == 0:
            field = re.match(r"([A-Za-z_$][\w$]*)\s*\??\s*:", line.strip())
            if field:
                fields.append(field.group(1))
        depth += line.count("{") - line.count("}")
    return fields


def _mask_ts(src: str) -> str:
    """`src` with the contents of strings, template literals and comments blanked, same length.

    Structural scanning runs on this; the text itself is read from the original. Without it a
    `${...}` inside a template literal, or a brace inside a string, throws off every depth count.
    """
    out = list(src)
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch in "'\"`":
            quote, i = ch, i + 1
            while i < n:
                if src[i] == "\\":
                    out[i] = out[i + 1] = " " if i + 1 < n else " "
                    i += 2
                    continue
                if src[i] == quote:
                    break
                if src[i] != "\n":
                    out[i] = " "
                i += 1
            i += 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                out[i] = " "
                i += 1
        elif src.startswith("/*", i):
            while i < n and not src.startswith("*/", i):
                if src[i] != "\n":
                    out[i] = " "
                i += 1
            i += 2
        else:
            i += 1
    return "".join(out)


def _enclosing_object(masked: str, idx: int) -> tuple[int, int]:
    depth, open_idx = 0, -1
    for i in range(idx, -1, -1):
        if masked[i] == "}":
            depth += 1
        elif masked[i] == "{":
            if depth == 0:
                open_idx = i
                break
            depth -= 1
    if open_idx < 0:
        return -1, -1
    close_idx = _matching_brace(masked, open_idx)
    return (open_idx, close_idx) if close_idx > open_idx else (-1, -1)


def _top_level_keys(masked: str, open_idx: int, close_idx: int) -> set[str]:
    keys, depth = set(), 0
    i = open_idx + 1
    while i < close_idx:
        ch = masked[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif depth == 0:
            match = re.match(r"([A-Za-z_$][\w$]*)\s*:", masked[i:close_idx])
            if match and (i == open_idx + 1 or not (masked[i - 1].isalnum() or masked[i - 1] in "_$.")):
                keys.add(match.group(1))
                i += match.end() - 1
        i += 1
    return keys


def _identifier_keys(src: str, masked: str, ident: str) -> set[str]:
    """Keys assembled onto a variable: `const x = { a: 1 }`, `x.b = ...`, `x['c'] = ...`."""
    keys: set[str] = set()
    for match in re.finditer(rf"\b{re.escape(ident)}\s*(?::[^\n=]*)?=\s*\{{", masked):
        open_idx = masked.index("{", match.end() - 1)
        close_idx = _matching_brace(masked, open_idx)
        if close_idx > open_idx:
            keys |= _top_level_keys(masked, open_idx, close_idx)
    keys |= set(re.findall(rf"\b{re.escape(ident)}\.([A-Za-z_$][\w$]*)\s*=[^=]", masked))
    keys |= set(re.findall(rf"\b{re.escape(ident)}\[\s*'([^']+)'\s*\]\s*=[^=]", src))
    return keys


def written_edits(src: str) -> dict:
    """The (entity, field) pairs the job writes, each field attributed to its own edit's entity.

    Pooling every key across every entity over-declares ont:writes and grants write permission the
    job never asked for. `id` is dropped: it targets the WHERE clause, not a written column.
    `unresolved` names any edit whose properties could not be traced, which callers must treat as
    "verify by hand" rather than "writes nothing".
    """
    masked = _mask_ts(src)
    pairs: set[tuple[str, str]] = set()
    entities: set[str] = set()
    unresolved: list[str] = []

    for match in re.finditer(r"\bentity\s*:\s*['\"]([^'\"]+)['\"]", src):
        entity = match.group(1)
        entities.add(entity)
        open_idx, close_idx = _enclosing_object(masked, match.start())
        if open_idx < 0:
            unresolved.append(entity)
            continue

        # Through the closing brace, not up to it: a trailing shorthand `properties }` has no
        # delimiter after it otherwise, and the shorthand form is a common one.
        body = masked[open_idx : close_idx + 1]
        inline = re.search(r"\bproperties\s*:\s*\{", body)
        named = re.search(r"\bproperties\s*:\s*([A-Za-z_$][\w$]*)", body)
        shorthand = re.search(r"\bproperties\s*[,}\n]", body)

        if inline:
            prop_open = open_idx + body.index("{", inline.end() - 1)
            prop_close = _matching_brace(masked, prop_open)
            if prop_close < 0:
                unresolved.append(entity)
                continue
            keys = _top_level_keys(masked, prop_open, prop_close)
        elif named:
            keys = _identifier_keys(src, masked, named.group(1))
        elif shorthand:
            keys = _identifier_keys(src, masked, "properties")
        else:
            unresolved.append(entity)
            continue

        keys.discard("id")
        if not keys:
            unresolved.append(entity)
        for key in keys:
            pairs.add((entity, key))

    return {"pairs": sorted(pairs), "entities": sorted(entities), "unresolved": sorted(set(unresolved))}
