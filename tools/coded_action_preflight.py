#!/usr/bin/env python3
"""Local, dependency-free preflight checks for UiPath coded-action pairs.

A coded action is two files that have to agree: {workdir}/{ontology}-{action}.ttl declaring
ont:language "IMPERATIVE", and {workdir}/jobs/{action}.<ext> holding the job. Nothing at author
time enforces the agreement, and both ways of breaking it fail late: the SDK validates job input
with additionalProperties:false, so a renamed field faults the job before the handler runs, and an
edit touching a field outside ont:writes is refused at 'Preparing write statement'
(SQL_GUARD_REJECTED) after the job has already executed.

Two contract idioms are understood: zod (`input: z.object({...}).strict()`, what generation
emits and the only idiom `uip functions pack` can lower) and type<T>() over plain interfaces
(packable only by Studio Web). The input-strictness gate checks that a zod input object carries
.strict(), since that is what emits additionalProperties:false; a type<T>() contract passes it
with a note, because the SDK derivation supplies the flag itself.

The TTL is scanned as text, not parsed as RDF. There is no rdflib here, so there is no IRI
resolution, no blank nodes, no @base, no collections beyond the flat ( ... ) lists these actions
use, and no datatype or language tags. What text can check is checked: statement termination,
duplicate subjects, the func: marker, RDF-list versus repeated-triple form, cross-references
between an action and its read/param nodes, and the presence of the predicates the runtime
requires. A file that passes here can still be rejected by a real Turtle parser; a file that fails
here is wrong under any parser.

Entity and field existence resolves against {workdir}/{ontology}.ofn, which is the authority. No
service is contacted, nothing is uploaded, and nothing on disk is modified.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


GATES = (
    "ttl-parses-and-well-formed",
    "signature-resolves",
    "input-matches-marker",
    "input-strictness",
    "writes-cover-edits",
    "fields-exist-in-schema",
    "folder-id-status",
    "job-language",
    "typecheck",
)
SUPPORTED_JOB_LANGUAGES = ("typescript",)
JOB_LANGUAGES = {".ts": "typescript", ".js": "javascript", ".py": "python", ".cs": "csharp", ".java": "java"}
PENDING_DEPLOY = "PENDING_DEPLOY"
SDK_MODULE = "@uipath/coded-functions-js-sdk"
TSC_FLAGS = (
    "--noEmit",
    "--strict",
    "--target",
    "ES2022",
    "--module",
    "ESNext",
    "--moduleResolution",
    "bundler",
    "--skipLibCheck",
)
# The stub keeps handler-satisfies-Output. The handler's return type is its own parameter
# constrained by O rather than plain O: typed as plain O, inference widens O to whatever the
# handler happens to return and the DeclaredEdit op-widening trap compiles clean.
SDK_STUB = """export declare function type<T>(): T;
export declare function defineFunction<I, O, R extends O>(config: {
  name: string;
  description?: string;
  method?: string;
  path?: string;
  input: I;
  output: O;
  handler: (input: I) => R | Promise<R>;
}): unknown;
"""

# The zod-idiom stub: input/output are zod schemas, the handler sees and returns the schemas'
# inferred types, and R extends z.output<O> keeps the op-widening trap detectable for the same
# reason as above. Used only when zod itself is resolvable, since the job imports it for real.
SDK_STUB_ZOD = """import type { z } from 'zod';
export declare function type<T>(): T;
export declare function defineFunction<I extends z.ZodType, O extends z.ZodType, R extends z.output<O>>(config: {
  name: string;
  description?: string;
  method?: string;
  path?: string;
  input: I;
  output: O;
  handler: (input: z.output<I>) => R | Promise<R>;
}): unknown;
"""

# TS scalar -> the xsd type the TTL declares. Anything else is reported rather than guessed at.
XSD_TYPES = {"string": "xsd:string", "number": "xsd:integer", "boolean": "xsd:boolean"}
# The zod scalar constructors that mark a field as a parameter rather than a read.
ZOD_SCALARS = {"string": "xsd:string", "number": "xsd:integer", "boolean": "xsd:boolean"}


# --------------------------------------------------------------------------- ttl text scanning


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
    """Objects of a repeated-triple predicate: `ont:writes "A.b", "C.d" ;`."""
    match = re.search(rf"{predicate}\s+((?:\"(?:\\.|[^\"])*\"\s*,?\s*)+)", body)
    return re.findall(r"\"((?:\\.|[^\"])*)\"", match.group(1)) if match else []


def first_quoted(body: str, predicate: str) -> str:
    match = re.search(rf"{predicate}\s+\"((?:\\.|[^\"])*)\"", body)
    return match.group(1) if match else ""


def ttl_model(text: str) -> dict:
    """Every subject in the file, plus the coded actions among them."""
    nodes: dict[str, list[str]] = {}
    unterminated: list[str] = []
    for body, terminated in ttl_statements(text):
        subject = subject_of(body)
        if not subject or is_directive(subject):
            continue
        nodes.setdefault(subject, []).append(body[body.index(subject) + len(subject) :])
        if not terminated:
            unterminated.append(subject)
    actions = {}
    for subject, bodies in nodes.items():
        body = "\n".join(bodies)
        if not re.search(r"(?:^|;|\s)a\s+[^;]*\bfno:Function\b", body):
            continue
        if first_quoted(body, "ont:language") != "IMPERATIVE":
            continue
        actions[subject] = parse_action(subject, body, nodes)
    return {"nodes": nodes, "actions": actions, "unterminated": unterminated}


def parse_action(subject: str, body: str, nodes: dict[str, list[str]]) -> dict:
    statements = list_items(body, "ont:statements")
    reads = list_items(body, "ont:reads") or []
    expects = list_items(body, "fno:expects") or []
    read_nodes = {}
    for node in reads:
        node_body = "\n".join(nodes.get(node, []))
        read_nodes[node] = {
            "defined": node in nodes,
            "bindsTo": first_quoted(node_body, "ont:bindsTo"),
            "statement": first_quoted(node_body, "ont:statement"),
        }
    param_nodes = {}
    for node in expects:
        node_body = "\n".join(nodes.get(node, []))
        param_nodes[node] = {
            "defined": node in nodes,
            "paramName": first_quoted(node_body, "ont:paramName"),
        }
    return {
        "subject": subject,
        "name": subject.split(":", 1)[-1],
        "statements": statements,
        "statements_is_list": statements is not None,
        "statements_scalar": first_quoted(body, "ont:statements"),
        "reads": reads,
        "read_nodes": read_nodes,
        "params": param_nodes,
        "writes": quoted_objects(body, "ont:writes"),
        "writes_is_list": list_items(body, "ont:writes") is not None,
        "process": first_quoted(body, r"ont:process(?![A-Za-z])"),
        "processFolderId": first_quoted(body, "ont:processFolderId"),
        "returns": list_items(body, "fno:returns") or [],
    }


def marker_of(action: dict) -> tuple[str, list[str]] | None:
    statements = action["statements"]
    if not statements or len(statements) != 1:
        return None
    match = re.fullmatch(r"func:(\w+)\(([^)]*)\)", statements[0].strip())
    if not match:
        return None
    return match.group(1), [arg.strip() for arg in match.group(2).split(",") if arg.strip()]


# --------------------------------------------------------------------------- job source
# Ported wholesale from the deploy skill's job_source.py: regex, not a TypeScript parser, because
# the job shapes are narrow. Every extraction failure is reported rather than read as "nothing".


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


def interface_field_types(src: str, name: str) -> dict[str, str] | None:
    body = _interface_body(src, name)
    if body is None:
        return None
    types: dict[str, str] = {}
    depth = 0
    for line in body.splitlines():
        if depth == 0:
            field = re.match(r"([A-Za-z_$][\w$]*)\s*\??\s*:\s*(.+?)\s*;?\s*$", line.strip())
            if field:
                types[field.group(1)] = field.group(2).rstrip(";").strip()
        depth += line.count("{") - line.count("}")
    return types


def input_signature(src: str) -> dict:
    """Split `interface Input` into reads and params.

    A read is a field typed as an array of a *named interface*: a read returns rows, and rows are
    objects. "Any array is a read" is wrong; `invoiceIds: string[]` is a parameter and
    `lines: InvoiceLine[]` is a read, and only this distinction separates them.
    """
    types = interface_field_types(src, "Input")
    if types is None:
        return {"args": [], "reads": [], "params": [], "unknown": []}
    reads, params, unknown = [], [], []
    for field, decl in types.items():
        array = decl.endswith("[]")
        base = decl[:-2].strip() if array else decl
        if array and base not in XSD_TYPES:
            reads.append({"bind": field, "row_type": base})
        elif base in XSD_TYPES:
            params.append({"name": field, "xsd": XSD_TYPES[base], "multiple": array})
        else:
            unknown.append({"name": field, "type": decl})
    return {"args": list(types.keys()), "reads": reads, "params": params, "unknown": unknown}


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


# --------------------------------------------------------------------------- zod idiom
# Generated jobs declare their contract with zod (`input: z.object({...}).strict()`); the
# type<T>() idiom above remains understood for existing sources. Same posture as the rest of this
# file: regex plus depth scanning, never a TypeScript parser, and extraction failures are reported
# rather than read as "nothing".


def job_idiom(src: str) -> str:
    """'zod' when the job imports zod, else 'typeT'."""
    return "zod" if re.search(r"from\s+['\"]zod['\"]", src) else "typeT"


def _matching_paren(text: str, open_idx: int) -> int:
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _object_entries(src: str, masked: str, open_idx: int, close_idx: int) -> dict:
    """{key: value expression} for the top level of the object literal at [open_idx, close_idx]."""
    segments, depth, seg_start = [], 0, open_idx + 1
    for i in range(open_idx + 1, close_idx):
        ch = masked[i]
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth -= 1
        elif ch == "," and depth == 0:
            segments.append((seg_start, i))
            seg_start = i + 1
    segments.append((seg_start, close_idx))
    entries = {}
    for a, b in segments:
        match = re.match(r"\s*([A-Za-z_$][\w$]*)\s*:\s*", masked[a:b])
        if match:
            entries[match.group(1)] = src[a + match.end() : b].strip()
    return entries


def _zod_object_of(expr_src: str) -> tuple:
    """(top-level {key: value-expr} of a z.object literal, whether its chain carries .strict()).

    `expr_src` starts at the schema expression: inline after `input:`, or the right-hand side of
    the const declaration the `input:` entry names. Returns (None, None) when no z.object /
    z.strictObject literal starts the expression.
    """
    masked = _mask_ts(expr_src)
    match = re.match(r"\s*z\s*\.\s*(strictObject|object)\s*\(", masked)
    if not match:
        return None, None
    strict = match.group(1) == "strictObject"
    call_open = match.end() - 1
    call_close = _matching_paren(masked, call_open)
    if call_close < 0:
        return None, None
    brace_open = expr_src.find("{", call_open, call_close)
    brace_close = _matching_brace(masked, brace_open) if brace_open >= 0 else -1
    if brace_close < 0 or brace_close > call_close:
        return None, None
    entries = _object_entries(expr_src, masked, brace_open, brace_close)
    # The method chain after the z.object(...) call, up to this expression's own end: a
    # depth-zero `,`, `;` or closing bracket belongs to the surrounding context.
    i, depth, chain = call_close + 1, 0, []
    while i < len(masked):
        ch = masked[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif ch in ",;" and depth == 0:
            break
        chain.append(ch)
        i += 1
    if re.search(r"\.\s*strict\s*\(", "".join(chain)):
        strict = True
    return entries, strict


def _classify_zod_value(value: str) -> tuple:
    """('read'|'param'|'unknown', detail) for one top-level field of the input z.object.

    A read is an array of an object schema, z.array(z.object({...})...) or
    z.array(SomeRowSchemaIdentifier), because a read returns rows and rows are objects. A param
    is a scalar or an array of scalars (z.string(), z.array(z.string()), ...).
    """
    value = value.strip()
    array = re.match(r"z\s*\.\s*array\s*\(", value)
    if array:
        masked = _mask_ts(value)
        close = _matching_paren(masked, array.end() - 1)
        inner = value[array.end() : close].strip() if close > 0 else value[array.end() :].strip()
        scalar = re.match(r"z\s*\.\s*(\w+)\s*\(", inner)
        if scalar and scalar.group(1) in ZOD_SCALARS:
            return "param", (ZOD_SCALARS[scalar.group(1)], True)
        if re.match(r"z\s*\.\s*(strictObject|object)\s*\(", inner):
            return "read", None
        if re.fullmatch(r"[A-Za-z_$][\w$]*", inner):
            return "read", inner
        return "unknown", None
    scalar = re.match(r"z\s*\.\s*(\w+)\s*\(", value)
    if scalar and scalar.group(1) in ZOD_SCALARS:
        return "param", (ZOD_SCALARS[scalar.group(1)], False)
    return "unknown", None


def zod_input(src: str) -> dict:
    """The zod-idiom counterpart of input_signature, plus the strictness of the input object.

    {found, args, reads, params, unknown, strict}. The input schema is the `input:` entry of the
    defineFunction config: an inline z.object({...}) chain, or an identifier whose const
    declaration is then read.
    """
    result = {"found": False, "args": [], "reads": [], "params": [], "unknown": [], "strict": None}
    masked = _mask_ts(src)
    call = re.search(r"\bdefineFunction\s*\(", masked)
    if not call:
        return result
    config_open = masked.find("{", call.end() - 1)
    config_close = _matching_brace(masked, config_open) if config_open >= 0 else -1
    if config_close < 0:
        return result
    expr = (_object_entries(src, masked, config_open, config_close).get("input") or "").strip()
    if not expr:
        return result
    if re.fullmatch(r"[A-Za-z_$][\w$]*", expr):
        decl = re.search(r"\b(?:const|let|var)\s+%s\s*(?::[^=\n]*)?=\s*" % re.escape(expr), masked)
        if not decl:
            return result
        expr = src[decl.end() :]
    fields, strict = _zod_object_of(expr)
    if fields is None:
        return result
    result.update({"found": True, "strict": strict, "args": list(fields)})
    for field, value in fields.items():
        kind, detail = _classify_zod_value(value)
        if kind == "read":
            result["reads"].append({"bind": field, "row_type": detail})
        elif kind == "param":
            result["params"].append({"name": field, "xsd": detail[0], "multiple": detail[1]})
        else:
            result["unknown"].append({"name": field, "type": value})
    return result


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


# --------------------------------------------------------------------------- schema


def schema_terms(schema_text: str) -> tuple[set[str], set[str]]:
    classes = set(re.findall(r"Declaration\(Class\(:([\w.-]+)\)\)", schema_text))
    data_props = set(re.findall(r"Declaration\(DataProperty\(:([\w.-]+)\)\)", schema_text))
    return classes, data_props


# --------------------------------------------------------------------------- gate bookkeeping


class GateLog:
    def __init__(self) -> None:
        self.entries: dict[str, list[tuple[str, str]]] = {gate: [] for gate in GATES}

    def add(self, gate: str, status: str, diagnostic: str = "") -> None:
        self.entries[gate].append((status, diagnostic))

    def results(self) -> list[dict]:
        results = []
        for gate in GATES:
            entries = self.entries[gate]
            statuses = {status for status, _ in entries}
            if "failed" in statuses:
                status = "failed"
            elif "passed" in statuses:
                status = "passed"
            else:
                status = "skipped"
            diagnostics = [
                detail if entry_status == "failed" else f"skipped: {detail}"
                for entry_status, detail in entries
                if entry_status in ("failed", "skipped") and detail
            ]
            results.append(
                {
                    "id": gate,
                    "status": status,
                    "passed": None if status == "skipped" else status == "passed",
                    "diagnostics": diagnostics,
                }
            )
        return results

    def errors(self) -> dict[str, list[str]]:
        return {
            gate: [detail for status, detail in self.entries[gate] if status == "failed"]
            for gate in GATES
            if any(status == "failed" for status, _ in self.entries[gate])
        }


# --------------------------------------------------------------------------- typecheck


def find_tsc(workdir: Path) -> tuple[list[str] | None, str]:
    candidates: list[list[str]] = []
    override = os.environ.get("CODED_ACTION_TSC")
    if override:
        candidates.append([override])
    on_path = shutil.which("tsc")
    if on_path:
        candidates.append([on_path])
    for parent in [workdir.resolve(), *workdir.resolve().parents]:
        local = parent / "node_modules" / ".bin" / "tsc"
        if local.is_file():
            candidates.append([str(local)])
    candidates.append(["npx", "--no-install", "tsc"])
    for command in candidates:
        try:
            proc = subprocess.run(command + ["--version"], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError):
            continue
        # The npm package literally named `tsc` is not the compiler and answers --version happily,
        # so the banner is checked rather than the exit code.
        if re.search(r"Version \d+\.\d+", proc.stdout):
            return command, ""
    return None, "no TypeScript compiler found (tried CODED_ACTION_TSC, PATH, node_modules/.bin, npx --no-install)"


def find_zod(workdir: Path) -> Path | None:
    """A real zod package near the workdir, for typechecking jobs that import it."""
    for parent in [workdir.resolve(), *workdir.resolve().parents]:
        candidate = parent / "node_modules" / "zod"
        if (candidate / "package.json").is_file():
            return candidate
    return None


def typecheck_job(job: Path, workdir: Path, idiom: str) -> tuple[str, str]:
    """('passed'|'failed'|'skipped', detail) for one TypeScript job, compiled against an SDK stub.

    A zod-idiom job imports zod for real, so the check needs the actual package; when it is not
    resolvable the gate is skipped rather than failed, since the miss says nothing about the job.
    """
    zod_dir = None
    if idiom == "zod":
        zod_dir = find_zod(workdir)
        if zod_dir is None:
            return "skipped", "zod not installed (the job imports 'zod'; no node_modules/zod found from the workdir upward)"
    command, reason = find_tsc(workdir)
    if command is None:
        return "skipped", reason
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stub = root / "node_modules" / SDK_MODULE
        stub.mkdir(parents=True)
        (stub / "index.d.ts").write_text(SDK_STUB_ZOD if idiom == "zod" else SDK_STUB, encoding="utf-8")
        (stub / "package.json").write_text(
            json.dumps({"name": SDK_MODULE, "version": "0.0.0", "types": "index.d.ts"}), encoding="utf-8"
        )
        if zod_dir is not None:
            os.symlink(zod_dir, root / "node_modules" / "zod")
        copy = root / job.name
        copy.write_text(job.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            proc = subprocess.run(
                command + list(TSC_FLAGS) + [copy.name], capture_output=True, text=True, timeout=300, cwd=root
            )
        except (OSError, subprocess.SubprocessError) as error:
            return "skipped", f"could not run the compiler: {error}"
        if proc.returncode == 0:
            return "passed", ""
        lines = [line.strip() for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
        return "failed", "; ".join(lines[:3]) or f"tsc exited {proc.returncode} with no output"


# --------------------------------------------------------------------------- discovery


def discover(workdir: Path, ontology: str, wanted: list[str]) -> tuple[list[dict], list[str], list[str]]:
    """Coded-action pairs in `workdir`, plus the TTL files that are not coded actions."""
    pairs: list[dict] = []
    other: list[str] = []
    errors: list[str] = []
    jobs_dir = workdir / "jobs"
    for path in sorted(workdir.glob(f"{ontology}-*.ttl")):
        action = path.name[len(ontology) + 1 : -len(".ttl")]
        if wanted and action not in wanted:
            continue
        text = path.read_text(encoding="utf-8")
        model = ttl_model(text)
        if not model["actions"]:
            other.append(path.name)
            continue
        jobs = sorted(p for p in jobs_dir.glob(f"{action}.*") if p.is_file() and p.stem == action)
        pairs.append({"action": action, "ttl": path, "model": model, "jobs": jobs})
    found = {pair["action"] for pair in pairs}
    errors.extend(
        f"--action {action}: no {ontology}-{action}.ttl declaring ont:language \"IMPERATIVE\" in {workdir}"
        for action in wanted
        if action not in found
    )
    if not wanted and not pairs:
        errors.append(f"no coded-action pairs found: no {ontology}-*.ttl declares ont:language \"IMPERATIVE\"")
    return pairs, other, errors


# --------------------------------------------------------------------------- gates


def check_ttl(log: GateLog, name: str, pair: dict) -> dict | None:
    """The ported ttl_actions validate rules that text can check. Returns the action, or None."""
    model = pair["model"]
    failures = [f"{name}: statement for {subject} is not terminated with '.'" for subject in model["unterminated"]]
    for subject, bodies in model["nodes"].items():
        if len(bodies) > 1:
            failures.append(
                f"{name}: subject '{subject}' is defined {len(bodies)} times; RDF merges these, so "
                f"ont:writes becomes the union of both and ont:process becomes ambiguous"
            )
    action = next(
        (candidate for candidate in model["actions"].values() if candidate["name"] == name),
        None,
    )
    if action is None:
        others = ", ".join(sorted(model["actions"])) or "none"
        failures.append(f"{name}: no fno:Function named '{name}' with ont:language \"IMPERATIVE\" (found: {others})")
        for failure in failures:
            log.add("ttl-parses-and-well-formed", "failed", failure)
        return None

    if not action["statements_is_list"]:
        failures.append(
            f"{name}: ont:statements must be an RDF list ( \"func:...\" ), found a plain string "
            f"{action['statements_scalar']!r}"
        )
    elif len(action["statements"]) != 1:
        failures.append(f"{name}: expected exactly one func: marker, found {len(action['statements'])}")
    elif marker_of(action) is None:
        failures.append(f"{name}: statement is not a func:name(args) marker: {action['statements'][0]!r}")

    for node, read in action["read_nodes"].items():
        if not read["defined"]:
            failures.append(f"{name}: ont:reads names {node}, which no statement in the file defines")
        elif not read["bindsTo"]:
            failures.append(f"{name}: read '{node}' has no ont:bindsTo")
        elif not read["statement"]:
            failures.append(f"{name}: read '{read['bindsTo']}' has no ont:statement")
    for node, param in action["params"].items():
        if not param["defined"]:
            failures.append(f"{name}: fno:expects names {node}, which no statement in the file defines")
        elif not param["paramName"]:
            failures.append(f"{name}: parameter '{node}' has no ont:paramName")

    if not action["process"]:
        failures.append(f"{name}: coded action declares no ont:process")
    if action["writes_is_list"]:
        failures.append(
            f"{name}: ont:writes is written as an RDF list; it must be repeated triples "
            f"(ont:writes \"A.b\", \"C.d\"), or the runtime sees zero writable targets"
        )
    elif not action["writes"]:
        failures.append(f"{name}: declares no ont:writes; every edit its job returns would be rejected")

    for failure in failures:
        log.add("ttl-parses-and-well-formed", "failed", failure)
    if not failures:
        log.add("ttl-parses-and-well-formed", "passed")
    return action


def check_signature(log: GateLog, name: str, action: dict) -> list[str] | None:
    marker = marker_of(action)
    if marker is None:
        log.add("signature-resolves", "skipped", f"{name}: no single well-formed func: marker to resolve against")
        return None
    marker_args = marker[1]
    params = [param["paramName"] for param in action["params"].values() if param["paramName"]]
    binds = [read["bindsTo"] for read in action["read_nodes"].values() if read["bindsTo"]]
    declared = set(params) | set(binds)
    unresolved = [arg for arg in marker_args if arg not in declared]
    unnamed = [bind for bind in binds if bind not in marker_args]
    if unresolved or unnamed:
        parts = []
        if unresolved:
            parts.append(f"arguments naming neither a parameter nor a read: {unresolved}")
        if unnamed:
            parts.append(f"reads the marker never names (fetched then discarded): {unnamed}")
        log.add("signature-resolves", "failed", f"{name}: " + "; ".join(parts))
    else:
        log.add("signature-resolves", "passed")
    return marker_args


def check_input(log: GateLog, name: str, marker_args: list[str], fields: list[str] | None, missing_msg: str) -> None:
    if fields is None:
        log.add("input-matches-marker", "failed", f"{name}: {missing_msg}")
        return
    missing = [arg for arg in marker_args if arg not in fields]
    extra = [field for field in fields if field not in marker_args]
    if missing or extra:
        detail = []
        if missing:
            detail.append(f"marker declares {missing}, absent from Input")
        if extra:
            detail.append(
                f"Input declares {extra}, which the marker never sends; the SDK validates with "
                f"additionalProperties:false, so the job faults before the handler runs"
            )
        log.add("input-matches-marker", "failed", f"{name}: " + "; ".join(detail))
    else:
        log.add("input-matches-marker", "passed")


def check_strictness(log: GateLog, name: str, idiom: str, zod: dict | None,
                     warnings: list[str], job_path=None) -> None:
    """input-strictness: additionalProperties:false is what faults a drifted Input before the
    handler runs, so every contract has to end up carrying it.

    A type<T>() contract is inert on its own; the manifest is derived from its interfaces at stage
    time, and that derivation is what supplies additionalProperties:false. Running the deriver
    here is therefore the real check: it fails on exactly the contracts that could not produce a
    manifest, and a job that cannot be lowered would otherwise fail at pack time with nothing
    written. A zod contract carries its own schema and needs .strict() on the top-level object.
    """
    if idiom == "zod":
        if zod is None or not zod["found"]:
            log.add("input-strictness", "skipped", f"{name}: no z.object input schema to check")
        elif zod["strict"]:
            log.add("input-strictness", "passed")
        else:
            log.add(
                "input-strictness",
                "failed",
                f"{name}: the top-level input z.object does not carry .strict(); .strict() is "
                f"what emits additionalProperties:false, which faults a drifted Input before the "
                f"handler runs, and a bare z.object() packs without it",
            )
        return

    module = _entry_points_module()
    if module is None:
        log.add("input-strictness", "skipped",
                f"{name}: tools/entry_points.py not found, cannot lower the type<T>() contract")
        return
    try:
        input_schema, _ = module.derive(job_path)
    except Exception as exc:
        log.add("input-strictness", "failed",
                f"{name}: the type<T>() contract cannot be lowered to a manifest, so the deploy "
                f"step could not derive entry-points.json and pack would fail: {exc}")
        return
    if input_schema.get("additionalProperties") is False:
        log.add("input-strictness", "passed")
    else:
        log.add("input-strictness", "failed",
                f"{name}: the derived input schema does not carry additionalProperties:false, so "
                f"a drifted Input would reach the handler instead of faulting")


_ENTRY_POINTS_CACHE: list = []


def _entry_points_module():
    """Load tools/entry_points.py, the shared contract deriver, or None when it is absent."""
    if _ENTRY_POINTS_CACHE:
        return _ENTRY_POINTS_CACHE[0]
    import importlib.util
    override = os.environ.get("ENTRY_POINTS_TOOL")
    candidates = [pathlib.Path(override)] if override else [
        pathlib.Path(__file__).resolve().parent / "entry_points.py"]
    found = next((c for c in candidates if c.is_file()), None)
    module = None
    if found:
        spec = importlib.util.spec_from_file_location("ontology_entry_points", found)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    _ENTRY_POINTS_CACHE.append(module)
    return module


def check_writes(log: GateLog, name: str, action: dict, edits: dict) -> None:
    writes = set(action["writes"])
    if edits["unresolved"]:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: could not trace the properties of the edit(s) on "
            + ", ".join(edits["unresolved"])
            + "; the edit shape is one this checker does not recognise, so verify by hand",
        )
        return
    if not edits["pairs"]:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: found no written properties in the job; either it never writes, or the edit "
            f"shape is one this checker does not recognise, so verify by hand",
        )
        return
    undeclared = sorted(
        f"{entity}.{key}"
        for entity, key in edits["pairs"]
        if entity not in writes and f"{entity}.{key}" not in writes
    )
    if undeclared:
        log.add(
            "writes-cover-edits",
            "failed",
            f"{name}: the job writes {undeclared} which ont:writes does not cover ({sorted(writes)}); "
            f"the runtime refuses these at 'Preparing write statement' with SQL_GUARD_REJECTED, "
            f"after the job has already run",
        )
    else:
        log.add("writes-cover-edits", "passed")


def check_fields(
    log: GateLog, name: str, action: dict, edits: dict | None, schema: tuple[set[str], set[str]] | None, reason: str
) -> None:
    if schema is None:
        log.add("fields-exist-in-schema", "skipped", f"{name}: {reason}")
        return
    classes, data_props = schema
    wanted = set(action["writes"])
    for read in action["read_nodes"].values():
        wanted.update(re.findall(r"\{\{([^}]+)\}\}", read["statement"]))
    if edits is not None:
        wanted.update(f"{entity}.{key}" for entity, key in edits["pairs"])
    unknown = []
    for entry in sorted(wanted):
        entity, _, field = entry.partition(".")
        if entity not in classes:
            unknown.append(f"{entry} (no such entity)")
        elif field and entry not in data_props:
            unknown.append(f"{entry} (no such field)")
    if unknown:
        log.add(
            "fields-exist-in-schema",
            "failed",
            f"{name}: not declared in the schema: {unknown}; a field named in the TTL or written by "
            f"the job but absent from the .ofn looks fine locally and fails at write time",
        )
    else:
        log.add("fields-exist-in-schema", "passed")


def check_folder_id(log: GateLog, name: str, action: dict) -> tuple[bool, str]:
    folder = action["processFolderId"]
    log.add("folder-id-status", "passed")
    if folder == PENDING_DEPLOY:
        return False, f"{name}: ont:processFolderId is the {PENDING_DEPLOY} placeholder; publish first, then patch it"
    if folder.isdigit():
        return True, f"{name}: ont:processFolderId is {folder}"
    if not folder:
        return False, f"{name}: no ont:processFolderId; the service-wide fallback applies, which is rarely wanted"
    return False, f"{name}: ont:processFolderId {folder!r} is neither numeric nor {PENDING_DEPLOY}"


def check_job_language(log: GateLog, name: str, jobs: list[Path]) -> tuple[str, Path | None]:
    if not jobs:
        log.add(
            "job-language",
            "failed",
            f"{name}: no job file at jobs/{name}.* ; a coded action is a TTL plus a job, and the "
            f"TTL alone deploys an action whose process has nothing to run",
        )
        return "", None
    if len(jobs) > 1:
        log.add(
            "job-language",
            "failed",
            f"{name}: {len(jobs)} job files match jobs/{name}.* ({[job.name for job in jobs]}); "
            f"exactly one job implements an action",
        )
        return "", None
    job = jobs[0]
    language = JOB_LANGUAGES.get(job.suffix.lower(), job.suffix.lstrip(".").lower() or "unknown")
    if language not in SUPPORTED_JOB_LANGUAGES:
        log.add(
            "job-language",
            "failed",
            f"{name}: job {job.name} is {language}; supported languages: {', '.join(SUPPORTED_JOB_LANGUAGES)}",
        )
        return language, job
    log.add("job-language", "passed")
    return language, job


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--ontology-name", required=True)
    parser.add_argument("--action", action="append", default=[], help="check only this action; repeatable")
    parser.add_argument("--skip-typecheck", action="store_true")
    args = parser.parse_args(argv)

    log = GateLog()
    warnings: list[str] = []
    pairs, other, discovery_errors = discover(args.workdir, args.ontology_name, args.action)

    schema_path = args.workdir / f"{args.ontology_name}.ofn"
    if schema_path.is_file():
        schema = schema_terms(schema_path.read_text(encoding="utf-8"))
        schema_reason = ""
    else:
        schema = None
        schema_reason = f"no schema at {schema_path.name}; entity and field existence cannot be resolved offline"

    reported: list[dict] = []
    for pair in pairs:
        name = pair["action"]
        action = check_ttl(log, name, pair)
        language, job = check_job_language(log, name, pair["jobs"])

        src, edits, idiom, zod = None, None, None, None
        if job is not None and language in SUPPORTED_JOB_LANGUAGES:
            src = job.read_text(encoding="utf-8")
            edits = written_edits(src)
            idiom = job_idiom(src)
            zod = zod_input(src) if idiom == "zod" else None

        marker_args = check_signature(log, name, action) if action else None
        if action is None:
            for gate in ("input-matches-marker", "input-strictness", "writes-cover-edits", "fields-exist-in-schema"):
                log.add(gate, "skipped", f"{name}: the action could not be read from the TTL")
            reported.append(
                {
                    "action": name,
                    "ttl": pair["ttl"].name,
                    "job": job.name if job else None,
                    "job_language": language or None,
                    "process": None,
                    "process_folder_id": None,
                    "deployable": False,
                }
            )
            continue

        job_reason = (
            f"{name}: no job source to read"
            if src is None and job is None
            else f"{name}: job source gates read {', '.join(SUPPORTED_JOB_LANGUAGES)} only, this job is {language}"
        )
        if src is None:
            log.add("input-matches-marker", "skipped", job_reason)
            log.add("input-strictness", "skipped", job_reason)
            log.add("writes-cover-edits", "skipped", job_reason)
            warnings.append(f"{name}: fields-exist-in-schema covered the TTL only; the job's edits were not read")
        else:
            if idiom == "zod":
                fields = zod["args"] if zod["found"] else None
                missing_msg = (
                    "could not find the z.object input schema in the job "
                    "(an inline z.object after `input:`, or a const the `input:` entry names)"
                )
            else:
                fields = interface_fields(src, "Input")
                missing_msg = "could not find `interface Input { ... }` in the job"
            if marker_args is None:
                log.add("input-matches-marker", "skipped", f"{name}: no marker arguments to compare Input against")
            else:
                check_input(log, name, marker_args, fields, missing_msg)
            check_strictness(log, name, idiom, zod, warnings, job)
            check_writes(log, name, action, edits)

        check_fields(log, name, action, edits, schema, schema_reason)
        deployable, folder_detail = check_folder_id(log, name, action)
        warnings.append(folder_detail)

        if args.skip_typecheck:
            log.add("typecheck", "skipped", f"{name}: --skip-typecheck")
        elif language != "typescript" or job is None:
            log.add("typecheck", "skipped", f"{name}: typecheck applies to typescript jobs only")
        else:
            status, detail = typecheck_job(job, args.workdir, idiom)
            log.add("typecheck", status, f"{name}: {detail}" if detail else "")

        reported.append(
            {
                "action": name,
                "ttl": pair["ttl"].name,
                "job": job.name if job else None,
                "job_language": language or None,
                "process": action["process"],
                "process_folder_id": action["processFolderId"],
                "deployable": deployable,
            }
        )

    results = log.results()
    errors = log.errors()
    if discovery_errors:
        errors["discovery"] = discovery_errors
    failed = discovery_errors or [item for item in results if item["status"] == "failed"]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "gate_results": results,
        "artifact_inventory": {
            "actions": [pair["ttl"].name for pair in pairs],
            "jobs": [entry["job"] for entry in reported if entry["job"]],
            "schema": [schema_path.name] if schema is not None else [],
            "other": other,
        },
        "pairs": reported,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
