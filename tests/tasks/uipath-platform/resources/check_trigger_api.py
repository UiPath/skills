#!/usr/bin/env python3
"""Verify API trigger lifecycle: slug+method persist; name update reflected."""

import json
import sys
from pathlib import Path


def load(name: str) -> dict:
    p = Path(name)
    if not p.is_file():
        sys.exit(f"FAIL: {name} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {name} is not valid JSON: {e}")


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def ok(env, label):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    return env.get("Data") or {}


seed = load("seed.json")
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json has no uuid8")

after_create = ok(load("get_after_create.json"), "get_after_create")
after_update = ok(load("get_after_update.json"), "get_after_update")

slug = _pick(after_create, "Slug")
method = _pick(after_create, "Method")
if slug != f"{uuid8}-api-slug":
    sys.exit(f"FAIL: slug={slug!r}, expected '{uuid8}-api-slug'")
if str(method).lower() != "post":
    sys.exit(f"FAIL: method={method!r}, expected 'Post'")

name_before = _pick(after_create, "Name")
name_after = _pick(after_update, "Name")
if name_before == name_after:
    sys.exit(f"FAIL: name did not change after update — both {name_before!r}")
if name_after != f"{uuid8}-api-renamed":
    sys.exit(f"FAIL: name after update = {name_after!r}, expected '{uuid8}-api-renamed'")

print(f"OK: trigger slug={slug!r} method={method!r} persisted; name {name_before!r} → {name_after!r}")
