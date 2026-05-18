#!/usr/bin/env python3
"""Verify time trigger lifecycle: enable flag flips correctly; cron persists across update."""

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


after_create = ok(load("get_after_create.json"), "get_after_create")
after_disable = ok(load("get_after_disable.json"), "get_after_disable")
after_enable = ok(load("get_after_enable.json"), "get_after_enable")
after_cron = ok(load("get_after_cron.json"), "get_after_cron")

enabled_create = _pick(after_create, "Enabled")
enabled_disable = _pick(after_disable, "Enabled")
enabled_enable = _pick(after_enable, "Enabled")

if enabled_create is not True:
    sys.exit(f"FAIL: trigger not enabled by default after create: {enabled_create!r}")
if enabled_disable is not False:
    sys.exit(f"FAIL: trigger still enabled after disable: {enabled_disable!r}")
if enabled_enable is not True:
    sys.exit(f"FAIL: trigger not re-enabled after enable: {enabled_enable!r}")

cron_create = _pick(after_create, "Cron", "CronExpression")
cron_after = _pick(after_cron, "Cron", "CronExpression")
if cron_after == cron_create:
    sys.exit(f"FAIL: cron did not change — before={cron_create!r} after={cron_after!r}")
if "30" not in str(cron_after):  # "0 30 4 * * ?"
    sys.exit(f"FAIL: cron after update doesn't match expected pattern: {cron_after!r}")

print(f"OK: enabled flag flipped true→false→true; cron updated {cron_create!r}→{cron_after!r}")
