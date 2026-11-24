#!/usr/bin/env python3
"""Reduce a coder-eval run dir to publishable result files; fail closed.

Runs carry a live UiPath login, so nothing agent- or grader-authored is trusted:

* Allow-list of files (see `allowed`); everything else is deleted unopened.
* Per-task reports are REBUILT from allow-listed structured fields only (status,
  scores, timings, criterion description/score/threshold/gating): `task.json` is
  rewritten and `task.html` re-rendered (html-escaped) from that data. Agent
  iterations, judge transcripts, criterion details/errors and command output are
  never copied, so no renderer escaping can hide a credential in them.
* Other kept files (`run.*`, `experiment.*`, `variant.*`, `task.log`) must be strict
  UTF-8 text; every forwarded secret and every UiPath token issued in the run is
  replaced verbatim, then a verify pass re-reads each file once.
* Task text is redacted before it is serialized to JSON or HTML (escaping would hide a
  secret from a byte match). A missing or non-object `run.json`, an unreadable
  `task.json`, a scheduled task id without a result in every variant, or a result
  nobody scheduled means the run is incomplete. Scheduled ids are exact: a task's `task_id`,
  or `<task_id>/<row>` for every dataset row; `ID!sampled` (a sampled dataset) is inconclusive.
* A `publication-disabled` flag in $RUNNER_TEMP (written when a rotated token could
  not be recorded), a missing issued-tokens record under CI, or any error wipes the
  run dir (best effort), prints a fixed message and exits 1. Publishing steps
  require this step's success.

Usage: scrub-run-artifacts.py <run_dir> [--expect-ids "ID ID/ROW ..."]
"""

from __future__ import annotations

import html
import json
import os
import pathlib
import re
import shutil
import sys

SECRET_ENV = (
    "AWS_BEARER_TOKEN_BEDROCK",
    "CODEX_API_KEY",
    "GEMINI_API_KEY",
    "E2E_PROCESS_KEY",
    "E2E_LONG_PROCESS_KEY",
    "UIPATH_ROPC_CLIENT_SECRET",
    "UIPATH_BOT_PASSWORD",
    "UIPATH_CLI_AUTH_TOKEN",
)
TOP_LEVEL = frozenset({"run.json", "run.md", "experiment.json", "experiment.md", "experiment.html", "experiment.log"})
VARIANT_LEVEL = frozenset({"variant.json", "variant.md", "variant.html"})
TASK_LEVEL = frozenset({"task.json", "task.log", "task.html"})
MIN_TOKEN = 28
_REPLICATE = re.compile(r"\d+")
# Structured fields copied into the published task.json (nothing free-form).
_TASK_FIELDS = (
    "task_id", "variant_id", "agent_type", "model_used", "started_at", "completed_at",
    "duration_seconds", "setup_ms", "grading_ms", "final_status", "max_turns_exhausted",
    "weighted_score", "iteration_count", "error_phase",
)
_CRITERION_FIELDS = (
    "result_kind", "criterion_type", "description", "score", "evaluation_status", "pass_threshold", "gating",
)
_STR_CAP = 2000


def allowed(rel: pathlib.PurePosixPath) -> bool:
    parts = rel.parts
    if "artifacts" in parts[:-1]:
        return False
    if len(parts) == 1:
        return parts[0] in TOP_LEVEL
    if len(parts) == 2:
        return parts[1] in VARIANT_LEVEL
    # <variant>/<task>/<NN>/ or, for a dataset row, <variant>/<suite>/<row>/<NN>/
    return len(parts) in (4, 5) and bool(_REPLICATE.fullmatch(parts[-2])) and parts[-1] in TASK_LEVEL


def _is_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _scalar(value: object, needles: list[bytes]) -> object:
    """Redact the whole string, then truncate: a token spanning the cap must not leave its prefix."""
    if isinstance(value, str):
        return _redact_value(value, needles)[:_STR_CAP]
    return value if isinstance(value, (bool, int, float)) or value is None else None


def _criteria(items: object, needles: list[bytes]) -> list[dict]:
    if not isinstance(items, list):
        return []
    return [{k: _scalar(c.get(k), needles) for k in _CRITERION_FIELDS} for c in items if isinstance(c, dict)]


def _redact_value(value: object, needles: list[bytes]) -> object:
    if isinstance(value, str):
        return _replace(value.encode("utf-8"), needles).decode("utf-8")
    return value


def sanitize_task(raw: dict, needles: list[bytes]) -> dict:
    """Structured fields only, redacted before any JSON or HTML serialization escapes them."""
    out = {k: _scalar(raw.get(k), needles) for k in _TASK_FIELDS}
    for key in ("success_criteria_results", "post_failure_criteria_results"):
        out[key] = _criteria(raw.get(key), needles)
    return out


def render_task_html(task: dict) -> str:
    esc = lambda v: html.escape("" if v is None else str(v))  # noqa: E731
    rows = "".join(
        f"<tr><td>{esc(c['description'])}</td><td>{esc(c['criterion_type'])}</td><td>{esc(c['score'])}</td>"
        f"<td>{esc(c['pass_threshold'])}</td><td>{esc(c['evaluation_status'])}</td></tr>"
        for c in task["success_criteria_results"] + task["post_failure_criteria_results"]
    )
    head = "".join(f"<li>{esc(k)}: {esc(task[k])}</li>" for k in _TASK_FIELDS)
    return (
        "<!doctype html><meta charset=utf-8><title>task result</title>"
        f"<h1>{esc(task['task_id'])}</h1><ul>{head}</ul>"
        "<table><tr><th>criterion</th><th>type</th><th>score</th><th>threshold</th><th>status</th></tr>"
        f"{rows}</table><p>Reduced report: agent output, judge transcripts and criterion details are not published.</p>"
    )


