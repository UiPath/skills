#!/usr/bin/env python3
"""pre_run: mint this run's reference token and stage the token-bearing fixtures.

Renders every `*-template.<ext>` in the sandbox (any depth, so a corpus can stage
one folder per document set) to `<name>.<ext>` with `{{RUN_TOKEN}}`
replaced by a fresh token, removes the templates, and records the token plus each
rendered file's sha256 in `seed.json` for the graders.

Why a per-run token: the tenant is SHARED with other suites and with parallel
replicates, so graders cannot assert on "the newest process" — they match this
run's token in the process name, and cleanup archives only processes carrying it.
The token is baked into the PDD and the BPMN name so the agent carries it into the
publish without being told to.

Runs after preflight_ah.py and merges its `ah-preflight.json` into the seed.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import SEED_FILE  # noqa: E402

PLACEHOLDER = "{{RUN_TOKEN}}"
TEMPLATE_MARKER = "-template"
PREFLIGHT_FILE = "ah-preflight.json"


def render(template_path: str, token: str) -> tuple[str, str]:
    with open(template_path, encoding="utf-8") as handle:
        body = handle.read()
    if PLACEHOLDER not in body:
        sys.exit(f"seed_publish: {template_path} has no {PLACEHOLDER} placeholder")
    rendered = body.replace(PLACEHOLDER, token)
    stem, ext = os.path.splitext(template_path)
    target = stem[: -len(TEMPLATE_MARKER)] + ext
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    os.remove(template_path)
    return target, hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def main() -> int:
    templates = sorted(p for p in glob.glob(f"**/*{TEMPLATE_MARKER}.*", recursive=True) if os.path.isfile(p))
    if not templates:
        sys.exit("seed_publish: no *-template.* fixtures in the sandbox")

    token = "AHE2E-" + uuid.uuid4().hex[:8].upper()
    fixtures = {}
    for template in templates:
        target, digest = render(template, token)
        fixtures[target] = digest

    seed = {"run_token": token, "fixtures": fixtures}
    if os.path.exists(PREFLIGHT_FILE):
        with open(PREFLIGHT_FILE, encoding="utf-8") as handle:
            seed.update(json.load(handle) or {})
        os.remove(PREFLIGHT_FILE)
    with open(SEED_FILE, "w", encoding="utf-8") as handle:
        json.dump(seed, handle, indent=1)

    print(f"seed_publish: run_token={token}; rendered {', '.join(fixtures)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
