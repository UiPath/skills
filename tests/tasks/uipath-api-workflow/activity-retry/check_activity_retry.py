#!/usr/bin/env python3
"""Grade per-activity (task-level) retry in an API workflow.

Modes:
  trycatch    In project `FlakyCompute`, a TryCatch whose catch carries `retry`
              (5 retries, 2000 ms, linear) around a JavaScript activity, a
              `catch.do` Response containing "failed", and a success-path Response.
  http        The seeded `HttpRequest_1` call sits in an `HttpRequest_1#Retry`
              wrapper without `catch.do`, whose `catch.retry` is 4 retries,
              1500 ms, exponential, with `when` exactly
              `${ [429, 503].includes($<catch.as>.status) }`. A TryCatch fails:
              Studio Web's TryCatch has no status filter and drops `when` on its
              next save. The call's `call`, `with`, `export` and non-display
              metadata must equal the seed; `activityType` / `displayName` /
              `fullName` may stay on the call or move to the wrapper. With the
              wrapper unwrapped, the rest of the workflow must equal the seed, and
              no workflow-level `httpRetryConfig` may be added.
  validation  `uip api-workflow validate` returns Valid, or reports only the
              documented validator gap of releases without UiPath/cli#5785.
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


ISO_DURATION_RE = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$")


def delay_ms(retry: dict[str, Any]) -> float | None:
    """Accept both delay forms the executor takes: an inline object or an ISO 8601 string."""
    delay = retry.get("delay")
    if isinstance(delay, str):
        match = ISO_DURATION_RE.match(delay)
        if not match:
            return None
        days, hours, minutes, seconds = (float(g or 0) for g in match.groups())
        return ((days * 24 + hours) * 60 + minutes) * 60_000 + seconds * 1000
    if not isinstance(delay, dict):
        return None
    return (
        (delay.get("days") or 0) * 86_400_000
        + (delay.get("hours") or 0) * 3_600_000
        + (delay.get("minutes") or 0) * 60_000
        + (delay.get("seconds") or 0) * 1000
        + (delay.get("milliseconds") or 0)
    )


def check_policy(retry: dict[str, Any], count: int, delay: int, backoff: str) -> list[str]:
    errors = []
    if ((retry.get("limit") or {}).get("attempt") or {}).get("count") != count:
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


def is_response(task: dict[str, Any]) -> bool:
    return "response" in task or (task.get("metadata") or {}).get("activityType") == "Response"


def check_trycatch(path: Path, document: dict[str, Any]) -> None:
    if path.parent.name != "FlakyCompute":
        fail(f"project folder is {path.parent.name!r}, expected 'FlakyCompute'")
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
        elif not any(is_response(t) and "failed" in json.dumps(t.get("response")) for _, t in tasks(catch["do"])):
            errors.append('catch.do returns no Response containing "failed"')
        catch_responses = {id(t) for _, t in tasks(catch.get("do")) if is_response(t)}
        if not any(is_response(t) and id(t) not in catch_responses for _, t in tasks(document.get("do"))):
            errors.append("no Response on the success path")
        if not any((t.get("metadata") or {}).get("activityType") == "JsInvoke" for _, t in tasks(task["try"])):
            errors.append("no JavaScript activity inside try")
        if not errors:
            return
        problems.append(f"{key}: {'; '.join(errors)}")
    fail(" | ".join(problems))


def unwrap(value: Any, owner_ids: set[int]) -> Any:
    """Copy of a task tree with each retry container replaced by its `try` list."""
    if isinstance(value, list):
        out: list[Any] = []
        for item in value:
            if isinstance(item, dict) and len(item) == 1:
                (key, task), = item.items()
                if id(task) in owner_ids:
                    out.extend(unwrap(task["try"], owner_ids))
                    continue
            out.append(unwrap(item, owner_ids))
        return out
    if isinstance(value, dict):
        return {key: unwrap(child, owner_ids) for key, child in value.items()}
    return value


# Exact copy of the regex in Studio Web's `parseStatusCondition`
# (packages/api-workflows-common/lib/translation/translators/retry-policy-translators.ts),
# also copied by `STATUS_CONDITION` in UiPath/cli api-workflow-tool's
# apiwf-validate-service.ts. Studio Web reads a status list back only in this form:
# group 1 is the code list, group 2 the error name.
STATUS_RE = re.compile(r"^\$\{\s*\[([\d,\s]*)\]\.includes\(\$([A-Za-z_$][\w$]*)\.status\)\s*\}$")

# Studio Web moves these from the call to its `#Retry` wrapper; a call that keeps
# them (a stub wrapped as-is) restores the same, so either place passes.
DISPLAY_KEYS = ("activityType", "displayName", "fullName")


def without_display(metadata: Any) -> Any:
    if not isinstance(metadata, dict):
        return metadata
    return {k: v for k, v in metadata.items() if k not in DISPLAY_KEYS}


def strip_call_display(value: Any) -> Any:
    """Copy of a task tree with HttpRequest_1's display metadata removed."""
    if isinstance(value, list):
        return [strip_call_display(item) for item in value]
    if isinstance(value, dict):
        return {
            key: (
                {**child, "metadata": without_display(child.get("metadata"))}
                if key == "HttpRequest_1" and isinstance(child, dict)
                else strip_call_display(child)
            )
            for key, child in value.items()
        }
    return value


