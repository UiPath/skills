#!/usr/bin/env python3
"""Assert the low-code eval suite is correctly SHAPED, not merely present.

The YAML's `command_executed` criteria prove the eval CLI sequence ran. This
grades the artifacts it produced, because every failure mode documented in
`references/lowcode/evaluations/` is a shape problem that `uip agent validate`
does NOT catch — it surfaces only in the cloud eval worker, after upload:

  1. `evaluatorRefs` that do not resolve to a real evaluator `id` (renaming a
     file or copy-pasting a UUID silently breaks resolution).
  2. An LLM-category evaluator with no `model` and no `same-as-agent`
     ("...is an LLM-based evaluator but 'model' is not set").
  3. Test cases whose `evalSetId` does not match the parent set's `id`.
  4. Test-case `inputs` that do not conform to `entry-points.json`.

It also enforces that the agent authored its OWN evaluator and eval set rather
than reusing the scaffolded defaults the fixture ships.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SOLUTION = "EvalSol"
AGENT = "TriageAgent"
REQUIRED_INPUT = "ticket"
DEFAULT_EVALUATOR_NAMES = {"Default Evaluator", "Default Trajectory Evaluator"}
DEFAULT_SET_NAMES = {"Default Evaluation Set"}
# Observed/documented (category, type) pairs: 0 Deterministic (exact=1,
# json-similarity=6), 1 LlmAsAJudge (semantic-similarity=5), 3 Trajectory
# (type 7 — what `uip agent init` scaffolds as "Default Trajectory Evaluator").
VALID_CATEGORIES = {0, 1, 3}
LLM_CATEGORY = 1
CWD = Path.cwd()


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_agent_dir() -> Path:
    direct = CWD / SOLUTION / AGENT
    if (direct / "agent.json").is_file():
        return direct
    for candidate in CWD.rglob("agent.json"):
        if candidate.parent.name == AGENT:
            return candidate.parent
    fail(f"Could not locate the {AGENT} project (looked for {AGENT}/agent.json under {CWD})")


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path.name} is not valid JSON: {exc}")
    except OSError as exc:
        fail(f"Could not read {path}: {exc}")


def load_all(directory: Path, label: str) -> list[tuple[Path, dict]]:
    if not directory.is_dir():
        fail(f"Missing {directory.relative_to(CWD)} — no {label} directory")
    docs = [(p, load(p)) for p in sorted(directory.glob("*.json"))]
    if not docs:
        fail(f"{directory.relative_to(CWD)} contains no {label}")
    return docs


def check_evaluators(evaluators: list[tuple[Path, dict]]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    authored = []

    for path, doc in evaluators:
        eid = doc.get("id")
        name = doc.get("name")
        if not eid:
            fail(f"{path.name} has no `id` — eval sets reference evaluators by UUID")
        if eid in by_id:
            fail(f"Duplicate evaluator id {eid!r} ({path.name}) — UUIDs must be unique")
        by_id[eid] = doc

        category = doc.get("category")
        if category not in VALID_CATEGORIES:
            fail(
                f"{path.name}: `category` must be one of {sorted(VALID_CATEGORIES)} "
                f"(0 Deterministic / 1 LlmAsAJudge / 3 Trajectory), got {category!r}"
            )
        if not isinstance(doc.get("type"), int):
            fail(f"{path.name}: `type` must be an integer discriminator, got {doc.get('type')!r}")

        # The documented cloud-worker failure: LLM evaluator with no resolvable model.
        if category == LLM_CATEGORY:
            model = doc.get("model")
            if model in (None, ""):
                config = doc.get("evaluatorConfig") or {}
                model = config.get("model")
            if model in (None, ""):
                fail(
                    f"{path.name} ({name!r}) is an LLM-as-a-judge evaluator (category 1) with no "
                    f"`model` — the cloud eval worker rejects this at run time and "
                    f"`uip agent validate` does not catch it. Set a model or 'same-as-agent'."
                )

        if name not in DEFAULT_EVALUATOR_NAMES:
            authored.append(name)

    if not authored:
        fail(
            f"No evaluator beyond the `uip agent init` defaults "
            f"({sorted(DEFAULT_EVALUATOR_NAMES)}) — the task asked for an evaluator scoring "
            f"closeness to the expected answer"
        )
    print(f"OK: {len(by_id)} evaluators, agent-authored: {authored}")
    return by_id


def check_eval_sets(sets: list[tuple[Path, dict]], evaluators: dict[str, dict], schema_props: set) -> None:
    authored = [
        (path, doc) for path, doc in sets if doc.get("name") not in DEFAULT_SET_NAMES
    ]
    if not authored:
        fail(
            f"No evaluation set beyond the scaffolded {sorted(DEFAULT_SET_NAMES)} — the task "
            f"asked the agent to create its own"
        )

    for path, doc in authored:
        set_id = doc.get("id")
        set_name = doc.get("name")
        if not set_id:
            fail(f"{path.name} has no `id`")

        refs = doc.get("evaluatorRefs")
        if not isinstance(refs, list) or not refs:
            fail(f"{path.name} ({set_name!r}) has no `evaluatorRefs` — nothing will score the run")

        dangling = [r for r in refs if r not in evaluators]
        if dangling:
            fail(
                f"{path.name} ({set_name!r}) references evaluator id(s) {dangling} that do not "
                f"exist. Known ids: {sorted(evaluators)}. Dangling refs fail silently at run time."
            )

        # The schema key is `evaluations[]`, not `testCases[]` — a documented trap.
        cases = doc.get("evaluations")
        if cases is None and "testCases" in doc:
            fail(
                f"{path.name} uses `testCases[]`; the schema key is `evaluations[]` "
                f"(evaluation-sets.md § Eval Set JSON Format)"
            )
        if not isinstance(cases, list) or len(cases) < 2:
            fail(
                f"{path.name} ({set_name!r}) has {len(cases or [])} test case(s); the task asked "
                f"for at least two covering different categories"
            )

        for case in cases:
            cname = case.get("name") or case.get("id")
            if case.get("evalSetId") != set_id:
                fail(
                    f"{path.name}: test case {cname!r} has evalSetId={case.get('evalSetId')!r} but "
                    f"its parent set id is {set_id!r} — use `uip agent eval add` so the CLI keeps "
                    f"these consistent"
                )
            inputs = case.get("inputs")
            if not isinstance(inputs, dict) or not inputs:
                fail(f"{path.name}: test case {cname!r} has no `inputs`")
            unknown = set(inputs) - schema_props
            if unknown:
                fail(
                    f"{path.name}: test case {cname!r} passes input(s) {sorted(unknown)} that are "
                    f"not in entry-points.json (known: {sorted(schema_props)}) — the run will "
                    f"reject them"
                )
            if REQUIRED_INPUT not in inputs:
                fail(
                    f"{path.name}: test case {cname!r} does not supply the required "
                    f"`{REQUIRED_INPUT}` input"
                )

        distinct = {json.dumps(c.get("expectedOutput"), sort_keys=True) for c in cases}
        if len(distinct) < 2:
            fail(
                f"{path.name} ({set_name!r}): all {len(cases)} test cases share one expected "
                f"output — the task asked for cases covering different categories"
            )

        print(f"OK: eval set {set_name!r} — {len(cases)} cases, {len(refs)} evaluator ref(s), all resolving")


def entry_point_inputs(agent_dir: Path) -> set:
    ep = agent_dir / "entry-points.json"
    if not ep.is_file():
        fail(f"Missing {ep.relative_to(CWD)} — run `uip agent refresh`")
    doc = load(ep)
    entries = doc.get("entryPoints") or []
    props: set = set()
    for entry in entries:
        if isinstance(entry, dict):
            schema = entry.get("input") or {}
            props |= set((schema.get("properties") or {}).keys())
    if not props:
        fail(f"entry-points.json advertises no input properties: {json.dumps(doc)[:200]}")
    if REQUIRED_INPUT not in props:
        fail(
            f"entry-points.json has no `{REQUIRED_INPUT}` input (got {sorted(props)}) — the agent "
            f"under evaluation is not the one that was asked for"
        )
    return props


def main() -> None:
    agent_dir = find_agent_dir()
    schema_props = entry_point_inputs(agent_dir)
    evaluators = check_evaluators(load_all(agent_dir / "evals" / "evaluators", "evaluators"))
    check_eval_sets(load_all(agent_dir / "evals" / "eval-sets", "eval sets"), evaluators, schema_props)
    print("PASS: low-code eval suite is correctly shaped")


if __name__ == "__main__":
    main()
