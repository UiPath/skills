#!/usr/bin/env python3
"""
Smoke-test the Data Fabric `records query` filter contract against a live entity.

Validates that the operator / parameter SHAPES the uipath-data-fabric skill
documents are accepted by the live CLI, and that the anti-pattern shapes the
skill warns against are NOT honored. This is a command-shape contract test —
it asserts the CLI's *acceptance* of each documented shape, not specific
record counts (counts depend on seed data; shape validity does not).

Each case carries an expectation:

    accept  — documented-correct shape; CLI must return Result == Success.
    drop    — wrong-KEY shape (`filters`/`field`); the server never parses the
              filter, so the CLI must return Success AND TotalCount equal to the
              unfiltered baseline (the filter did not narrow anything).
    error   — wrong-OPERATOR shape (`==`/`Equals`) or other documented failure
              mode; CLI must reject (non-Success / 400).

Coverage:
    A. Wrong key (`filters`/`field`)        → drop (filter silently ignored)
       Wrong operator (`==`/`Equals`)       → error (400, request declined)
    B. 12 supported operators  = != > < >= <= contains
       not-contains startswith endswith in not-in              → accept
    C. logicalOperator forms   int 0/1, string AND/And/and      → accept
    D. Nested filterGroups                                       → accept
    E. sortOptions + isDescending                                → accept
    F. selectedFields projection                                 → accept
    G. Aggregates (groupBy + COUNT)                              → accept
    H. is empty / is not empty (`=` / `!=` with value: null)     → accept

Each operator is exercised on a field type where the support matrix
(filter-platform-contract.md §4) marks it supported — string ops on a STRING
field, comparison on a numeric field. Out-of-matrix combinations (e.g. `<` on
Text) are NOT asserted here: the live API executes them rather than rejecting
them, so the skill gates them at the agent level (the unsupported-operator
prompt flow, SKILL.md Rule 17), not at the API. This script only proves the
supported set works and that malformed operators are rejected.

Cases reference fields by configurable names (see --field-* flags and
DEFAULT_PROFILES). A case whose field is absent from the target entity is
skipped, not failed.

Usage:
    # Default: the CodeEvalTestEntity seed (20 movie records).
    verify_filter_contract.py

    # Against a specific entity by name (auto-resolves the ID):
    verify_filter_contract.py --entity-name CE_IntegrationOrders

    # Against a specific entity by ID, overriding the test fields:
    verify_filter_contract.py --entity-id <uuid> \
        --field-str Code --field-num Value --sample-str ORD-001 --sample-num 100

Auth: uses the active `uip` login.

Exit codes:
    0  — every documented shape behaved as the contract requires.
    1  — at least one contract violation (a documented shape was rejected, or
          an anti-pattern shape was honored). Details printed per case.
    2  — setup failure (auth/entity-not-found/baseline unavailable) — the
          contract could not be evaluated.
"""

import argparse
import json
import subprocess
import sys
import time


UIP_TIMEOUT_SECONDS = 60


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return r.returncode, r.stdout, r.stderr


def find_entity_id(name: str) -> str | None:
    code, out, _ = run_uip("df", "entities", "list", "--native-only")
    if code != 0 or not out.strip():
        return None
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        return None
    inner = d.get("Data") if isinstance(d, dict) else None
    recs = inner if isinstance(inner, list) else (inner or {}).get("Records") or []
    for ent in recs:
        if isinstance(ent, dict) and (ent.get("Name") or ent.get("name")) == name:
            return ent.get("ID") or ent.get("Id") or ent.get("id")
    return None


def entity_field_names(entity_id: str) -> set[str] | None:
    """Field names declared on the entity schema, or None if unavailable."""
    code, out, _ = run_uip("df", "entities", "get", entity_id)
    if code != 0 or not out.strip():
        return None
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        return None
    data = (d.get("Data") if isinstance(d, dict) else None) or d
    fields = (data or {}).get("fields") or (data or {}).get("Fields") or []
    names = set()
    for f in fields:
        if isinstance(f, dict):
            n = f.get("fieldName") or f.get("Name") or f.get("name")
            if n:
                names.add(n)
    return names or None


