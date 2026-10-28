#!/usr/bin/env python3
"""Check migration trace integrity, not behavior or source-inventory completeness.

Use --help for inputs. Inventories and traces are data: no framework code, model,
project configuration or referenced executable is loaded. Exit 0 means references
are current and all INVENTORIED items have a disposition; unresolved items exit 1.
The source reader and project owner must independently establish inventory scope.
Contract: references/migration-trace-guide.md.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import xml.etree.ElementTree as ET


MAX_FILES = 20000
MAX_BYTES = 512 * 1024 * 1024
MAX_PARSE_BYTES = 16 * 1024 * 1024
MAX_ITEMS = 100000
GENERATED = {".git", ".local", ".vs", "bin", "obj", "node_modules", ".venv"}
STATUSES = {"mapped", "changed", "omitted", "excluded", "unresolved", "structural", "added"}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def string(value):
    return isinstance(value, str) and bool(value.strip())


def fields(value, required, optional=()):
    require(isinstance(value, dict), "expected an object")
    require(set(required) <= value.keys(), "missing fields: " + str(set(required) - value.keys()))
    require(value.keys() <= set(required) | set(optional), "unknown fields: " + str(value.keys() - set(required) - set(optional)))


def sequence(value, label, nonempty=False):
    require(isinstance(value, list), label + " must be an array")
    require(len(value) <= MAX_ITEMS and (value or not nonempty), label + " is empty or exceeds limit")
    return value


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def json_bytes(raw):
    require(len(raw) <= MAX_PARSE_BYTES, "JSON exceeds parse limit")
    return json.loads(raw, object_pairs_hook=no_duplicate_keys, parse_constant=invalid_constant)


def invalid_constant(value):
    raise Invalid("non-finite JSON number: " + value)


def relative(value):
    require(string(value) and "\\" not in value and ":" not in value, "expected a portable relative path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in {".", "..", ""} for p in value.split("/")), "unsafe path: " + value)
    return path


def beneath(root, value):
    rel = relative(value)
    current = root
    for part in rel.parts:
        current = current / part
        require(not current.is_symlink(), "symlink not allowed: " + value)
    require(current.resolve().is_relative_to(root), "path escapes root: " + value)
    return current


class Inputs:
    def __init__(self):
        self.bytes = 0
        self.files = 0
        self.cache = {}

    def read(self, path):
        if path not in self.cache:
            require(path.is_file() and not path.is_symlink(), "missing file or symlink: " + str(path))
            size = path.stat().st_size
            require(self.files < MAX_FILES and self.bytes + size <= MAX_BYTES, "input budget exceeded")
            # A bounded read also catches files that grow after stat().
            with path.open("rb") as handle:
                raw = handle.read(min(MAX_BYTES - self.bytes, 64 * 1024 * 1024) + 1)
            require(len(raw) == size and len(raw) <= 64 * 1024 * 1024, "file changed during read or exceeds file limit")
            self.files += 1
            self.bytes += len(raw)
            self.cache[path] = raw
        return self.cache[path]

    def json(self, path):
        return json_bytes(self.read(path))


def file_set(root, projects=None):
    found = set()
    seen = 0
    starts = [beneath(root, p) for p in projects] if projects else [root]
    require(not any(a != b and a.is_relative_to(b) for a in starts for b in starts), "overlapping project scopes")
    for start in starts:
        require(start.is_dir(), "missing input directory: " + str(start))
        pending = [start]
        while pending:
            directory = pending.pop()
            for child in directory.iterdir():
                seen += 1
                require(seen <= MAX_ITEMS, "directory enumeration limit exceeded")
                require(not child.is_symlink(), "symlink in artifact tree: " + str(child))
                if child.is_dir():
                    if projects is None or child.name not in GENERATED:
                        pending.append(child)
                else:
                    require(child.is_file(), "non-regular artifact: " + str(child))
                    key = child.relative_to(root).as_posix()
                    require(key not in found, "overlapping project scopes: " + key)
                    found.add(key)
                    require(len(found) <= MAX_FILES, "artifact count limit exceeded")
    return found


def artifacts(rows, root, actual, inputs):
    result = {}
    for row in sequence(rows, "artifacts", nonempty=True):
        fields(row, ("path", "sha256"))
        path = str(relative(row["path"]))
        require(path not in result, "duplicate artifact: " + path)
        require(isinstance(row["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]), "invalid SHA-256")
        raw = inputs.read(beneath(root, path))
        require(digest(raw) == row["sha256"], "stale artifact: " + path)
        result[path] = raw
    require(set(result) == actual, "artifact inventory differs from disk; missing=" + str(sorted(actual - result.keys())) + "; extra=" + str(sorted(result.keys() - actual)))
    return result


def locate(raw, locator, parsed):
    require(isinstance(locator, dict), "locator must be an object")
    kind = locator.get("kind")
    require(len(raw) <= MAX_PARSE_BYTES, "referenced artifact exceeds parse limit")
    if kind == "xml":
        fields(locator, ("kind", "path", "tag", "attributes"))
        require(b"<!DOCTYPE" not in raw.replace(b"\x00", b"").upper(), "XML DTD is not supported")
        key = (id(raw), kind)
        if key not in parsed:
            root = ET.fromstring(raw)
            require(sum(1 for _ in root.iter()) <= MAX_ITEMS, "XML node limit exceeded")
            parsed[key] = root
        node = parsed[key]
        for index in sequence(locator["path"], "XML path"):
            require(type(index) is int and index >= 0 and index < len(node), "XML path does not resolve")
            node = node[index]
        require(string(locator["tag"]) and node.tag == locator["tag"], "XML tag does not match")
        attrs = locator["attributes"]
        require(isinstance(attrs, dict) and all(string(k) and isinstance(v, str) for k, v in attrs.items()), "invalid XML attribute guards")
        require(all(node.get(k) == v for k, v in attrs.items()), "XML identity guard does not match")
    elif kind == "json":
        fields(locator, ("kind", "pointer"))
        pointer = locator["pointer"]
        require(isinstance(pointer, str) and (pointer == "" or pointer.startswith("/")), "invalid JSON pointer")
        key = (id(raw), kind)
        if key not in parsed:
            parsed[key] = json_bytes(raw)
        node = parsed[key]
        for token in pointer.split("/")[1:]:
            require(not re.search(r"~(?![01])", token), "invalid JSON pointer escape")
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(node, list):
                require(re.fullmatch(r"0|[1-9][0-9]*", token) and len(token) <= 9, "invalid JSON array index")
                require(int(token) < len(node), "JSON pointer does not resolve")
                node = node[int(token)]
            else:
                require(isinstance(node, dict) and token in node, "JSON pointer does not resolve")
                node = node[token]
    elif kind == "text":
        fields(locator, ("kind", "start", "end", "sha256"), ("symbol",))
        start, end = locator["start"], locator["end"]
        require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw), "invalid text byte range")
        require(digest(raw[start:end]) == locator["sha256"], "text range hash does not match")
        require("symbol" not in locator or string(locator["symbol"]), "invalid symbol label")
    else:
        raise Invalid("unsupported locator kind: " + str(kind))


def validate(inventory_path, trace_path, source_root, target_root, projects, solution_files=()):
    inputs = Inputs()
    inventory_raw = inputs.read(inventory_path)
    inventory = json_bytes(inventory_raw)
    trace = inputs.json(trace_path)
    fields(inventory, ("version", "framework", "scope", "artifacts", "items"))
    fields(trace, ("version", "sourceInventorySha256", "targetArtifacts", "fragments"))
    require(type(inventory["version"]) is int and inventory["version"] == 1 and type(trace["version"]) is int and trace["version"] == 1, "unsupported version")
    require(string(inventory["framework"]) and string(inventory["scope"]), "framework and scope are required")
    require(trace["sourceInventorySha256"] == digest(inventory_raw), "source inventory changed")
    source_files = artifacts(inventory["artifacts"], source_root, file_set(source_root), inputs)
    target_paths = file_set(target_root, projects)
    for path in solution_files:
        require(path not in target_paths, "duplicate target scope: " + path)
        require(beneath(target_root, path).is_file(), "missing solution file: " + path)
        target_paths.add(path)
    target_files = artifacts(trace["targetArtifacts"], target_root, target_paths, inputs)
    items = {}
    parsed = {}
    identities = set()
    positions = set()
    for item in sequence(inventory["items"], "source items", nonempty=True):
        fields(item, ("id", "identity", "artifact", "kind", "locator"))
        require(string(item["id"]) and item["id"] not in items, "duplicate or empty source item id")
        identity = tuple(sequence(item["identity"], "scoped native identity", nonempty=True))
        require(all(string(x) for x in identity), "invalid native identity")
        key = (item["artifact"], identity)
        require(key not in identities, "duplicate scoped source identity")
        identities.add(key)
        require(isinstance(item["locator"], dict), "locator must be an object")
        address = {k: v for k, v in item["locator"].items() if k in {"kind", "path", "pointer", "start", "end"}}
        position = (item["artifact"], json.dumps(address, sort_keys=True))
        require(position not in positions, "duplicate source position")
        positions.add(position)
        require(item["kind"] in {"behavior", "structure"}, "invalid source item kind")
        require(item["artifact"] in source_files, "unknown source artifact")
        locate(source_files[item["artifact"]], item["locator"], parsed)
        items[item["id"]] = item
    seen = set()
    counts = Counter({status: 0 for status in sorted(STATUSES)})
    fragment_paths = set()
    for fragment in sequence(trace["fragments"], "fragments", nonempty=True):
        path = beneath(trace_path.parent, fragment)
        require(path not in fragment_paths, "duplicate fragment")
        fragment_paths.add(path)
        part = inputs.json(path)
        fields(part, ("version", "records"))
        require(type(part["version"]) is int and part["version"] == 1, "unsupported fragment version")
        for row in sequence(part["records"], "records", nonempty=True):
            fields(row, ("sources", "targets", "status", "reason"), ("relation", "decision", "bindings"))
            sources = sequence(row["sources"], "record sources")
            targets = sequence(row["targets"], "record targets")
            status = row["status"]
            require(isinstance(status, str) and status in STATUSES, "unknown disposition")
            require(string(row["reason"]), "record needs a reason")
            require(all(string(x) and x in items for x in sources), "unknown source item")
            require(len(sources) == len(set(sources)) and not seen.intersection(sources), "source item accounted for twice")
            require(bool(sources) == (status != "added"), "only added records have no source")
            require(status != "structural" or all(items[x]["kind"] == "structure" for x in sources), "behavior cannot be classified as structural")
            if "relation" in row:
                require(isinstance(row["relation"], str) and row["relation"] in {"direct", "split", "merge", "rewrite", "moved", "shared", "group"}, "unknown relation")
            if "decision" in row:
                require(string(row["decision"]), "invalid decision reference")
            if status in {"mapped", "changed", "added"}:
                require(bool(targets), "implemented or added record needs targets")
                require(row.get("relation") in {"direct", "split", "merge", "rewrite", "moved", "shared", "group"}, "record needs a relation")
            elif status != "structural":
                require(not targets, "unimplemented record must not claim targets")
            if status == "changed":
                require(string(row.get("decision")), "changed behavior needs a decision reference")
            if row.get("relation") == "shared":
                require({x.get("role") for x in targets if isinstance(x, dict)} >= {"call-site", "implementation"}, "shared mapping needs call-site and implementation")
                require("bindings" in row, "shared mapping needs explicit bindings (empty for no arguments)")
            for binding in sequence(row.get("bindings", []), "bindings"):
                fields(binding, ("source", "target", "direction"))
                require(string(binding["source"]) and string(binding["target"]) and binding["direction"] in {"in", "out", "inout", "return"}, "invalid argument binding")
            for target in targets:
                fields(target, ("artifact", "role", "locator"))
                require(string(target["role"]) and target["artifact"] in target_files, "unknown target artifact or role")
                locate(target_files[target["artifact"]], target["locator"], parsed)
            seen.update(sources)
            counts[status] += len(sources) if sources else 1
    require(seen == items.keys(), "unaccounted source items: " + str(sorted(items.keys() - seen)))
    return {"integrityValid": True, "allInventoriedItemsAccountedFor": True,
            "unresolvedItems": counts["unresolved"], "counts": dict(counts),
            "sourceInventoryCompleteness": "not-established-by-this-check",
            "behavioralCorrectness": "not-assessed", "targetProjectCount": len(projects)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--project", action="append", required=True, help="Repeat for every project, relative to target root (use '.' for a standalone root).")
    parser.add_argument("--solution-file", action="append", default=[], help="Repeat for solution manifests and resource definitions outside projects, relative to target root.")
    parser.add_argument("--output", choices=["json"], default="json")
    args = parser.parse_args(argv)
    try:
        roots = [args.source_root, args.target_root]
        require(all(p.is_dir() and not p.is_symlink() for p in roots), "roots must be real directories")
        # Standalone root is the only accepted dot path; other paths stay strict.
        projects = args.project
        require(len(projects) == len(set(projects)), "duplicate project scope")
        if "." in projects:
            require(projects == ["."], "standalone root cannot overlap other projects")
            target_root = args.target_root.resolve()
            # file_set accepts the root itself via an empty projects list.
            report = validate(args.inventory.resolve(), args.trace.resolve(), args.source_root.resolve(), target_root, [], args.solution_file)
            report["targetProjectCount"] = 1
        else:
            report = validate(args.inventory.resolve(), args.trace.resolve(), args.source_root.resolve(), args.target_root.resolve(), projects, args.solution_file)
        print(json.dumps(report, indent=2))
        return 1 if report["unresolvedItems"] else 0
    except (Invalid, OSError, ValueError, TypeError, KeyError, IndexError, RecursionError, ET.ParseError) as exc:
        print(json.dumps({"integrityValid": False, "error": str(exc), "behavioralCorrectness": "not-assessed"}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
