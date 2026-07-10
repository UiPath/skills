#!/usr/bin/env python3
"""Conversational custom Tool-guardrail check (conversational Critical Rule 1).

Conversational agents support ONE guardrail type: a `$guardrailType: "custom"`
deterministic rule scoped to a Tool. Built-in validators (any
`$guardrailType: "builtInValidator"`) are autonomous-only and never run on a
conversational agent.

The `agent.json` root `guardrails[]` array is the source of truth for both the
Studio Web UI and the runtime. The tool's `resources/<Tool>/resource.json` ->
`guardrail.policies[]` is a derived mirror the product also persists on disk;
it is reported here when present but is not required (the root is authoritative).

PASS requires ALL of:
  1. No `builtInValidator` guardrail anywhere (agent.json root OR any tool
     resource.json), detected by the `$guardrailType` discriminator.
  2. A valid custom word-rule guardrail in `agent.json` root `guardrails[]`:
       - `$guardrailType` == "custom"
       - `selector.scopes` contains "Tool" and NOT "Agent"/"Llm"
       - `selector.matchNames` is non-empty
       - a rule with `$ruleType` == "word", `operator` == "contains",
         `value` == "CONFIDENTIAL", and a `fieldSelector.$selectorType`
       - `action.$actionType` == "block"
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocGuardSol" / "DocGuardBot"
AGENT = ROOT / "agent.json"
RESOURCES = ROOT / "resources"

FORBIDDEN_SCOPES = {"Agent", "Llm"}
VALID_SELECTOR_TYPES = {"all", "specific"}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def is_builtin(g: dict) -> bool:
    return g.get("$guardrailType") == "builtInValidator"


def is_valid_custom_word(g: dict) -> bool:
    if g.get("$guardrailType") != "custom":
        return False
    selector = g.get("selector") or {}
    scopes = selector.get("scopes") or []
    if "Tool" not in scopes or (set(scopes) & FORBIDDEN_SCOPES):
        return False
    if not (selector.get("matchNames") or []):
        return False
    if (g.get("action") or {}).get("$actionType") != "block":
        return False
    for rule in g.get("rules") or []:
        if rule.get("$ruleType") != "word":
            continue
        if (rule.get("fieldSelector") or {}).get("$selectorType") not in VALID_SELECTOR_TYPES:
            continue
        if rule.get("operator") != "contains":
            continue
        if rule.get("value") != "CONFIDENTIAL":
            continue
        return True
    return False


def main() -> None:
    agent = load(AGENT)
    root_guardrails = agent.get("guardrails") or []

    # Tool-resource policy guardrails — used for the built-in scan and the mirror report.
    tool_policy_guardrails = []  # (source_label, guardrail)
    if RESOURCES.is_dir():
        for rj in sorted(RESOURCES.glob("*/resource.json")):
            r = load(rj)
            for g in ((r.get("guardrail") or {}).get("policies")) or []:
                tool_policy_guardrails.append((f"{rj.relative_to(ROOT)} guardrail.policies[]", g))

    # 1. No built-in validators anywhere (detected purely by the discriminator).
    builtins = [("agent.json root guardrails[]", g) for g in root_guardrails if is_builtin(g)]
    builtins += [(src, g) for src, g in tool_policy_guardrails if is_builtin(g)]
    if builtins:
        lines = [
            "FAIL: built-in validator guardrail(s) found — built-in validators "
            "are autonomous-only and do NOT run on conversational agents:"
        ]
        for src, g in builtins:
            lines.append(f"  - in {src}: name={g.get('name', '?')!r}")
        sys.exit("\n".join(lines))
    print("OK: no built-in validator guardrails (agent.json root + per-tool resource.json)")

    # 2. A valid custom word Tool-guardrail in agent.json root (authoritative source of truth).
    root_valid = [g for g in root_guardrails if is_valid_custom_word(g)]
    if not root_valid:
        sys.exit(
            "FAIL: no valid custom word-rule Tool guardrail in agent.json root "
            'guardrails[]. Required: $guardrailType=="custom", selector.scopes '
            'contains "Tool" (no Agent/Llm) with matchNames, a word rule '
            '(operator "contains", value "CONFIDENTIAL"), and '
            'action.$actionType=="block". The root array is authoritative for the '
            "Studio Web UI and both runtimes."
        )
    g = root_valid[0]
    print(
        f"OK: custom word Tool-guardrail in agent.json root guardrails[] "
        f"(scopes={g['selector']['scopes']}, matchNames={g['selector'].get('matchNames')}, action=block)"
    )

    # Report the tool-resource mirror (the product persists it; not required for a PASS).
    mirrored = [src for src, gg in tool_policy_guardrails if is_valid_custom_word(gg)]
    if mirrored:
        print(f"OK: also mirrored into {mirrored[0]}")
    else:
        print(
            "NOTE: not mirrored into a tool resource.json guardrail.policies[] "
            "(the product persists that mirror; the root remains authoritative)."
        )

    print("\nAll conversational custom-guardrail checks passed (conversational Critical Rule 1).")


if __name__ == "__main__":
    main()
