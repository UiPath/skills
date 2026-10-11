#!/usr/bin/env python3
"""Golden scenario: run the agent's VAT-check workflow against the live EU VIES service
and compare `isValid` with the expected value.

The prompt names the output (`isValid`) but neither the input nor whether the
VAT number carries its country prefix, so several input contracts are tried (see
`input_candidates`). Expect true: some contract returns isValid true. Expect false: no
contract returns true and at least one returns false, so a hardcoded answer fails.

VIES itself is asked first. When it gives no answer (outage or saturation) or no longer
gives the expected one, the grader prints an `INFRA:` line and exits INFRA_EXIT. coder_eval
still scores that as a failed criterion, so leave INFRA runs out of reported pass rates.
"""
import argparse
import http.client
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "_setup"))
from eval_scoring import run_row  # noqa: E402

VIES_CHECK_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"
INFRA_EXIT = 3
BUDGET_SECONDS = 110
RUN_TIMEOUT = 45
VIES_TIMEOUT = 10
MAX_CANDIDATES = 8
COUNTRY_NAME = re.compile(r"country|member|state", re.IGNORECASE)
NUMBER_NAME = re.compile(r"vat|number|tax|cui|fiscal", re.IGNORECASE)
SIDE_FIELD = re.compile(r"^(requester|trader)", re.IGNORECASE)


class InfraError(Exception):
    pass


def find_workflow(root="."):
    root = Path(root).resolve()
    found = sorted((p for p in root.rglob("Workflow.json") if p.parent != root and "node_modules" not in p.parts),
                   key=str)
    return found[0] if found else None


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def declared_inputs(workflow):
    document = _as_dict(_as_dict(_as_dict(workflow.get("input")).get("schema")).get("document"))
    properties = document.get("properties")
    return list(properties)[:20] if isinstance(properties, dict) else []


def input_candidates(names, country, number):
    names = [n for n in names if not SIDE_FIELD.match(n)] or list(names)
    countries = [n for n in names if COUNTRY_NAME.search(n)]
    others = [n for n in names if n not in countries]
    numbers = [n for n in others if NUMBER_NAME.search(n)] or others or names
    candidates = []
    for name in numbers:
        candidates += [{name: f"{country}{number}"}, {name: number}]
    for country_name in countries:
        candidates += [{country_name: country, name: number} for name in numbers if name != country_name]
    if not countries and len(names) == 2:
        first, second = names
        candidates += [{first: country, second: number}, {first: number, second: country}]
    unique = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique[:MAX_CANDIDATES]


def is_valid_of(raw):
    if isinstance(raw, dict) and isinstance(raw.get("isValid"), bool):
        return raw["isValid"]
    return None


def verdict(observations, expected):
    """`observations` holds (inputs, isValid or None, detail) per run, across attempts."""
    summary = "; ".join(f"{json.dumps(inputs)} -> {detail}" for inputs, _, detail in observations)
    answers = [value for _, value, _ in observations if value is not None]
    if not answers:
        return False, f"no input contract returned a boolean isValid: {summary}"
    if expected and True in answers:
        return True, f"isValid true as expected: {summary}"
    if not expected and True not in answers:
        return True, f"isValid false as expected: {summary}"
    return False, f"isValid did not match expected {str(expected).lower()}: {summary}"


def vies_valid(country, number, deadline, attempts=3):
    """VIES's own answer as (valid, None), or (None, reason) when it gives no boolean."""
    body = json.dumps({"countryCode": country, "vatNumber": number}).encode()
    reason = "no time left to ask"
    for attempt in range(attempts):
        if attempt:
            pause = 5 * 2 ** (attempt - 1)
            if time.monotonic() + pause + VIES_TIMEOUT > deadline:
                break
            time.sleep(pause)
        request = urllib.request.Request(VIES_CHECK_URL, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=VIES_TIMEOUT) as response:
                payload = json.load(response)
        except (OSError, ValueError, http.client.HTTPException) as exc:
            reason = f"{type(exc).__name__}: {exc}"
            continue
        if isinstance(payload, dict) and isinstance(payload.get("valid"), bool):
            return payload["valid"], None
        errors = payload.get("errorWrappers") if isinstance(payload, dict) else None
        reason = json.dumps(errors or payload)[:200]
    return None, reason


def evaluate(workflow_path, candidates, deadline):
    observations = []
    for inputs in candidates:
        remaining = deadline - time.monotonic()
        if remaining < 10:
            observations.append((inputs, None, "not run: grading time budget used up"))
            continue
        try:
            ok, raw, error = run_row(workflow_path, inputs, timeout=int(min(RUN_TIMEOUT, remaining - 5)))
        except OSError as exc:
            raise InfraError(f"cannot run uip: {exc}") from exc
        observations.append((inputs, is_valid_of(raw) if ok else None, json.dumps(raw) if ok else error))
    return observations


def grade(workflow_path, candidates, country, number, expected, deadline):
    vat = f"{country}{number}"
    truth, reason = vies_valid(country, number, deadline)
    if truth is None:
        raise InfraError(f"VIES gave no answer for {vat} ({reason})")
    if truth != expected:
        raise InfraError(f"VIES now reports {vat} as {'valid' if truth else 'invalid'}; update the fixture")

    observations = evaluate(workflow_path, candidates, deadline)
    passed, summary = verdict(observations, expected)
    definitive = not expected and any(value is True for _, value, _ in observations)
    if not passed and not definitive and deadline - time.monotonic() > 20:
        truth, reason = vies_valid(country, number, deadline)
        if truth is None:
            raise InfraError(f"VIES stopped answering for {vat} mid-run ({reason})")
        observations += evaluate(workflow_path, candidates, deadline)
        passed, summary = verdict(observations, expected)
    return passed, summary


def main(argv=None):
    deadline = time.monotonic() + BUDGET_SECONDS
    parser = argparse.ArgumentParser(description="Grade the golden VAT-check API workflow against live VIES.")
    parser.add_argument("--vat", required=True, help="VAT id with its country prefix, e.g. RO34737997")
    parser.add_argument("--expect", required=True, choices=["true", "false"])
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Z]{2}[0-9A-Z]+", args.vat):
        parser.error("--vat must be a country prefix followed by the number, e.g. RO34737997")
    country, number, expected = args.vat[:2], args.vat[2:], args.expect == "true"

    workflow_path = find_workflow()
    if workflow_path is None:
        sys.exit("FAIL: no Workflow.json inside a project folder")
    shown = workflow_path.relative_to(Path.cwd().resolve())
    try:
        workflow = json.loads(workflow_path.read_text())
    except (OSError, ValueError) as exc:
        sys.exit(f"FAIL: {shown} is not readable JSON: {exc}")
    if not isinstance(workflow, dict):
        sys.exit(f"FAIL: {shown} is not a workflow object")
    names = declared_inputs(workflow)
    candidates = input_candidates(names, country, number)
    if not candidates:
        sys.exit(f"FAIL: {shown} declares no workflow inputs; the VAT number must be an input")

    try:
        passed, summary = grade(workflow_path, candidates, country, number, expected, deadline)
    except InfraError as exc:
        print(f"INFRA: {exc}; this run says nothing about {shown}", file=sys.stderr)
        return INFRA_EXIT
    if not passed:
        sys.exit(f"FAIL: {shown}: {summary}")
    print(f"OK: {shown}: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
