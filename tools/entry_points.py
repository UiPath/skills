#!/usr/bin/env python3
"""Lower a coded-action job's TypeScript contract into a Functions entry-points manifest.

Why this exists: `type<T>()` is inert at runtime by design, and something has to turn it into the
JSON Schema the platform validates against. Studio Web's packer carries that derivation walker;
`uip functions pack` does not, and fails outright on the idiom. Deriving the manifest here keeps
the interfaces as the single source of truth and keeps the pipeline on `uip solution pack` alone,
which only zips a directory and reads no TypeScript.

The lowering matches what Studio Web produced for the verified support job, byte for byte. Only
the constrained grammar the contract guide mandates is accepted; anything else fails loudly rather
than being guessed at, because a wrong manifest faults the job before its handler runs.

    python3 tools/entry_points.py JOB.ts                       # print the manifest
    python3 tools/entry_points.py JOB.ts --out entry-points.json
    python3 tools/entry_points.py JOB.ts --check entry-points.json   # compare, exit 1 on drift

Exit codes: 0 ok, 1 unlowerable contract or drift, 2 bad usage.
"""

import argparse
import json
import pathlib
import re
import sys
import uuid

SCHEMA_URL = "https://cloud.uipath.com/draft/2024-12/entry-point"
SCALARS = {"string": "string", "number": "number", "boolean": "boolean"}
INDEX_SIGNATURE = re.compile(r"^\[\s*\w+\s*:\s*string\s*\]\s*:")
FIELD = re.compile(r"^(?P<name>[A-Za-z_$][\w$]*)\s*(?P<opt>\?)?\s*:\s*(?P<type>.+?)\s*;?$")
RECORD_ANY = re.compile(r"^Record<\s*string\s*,\s*(unknown|any)\s*>$")
STRING_UNION = re.compile(r"^'[^']*'(\s*\|\s*'[^']*')*$")


class Unlowerable(Exception):
    pass


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//[^\n]*", "", src)


def parse_interfaces(src):
    """Return {name: {"fields": [(name, type, optional)], "open": bool}}.

    `open` records an index signature, which is what lowers to a permissive
    `additionalProperties`. Read rows need it: reads are `SELECT *`, so a row carries columns the
    job never declared.
    """
    out = {}
    for match in re.finditer(r"\binterface\s+([A-Za-z_$][\w$]*)\s*\{", src):
        name, start = match.group(1), match.end()
        depth, i = 1, start
        while i < len(src) and depth:
            depth += {"{": 1, "}": -1}.get(src[i], 0)
            i += 1
        if depth:
            raise Unlowerable("interface %s is not closed" % name)
        fields, open_obj = [], False
        for line in (l.strip() for l in src[start:i - 1].split("\n")):
            if not line:
                continue
            if INDEX_SIGNATURE.match(line):
                open_obj = True
                continue
            found = FIELD.match(line)
            if not found:
                raise Unlowerable("cannot read field %r in interface %s" % (line, name))
            fields.append((found.group("name"), found.group("type").strip(),
                           bool(found.group("opt"))))
        out[name] = {"fields": fields, "open": open_obj}
    return out


def lower_type(spec, interfaces, stack):
    if spec in SCALARS:
        return {"type": SCALARS[spec]}
    if RECORD_ANY.match(spec):
        # A free-form bag. Studio Web lowers this to an object with a permissive
        # additionalProperties and no declared properties.
        return {"type": "object", "additionalProperties": {}}
    if STRING_UNION.match(spec):
        return {"type": "string", "enum": re.findall(r"'([^']*)'", spec)}
    if spec.endswith("[]"):
        return {"type": "array", "items": lower_type(spec[:-2].strip(), interfaces, stack)}
    if spec.startswith("Array<") and spec.endswith(">"):
        return {"type": "array", "items": lower_type(spec[6:-1].strip(), interfaces, stack)}
    if spec in interfaces:
        return lower_interface(spec, interfaces, stack)
    raise Unlowerable(
        "cannot lower type %r. The contract grammar is string, number, boolean, a union of "
        "string literals, Record<string, unknown>, an array of any of those, or a named "
        "interface declared in the same file." % spec)


def lower_interface(name, interfaces, stack):
    if name in stack:
        raise Unlowerable("interface %s is recursive; the manifest cannot express that" % name)
    shape = interfaces[name]
    properties, required = {}, []
    for field, spec, optional in shape["fields"]:
        properties[field] = lower_type(spec, interfaces, stack + [name])
        if not optional:
            required.append(field)
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    # An index signature means "and whatever else the source returns"; its absence means the
    # object is closed, and the platform faults a drifted payload before the handler runs.
    schema["additionalProperties"] = {} if shape["open"] else False
    return schema


