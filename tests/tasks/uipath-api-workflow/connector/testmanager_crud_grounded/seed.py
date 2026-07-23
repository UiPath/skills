#!/usr/bin/env python3
"""Shared seed for data-grounded TM connector CRUD tasks.
Writes seed.json (unique name + project) into the sandbox. Run from pre_run via
the $SKILLS_REPO_PATH-absolute path ($TASK_DIR is not available in pre_run).
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
