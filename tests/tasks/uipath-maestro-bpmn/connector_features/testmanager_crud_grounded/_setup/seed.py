#!/usr/bin/env python3
"""Shared seed for data-grounded TM connector CRUD tasks.
Writes seed.json (unique name + project) into the sandbox. Staged into the
sandbox via sandbox.template_sources and run as ./_setup/seed.py.
"""
import json
import os
import uuid

seed = {
    "name": f"DataEval-{uuid.uuid4().hex[:8]}",
    "project_key": os.environ.get("TM_EVAL_PROJECT_KEY", "HEALTH"),
}
with open("seed.json", "w", encoding="utf-8") as fh:
    json.dump(seed, fh)
print(f"seeded name: {seed['name']} (project {seed['project_key']})")