def _values(env: dict[str, str], auth_file: pathlib.Path, issued: pathlib.Path) -> list[bytes]:
    values = [env[n] for n in SECRET_ENV if len(env.get(n, "")) >= 8]
    for source, prefixes in ((auth_file, ("UIPATH_ACCESS_TOKEN=", "UIPATH_REFRESH_TOKEN=")), (issued, ())):
        if source.is_file():
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if prefixes:  # tokens only: org/tenant slugs would garble reports
                    line = next((line.split("=", 1)[1] for p in prefixes if line.startswith(p)), "")
                if len(line) > MIN_TOKEN:
                    values.append(line)
    return sorted({v.encode("utf-8") for v in values}, key=len, reverse=True)


def _replace(data: bytes, needles: list[bytes]) -> bytes:
    for needle in needles:
        data = data.replace(needle, b"***")
    return data


def check_coverage(found: dict[str, set[str]], expected_ids: list[str]) -> None:
    """Every expected task or dataset row has a result in every variant, and no result is unexpected."""
    if not found:
        raise RuntimeError("no variant results")
    if any("!" in e for e in expected_ids):  # a sampled dataset: the runner's row selection is not knowable here
        raise RuntimeError("dataset row selection unknown")
    expected = set(expected_ids)
    for ids in found.values():
        if ids != expected:
            raise RuntimeError("task results do not match the scheduled tasks")


def scrub(root: pathlib.Path, needles: list[bytes], expect_ids: list[str] | None = None) -> int:
    """Reduce `root` in place; returns the number of withheld files."""
    withheld = 0
    found: dict[str, set[str]] = {}
    run_manifest = False
    kept: list[pathlib.Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        rel = pathlib.PurePosixPath(path.relative_to(root).as_posix())
        if path.is_symlink() or not path.is_file() or not allowed(rel):  # never opened
            path.unlink()
            withheld += 1
            continue
        data = path.read_bytes()
        if not _is_text(data):
            if rel.name in ("run.json", "task.json"):
                raise RuntimeError("required result unreadable")
            path.unlink()
            withheld += 1
            continue
        if rel.name == "task.json":
            task = sanitize_task(json.loads(data), needles)
            if not task["task_id"] or task["final_status"] is None:
                raise RuntimeError("task result incomplete")
            if "/".join(rel.parts[1:-2]) != task["task_id"]:  # coder-eval derives the dir from the id
                raise RuntimeError("task result misplaced")
            ids = found.setdefault(rel.parts[0], set())
            ids.add(task["task_id"])
            data = json.dumps(task, indent=2).encode("utf-8")
            (path.parent / "task.html").write_bytes(render_task_html(task).encode("utf-8"))
        elif rel == pathlib.PurePosixPath("run.json"):
            if not isinstance(json.loads(data), dict):
                raise RuntimeError("run manifest unreadable")
            run_manifest = True
        elif rel.name == "task.html":
            continue  # re-rendered from its task.json
        path.write_bytes(_replace(data, needles))
        kept.append(path)
    for html_path in root.rglob("task.html"):  # a task.html without a task.json is not published
        if not (html_path.parent / "task.json").is_file():
            html_path.unlink()
            withheld += 1
    for html_path in root.rglob("task.html"):
        kept.append(html_path)
        html_path.write_bytes(_replace(html_path.read_bytes(), needles))
    if not run_manifest:
        raise RuntimeError("run manifest missing")
    if expect_ids is not None:
        check_coverage(found, expect_ids)
    for path in kept:  # verify, one read per file
        data = path.read_bytes()
        if any(n in data for n in needles):
            raise RuntimeError("secret survived the scrub")
    return withheld


def _wipe(root: pathlib.Path) -> None:
    try:
        children = list(root.iterdir()) if root.is_dir() else []
    except OSError:
        children = []
    for child in children:
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        except OSError:
            pass  # best effort; publication is blocked by the exit code


def main(argv: list[str]) -> int:
    try:
        root = pathlib.Path(argv[1])
        expect = argv[argv.index("--expect-ids") + 1].split() if "--expect-ids" in argv else None
        runner_temp = pathlib.Path(os.environ.get("RUNNER_TEMP", ""))
        issued = runner_temp / "issued-tokens"
        if os.environ.get("GITHUB_ACTIONS"):
            if (runner_temp / "publication-disabled").exists():
                raise RuntimeError("publication disabled")
            if not _values({}, pathlib.Path(os.devnull), issued):
                raise RuntimeError("no issued-tokens record")
        needles = _values(dict(os.environ), pathlib.Path(os.path.expanduser("~/.uipath/.auth")), issued)
        withheld = scrub(root, needles, expect)
    except BaseException:  # fixed message only: never echo a value or a path
        if len(argv) > 1:
            _wipe(pathlib.Path(argv[1]))
        print("::error::scrub failed; run files withheld from publication")
        return 1
    print(f"::notice::{withheld} file(s) outside the publication allow-list withheld")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
