#!/usr/bin/env python3
"""Task-specific assertions for stale_expectations.

`dataset`  — the `score 55` row now expects {"grade":"PASS"}; the 85/40/60 rows and
             the evaluator are unchanged; no row was dropped. Grades the
             logic-change guidance of references/testing-and-evals.md §4: re-derive
             only the expectations the behaviour change invalidated.
`behavior` — the workflow really moved to threshold 50: 55 -> PASS, 50 -> PASS,
             49 -> FAIL, read from the RAW output (not the CLI's PascalCased Data).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_fixtures import PROJECT_NAME, build_evaluator, evaluator_path  # noqa: E402
from eval_scoring import deep_equal, exact_match, load_eval_sets, load_evaluators, parse_expected, run_row, wrap_output  # noqa: E402
from seed import ROWS  # noqa: E402

mode = sys.argv[1] if len(sys.argv) > 1 else "dataset"
project = Path(PROJECT_NAME)

if mode == "behavior":
    problems = []
    for score, grade in ((55, "PASS"), (50, "PASS"), (49, "FAIL")):
        ok, raw, error = run_row(project / "Workflow.json", {"score": score})
        if not ok:
            problems.append(f"score {score}: run failed — {error}")
        elif not deep_equal(wrap_output(raw), {"grade": grade}):
            problems.append(f"score {score}: raw output {json.dumps(raw)} != {{\"grade\": \"{grade}\"}}")
    if problems:
        sys.exit("FAIL: " + "; ".join(problems))
    print("OK: workflow grades with threshold 50 (55/50 -> PASS, 49 -> FAIL)")
    sys.exit(0)

problems = []
if json.loads(evaluator_path(project).read_text()) != build_evaluator():
    problems.append("evaluator file changed")

expected_by_score = {score: {"grade": ("PASS" if score == 55 else grade)} for _, _, score, grade in ROWS}
evaluators = load_evaluators(project)
seen = {}
for set_path in load_eval_sets(project):
    eval_set = json.loads(set_path.read_text())
    for row in eval_set.get("evaluations", []):
        score = (row.get("inputs") or {}).get("score")
        for ref in eval_set.get("evaluatorRefs", []):
            criteria = (row.get("evaluationCriterias") or {}).get(ref)
            evaluator = evaluators.get(ref)
            if criteria is None or evaluator is None or score not in expected_by_score:
                continue
            target = (evaluator.get("evaluatorConfig") or {}).get("targetOutputKey", "*")
            seen[score] = exact_match(expected_by_score[score], parse_expected(criteria.get("expectedOutput")), target)

for score, want in expected_by_score.items():
    if score not in seen:
        problems.append(f"row for score {score} missing (was it deleted?)")
    elif not seen[score]:
        problems.append(f"row for score {score} should expect {json.dumps(want)}" + (" — its expectation went stale with the new threshold" if score == 55 else " — it was still valid and must not change"))

if problems:
    sys.exit("FAIL: " + "; ".join(problems))
print("OK: only the stale `score 55` row was re-derived; 85/40/60 rows and the evaluator are unchanged")
