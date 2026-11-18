#!/usr/bin/env python3
"""HttpRequestSingleCase: run the case once under debug and check what the
call did.

postman-echo.com/post answers only a POST and sends back the query, headers and
JSON body it received, so the echo is the effect: it proves the request went out
with the invoice number, the probe value and the `source` query the request
names. The grader reads it from the case variable the prompt names,
`echoResponse`, on the debug instance, and checks that the task that called the
service completed. Any task layout that does this passes.

Also refuses a credential header on an http-request task (none is needed, and
one would ship in caseplan.case).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from case_run_evidence import (  # noqa: E402
    RunEvidence,
    assert_completed,
    fail,
    read_run,
    since_iso,
    text_of,
)
from _shared.case_check import iter_tasks, read_caseplan, run_debug  # noqa: E402

URL = "postman-echo.com/post"
PROBE = "skills-case-http-7f3a"
INVOICE = "INV-1042"
QUERY_SOURCE = "skills-case-eval"
BOUND_VAR = "echoResponse"
CREDENTIAL_HEADERS = {"authorization", "proxy-authorization", "cookie", "x-api-key", "api-key"}


def check_no_credential_headers(plan: dict) -> None:
    for task in iter_tasks(plan):
        if task.get("type") != "http-request":
            continue
        for entry in (task.get("data") or {}).get("inputs") or []:
            body = entry.get("body") if isinstance(entry.get("body"), dict) else {}
            headers = body.get("headers") if isinstance(body.get("headers"), dict) else {}
            leaked = sorted(h for h in headers if str(h).lower() in CREDENTIAL_HEADERS)
            if leaked:
                fail(f"task {task.get('displayName')!r} sends credential header(s) {leaked}")


def calling_tasks(plan: dict, evidence: RunEvidence) -> list[dict]:
    """Tasks whose runtime inputs name the echo endpoint."""
    return [
        task for task in iter_tasks(plan)
        if URL in text_of(evidence.task_io_or_empty(str(task.get("id")))[0])
    ]


def check_run(plan: dict, payload: dict, evidence: RunEvidence) -> str:
    callers = calling_tasks(plan, evidence)
    if not callers:
        fail(f"no task in the run sent a request to {URL}")
    for task in callers:
        assert_completed(payload, task)

    echo = evidence.value(BOUND_VAR)
    echoed = text_of(echo)
    missing = [v for v in (PROBE, INVOICE, QUERY_SOURCE) if v.lower() not in echoed]
    if missing:
        fail(
            f"{BOUND_VAR} does not hold the echo of the request: {missing} missing from "
            f"{echoed[:800]}"
        )
    return ", ".join(repr(t.get("displayName")) for t in callers)


def main() -> None:
    plan = read_caseplan()
    check_no_credential_headers(plan)
    since = since_iso()
    payload = run_debug(timeout=540)
    evidence = read_run(payload, since)
    callers = check_run(plan, payload, evidence)
    print(
        f"OK: debug Completed; {callers} called {URL} and completed; {BOUND_VAR} holds "
        f"the echo of {INVOICE}, the probe and source={QUERY_SOURCE}"
    )


if __name__ == "__main__":
    main()
