#!/usr/bin/env python3
"""HttpRequestSingleCase: the http-request task carries the SDD's request and
its Outputs arrow row, no header holds a credential, and debug echoes the
probe back from postman-echo.com."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    assert_outputs_contain,
    assert_task_type_present,
    run_debug,
)

URL = "https://postman-echo.com/post"
PROBE = "skills-case-http-7f3a"
BOUND_VAR = "echoResponse"
# Any of these in the request would ship a credential in caseplan.case.
CREDENTIAL_HEADERS = {"authorization", "proxy-authorization", "cookie", "x-api-key", "api-key"}


def request_body(task: dict) -> dict:
    for entry in (task.get("data") or {}).get("inputs") or []:
        if entry.get("name") == "body" and isinstance(entry.get("body"), dict):
            return entry["body"]
    sys.exit("FAIL: the http-request task has no `body` input carrying the request.")


def check_structure(task: dict) -> None:
    data = task.get("data") or {}
    if data.get("serviceType") != "Intsvc.UnifiedHttpRequest":
        sys.exit(f"FAIL: serviceType is {data.get('serviceType')!r}, expected 'Intsvc.UnifiedHttpRequest'.")
    req = request_body(task)
    if req.get("authentication") != "manual":
        sys.exit(f"FAIL: authentication is {req.get('authentication')!r}; the SDD names no connector.")
    if str(req.get("method", "")).upper() != "POST":
        sys.exit(f"FAIL: method is {req.get('method')!r}, expected POST.")
    if req.get("url") != URL:
        sys.exit(f"FAIL: url is {req.get('url')!r}, expected {URL!r}.")
    if PROBE not in str(req.get("body")):
        sys.exit(f"FAIL: the request body does not carry the SDD's probe value: {req.get('body')!r}")
    if not isinstance(req.get("query"), dict) or req["query"].get("source") != "skills-case-eval":
        sys.exit(f"FAIL: query is {req.get('query')!r}, expected the SDD's {{'source': 'skills-case-eval'}}.")
    headers = req.get("headers") if isinstance(req.get("headers"), dict) else {}
    leaked = sorted(h for h in headers if str(h).lower() in CREDENTIAL_HEADERS)
    if leaked:
        sys.exit(f"FAIL: request headers carry credential header(s) {leaked}; authenticate with a connection.")

    body_out = next((o for o in data.get("outputs") or [] if o.get("name") == "body"), None)
    if body_out is None:
        sys.exit("FAIL: the http-request task has no `body` output.")
    if body_out.get("var") != BOUND_VAR or body_out.get("source") != "=response.body":
        sys.exit(
            f"FAIL: the SDD's `Body -> {BOUND_VAR}` row did not bind: body output has "
            f"var={body_out.get('var')!r}, source={body_out.get('source')!r}."
        )


def main():
    task = assert_task_type_present("http-request")
    check_structure(task)
    payload = run_debug(timeout=540)
    # postman-echo returns the posted JSON under `json`, so the probe reaching the
    # outputs proves the request went out and the response landed in the variable.
    assert_outputs_contain(payload, PROBE)
    print(f"OK: http-request task wired (displayName={task.get('displayName')!r}); "
          f"debug Completed and echoed {PROBE!r}")


if __name__ == "__main__":
    main()
