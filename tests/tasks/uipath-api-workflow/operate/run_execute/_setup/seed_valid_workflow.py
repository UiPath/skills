#!/usr/bin/env python3
"""Seed a VALID score->grade API workflow into the sandbox working dir.

mode:operate — the workflow is already correct. The agent's job is to *operate*
(execute) it, not author or repair it: run it locally for the requested inputs
and report the grade each run returns. Graded on the agent invoking
`uip api-workflow run` and on the runs producing the correct PASS/FAIL output.

Writes Workflow.json to the current working directory (the agent's sandbox).
"""
import json
import os

VAR_EXPORT = "{ ...$context, variables: { ...$context.variables, ...$output } }"


def out_export(key):
    return '{ ...$context, outputs: { ...$context?.outputs, "%s": $output } }' % key


WORKFLOW_START_SET = (
    "${Object.entries($workflow.definition?.document?.metadata?.variables?.schema"
    "?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, "
    "[name]: def?.default }), {}) }"
)


def assign(key, var, expr, disp):
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


workflow = {
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
                                                    "when": "${$workflow.input.score >= 60}",
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
                                        "do": [assign("Assign_Pass", "grade", "${'PASS'}", "Set PASS")],
                                        "then": "exit",
                                    }
                                },
                                {
                                    "If_1#Else": {
                                        "do": [assign("Assign_Fail", "grade", "${'FAIL'}", "Set FAIL")],
                                        "then": "exit",
                                    }
                                },
                            ],
                            "export": {"as": out_export("If_1")},
                            "metadata": {
                                "activityType": "If",
                                "displayName": "If",
                                "fullName": "If",
                            },
                        }
                    },
                    {
                        "Response_1": {
                            "response": "${{ grade: $context.variables.grade }}",
                            "markJobAsFailed": False,
                            "then": "end",
                            "export": {"as": out_export("Response_1")},
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

out = os.path.join(os.getcwd(), "Workflow.json")
with open(out, "w") as f:
    json.dump(workflow, f, indent=2)
print(f"OK: seeded valid Workflow.json at {out}")
