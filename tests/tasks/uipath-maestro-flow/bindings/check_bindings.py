#!/usr/bin/env python3
"""Validate Connection-binding shape in produced .flow files.

Regression coverage for MST-10236 / UiPath/cli#2197: `uip maestro flow node
configure` previously appended brand-new Connection bindings instead of
claiming the empty-keyed stubs that flow-core hoists at `node add` time.
The produced .flow shipped with two binding rows per real connection;
Studio Web's runtime resolved the empty stub first and failed with
`Value cannot be null. (Parameter 'Connection')`.

Usage:
    check_bindings.py <subcommand> <flow_glob> [<extra>...]

Subcommands:
    structure       <flow_glob>
        Flow file exists, valid JSON, has nodes + bindings.

    no_empty_stubs  <flow_glob>
        Zero Connection bindings with empty resourceKey.

    no_duplicates   <flow_glob>
        No duplicate (name, propertyAttribute) under Connection resource.

    matched_default <flow_glob>
        Every ConnectionId binding has non-empty resourceKey == default.

    bindings_v2_no_empty_stubs <flow_glob_for_v2>
        bindings_v2.json (derived artifact), if emitted, has no empty-keyed
        Connection rows. Silently passes if not emitted.

    count_equal      <flow_a> <flow_b>
        Two flow snapshots have the same bindings array length (idempotency).

    same_connection_id <flow_a> <flow_b>
        Two flow snapshots agree on the ConnectionId binding's resourceKey.

    has_connection_key <flow_glob> <connection_id>
        Flow has at least one Connection binding with the given resourceKey.

    no_connection_leak <flow_glob> <old_connection_id>
        Flow has zero references to the given old connection id (resourceKey
        or default).

    connection_id_is  <flow_glob> <expected_connection_id>
        Every ConnectionId binding has resourceKey == expected_connection_id.

    no_triplet_dups  <flow_glob>
        No (name, propertyAttribute, resourceKey) triplet duplicates across
        Connection bindings.

    both_ids_present <flow_glob> <connection_a_id> <connection_b_id>
        Both connection ids appear as ConnectionId resourceKey values, each
        on its own binding row.

    has_connection_key_from_json <flow_glob> <json_path> <key>
    no_connection_leak_from_json <flow_glob> <json_path> <key>
    connection_id_is_from_json <flow_glob> <json_path> <key>
        Same as their non-`_from_json` counterparts, but read the connection
        id from `json_path[key]` (string). Lets the YAML pass conn_ids.json
        without inline jq/python wrapping.

    both_ids_present_from_json <flow_glob> <json_path>
        Reads `a` and `b` from json_path and runs both_ids_present.

Exit 0 on success; non-zero with stderr message on failure.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
from collections import Counter
from typing import Any, NoReturn


def _fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def _dedupe_aliases(paths: list[str]) -> list[str]:
    # Glob matches that point at the same underlying flow definition are not
    # duplicate files. Two collapse passes:
    #   1. realpath — symlink + target case (e.g. flow_files/X.flow → ../X/X.flow)
    #   2. content hash — agents that `cp` instead of `ln -s` produce two
    #      distinct inodes with byte-identical contents
    # Either way, the multi-match guard should only fire on genuinely
    # distinct flow files. Keep the lexicographically-first path per group.
    by_realpath: dict[str, str] = {}
    for p in paths:
        try:
            key = os.path.realpath(p)
        except OSError:
            key = p
        by_realpath.setdefault(key, p)

    by_hash: dict[str, str] = {}
    for p in by_realpath.values():
        try:
            with open(p, "rb") as fh:
                key = hashlib.sha1(fh.read()).hexdigest()
        except OSError:
            key = p  # unreadable — don't collapse with anything else
        by_hash.setdefault(key, p)

    return sorted(by_hash.values())


def _load_one(pattern: str) -> tuple[str, dict[str, Any]]:
    matches = _dedupe_aliases(glob.glob(pattern, recursive=True))
    if not matches:
        _fail(f"No file found for {pattern!r}")
    if len(matches) > 1:
        _fail(f"Multiple files found for {pattern!r}: {matches}")
    try:
        with open(matches[0], encoding="utf-8") as fh:
            return matches[0], json.load(fh)
    except json.JSONDecodeError as exc:
        _fail(f"{matches[0]} is not valid JSON: {exc}")


def _load_flow_bindings(pattern: str) -> tuple[str, list[dict[str, Any]]]:
    path, flow = _load_one(pattern)
    bindings = flow.get("bindings")
    if not isinstance(bindings, list):
        _fail(f"{path} has no `bindings` array (got {type(bindings).__name__})")
    return path, bindings


def _connection_rows(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        b
        for b in bindings
        if isinstance(b, dict) and (b.get("resource") or "").lower() == "connection"
    ]


def _connection_id_rows(bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [b for b in _connection_rows(bindings) if b.get("propertyAttribute") == "ConnectionId"]


def cmd_structure(pattern: str) -> None:
    path, flow = _load_one(pattern)
    if "nodes" not in flow:
        _fail(f"{path} missing `nodes`")
    if "bindings" not in flow:
        _fail(f"{path} missing `bindings`")
    print(f"OK: {path} valid JSON with nodes + bindings")


def cmd_no_empty_stubs(pattern: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    empty = [b for b in _connection_rows(bindings) if not b.get("resourceKey")]
    if empty:
        _fail(
            f"{path}: found {len(empty)} empty-keyed Connection binding(s) "
            f"after configure (would cause Studio Web `Value cannot be null` "
            f"errors at runtime): {empty}"
        )
    print(f"OK: {path} has no empty-keyed Connection bindings")


def cmd_no_duplicates(pattern: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    keys = [(b.get("name"), b.get("propertyAttribute")) for b in _connection_rows(bindings)]
    dups = [k for k, c in Counter(keys).items() if c > 1]
    if dups:
        _fail(f"{path}: duplicate (name, propertyAttribute) under Connection resource: {dups}")
    print(f"OK: {path} has no duplicate Connection binding (name, propertyAttribute) pairs")


def cmd_matched_default(pattern: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    conn = _connection_id_rows(bindings)
    if not conn:
        _fail(f"{path}: no ConnectionId binding emitted")
    bad = [b for b in conn if not (b.get("resourceKey") and b["resourceKey"] == b.get("default"))]
    if bad:
        _fail(f"{path}: ConnectionId binding(s) with mismatched/empty resourceKey vs default: {bad}")
    print(f"OK: {path} ConnectionId binding has non-empty resourceKey == default")


def cmd_bindings_v2_no_empty_stubs(pattern: str) -> None:
    matches = _dedupe_aliases(glob.glob(pattern, recursive=True))
    if not matches:
        print(f"OK: no {pattern!r} emitted on this code path (criterion skipped)")
        return
    try:
        with open(matches[0], encoding="utf-8") as fh:
            payload = json.load(fh)
    except json.JSONDecodeError as exc:
        _fail(f"{matches[0]} is not valid JSON: {exc}")
    rows = payload if isinstance(payload, list) else payload.get("bindings", [])
    empty = [
        x
        for x in rows
        if isinstance(x, dict)
        and (x.get("resource") or "").lower() == "connection"
        and not x.get("resourceKey")
    ]
    if empty:
        _fail(f"{matches[0]}: empty-keyed Connection row(s) in derived bindings_v2.json: {empty}")
    print(f"OK: {matches[0]} has no empty-keyed Connection rows")


def cmd_count_equal(pattern_a: str, pattern_b: str) -> None:
    path_a, bindings_a = _load_flow_bindings(pattern_a)
    path_b, bindings_b = _load_flow_bindings(pattern_b)
    if len(bindings_a) != len(bindings_b):
        _fail(
            f"bindings count changed across snapshots: "
            f"{path_a} has {len(bindings_a)}, {path_b} has {len(bindings_b)}"
        )
    print(f"OK: {path_a} and {path_b} have equal bindings count = {len(bindings_a)}")


def cmd_same_connection_id(pattern_a: str, pattern_b: str) -> None:
    path_a, bindings_a = _load_flow_bindings(pattern_a)
    path_b, bindings_b = _load_flow_bindings(pattern_b)
    a_keys = {b.get("resourceKey") for b in _connection_id_rows(bindings_a)}
    b_keys = {b.get("resourceKey") for b in _connection_id_rows(bindings_b)}
    if not a_keys or not b_keys:
        _fail(f"no ConnectionId binding rows found: {path_a}={a_keys}, {path_b}={b_keys}")
    if a_keys != b_keys:
        _fail(f"ConnectionId resourceKey differs across snapshots: {path_a}={a_keys} vs {path_b}={b_keys}")
    print(f"OK: ConnectionId resourceKey stable across snapshots ({a_keys})")


def cmd_has_connection_key(pattern: str, connection_id: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    keys = {b.get("resourceKey") for b in _connection_rows(bindings)}
    if connection_id not in keys:
        _fail(f"{path}: connection {connection_id!r} not present in Connection bindings (got {keys})")
    print(f"OK: {path} references connection {connection_id!r}")


def cmd_no_connection_leak(pattern: str, old_connection_id: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    leaked = [
        b
        for b in bindings
        if isinstance(b, dict)
        and (b.get("resourceKey") == old_connection_id or b.get("default") == old_connection_id)
    ]
    if leaked:
        _fail(f"{path}: stale binding(s) referencing old connection {old_connection_id!r}: {leaked}")
    print(f"OK: {path} has no references to old connection {old_connection_id!r}")


def cmd_connection_id_is(pattern: str, expected: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    conn = _connection_id_rows(bindings)
    if not conn:
        _fail(f"{path}: no ConnectionId binding emitted")
    bad = [b for b in conn if b.get("resourceKey") != expected]
    if bad:
        _fail(f"{path}: some ConnectionId binding does not point at {expected!r}: {bad}")
    print(f"OK: {path} all ConnectionId bindings point at {expected!r}")


def cmd_no_triplet_dups(pattern: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    trips = [
        (b.get("name"), b.get("propertyAttribute"), b.get("resourceKey"))
        for b in _connection_rows(bindings)
    ]
    dups = [k for k, c in Counter(trips).items() if c > 1]
    if dups:
        _fail(f"{path}: duplicate Connection binding triplet(s): {dups}")
    print(f"OK: {path} has no duplicate Connection (name, propertyAttribute, resourceKey) triplets")


def cmd_both_ids_present(pattern: str, conn_a: str, conn_b: str) -> None:
    path, bindings = _load_flow_bindings(pattern)
    conn_id_rows = _connection_id_rows(bindings)
    a_rows = [b for b in conn_id_rows if b.get("resourceKey") == conn_a]
    b_rows = [b for b in conn_id_rows if b.get("resourceKey") == conn_b]
    if not a_rows or not b_rows:
        _fail(
            f"{path}: each connection must have at least one ConnectionId binding "
            f"(A={a_rows}, B={b_rows})"
        )
    print(f"OK: {path} both connections present in ConnectionId bindings")


def _read_json_value(json_path: str, key: str) -> str:
    try:
        with open(json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"cannot read {json_path!r}: {exc}")
    if not isinstance(data, dict) or key not in data:
        _fail(f"{json_path}: missing required key {key!r}")
    value = data[key]
    if not isinstance(value, str) or not value:
        _fail(f"{json_path}: key {key!r} must be a non-empty string (got {value!r})")
    return value


def cmd_has_connection_key_from_json(pattern: str, json_path: str, key: str) -> None:
    cmd_has_connection_key(pattern, _read_json_value(json_path, key))


def cmd_no_connection_leak_from_json(pattern: str, json_path: str, key: str) -> None:
    cmd_no_connection_leak(pattern, _read_json_value(json_path, key))


def cmd_connection_id_is_from_json(pattern: str, json_path: str, key: str) -> None:
    cmd_connection_id_is(pattern, _read_json_value(json_path, key))


def cmd_both_ids_present_from_json(pattern: str, json_path: str) -> None:
    cmd_both_ids_present(
        pattern,
        _read_json_value(json_path, "a"),
        _read_json_value(json_path, "b"),
    )


_COMMANDS = {
    "structure": cmd_structure,
    "no_empty_stubs": cmd_no_empty_stubs,
    "no_duplicates": cmd_no_duplicates,
    "matched_default": cmd_matched_default,
    "bindings_v2_no_empty_stubs": cmd_bindings_v2_no_empty_stubs,
    "count_equal": cmd_count_equal,
    "same_connection_id": cmd_same_connection_id,
    "has_connection_key": cmd_has_connection_key,
    "no_connection_leak": cmd_no_connection_leak,
    "connection_id_is": cmd_connection_id_is,
    "no_triplet_dups": cmd_no_triplet_dups,
    "both_ids_present": cmd_both_ids_present,
    "has_connection_key_from_json": cmd_has_connection_key_from_json,
    "no_connection_leak_from_json": cmd_no_connection_leak_from_json,
    "connection_id_is_from_json": cmd_connection_id_is_from_json,
    "both_ids_present_from_json": cmd_both_ids_present_from_json,
}


def main() -> None:
    if len(sys.argv) < 2:
        _fail(f"usage: check_bindings.py <subcommand> [...] (subcommands: {sorted(_COMMANDS)})")
    sub = sys.argv[1]
    fn = _COMMANDS.get(sub)
    if fn is None:
        _fail(f"unknown subcommand {sub!r}; choose from {sorted(_COMMANDS)}")
    fn(*sys.argv[2:])


if __name__ == "__main__":
    main()
