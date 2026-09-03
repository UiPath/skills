"""Turtle lexing by text, never a parser.

An action TTL is read by masking comments and string bodies to preserve offsets, then slicing on
statement terminators. The masking matters: `ont:writes "Ticket.tags"` and a comment mentioning
the same text must not be confused, and a real RDF library is not available to a dependency-free
tool. Extraction failures are reported by the caller rather than read as "nothing found".
"""

from __future__ import annotations

import re


def mask_ttl(text: str, blank_strings: bool = True) -> str:
    """`text` with comments (and optionally string/IRI bodies) blanked, same length as the input."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if text.startswith('"""', i) or text.startswith("'''", i):
            quote = text[i : i + 3]
            close = text.find(quote, i + 3)
            end = n if close < 0 else close + 3
            if blank_strings:
                for k in range(i + 3, min(end, n) - 3 if close >= 0 else n):
                    if text[k] != "\n":
                        out[k] = " "
            i = end
        elif ch in "\"'":
            quote, i = ch, i + 1
            while i < n and text[i] != quote:
                if text[i] == "\\":
                    if blank_strings:
                        out[i] = " "
                        if i + 1 < n:
                            out[i + 1] = " "
                    i += 2
                    continue
                if blank_strings and text[i] != "\n":
                    out[i] = " "
                i += 1
            i += 1
        elif ch == "<" and re.match(r"<[^\s<>\"{}|^`\\]*>", text[i:]):
            close = text.index(">", i)
            if blank_strings:
                for k in range(i + 1, close):
                    out[k] = " "
            i = close + 1
        elif ch == "#":
            while i < n and text[i] != "\n":
                out[i] = " "
                i += 1
        else:
            i += 1
    return "".join(out)


def ttl_statements(text: str) -> list[tuple[str, bool]]:
    """(statement text with comments stripped, terminated) for each '.'-terminated statement."""
    structure = mask_ttl(text)
    clean = mask_ttl(text, blank_strings=False)
    statements: list[tuple[str, bool]] = []
    depth, start = 0, 0
    for i, ch in enumerate(structure):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "." and depth == 0 and (i + 1 == len(structure) or structure[i + 1] in " \t\r\n"):
            statements.append((clean[start:i], True))
            start = i + 1
    if clean[start:].strip():
        statements.append((clean[start:], False))
    return [(body, terminated) for body, terminated in statements if body.strip()]


def subject_of(statement: str) -> str:
    match = re.match(r"\s*(\S+)", statement)
    return match.group(1) if match else ""


def is_directive(subject: str) -> bool:
    return subject.startswith("@") or subject.upper() in {"PREFIX", "BASE"}


def list_items(body: str, predicate: str) -> list[str] | None:
    """Members of `predicate ( ... )`, or None when the predicate is absent or not a list.

    The closing paren is found by depth on a string-masked copy: the func: marker carries its own
    parens inside a quoted string, and a non-greedy regex stops at that one.
    """
    match = re.search(rf"{predicate}\s*\(", body)
    if not match:
        return None
    structure = mask_ttl(body)
    depth, close = 0, -1
    for i in range(match.end() - 1, len(structure)):
        if structure[i] == "(":
            depth += 1
        elif structure[i] == ")":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close < 0:
        return None
    inner = body[match.end() : close]
    return [quoted or bare for quoted, bare in re.findall(r"\"((?:\\.|[^\"])*)\"|(\S+)", inner) if quoted or bare]


def quoted_objects(body: str, predicate: str) -> list[str]:
    """Objects of a repeated-triple predicate: `ont:writes \"A.b\", \"C.d\" ;`."""
    found: list[str] = []
    for match in re.finditer(rf"{predicate}\s+((?:\"(?:\\.|[^\"])*\"\s*,?\s*)+)", body):
        found.extend(re.findall(r"\"((?:\\.|[^\"])*)\"", match.group(1)))
    return found


def first_quoted(body: str, predicate: str) -> str:
    match = re.search(rf"{predicate}\s+\"((?:\\.|[^\"])*)\"", body)
    return match.group(1) if match else ""
