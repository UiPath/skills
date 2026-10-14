#!/usr/bin/env python3
"""Fixtures for the evals tasks: a score->grade API workflow plus the `evals/` files
Studio Web's Evaluations panel reads (`@uipath/unified-evals` layout).

The workflow is parameterised so each task can seed a different starting point:
the comparison operator / threshold (a logic bug or a requested change) and the key
the Response emits (`Grade` instead of `grade` is the casing bug the CLI's
PascalCased output hides — see the skill's testing-and-evals reference §2).

Shared by the seed scripts (pre_run) and the check scripts (success_criteria), so
"untouched" assertions compare against the exact JSON that was seeded.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_NAME = "GradeCheck"
SCOPE = "default"
EVALUATOR_REF = "exact-match-evaluator"
EVAL_SET_FILE = "evaluation-set.json"

VAR_EXPORT = "{ ...$context, variables: { ...$context.variables, ...$output } }"
WORKFLOW_START_SET = (
    "${Object.entries($workflow.definition?.document?.metadata?.variables?.schema"
    "?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, "
    "[name]: def?.default }), {}) }"
)


def _out_export(key):
    return '{ ...$context, outputs: { ...$context?.outputs, "%s": $output } }' % key


def _assign(key, var, expr, disp):
    return {
        key: {
            "set": {var: expr},
            "export": {"as": VAR_EXPORT},
            "metadata": {
                "activityType": "Assign",
                "displayName": disp,
                "fullName": "Assign",
                "isTransparent": False,
            },
        }
    }


def build_workflow(threshold=60, op=">=", response_key="grade"):
    """score->grade workflow. `output.schema` always declares `grade`; `response_key`
    is what the Response actually emits, so a value other than `grade` is a bug."""
    return {
        "document": {
            "dsl": "1.0.0",
            "name": "Workflow",
            "version": "0.0.1",
            "namespace": "default",
            "metadata": {
                "variables": {
                    "schema": {
                        "format": "json",
                        "document": {
                            "type": "object",
                            "properties": {"grade": {"type": "string", "default": ""}},
                            "title": "Variables",
                        },
                    }
                }
            },
        },
        "input": {
            "schema": {
                "format": "json",
                "document": {
                    "type": "object",
                    "properties": {"score": {"type": "number"}},
                    "title": "Inputs",
                },
            }
        },
        "output": {
            "schema": {
                "format": "json",
                "document": {
                    "type": "object",
                    "properties": {"grade": {"type": "string"}},
                    "title": "Outputs",
                },
            }
        },
        "do": [
            {
                "Sequence_1": {
                    "do": [
                        {
                            "WorkflowStart": {
                                "set": WORKFLOW_START_SET,
                                "output": {"as": "${$input}"},
                                "export": {"as": VAR_EXPORT},
                                "metadata": {
                                    "activityType": "Assign",
                                    "displayName": "Workflow start",
                                    "fullName": "Assign",
                                    "isTransparent": True,
                                },
                            }
                        },
                        {
                            "If_1#Wrapper": {
                                "do": [
                                    {
                                        "If_1": {
                                            "switch": [
                                                {
                                                    "case": {
                                                        "when": "${$workflow.input.score %s %d}" % (op, threshold),
                                                        "then": "If_1#Then",
                                                    }
                                                },
                                                {"default": {"then": "If_1#Else"}},
                                            ],
                                            "metadata": {"displayName": "If"},
                                        }
                                    },
                                    {
                                        "If_1#Then": {
                                            "do": [_assign("Assign_Pass", "grade", "${'PASS'}", "Set PASS")],
                                            "then": "exit",
                                        }
                                    },
                                    {
                                        "If_1#Else": {
                                            "do": [_assign("Assign_Fail", "grade", "${'FAIL'}", "Set FAIL")],
                                            "then": "exit",
                                        }
                                    },
                                ],
                                "export": {"as": _out_export("If_1")},
                                "metadata": {
                                    "activityType": "If",
                                    "displayName": "If",
                                    "fullName": "If",
                                },
                            }
                        },
                        {
                            "Response_1": {
                                "response": "${{ %s: $context.variables.grade }}" % response_key,
                                "markJobAsFailed": False,
                                "then": "end",
                                "export": {"as": _out_export("Response_1")},
                                "metadata": {
                                    "activityType": "Response",
                                    "displayName": "Response",
                                    "fullName": "Response",
                                },
                            }
                        },
                    ],
                    "metadata": {
                        "activityType": "Sequence",
                        "displayName": "Sequence",
                        "fullName": "Sequence",
                    },
                }
            }
        ],
        "evaluate": {"mode": "strict", "language": "javascript"},
    }


def build_evaluator():
    return {
        "version": "1.0",
        "id": "exact-match-eval-001",
        "name": "Exact Match",
        "description": "Exact Match",
        "evaluatorTypeId": "uipath-exact-match",
        "evaluatorConfig": {
            "name": "Exact Match",
            "targetOutputKey": "*",
            "defaultEvaluationCriteria": {"expectedOutput": {}},
        },
    }


def build_eval_set(rows):
    """`rows`: list of (row_id, name, score, expected_grade)."""
    return {
        "version": "1.0",
        "id": "eval-set-001",
        "name": "Dataset",
        "evaluatorRefs": [EVALUATOR_REF],
        "evaluations": [
            {
                "id": row_id,
                "name": name,
                "inputs": {"score": score},
                "evaluationCriterias": {EVALUATOR_REF: {"expectedOutput": {"grade": grade}}},
            }
            for row_id, name, score, grade in rows
        ],
    }


def evals_dir(project_dir):
    return Path(project_dir) / "evals" / SCOPE


def eval_set_path(project_dir):
    return evals_dir(project_dir) / "eval-sets" / EVAL_SET_FILE


def evaluator_path(project_dir):
    return evals_dir(project_dir) / "evaluators" / f"{EVALUATOR_REF}.json"


def scaffold_project(project_dir):
    """`uip api-workflow init` gives the Studio Web project shape (project.uiproj,
    entry-points.json, bindings_v2.json). Falls back to a bare directory when the CLI
    is unavailable — the graded behaviour needs Workflow.json + evals/, not the shell."""
    project_dir = Path(project_dir)
    if project_dir.exists():
        return
    try:
        subprocess.run(
            ["uip", "api-workflow", "init", project_dir.name, "--skip-solution-registration", "--output", "json"],
            cwd=project_dir.parent,
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"WARN: `uip api-workflow init` unavailable ({exc}); seeding a bare project dir", file=sys.stderr)
        project_dir.mkdir(parents=True)


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def seed_project(workflow, eval_rows=None, root=None):
    project_dir = Path(root or os.getcwd()) / PROJECT_NAME
    scaffold_project(project_dir)
    write_json(project_dir / "Workflow.json", workflow)
    if eval_rows is not None:
        write_json(evaluator_path(project_dir), build_evaluator())
        write_json(eval_set_path(project_dir), build_eval_set(eval_rows))
    return project_dir
