#!/usr/bin/env python3
"""Grade per-activity (task-level) retry in an API workflow.

Modes:
  trycatch    A TryCatch whose catch carries `retry` (5 retries, 2000 ms, linear)
              around a JavaScript activity, with a non-empty `catch.do`.
  http        The seeded `HttpRequest_1` call sits inside a `try` whose catch
              carries `retry` (4 retries, 1500 ms, exponential, `when` filtering on
              exactly 429 and 503 via `$<catch.as>.status`). Accepts both Studio Web
              shapes: a TryCatch, or an `HttpRequest_1#Retry` wrapper without
              `catch.do`. The call itself must be unchanged and no workflow-level
              `httpRetryConfig` may be added.
  validation  `uip api-workflow validate` returns Valid.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator, NoReturn


def fail(message: str) -> NoReturn:
    sys.exit(f"FAIL: {message}")


def workflow_path() -> Path:
    matches = sorted(
        path
        for path in Path.cwd().rglob("Workflow.json")
        if "node_modules" not in path.parts
        and "_setup" not in path.parts
        and path.parent != Path.cwd()
    )
    if len(matches) != 1:
        fail(f"expected one project Workflow.json, found {len(matches)}")
    return matches[0]


def load(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON from {path}: {exc}")
    if not isinstance(document, dict):
        fail("Workflow.json root must be an object")
    return document


def tasks(value: Any) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield every (key, task) pair in a task list tree."""
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(child, dict) and any(k in child for k in ("call", "try", "do", "run", "set", "for", "response")):
                yield key, child
            yield from tasks(child)
    elif isinstance(value, list):
        for child in value:
            yield from tasks(child)


def direct_keys(task_list: Any) -> list[str]:
    return [k for item in task_list or [] if isinstance(item, dict) for k in item]


def contains_key(task_list: Any, wanted: str) -> bool:
    return any(key == wanted for key, _ in tasks(task_list))


def retried_try_tasks(document: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    return [
        (key, task)
        for key, task in tasks(document.get("do"))
        if isinstance(task.get("try"), list) and isinstance(task.get("catch"), dict) and isinstance(task["catch"].get("retry"), dict)
    ]


def delay_ms(retry: dict[str, Any]) -> float | None:
    delay = retry.get("delay")
    if not isinstance(delay, dict):
        return None
    return (
        delay.get("milliseconds", 0)
        + delay.get("seconds", 0) * 1000
        + delay.get("minutes", 0) * 60_000
    )


def check_policy(retry: dict[str, Any], count: int, delay: int, backoff: str) -> list[str]:
    errors = []
    if (retry.get("limit") or {}).get("attempt", {}).get("count") != count:
        errors.append(f"limit.attempt.count != {count}")
    if delay_ms(retry) != delay:
        errors.append(f"delay != {delay} ms")
    if not isinstance(retry.get("backoff"), dict) or backoff not in retry["backoff"]:
        errors.append(f"backoff is not {{ {backoff}: ... }}")
    return errors


def no_misplaced_retry(document: dict[str, Any]) -> None:
    for key, task in tasks(document.get("do")):
        if key != "catch" and ("retry" in task or "retryConfig" in task):
            fail(f"`retry` placed directly on task {key}; it belongs in catch.retry")


def check_trycatch(document: dict[str, Any]) -> None:
    no_misplaced_retry(document)
    candidates = [
        (key, task)
        for key, task in retried_try_tasks(document)
        if (task.get("metadata") or {}).get("activityType") == "TryCatch"
    ]
    if not candidates:
        fail("no TryCatch activity with catch.retry")
    problems = []
    for key, task in candidates:
        catch = task["catch"]
        errors = check_policy(catch["retry"], count=5, delay=2000, backoff="linear")
        if not isinstance(catch.get("as"), str) or not catch["as"]:
            errors.append("catch.as missing")
        if not catch.get("do"):
            errors.append("catch.do empty")
        if not any((t.get("metadata") or {}).get("activityType") == "JsInvoke" for _, t in tasks(task["try"])):
            errors.append("no JavaScript activity inside try")
        if not errors:
            return
        problems.append(f"{key}: {'; '.join(errors)}")
    fail(" | ".join(problems))


STATUS_RE = re.compile(r"\[([\d,\s]*)\]\s*\.includes\(\s*\$([A-Za-z_$][\w$]*)\.status\s*\)")


def check_http(document: dict[str, Any], seed: dict[str, Any]) -> None:
    no_misplaced_retry(document)
    if "httpRetryConfig" in document:
        fail("workflow-level httpRetryConfig added; the request was per-activity retry")
    seed_call = next(task for key, task in tasks(seed.get("do")) if key == "HttpRequest_1")
    calls = [task for key, task in tasks(document.get("do")) if key == "HttpRequest_1"]
    if len(calls) != 1:
        fail(f"expected exactly one HttpRequest_1 task, found {len(calls)}")
    call = calls[0]
    for field in ("call", "with", "metadata", "export"):
        if call.get(field) != seed_call.get(field):
            fail(f"HttpRequest_1.{field} changed; keep the registry-generated call as is")

    owners = [(key, task) for key, task in retried_try_tasks(document) if contains_key(task["try"], "HttpRequest_1")]
    if not owners:
        fail("HttpRequest_1 is not inside a try task with catch.retry")
    problems = []
    for key, task in owners:
        catch = task["catch"]
        retry = catch["retry"]
        errors = check_policy(retry, count=4, delay=1500, backoff="exponential")
        when = retry.get("when")
        match = STATUS_RE.search(when) if isinstance(when, str) else None
        if not match:
            errors.append("retry.when is not a `[...].includes($<as>.status)` filter")
        else:
            codes = {int(c) for c in match.group(1).replace(" ", "").split(",") if c}
            if codes != {429, 503}:
                errors.append(f"status filter {sorted(codes)} != [429, 503]")
            if match.group(2) != catch.get("as", "error"):
                errors.append(f"filter reads ${match.group(2)} but catch.as is {catch.get('as')!r}")
        if key.endswith("#Retry"):
            if key != "HttpRequest_1#Retry":
                errors.append("wrapper key must be HttpRequest_1#Retry")
            if "do" in catch:
                errors.append("#Retry wrapper must not have catch.do")
            if direct_keys(task["try"]) != ["HttpRequest_1"]:
                errors.append("#Retry wrapper try must hold only the call")
        elif (task.get("metadata") or {}).get("activityType") != "TryCatch":
            errors.append("retrying try is neither a TryCatch nor an <id>#Retry wrapper")
        if not errors:
            return
        problems.append(f"{key}: {'; '.join(errors)}")
    fail(" | ".join(problems))


def check_validation(path: Path) -> None:
    result = subprocess.run(
        ["uip", "api-workflow", "validate", str(path), "--output", "json"],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"validator did not return JSON: {exc}")
    if result.returncode != 0 or payload.get("Data", {}).get("Status") != "Valid":
        fail(f"validate did not return Valid: {payload.get('Instructions', '')}")


def main() -> None:
    modes = {"trycatch", "http", "validation"}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        fail(f"usage: check_activity_retry.py {'|'.join(sorted(modes))}")
    path = workflow_path()
    document = load(path)
    mode = sys.argv[1]
    if mode == "trycatch":
        check_trycatch(document)
    elif mode == "http":
        seed = Path.cwd() / "_setup" / "seed-workflow.json"
        check_http(document, load(seed))
    else:
        check_validation(path)
    print(f"OK: activity retry {mode} check passed")


if __name__ == "__main__":
    main()
