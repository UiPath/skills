#!/usr/bin/env python3
"""Verify the solution deploy round-trip: publish → deploy → list-contains → uninstall."""

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


seed = load("seed.json")
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json has no uuid8")
deploy_name = f"{uuid8}-deploy"


def assert_ok(env: dict, label: str, allow_already_exists: bool = False):
    result = env.get("Result")
    if result == "Success":
        return env.get("Data")
    if allow_already_exists:
        msg = (env.get("Message") or "").lower()
        if "already exists" in msg or "duplicate" in msg or "conflict" in msg:
            return env.get("Data")
    sys.exit(f"FAIL: {label} Result={result!r} Message={env.get('Message')!r}")


# 1. Publish succeeded (or was already published — idempotent)
publish = load("publish.json")
publish_data = assert_ok(publish, "publish", allow_already_exists=True) or {}
package_name = _pick(publish_data, "PackageName")
if package_name and package_name != "e2e-stub":
    sys.exit(f"FAIL: published package name = {package_name!r}, expected 'e2e-stub'")

# 2. Deploy reached a terminal state
deploy = load("deploy_run.json")
deploy_data = assert_ok(deploy, "deploy_run") or {}
status = _pick(deploy_data, "Status") or ""
if status not in ("DeploymentSucceeded", "DeploymentSuccessful", "Succeeded"):
    sys.exit(f"FAIL: deploy_run status = {status!r}, expected DeploymentSucceeded")
folder_path = _pick(deploy_data, "FolderPath") or ""
if "Shared" not in folder_path:
    sys.exit(f"FAIL: deploy folder_path = {folder_path!r}, expected to contain 'Shared'")

# 3. List contained the deploy
lst = load("deploy_list.json")
lst_data = assert_ok(lst, "deploy_list")
items = lst_data if isinstance(lst_data, list) else (
    _pick(lst_data, "Value", "Items", "Results") or []
)
names = [_pick(it, "Name") or _pick(it, "DeploymentName") for it in items if isinstance(it, dict)]
if deploy_name not in names:
    sys.exit(f"FAIL: deploy_list does not contain {deploy_name!r}; saw {names[:5]}")

# 4. Uninstall succeeded
uninstall = load("uninstall.json")
uninstall_data = assert_ok(uninstall, "uninstall") or {}
ustatus = _pick(uninstall_data, "Status") or ""
if "Uninstall" not in ustatus:
    sys.exit(f"FAIL: uninstall status = {ustatus!r}, expected SuccessfulUninstall")

print(f"OK: deploy {deploy_name!r} round-trip — published, deployed ({folder_path}), listed, uninstalled ({ustatus})")
