#!/usr/bin/env python3
"""Cross-check the guardrail catalog's availability against what the report claims.

WHAT THIS FIXES. The paired `command_executed` criterion on
`uip\\s+agent\\s+guardrails\\s+catalog` carries `require_success: true`, which
reads the *wrapper's* exit code (`agents/codex_agent.py`). Agents batch several
CLI calls into one `bash -lc` script that opens `set +e` and closes `exit 0`, so
the wrapper always reports success. Observed twice in live Codex runs: the
criterion scored 1.00 while the command itself returned
`unknown command 'catalog'`. That is a silent false pass -- the eval reported
catalog-grounded findings as verified when the catalog was never read.

WHAT THIS DOES NOT DO. Unlike the review-CLI provenance check, this cannot prove
the AGENT fetched the catalog. There is no artifact to prove it with: the
catalog's unique fields (`DetectionMethod`, `Examples[].Name`) are never required
in a report, the mandated "matched catalog clause" is paraphrased in practice,
and the `.guardrails-catalog-cache.json` that Step 0 asks for was absent from the
final sandbox in 10 of 10 measured runs (agents redirect to /tmp, pipe to `head`,
or clean up). So the paired `command_executed` is deliberately KEPT as the
behavioural signal, and this criterion closes the hole that flag cannot:
it establishes whether the catalog was actually reachable, and holds the report
to the skill's contract for the unreachable case.

  reachable + report silent            -> PASS   (normal healthy run)
  reachable + report says unavailable  -> FAIL   (contradiction; usually a CLI
                                                  divergence, sometimes a false claim)
  unreachable + report says unavailable-> PASS   (Critical Rule 11 honoured)
  unreachable + report silent          -> FAIL   (catalog-grounded verdicts with
                                                  no catalog, and no disclosure)

Exit 0 on PASS; sys.exit(str) on failure.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from report_evidence import cli_identity, declares_unavailable

# Names a report may use for the catalog when declaring it skipped.
CATALOG_SUBJECT = r"guardrails?\s+catalog|catalog|live\s+catalog"


def _fetch_catalog(uip: str) -> tuple[bool, list, str]:
    """Return (reachable, validators, diagnostic)."""
    argv = [uip, "agent", "guardrails", "catalog", "--output", "json"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        return False, [], f"{uip} not on PATH"
    except subprocess.TimeoutExpired:
        return False, [], "catalog fetch timed out after 180s"
    # The CLI writes both success and error JSON to stdout (guardrails-review.md
    # Step 0), so a non-zero exit is not the only failure shape to handle.
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        tail = (proc.stderr or proc.stdout or "").strip()[-300:]
        return False, [], f"non-JSON output (exit {proc.returncode}): {tail}"
    if payload.get("Code") == "GuardrailCatalogUnavailable":
        return False, [], "CLI reported GuardrailCatalogUnavailable"
    if payload.get("Result") != "Success":
        return False, [], f"Result={payload.get('Result')}: {str(payload.get('Message'))[:200]}"
    validators = [g.get("ValidatorId") for g in (payload.get("Data") or {}).get("Guardrails") or []]
    if not validators:
        return False, [], "catalog returned zero validators"
    return True, validators, ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="_review_report.md")
    args = ap.parse_args()

    report = Path(os.getcwd()) / args.report
    if not report.is_file():
        sys.exit(f"FAIL: {report} not found")
    text = report.read_text(encoding="utf-8", errors="replace")

    uip = os.environ.get("UIP", "uip")
    print(f"Checker resolved `{uip}` -> {cli_identity(uip)}")
    reachable, validators, why = _fetch_catalog(uip)
    declared = declares_unavailable(text, CATALOG_SUBJECT)

    if reachable:
        print(f"Catalog reachable: {len(validators)} validators {validators}")
        if declared:
            sys.exit(
                "FAIL: the report declares the guardrail catalog unavailable under 'Rules Skipped', "
                f"but this checker fetched it successfully via {cli_identity(uip)} "
                f"({len(validators)} validators). Either the agent resolved a different `uip` than the "
                "checker (compare `which -a uip`; a login shell or a per-task HOME from "
                "sandbox.mock_path_dirs can pick a stale one), or the claim is false. Fix the "
                "environment before reading this as a skill regression."
            )
        print("OK: catalog is reachable and the report does not claim otherwise")
        print("PASS")
        return

    print(f"WARN: catalog NOT reachable from the sandbox ({why})")
    if declared:
        print("OK: report declares the guardrail catalog unavailable under 'Rules Skipped'")
        print("PASS")
        return
    sys.exit(
        f"FAIL: the guardrail catalog could not be fetched at check time ({why}), and the report "
        "does not declare it unavailable under 'Rules Skipped'. Any catalog-grounded finding in "
        "this report is therefore unverified (guardrails-review.md Step 0 requires recording the "
        "catalog-dependent rules as skipped when the catalog is missing)."
    )


if __name__ == "__main__":
    main()