def check_http(document: dict[str, Any], seed: dict[str, Any]) -> None:
    no_misplaced_retry(document)
    if "httpRetryConfig" in document:
        fail("workflow-level httpRetryConfig added; the request was per-activity retry")
    seed_call = next(task for key, task in tasks(seed.get("do")) if key == "HttpRequest_1")
    calls = [task for key, task in tasks(document.get("do")) if key == "HttpRequest_1"]
    if len(calls) != 1:
        fail(f"expected exactly one HttpRequest_1 task, found {len(calls)}")
    call = calls[0]
    for field in ("call", "with", "export"):
        if call.get(field) != seed_call.get(field):
            fail(f"HttpRequest_1.{field} changed; keep the registry-generated call as is")
    call_meta = call.get("metadata") or {}
    seed_meta = seed_call.get("metadata") or {}
    if without_display(call_meta) != without_display(seed_meta):
        fail("HttpRequest_1.metadata changed beyond moving activityType / displayName / fullName to the wrapper")
    for k in DISPLAY_KEYS:
        if k in call_meta and call_meta[k] != seed_meta.get(k):
            fail(f"HttpRequest_1.metadata.{k} changed")

    owners = [(key, task) for key, task in retried_try_tasks(document) if contains_key(task["try"], "HttpRequest_1")]
    if not owners:
        fail("HttpRequest_1 is not inside a try task with catch.retry")
    owner_ids = {id(task) for _, task in owners}
    if strip_call_display(unwrap(document.get("do"), owner_ids)) != strip_call_display(seed.get("do")):
        fail("tasks outside the retry container changed; leave the rest of the workflow as it is")
    for field in ("input", "output", "evaluate"):
        if document.get(field) != seed.get(field):
            fail(f"workflow {field} changed")
    problems = []
    for key, task in owners:
        catch = task["catch"]
        retry = catch["retry"]
        errors = check_policy(retry, count=4, delay=1500, backoff="exponential")
        when = retry.get("when")
        match = STATUS_RE.match(when) if isinstance(when, str) else None
        if not match:
            errors.append("retry.when is not exactly `${ [<codes>].includes($<as>.status) }`")
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
            wrapper_meta = task.get("metadata") or {}
            if wrapper_meta.get("activityType") != "Connector":
                errors.append("#Retry wrapper metadata.activityType must be 'Connector'")
            for k in DISPLAY_KEYS:
                if k not in call_meta and k in seed_meta and wrapper_meta.get(k) != seed_meta[k]:
                    errors.append(f"{k} left the call but is not on the wrapper")
        elif (task.get("metadata") or {}).get("activityType") == "TryCatch":
            errors.append(
                "status filter on a TryCatch: Studio Web drops `when` on save; "
                "use the HTTP Request's own Retry (HttpRequest_1#Retry)"
            )
        else:
            errors.append("retrying try is not an HttpRequest_1#Retry wrapper")
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
    if not isinstance(payload, dict):
        fail("validator JSON is not an object")
    if result.returncode == 0 and (payload.get("Data") or {}).get("Status") == "Valid":
        return
    instructions = str(payload.get("Instructions", ""))
    errors = ERROR_LINE_RE.findall(instructions)
    if errors and all(is_documented_gap(p, m) for p, m in errors):
        print("NOTE: only the documented task-level retry validator gap was reported")
        return
    fail(f"validate did not return Valid: {instructions}")


# The errors that `uip` releases without UiPath/cli#5785 report for valid task-level
# retry shapes. The skill tells agents to treat these, and only these, as a
# validator gap (references/http-retry-config.md, Validation Gap).
ERROR_LINE_RE = re.compile(r"^\s*- \[error\] \[([^\]]+)\] (.*)$", re.M)
GAP_WHEN_MESSAGES = (
    "Expected type 'object' but got a different type",
    "Expected type 'array' but got a different type",
    "Value must match exactly one of the allowed formats",
)


def is_documented_gap(path: str, message: str) -> bool:
    if path.endswith(("/catch/retry/when", "/catch/retry/exceptWhen")):
        return message in GAP_WHEN_MESSAGES
    return path.endswith("#Retry") and "has activityType 'Connector' but must contain 'call'" in message


def main() -> None:
    modes = {"trycatch", "http", "validation"}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        fail(f"usage: check_activity_retry.py {'|'.join(sorted(modes))}")
    path = workflow_path()
    document = load(path)
    mode = sys.argv[1]
    if mode == "trycatch":
        check_trycatch(path, document)
    elif mode == "http":
        seed = Path.cwd() / "_setup" / "seed-workflow.json"
        check_http(document, load(seed))
    else:
        check_validation(path)
    print(f"OK: activity retry {mode} check passed")


if __name__ == "__main__":
    main()