def total_count_unfiltered(entity_id: str) -> int | None:
    code, out, _ = run_uip("df", "records", "list", entity_id, "--limit", "1")
    if code != 0 or not out.strip():
        return None
    try:
        d = json.loads(out)
    except json.JSONDecodeError:
        return None
    return ((d.get("Data") or {}).get("TotalCount"))


def run_query(entity_id: str, body: dict, retries: int = 2) -> tuple[bool, int | None, str]:
    """Run a query, retrying transient failures with backoff.

    Returns (success, total_count, error_message). The CLI reports throttling
    and genuine 400s with the same opaque "Error querying records" message, so
    a batch of rapid queries can hit rate limits; retry-with-backoff absorbs
    that. Callers that *expect* a rejection pass retries=0 to avoid pointless
    waits (a retried rejection still rejects).
    """
    body_str = json.dumps(body)
    last: tuple[bool, int | None, str] = (False, None, "no attempt")
    for attempt in range(retries + 1):
        code, out, err = run_uip("df", "records", "query", entity_id, "--body", body_str)
        if code != 0 and not out.strip():
            last = (False, None, (err or out).strip()[:120])
        else:
            try:
                d = json.loads(out)
            except json.JSONDecodeError as e:
                last = (False, None, f"parse-err: {e}")
            else:
                if d.get("Result") in ("Success", None):
                    return True, ((d.get("Data") or {}).get("TotalCount")), ""
                last = (False, None, f"{d.get('Code')}: {(d.get('Message') or '')[:80]}")
        if attempt < retries:
            time.sleep(0.8 * (attempt + 1))  # 0.8s, 1.6s backoff
    return last


