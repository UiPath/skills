#!/usr/bin/env python3
"""Seed a unique, deterministic Test Case name for the data-grounded CRUD task.
Runs in pre_run; writes seed.json into the sandbox for the agent + checker to read.
"""
import json
import os
import uuid

name = f"DataEval-TC-{uuid.uuid4().hex[:8]}"
seed = {
    "name": name,
    # Project the test case is created under. Override via env for the eval tenant.
    "project_key": os.environ.get("TM_EVAL_PROJECT_KEY", "HEALTH"),
}
with open("seed.json", "w", encoding="utf-8") as fh:
    json.dump(seed, fh)
print(f"seeded test case name: {name} (project {seed['project_key']})")
