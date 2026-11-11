"""Only metrics named in intent.json must export fetchData; a shared helper in metrics/ is fine."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_dashboard.py")


def run(metrics: dict) -> int:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        files = {
            "package.json": "{}",
            "uipath.json": json.dumps({k: "" for k in ("scope", "orgName", "tenantName", "baseUrl", "clientId")}),
            "vite.config.ts": "uipathCodedApps()",
            "intent.json": json.dumps({"schemaVersion": 2, "metrics": [{"name": "runs"}]}),
            "src/dashboard/widgets/Runs.tsx": "",
            **{f"metrics/{n}.ts": body for n, body in metrics.items()},
        }
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(text)
        return subprocess.run([sys.executable, CHECKER], cwd=root, capture_output=True).returncode


def test_helper_without_fetchData_passes():
    assert run({"runs": "export const fetchData = 1", "cohort": "export const helper = 1"}) == 0


def test_named_metric_without_fetchData_fails():
    assert run({"runs": "export const helper = 1"}) == 1