# Each case: (label, fields-it-touches, body, expectation)
#   expectation ∈ {"accept", "drop", "error"}
def build_cases(field_str: str, field_num: str, sample_str: str, sample_num: str):
    qf = lambda **kw: {"filterGroup": {"logicalOperator": 0, "queryFilters": [kw]}}
    cases = [
        # A) Anti-patterns. Wrong KEY → silently dropped (server never parses
        #    the filter, returns the unfiltered baseline). Wrong OPERATOR →
        #    400 rejected ("Unexpected operator …", contract §2).
        ("A1. wrong key `filters` + `field`", {field_str},
         {"filterGroup": {"logicalOperator": "AND",
                          "filters": [{"field": field_str, "operator": "=", "value": sample_str}]}},
         "drop"),
        ("A2. wrong operator alias `Equals`", {field_str},
         {"filterGroup": {"logicalOperator": 0,
                          "queryFilters": [{"fieldName": field_str, "operator": "Equals", "value": sample_str}]}},
         "error"),
        ("A3. wrong operator alias `==`", {field_str},
         {"filterGroup": {"logicalOperator": 0,
                          "queryFilters": [{"fieldName": field_str, "operator": "==", "value": sample_str}]}},
         "error"),

        # B) 12 supported operators — must be accepted
        ("B1.  =",            {field_str}, qf(fieldName=field_str, operator="=",  value=sample_str), "accept"),
        ("B2.  !=",           {field_str}, qf(fieldName=field_str, operator="!=", value=sample_str), "accept"),
        ("B3.  >",            {field_num}, qf(fieldName=field_num, operator=">",  value=sample_num), "accept"),
        ("B4.  <",            {field_num}, qf(fieldName=field_num, operator="<",  value=sample_num), "accept"),
        ("B5.  >=",           {field_num}, qf(fieldName=field_num, operator=">=", value=sample_num), "accept"),
        ("B6.  <=",           {field_num}, qf(fieldName=field_num, operator="<=", value=sample_num), "accept"),
        ("B7.  contains",     {field_str}, qf(fieldName=field_str, operator="contains",     value=sample_str[:3]), "accept"),
        ("B8.  not contains", {field_str}, qf(fieldName=field_str, operator="not contains", value=sample_str[:3]), "accept"),
        ("B9.  startswith",   {field_str}, qf(fieldName=field_str, operator="startswith",   value=sample_str[:3]), "accept"),
        ("B10. endswith",     {field_str}, qf(fieldName=field_str, operator="endswith",     value=sample_str[-3:]), "accept"),
        ("B11. in (valueList)",     {field_str},
         {"filterGroup": {"logicalOperator": 0, "queryFilters": [{"fieldName": field_str, "operator": "in", "valueList": [sample_str]}]}}, "accept"),
        ("B12. not in (valueList)", {field_str},
         {"filterGroup": {"logicalOperator": 0, "queryFilters": [{"fieldName": field_str, "operator": "not in", "valueList": [sample_str]}]}}, "accept"),

        # C) logicalOperator forms — must be accepted
        ("C1. logicalOperator 0 (int)",   {field_str}, qf(fieldName=field_str, operator="=", value=sample_str), "accept"),
        ("C2. logicalOperator 'AND'",     {field_str},
         {"filterGroup": {"logicalOperator": "AND", "queryFilters": [{"fieldName": field_str, "operator": "=", "value": sample_str}]}}, "accept"),
        ("C3. logicalOperator 'And'",     {field_str},
         {"filterGroup": {"logicalOperator": "And", "queryFilters": [{"fieldName": field_str, "operator": "=", "value": sample_str}]}}, "accept"),
        ("C4. logicalOperator 'and'",     {field_str},
         {"filterGroup": {"logicalOperator": "and", "queryFilters": [{"fieldName": field_str, "operator": "=", "value": sample_str}]}}, "accept"),

        # D) Nested filterGroups — must be accepted
        ("D1. nested filterGroups", {field_str, field_num},
         {"filterGroup": {"logicalOperator": 1, "filterGroups": [
             {"logicalOperator": 0, "queryFilters": [
                 {"fieldName": field_str, "operator": "=", "value": sample_str},
                 {"fieldName": field_num, "operator": ">", "value": sample_num}]},
             {"logicalOperator": 0, "queryFilters": [
                 {"fieldName": field_num, "operator": "<", "value": sample_num}]}]}}, "accept"),

        # E) sortOptions — must be accepted
        ("E1. sortOptions isDescending", {field_num},
         {"sortOptions": [{"fieldName": field_num, "isDescending": True}]}, "accept"),

        # F) selectedFields projection — must be accepted
        ("F1. selectedFields projection", {field_str},
         {"selectedFields": [field_str]}, "accept"),

        # G) Aggregates — must be accepted
        ("G1. aggregates COUNT + groupBy", {field_str},
         {"selectedFields": [field_str], "groupBy": [field_str],
          "aggregates": [{"function": "COUNT", "field": "Id", "alias": "total"}]}, "accept"),

        # H) is empty / is not empty — `=` / `!=` with a null value
        ("H1. is empty (= null)", {field_str},
         {"filterGroup": {"logicalOperator": 0, "queryFilters": [{"fieldName": field_str, "operator": "=", "value": None}]}}, "accept"),
        ("H2. is not empty (!= null)", {field_str},
         {"filterGroup": {"logicalOperator": 0, "queryFilters": [{"fieldName": field_str, "operator": "!=", "value": None}]}}, "accept"),
    ]
    return cases


