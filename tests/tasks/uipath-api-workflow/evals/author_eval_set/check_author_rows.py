#!/usr/bin/env python3
"""Task-specific assertions for author_eval_set.

`rows`      — the authored dataset covers the three requested cases with the RAW output
              keys the workflow emits: 85 -> {"grade":"PASS"}, 40 -> {"grade":"FAIL"},
              60 -> {"grade":"PASS"}. A row written as {"Grade": ...} (copied from the
              CLI's PascalCased Data) fails here exactly as it fails in the panel.
`workflow`  — Workflow.json is byte-for-byte the seeded workflow: the task was to add
              tests, not to change behaviour.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from eval_fixtures import PROJECT_NAME, build_workflow  # noqa: E402
from eval_scoring import exact_match, load_eval_sets, load_evaluators, parse_expected  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "rows"
project = Path(PROJECT_NAME)

if mode == "workflow":
    actual = json.loads((project / "Workflow.json").read_text())
    if actual != build_workflow(threshold=60, op=">=", response_key="grade"):
        sys.exit("FAIL: Workflow.json was modified — the task was to add tests, not to change the workflow")
    print("OK: Workflow.json untouched")
    sys.exit(0)

WANTED = {85: {"grade": "PASS"}, 40: {"grade": "FAIL"}, 60: {"grade": "PASS"}}
evaluators = load_evaluators(project)
covered = {}
for set_path in load_eval_sets(project):
    eval_set = json.loads(set_path.read_text())
    for row in eval_set.get("evaluations", []):
        score = (row.get("inputs") or {}).get("score")
        if score not in WANTED:
            continue
        for ref in eval_set.get("evaluatorRefs", []):
            criteria = (row.get("evaluationCriterias") or {}).get(ref)
            evaluator = evaluators.get(ref)
            if not criteria or not evaluator:
                continue
            target = (evaluator.get("evaluatorConfig") or {}).get("targetOutputKey", "*")
            expected = parse_expected(criteria.get("expectedOutput"))
            # The row's expectation must be satisfied by the RAW output the workflow really emits.
            covered[score] = exact_match(WANTED[score], expected, target)
            if not covered[score]:
                print(f"row score={score}: expectedOutput {json.dumps(expected)} does not exact-match the raw output {json.dumps(WANTED[score])} (target key {target!r})")

missing = [s for s in WANTED if s not in covered]
wrong = [s for s, ok in covered.items() if not ok]
if missing or wrong:
    sys.exit(f"FAIL: missing rows for scores {missing}; wrong expectations for scores {wrong}")
print("OK: rows for 85/40/60 carry expectations that exact-match the workflow's raw output")