def contract_roots(src):
    """The interface names behind `input: type<X>()` and `output: type<Y>()`."""
    roots = {}
    for slot in ("input", "output"):
        found = re.search(r"\b%s\s*:\s*type\s*<\s*([A-Za-z_$][\w$]*)\s*>\s*\(\s*\)" % slot, src)
        if found:
            roots[slot] = found.group(1)
    return roots


def derive(job_path):
    """Return (input_schema, output_schema) for a job that declares its contract with type<T>()."""
    src = strip_comments(pathlib.Path(job_path).read_text())
    roots = contract_roots(src)
    missing = [s for s in ("input", "output") if s not in roots]
    if missing:
        raise Unlowerable(
            "no type<T>() contract found for: %s. This deriver reads the type<T>() idiom; a job "
            "declaring its contract another way already carries a schema the platform can read "
            "and does not need one derived." % ", ".join(missing))
    interfaces = parse_interfaces(src)
    for slot, name in roots.items():
        if name not in interfaces:
            raise Unlowerable("%s: type<%s>() names no interface in this file" % (slot, name))
    return (lower_interface(roots["input"], interfaces, []),
            lower_interface(roots["output"], interfaces, []))


def manifest(job_path, existing=None, file_path="content/main.ts"):
    """Build the manifest, preserving only an existing entry point's identity.

    `uniqueId` is referenced by the project's bindings, so regenerating must keep it; a fresh
    project has none and gets one minted.

    `filePath` is NOT inherited. It names the file that was just staged, so the caller's value has
    to win: an older manifest may name a path from a previous layout, and silently keeping it
    would point the entry point at a file the package does not contain.
    """
    input_schema, output_schema = derive(job_path)
    entry = {"filePath": file_path, "uniqueId": str(uuid.uuid4()), "type": "function"}
    if existing:
        for point in existing.get("entryPoints") or []:
            entry["uniqueId"] = point.get("uniqueId", entry["uniqueId"])
            break
    entry["input"] = input_schema
    entry["output"] = output_schema
    return {"$schema": SCHEMA_URL, "$id": "entry-points.json", "entryPoints": [entry]}


def schemas_of(doc):
    points = doc.get("entryPoints") or []
    if not points:
        return None, None
    return points[0].get("input"), points[0].get("output")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("job", help="the job's .ts source")
    parser.add_argument("--out", help="write the manifest here instead of printing it")
    parser.add_argument("--check", metavar="MANIFEST",
                        help="compare against an existing manifest; exit 1 on drift")
    parser.add_argument("--file-path", default="content/main.ts",
                        help="entry point filePath (default: content/main.ts)")
    args = parser.parse_args(argv)

    job = pathlib.Path(args.job)
    if not job.is_file():
        print(json.dumps({"ok": False, "error": "job not found: %s" % job}), file=sys.stderr)
        return 2

    if args.check:
        target = pathlib.Path(args.check)
        if not target.is_file():
            print(json.dumps({"ok": False, "error": "manifest not found: %s" % target}),
                  file=sys.stderr)
            return 1
        try:
            want_in, want_out = derive(job)
        except Unlowerable as exc:
            print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
            return 1
        got_in, got_out = schemas_of(json.loads(target.read_text()))
        drift = [slot for slot, want, got in (("input", want_in, got_in),
                                              ("output", want_out, got_out)) if want != got]
        if drift:
            print(json.dumps({"ok": False, "drift": drift,
                              "error": "the manifest disagrees with the job's interfaces (%s). "
                                       "Regenerate it: the interfaces are the contract."
                                       % ", ".join(drift)}, indent=2), file=sys.stderr)
            return 1
        print(json.dumps({"ok": True, "checked": str(target)}))
        return 0

    existing = None
    if args.out and pathlib.Path(args.out).is_file():
        existing = json.loads(pathlib.Path(args.out).read_text())
    try:
        doc = manifest(job, existing, args.file_path)
    except Unlowerable as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1
    text = json.dumps(doc, indent=2) + "\n"
    if args.out:
        pathlib.Path(args.out).write_text(text)
        print(json.dumps({"ok": True, "wrote": args.out,
                          "uniqueId": doc["entryPoints"][0]["uniqueId"]}))
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
