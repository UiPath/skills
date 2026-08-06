"""Regression tests for the mock uip dispatcher's hardened channels.

Guards the three fixes in mock_src/uip.py:
  1. Passthrough is cache-only - a cache miss must never start the real
     `uip` CLI (previously it proxied agent-controlled argv to a live,
     credentialed process).
  2. Cache entries are validated (schema + args match + HMAC provenance)
     before replay, so an agent-planted file in the sandbox is rejected.
  3. A call-log write failure fails the invocation loudly instead of being
     swallowed (previously `chmod`/dir-swap on m/.log silently blanked the
     coverage log while uip kept answering).

Also covers the operator-only recorder (scripts/record_passthrough.py)
end to end: record with a stub CLI, then replay through the dispatcher.

Run from repo root:
    pytest tests/tasks/uipath-troubleshoot/_shared/scripts/test_mock_dispatcher.py
"""

import importlib.util
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parents[1]
UIP_SRC = SHARED_DIR / "mock_src" / "uip.py"
RECORDER = SHARED_DIR / "scripts" / "record_passthrough.py"

DEFAULT_RESPONSE = "[]\n"
FIXTURE_BODY = '{"jobs": []}\n'


def _load_uip_module():
    spec = importlib.util.spec_from_file_location("mock_uip_under_test", UIP_SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


uip_mod = _load_uip_module()


def _make_mock_dir(tmp_path: Path, manifest: dict) -> Path:
    """Stage an unsealed mock dir: dispatcher source + r/ fixtures."""
    mock_dir = tmp_path / "m"
    responses = mock_dir / "r"
    responses.mkdir(parents=True)
    (mock_dir / "uip.py").write_bytes(UIP_SRC.read_bytes())
    (responses / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (responses / "jobs.json").write_bytes(FIXTURE_BODY.encode("utf-8"))
    return mock_dir


def _make_fake_real_uip(tmp_path: Path) -> tuple[Path, Path]:
    """Create a stand-in for the real `uip` CLI that records being executed.

    Returns (bin_dir_for_PATH, marker_path). If any code under test starts a
    real `uip`, the marker file appears.
    """
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    marker = tmp_path / "live_cli_executed"
    payload = '{"answer": "LIVE TENANT RESPONSE"}'
    (bin_dir / "uip.cmd").write_text(
        f'@echo off\necho executed> "{marker}"\necho {payload}\n', encoding="utf-8"
    )
    posix_stub = bin_dir / "uip"
    posix_stub.write_text(f'#!/bin/sh\necho executed > "{marker}"\necho \'{payload}\'\n', encoding="utf-8")
    posix_stub.chmod(posix_stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir, marker


def _run_uip(mock_dir: Path, cli_args: list[str], path_prepend: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if path_prepend is not None:
        env["PATH"] = str(path_prepend) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        [sys.executable, str(mock_dir / "uip.py"), *cli_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _signed_entry(args_str: str, stdout: str, exit_code: int = 0) -> dict:
    entry = {
        "args": args_str,
        "stdout": stdout,
        "exit_code": exit_code,
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    entry["sig"] = uip_mod._cache_sig(entry)
    return entry


def _write_cache(mock_dir: Path, entry: dict) -> Path:
    cache_dir = mock_dir / "_cache"
    cache_dir.mkdir(exist_ok=True)
    path = cache_dir / f"{uip_mod._cache_key(entry['args'])}.json"
    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    return path


def _read_log(mock_dir: Path) -> list[dict]:
    log = mock_dir / ".log"
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


MANIFEST = {
    "version": 2,
    "rules": [
        {"match": "docsai ask", "passthrough": True},
        {"match": "or jobs list", "file": "jobs.json"},
    ],
    "unmocked_default": {"response": DEFAULT_RESPONSE, "exit_code": 0},
}


def test_cache_hit_replays_recorded_response(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    bin_dir, marker = _make_fake_real_uip(tmp_path)
    recorded = _signed_entry("docsai ask how do I retry a job", '{"answer": "recorded"}\n', exit_code=0)
    _write_cache(mock_dir, recorded)

    proc = _run_uip(mock_dir, ["docsai", "ask", "how", "do", "I", "retry", "a", "job"], bin_dir)

    assert proc.returncode == 0
    assert proc.stdout == '{"answer": "recorded"}\n'
    assert not marker.exists(), "cache hit must not start the real CLI"
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cached"


def test_cache_miss_never_starts_live_cli(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    bin_dir, marker = _make_fake_real_uip(tmp_path)

    proc = _run_uip(mock_dir, ["docsai", "ask", "a", "query", "nobody", "recorded"], bin_dir)

    assert not marker.exists(), "cache miss must not start the real CLI"
    assert proc.returncode == 0
    assert proc.stdout == DEFAULT_RESPONSE, "miss must fall through to unmocked_default"
    assert "LIVE TENANT RESPONSE" not in proc.stdout
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cache_miss"


def test_cache_miss_without_default_errors_explicitly(tmp_path):
    manifest = {k: v for k, v in MANIFEST.items() if k != "unmocked_default"}
    mock_dir = _make_mock_dir(tmp_path, manifest)
    bin_dir, marker = _make_fake_real_uip(tmp_path)

    proc = _run_uip(mock_dir, ["docsai", "ask", "something"], bin_dir)

    assert not marker.exists()
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "error" in proc.stderr


def test_tampered_cache_entry_is_rejected(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    bin_dir, marker = _make_fake_real_uip(tmp_path)
    entry = _signed_entry("docsai ask q", '{"answer": "recorded"}\n')
    entry["stdout"] = '{"answer": "TAMPERED"}\n'  # signature no longer matches
    _write_cache(mock_dir, entry)

    proc = _run_uip(mock_dir, ["docsai", "ask", "q"], bin_dir)

    assert "TAMPERED" not in proc.stdout
    assert proc.stdout == DEFAULT_RESPONSE
    assert not marker.exists()
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cache_invalid"


def test_planted_unsigned_cache_entry_is_rejected(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    args_str = "docsai ask planted"
    cache_dir = mock_dir / "_cache"
    cache_dir.mkdir()
    planted = {"args": args_str, "stdout": '{"answer": "PLANTED"}\n', "exit_code": 0}
    (cache_dir / f"{uip_mod._cache_key(args_str)}.json").write_text(json.dumps(planted), encoding="utf-8")

    proc = _run_uip(mock_dir, ["docsai", "ask", "planted"])

    assert "PLANTED" not in proc.stdout
    assert proc.stdout == DEFAULT_RESPONSE
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cache_invalid"


def test_cache_entry_for_other_args_is_rejected(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    # Validly signed entry for query A, planted under query B's key.
    entry = _signed_entry("docsai ask query A", '{"answer": "for A"}\n')
    cache_dir = mock_dir / "_cache"
    cache_dir.mkdir()
    key = uip_mod._cache_key("docsai ask query B")
    (cache_dir / f"{key}.json").write_text(json.dumps(entry), encoding="utf-8")

    proc = _run_uip(mock_dir, ["docsai", "ask", "query", "B"])

    assert proc.stdout == DEFAULT_RESPONSE
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cache_invalid"


def test_log_write_failure_is_loud(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    (mock_dir / ".log").mkdir()  # cross-platform stand-in for chmod 000

    proc = _run_uip(mock_dir, ["or", "jobs", "list"])

    assert proc.returncode == 3, "a suppressed log must fail the invocation"
    assert FIXTURE_BODY not in proc.stdout, "no response may be emitted when the call cannot be logged"
    assert "error" in proc.stderr


def test_log_intact_baseline_still_serves_fixture(tmp_path):
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)

    proc = _run_uip(mock_dir, ["or", "jobs", "list"])

    assert proc.returncode == 0
    assert proc.stdout == FIXTURE_BODY
    assert _read_log(mock_dir)[-1]["matched_rule"] == "or jobs list"


def test_recorder_roundtrip(tmp_path):
    # Operator records with a stub `uip` on PATH; dispatcher then replays.
    scenario = tmp_path / "scenario"
    responses = scenario / "data" / "m" / "r"
    responses.mkdir(parents=True)
    (responses / "manifest.json").write_text(json.dumps(MANIFEST), encoding="utf-8")
    bin_dir, marker = _make_fake_real_uip(tmp_path)

    env = os.environ.copy()
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    rec = subprocess.run(
        [sys.executable, str(RECORDER), str(scenario), "--", "docsai", "ask", "what is a queue"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    assert rec.returncode == 0, rec.stderr
    assert marker.exists(), "recorder is the one path that runs the real CLI"

    key = uip_mod._cache_key("docsai ask what is a queue")
    cache_file = responses / "_cache" / f"{key}.json"
    assert cache_file.is_file()
    entry = json.loads(cache_file.read_text(encoding="utf-8"))
    assert uip_mod._cache_entry_valid(entry, "docsai ask what is a queue")

    # Stage the recorded entry the way a sandbox sees it (legacy r/_cache
    # location, which the dispatcher checks too) and replay it.
    marker.unlink()
    mock_dir = _make_mock_dir(tmp_path, MANIFEST)
    legacy_cache = mock_dir / "r" / "_cache"
    legacy_cache.mkdir()
    (legacy_cache / cache_file.name).write_bytes(cache_file.read_bytes())

    proc = _run_uip(mock_dir, ["docsai", "ask", "what", "is", "a", "queue"], bin_dir)

    assert proc.returncode == 0
    assert "LIVE TENANT RESPONSE" in proc.stdout
    assert not marker.exists(), "replay must not start the real CLI"
    assert _read_log(mock_dir)[-1]["error"] == "passthrough_cached"


def test_dispatcher_source_has_no_process_spawning():
    # Structural guard: the agent-facing dispatcher must not even import a
    # process-spawning module - re-recording lives in record_passthrough.py.
    source = UIP_SRC.read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "os.exec" not in source and "os.spawn" not in source and "os.system" not in source