DEFAULT_PROFILES = {
    "CodeEvalTestEntity": {"field_str": "Title", "field_num": "Score",
                           "sample_str": "Inception", "sample_num": "7"},
    "CE_IntegrationOrders": {"field_str": "Code", "field_num": "Value",
                             "sample_str": "ORD-001", "sample_num": "100"},
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the Data Fabric filter contract against a live entity.")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--entity-name", default="CodeEvalTestEntity",
                   help="Entity to query (default: CodeEvalTestEntity).")
    g.add_argument("--entity-id", help="Entity ID (overrides --entity-name lookup).")
    parser.add_argument("--field-str", help="STRING field name to use in tests")
    parser.add_argument("--field-num", help="Numeric (INTEGER/DECIMAL) field name")
    parser.add_argument("--sample-str", help="Sample STRING value present in the entity")
    parser.add_argument("--sample-num", help="Sample numeric value as a string")
    args = parser.parse_args()

    if args.entity_id:
        entity_id = args.entity_id
        ename = "(provided)"
        profile = {}
    else:
        ename = args.entity_name
        entity_id = find_entity_id(ename)
        if not entity_id:
            print(f"SETUP FAIL: entity '{ename}' not found in this tenant.", file=sys.stderr)
            sys.exit(2)
        profile = DEFAULT_PROFILES.get(ename, {})

    field_str = args.field_str or profile.get("field_str") or "Name"
    field_num = args.field_num or profile.get("field_num") or "Score"
    sample_str = args.sample_str or profile.get("sample_str") or "test"
    sample_num = args.sample_num or profile.get("sample_num") or "0"

    baseline = total_count_unfiltered(entity_id)
    if baseline is None:
        print(f"SETUP FAIL: could not read unfiltered baseline for {ename} ({entity_id}).", file=sys.stderr)
        sys.exit(2)

    schema_fields = entity_field_names(entity_id)  # None ⇒ can't filter cases by field

    print(f"Entity: {ename} ({entity_id})")
    print(f"Test fields: STRING={field_str!r}, numeric={field_num!r}, "
          f"sample STRING={sample_str!r}, sample num={sample_num!r}")
    print(f"Unfiltered TotalCount baseline: {baseline}\n")

    cases = build_cases(field_str, field_num, sample_str, sample_num)
    print(f"{'Case':34} {'Expect':7} {'Result':8} {'Count':>6}  Notes")
    print("-" * 92)

    failures = 0
    skipped = 0
    for label, needs_fields, body, expect in cases:
        if schema_fields is not None and not needs_fields.issubset(schema_fields):
            missing = ", ".join(sorted(needs_fields - schema_fields))
            print(f"{label:34} {expect:7} {'SKIP':8} {'-':>6}  field(s) absent: {missing}")
            skipped += 1
            continue

        # `error`-expected cases need no retry — a retried rejection still
        # rejects, and skipping retries keeps the run fast.
        success, tc, err = run_query(entity_id, body, retries=0 if expect == "error" else 2)
        ok, note = _evaluate(expect, success, tc, baseline, err)
        if not ok:
            failures += 1
        verdict = "PASS" if ok else "FAIL"
        print(f"{label:34} {expect:7} {verdict:8} {str(tc):>6}  {note}")

    print("-" * 92)
    total_run = len(cases) - skipped
    print(f"\n{total_run} case(s) run, {skipped} skipped, {failures} failure(s).")

    if failures:
        print("CONTRACT VIOLATION: see FAIL rows above.", file=sys.stderr)
        sys.exit(1)
    print("OK: every documented filter shape behaved per the contract.")
    sys.exit(0)


def _evaluate(expect: str, success: bool, tc: int | None, baseline: int,
              err: str) -> tuple[bool, str]:
    """Return (passed, note) for one case given its expectation."""
    if expect == "accept":
        if success:
            return True, "accepted"
        return False, f"expected acceptance but CLI rejected — {err}"

    if expect == "drop":
        if not success:
            return False, f"expected silent drop but CLI errored — {err}"
        if tc == baseline:
            return True, "silently dropped (matches baseline)"
        return False, f"anti-pattern was HONORED (count {tc} != baseline {baseline})"

    if expect == "error":
        if success:
            return False, f"expected rejection but CLI accepted (count {tc})"
        return True, f"rejected as expected — {err}"

    return False, f"unknown expectation {expect!r}"


if __name__ == "__main__":
    main()
