#!/usr/bin/env python3
"""Pre-run: stage the `UnsupportedTypes` product fixture into the sandbox,
mimicking a completed `template list` bootstrap so the guardrail scenario runs
offline (no governance service, no login).

The fixtures are stored flat under `aops-policy/fixtures/` with descriptive
names; this script reconstructs the per-product folder layout the skill expects
(`./products/<PRODUCT>/form-template.json`, etc.) in the sandbox cwd.

The agent is then asked to author a policy from the staged product. The
`uipath-governance` skill MUST abort on the unsupported data types it carries
(`file`, `signature`, `address`, `datamap`) and surface a "not supported"
warning instead of serializing them into policy data or calling `create`.

Fails loudly (exit 1) if the fixture cannot be staged: this scenario's success
criteria are all absence checks, so an empty/partial workspace would otherwise
score a false green. A non-zero pre_run aborts the run instead.
"""

import os
import shutil
import sys

FIXTURE_DIR = os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks",
                           "uipath-governance", "aops-policy", "fixtures")

# flat fixture file -> the name the skill reads inside products/<PRODUCT>/
FILES = {
    "unsupported_datatypes_guardrail_form_template.json": "form-template.json",
    "unsupported_datatypes_guardrail_form_data.json": "form-data.json",
    "unsupported_datatypes_guardrail_locale_resource.json": "form-template-locale-resource.json",
}

dst_dir = os.path.join(os.getcwd(), "products", "UnsupportedTypes")

try:
    os.makedirs(dst_dir, exist_ok=True)
    for flat_name, product_name in FILES.items():
        shutil.copyfile(os.path.join(FIXTURE_DIR, flat_name),
                        os.path.join(dst_dir, product_name))
except Exception as exc:  # noqa: BLE001
    sys.exit(f"stage failed: {exc}")

# Verify every expected file landed, else the absence checks would false-green.
missing = [n for n in FILES.values() if not os.path.exists(os.path.join(dst_dir, n))]
if missing:
    sys.exit(f"stage incomplete, missing: {missing}")
print(f"staged UnsupportedTypes fixture -> {dst_dir}")
