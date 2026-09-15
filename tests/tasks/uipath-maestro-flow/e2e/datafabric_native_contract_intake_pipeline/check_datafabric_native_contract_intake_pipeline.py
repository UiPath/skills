#!/usr/bin/env python3
"""Verify the ContractRegistry linear CRUD chain built from the native
`core.datafabric.*` entity nodes — native node shape only:

- >=1 core.datafabric.create on ContractRegistry, fieldValues has contractTitle
- >=1 core.datafabric.read (resultMode: single) on ContractRegistry, filtered
      on Id, wired to the create node's output Id
- >=1 core.datafabric.read (resultMode: multiple) on ContractRegistry,
      filtered on contractTitle, sorted by priority DESC
- >=1 core.datafabric.update on ContractRegistry, recordSource byId wired to
      the create node's output Id, fieldUpdates contains ONLY `status`
- >=1 core.datafabric.delete on ContractRegistry, recordSource byId wired to
      the create node's output Id

Loop / branch / multi-node orchestration is intentionally NOT enforced —
that's core-flow ownership, not the entity nodes'. Node-definition/manifest
shape (definitions[], no instance outputs/model block, no error port) is
covered separately by check_native_node_shape.py."""
import glob
import json
import sys

ENTITY = "ContractRegistry"
CREATE_T = "core.datafabric.create"
READ_T = "core.datafabric.read"
UPDATE_T = "core.datafabric.update"
DELETE_T = "core.datafabric.delete"


def entity_config(node):
    return node.get("inputs", {}).get("entityConfig", {}) or {}


def targets_entity(node):
    return entity_config(node).get("entityName") == ENTITY


def filters_rows(node):
    return ((entity_config(node).get("_filters") or {}).get("rows")) or []


def field_values(node):
    return entity_config(node).get("fieldValues") or []


def field_updates(node):
    return entity_config(node).get("fieldUpdates") or []


def is_wired_to_create(expr, create_ids):
    expr = str(expr or "")
    if not expr.startswith("=js:"):
        return False
    return any(cid and cid in expr for cid in create_ids)


def record_id_expr(node):
    cfg = entity_config(node)
    return cfg.get("recordId") if cfg.get("recordSource") == "byId" else None


def has_id_filter_wired(node, create_ids):
    for row in filters_rows(node):
        if str(row.get("field", "")).lower() != "id":
            continue
        if str(row.get("operator", "")) != "=":
            continue
        if is_wired_to_create(row.get("value"), create_ids):
            return True
    return False


def has_contract_title_filter(node):
    return any(
        str(row.get("field", "")) == "contractTitle"
        for row in filters_rows(node)
    )


def has_priority_desc_sort(node):
    sort = entity_config(node).get("_sort") or {}
    field = str(sort.get("field", ""))
    direction = str(sort.get("direction", ""))
    return field.lower() == "priority" and direction.lower() == "desc"


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)

        creates, reads, updates, deletes = [], [], [], []
        for n in doc.get("nodes", []):
            if not targets_entity(n):
                continue
            t = n.get("type", "")
            if t == CREATE_T:
                creates.append(n)
            elif t == READ_T:
                reads.append(n)
            elif t == UPDATE_T:
                updates.append(n)
            elif t == DELETE_T:
                deletes.append(n)

        if not creates:
            print(f"FAIL: {path} — no {CREATE_T} on {ENTITY}", file=sys.stderr)
            continue
        if not any(
            any(fv.get("field") == "contractTitle" and fv.get("value") for fv in field_values(c))
            for c in creates
        ):
            print(f"FAIL: {path} — create fieldValues missing contractTitle", file=sys.stderr)
            continue

        create_ids = [c.get("id") for c in creates]

        single_reads = [r for r in reads if entity_config(r).get("resultMode") == "single"]
        multi_reads = [r for r in reads if entity_config(r).get("resultMode") == "multiple"]

        if not single_reads:
            print(f"FAIL: {path} — no {READ_T} (resultMode: single) on {ENTITY}", file=sys.stderr)
            continue
        if not any(has_id_filter_wired(r, create_ids) for r in single_reads):
            print(f"FAIL: {path} — single-record read has no Id filter wired to create output",
                  file=sys.stderr)
            continue

        if not multi_reads:
            print(f"FAIL: {path} — no {READ_T} (resultMode: multiple) on {ENTITY}", file=sys.stderr)
            continue
        if not any(has_contract_title_filter(r) for r in multi_reads):
            print(f"FAIL: {path} — multi-record read has no contractTitle filter", file=sys.stderr)
            continue
        if not any(has_priority_desc_sort(r) for r in multi_reads):
            print(f"FAIL: {path} — no multi-record read with priority DESC sort", file=sys.stderr)
            continue

        if not updates:
            print(f"FAIL: {path} — no {UPDATE_T} on {ENTITY}", file=sys.stderr)
            continue
        byid_updates = [u for u in updates if entity_config(u).get("recordSource") == "byId"]
        partial_status_updates = [
            u for u in byid_updates if set(fu.get("field") for fu in field_updates(u)) == {"status"}
        ]
        if not partial_status_updates:
            keys_seen = [sorted(fu.get("field") for fu in field_updates(u)) for u in updates]
            print(f"FAIL: {path} — no byId update whose fieldUpdates is exactly {{'status'}} "
                  f"(found: {keys_seen})", file=sys.stderr)
            continue
        if not any(is_wired_to_create(record_id_expr(u), create_ids) for u in partial_status_updates):
            print(f"FAIL: {path} — status-only update recordId not wired to create output",
                  file=sys.stderr)
            continue

        if not deletes:
            print(f"FAIL: {path} — no {DELETE_T} on {ENTITY}", file=sys.stderr)
            continue
        byid_deletes = [d for d in deletes if entity_config(d).get("recordSource") == "byId"]
        if not any(is_wired_to_create(record_id_expr(d), create_ids) for d in byid_deletes):
            print(f"FAIL: {path} — delete recordId not wired to create output", file=sys.stderr)
            continue

        print(f"OK: {path} — Create → Read(single, by Id) → Read(multiple, "
              f"contractTitle filter + priority DESC) → Update(status only) → "
              f"Delete, all native core.datafabric.* nodes on {ENTITY}, recordId "
              f"chained from create output")
        return 0

    print("FAIL: no .flow satisfies the native CRUD-chain shape", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
