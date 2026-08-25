#!/usr/bin/env python3
"""Read a policy's stored form data back and check the fields the scenario asked for.

  AOPS_SEED_KEY        seed.json key naming the policy the agent authored (required)
  AOPS_PRODUCT         product the policy must be registered under (required)
  AOPS_FIELD_LABEL     regex matched (case-insensitively) against the product's locale-resolved
                       field labels; the matching field's key is read from the policy data
  AOPS_FIELD_EXPECT    JSON literal the field must hold (e.g. false, true, "Warning")
  AOPS_FIELD_LABEL2 / AOPS_FIELD_EXPECT2   optional second field
  AOPS_ROW_KEY_REGEX   regex for a repeating-row (editgrid) key in the policy data
  AOPS_ROW_CODE        a row must carry this value (e.g. an analyzer rule code) and an
                       `*enabled*` field that is true

The field keys are resolved from the LIVE template (`template get --output-template-locale-resource`)
at check time, so the check survives template drift and never hard-codes a component key. Keys are
compared case- and separator-insensitively: the template uses kebab-case (`gemini-control-toggle`)
while `aops-policy get` echoes the stored data PascalCased (`GeminiControlToggle`). A policy created
from untouched defaults fails on the value comparison.

Exits 0 on success, 1 on failure.
"""

import json
import logging
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import aops_get, aops_search, fail, ok, poll, run_cli, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_aops_policy_data: %(message)s")

STRUCTURAL = {"components", "columns", "rows", "values", "data", "template", "defaultdata"}


def norm(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def payload_of(policy: dict) -> dict:
    """The stored form data — `get` nests it under Data (sometimes twice, sometimes lower-case)."""
    node = policy.get("Data", policy.get("data"))
    while isinstance(node, dict):
        inner = node.get("Data", node.get("data"))
        if isinstance(inner, dict) and len(node) <= 2:
            node = inner
        else:
            break
    return node if isinstance(node, dict) else {}


def walk(obj, parent_key=None):
    """Yield (parent_key, dict) for every dict in a JSON document."""
    if isinstance(obj, dict):
        yield parent_key, obj
        for k, v in obj.items():
            yield from walk(v, k)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v, parent_key)


def locale_resource(product: str) -> dict:
    path = os.path.join(tempfile.gettempdir(), f"aops-locale-{product}-{os.getpid()}.json")
    data = run_cli(["gov", "aops-policy", "template", "get", product,
                    "--output-template-locale-resource", path], timeout=120)
    if not data or data.get("Result") != "Success" or not os.path.exists(path):
        fail(f"could not fetch the {product} locale resource to resolve field keys")
    try:
        with open(path, encoding="utf-8-sig") as fh:
            return json.load(fh)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def keys_for_label(resource: dict, label_re: str) -> list[str]:
    rx = re.compile(label_re, re.IGNORECASE)
    keys = []
    for parent, d in walk(resource):
        label = d.get("label") or d.get("Label")
        if isinstance(label, str) and rx.search(label) and parent and norm(parent) not in STRUCTURAL \
                and parent not in keys:
            keys.append(parent)
    return keys


def find_value(payload, key: str):
    """Value stored under `key` anywhere in the policy data, casing/separators ignored."""
    want = norm(key.split(".")[-1])
    for _, d in walk(payload):
        for k, v in d.items():
            if norm(k) == want:
                return True, v
    return False, None


def truthy(v) -> bool:
    return v is True or (isinstance(v, str) and v.strip().lower() in ("true", "yes", "1", "on"))


def _equal(value, expect) -> bool:
    if isinstance(expect, bool):
        return truthy(value) == expect if isinstance(value, (bool, str)) else False
    if isinstance(expect, str) and isinstance(value, str):
        return value.strip().lower() == expect.strip().lower()
    return value == expect


def check_field(payload: dict, resource: dict, label_re: str, expect_raw: str):
    expect = json.loads(expect_raw)
    keys = keys_for_label(resource, label_re)
    if not keys:
        fail(f"no field in the live template has a label matching /{label_re}/i — "
             f"the scenario's field does not exist on this tenant's template")
    hits = []
    for k in keys:
        present, value = find_value(payload, k)
        if present:
            hits.append((k, value))
    if not hits:
        fail(f"none of the fields labelled /{label_re}/i ({keys}) are present in the policy data — "
             f"the policy was not composed from the product template")
    if not any(_equal(v, expect) for _, v in hits):
        fail(f"field(s) labelled /{label_re}/i hold {hits}, expected {expect!r} — "
             f"the user's intent was not applied to the policy data")
    logging.info("field(s) %s -> %r as requested", [k for k, v in hits if _equal(v, expect)], expect)


def check_row(payload: dict, key_re: str, code: str):
    rx = re.compile(norm(key_re) or key_re, re.IGNORECASE)
    arrays = [(k, v) for _, d in walk(payload) for k, v in d.items()
              if isinstance(v, list) and rx.search(norm(k))]
    if not arrays:
        fail(f"no repeating-row field matching /{key_re}/i in the policy data")
    for key, rows in arrays:
        for row in rows:
            if not isinstance(row, dict):
                continue
            values = {str(v).strip().lower() for v in row.values() if isinstance(v, (str, int))}
            if code.lower() not in values:
                continue
            enabled = [v for k, v in row.items() if "enabled" in norm(k)]
            if enabled and not any(truthy(v) for v in enabled):
                fail(f"row for {code} exists under {key} but is not enabled: {row}")
            logging.info("row for %s present under %s and enabled", code, key)
            return
    fail(f"no row carrying {code!r} under {[k for k, _ in arrays]} — the rule was not added to the grid")


def main():
    key = (os.environ.get("AOPS_SEED_KEY") or "").strip()
    product = (os.environ.get("AOPS_PRODUCT") or "").strip()
    if not key or not product:
        fail("AOPS_SEED_KEY and AOPS_PRODUCT must be set")
    entry = seed_entry(key)
    if not entry or not entry.get("name"):
        fail(f"seed.json has no '{key}' entry — the pre_run seed did not complete")
    name = entry["name"]

    rows = poll(lambda: [r for r in aops_search(name) if (r.get("Name") or "") == name],
                max_attempts=3, delay=4)
    if not rows:
        fail(f"no aops policy named '{name}' — nothing was created")
    row = rows[0]
    got_product = ((row.get("Product") or {}).get("Name")) or ""
    if got_product != product:
        fail(f"policy '{name}' is registered under {got_product!r}, expected {product!r} — wrong product selected")
    ident = str(row.get("Identifier") or "")
    full = aops_get(ident)
    payload = payload_of(full or {})
    if not payload:
        fail(f"policy '{name}' has no form-data payload — it was created without --input")

    resource = None
    for suffix in ("", "2"):
        label_re = (os.environ.get(f"AOPS_FIELD_LABEL{suffix}") or "").strip()
        expect = (os.environ.get(f"AOPS_FIELD_EXPECT{suffix}") or "").strip()
        if label_re and expect:
            resource = resource or locale_resource(product)
            check_field(payload, resource, label_re, expect)

    row_key = (os.environ.get("AOPS_ROW_KEY_REGEX") or "").strip()
    code = (os.environ.get("AOPS_ROW_CODE") or "").strip()
    if row_key and code:
        check_row(payload, row_key, code)

    ok(f"policy '{name}' ({ident}) under {product} carries the requested settings")


main()
