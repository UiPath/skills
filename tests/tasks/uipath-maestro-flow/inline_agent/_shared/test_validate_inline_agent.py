"""Tests for validate_inline_agent.py, with a fake `uip` on PATH."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_inline_agent.py")
AGENT_A = "11111111-1111-4111-8111-111111111111"
AGENT_B = "22222222-2222-4222-8222-222222222222"

# Answers per agent directory name: what `uip agent validate` prints.
FAKE_UIP = r'''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
assert args[:2] == ["agent", "validate"] and "--inline-in-flow" in args, args
answers = json.loads(os.environ["FAKE_UIP_ANSWERS"])
print(json.dumps(answers[os.path.basename(args[2])]))
'''

SUCCESS = {"Result": "Success", "Code": "AgentValidation"}
DRIFT = {
    "Result": "Failure",
    "Code": "AgentValidationDrift",
    "Message": "Derived artifacts are out of sync with source (1 issue(s))",
    "Data": {"Errors": ["/x/Flow/bindings_v2.json: missing"]},
}


def make_project(tmp: Path, agents: list[str]) -> Path:
    project = tmp / "Sol" / "Flow"
    project.mkdir(parents=True)
    nodes = [{"id": "start", "type": "uipath.core.trigger.manual"}]
    for i, source in enumerate(agents):
        (project / source).mkdir()
        (project / source / "agent.json").write_text("{}")
        nodes.append({"id": f"agent{i}", "type": "uipath.agent.autonomous", "inputs": {"source": source}})
    flow = project / "Flow.flow"
    flow.write_text(json.dumps({"nodes": nodes}))
    return flow


def run(tmp: Path, flow: Path, answers: dict) -> subprocess.CompletedProcess:
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)
    uip = bin_dir / "uip"
    uip.write_text(FAKE_UIP)
    uip.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
           "FAKE_UIP_ANSWERS": json.dumps(answers)}
    return subprocess.run([sys.executable, str(SCRIPT), str(flow)], capture_output=True, text=True, env=env)


def test_passes_when_every_agent_validates(tmp_path):
    flow = make_project(tmp_path, [AGENT_A, AGENT_B])
    result = run(tmp_path, flow, {AGENT_A: SUCCESS, AGENT_B: SUCCESS})
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("OK:") == 2


def test_fails_when_one_agent_drifts_and_names_the_error(tmp_path):
    flow = make_project(tmp_path, [AGENT_A, AGENT_B])
    result = run(tmp_path, flow, {AGENT_A: SUCCESS, AGENT_B: DRIFT})
    assert result.returncode == 1
    assert "AgentValidationDrift" in result.stderr
    assert "bindings_v2.json: missing" in result.stderr


def test_fails_on_a_flow_without_an_inline_agent(tmp_path):
    flow = make_project(tmp_path, [])
    result = run(tmp_path, flow, {})
    assert result.returncode == 1
    assert "uipath.agent.autonomous" in result.stderr


def test_fails_when_the_agent_directory_is_missing(tmp_path):
    flow = make_project(tmp_path, [AGENT_A])
    (flow.parent / AGENT_A / "agent.json").unlink()
    result = run(tmp_path, flow, {AGENT_A: SUCCESS})
    assert result.returncode == 1
    assert "agent.json does not exist" in result.stderr


def test_fails_when_uip_prints_no_envelope(tmp_path):
    flow = make_project(tmp_path, [AGENT_A])
    result = run(tmp_path, flow, {AGENT_A: "not an envelope"})
    # The fake prints a JSON string, not an object: reported, not a traceback.
    assert result.returncode == 1
    assert "printed no JSON envelope" in result.stderr
