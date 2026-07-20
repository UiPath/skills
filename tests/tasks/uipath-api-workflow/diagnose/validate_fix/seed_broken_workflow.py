#!/usr/bin/env python3
"""Seed a deliberately BROKEN API workflow into the sandbox working dir.

The break is a genuine STATIC fault that `uip api-workflow validate` rejects: the
`If_1` activity has NO `switch` block. The validator's `validateIfBranches` check
requires every If to have a switch child, so validation fails outright (this is
the one If-structure rule the static validator enforces). Both branch blocks
(`If_1#Then` -> PASS, `If_1#Else` -> FAIL) are present and correct — only the
routing switch is missing, so the agent's fix is to restore the switch that maps
score >= 60 to #Then and the default to #Else, WITHOUT discarding the score->grade
PASS/FAIL intent.

Contrast with diagnose/runtime_fix, whose fault PASSES validate and only surfaces
at run time. This task exercises the *static* validate -> read errors -> fix ->
re-validate loop (rule 20).

Writes Workflow.json to the current working directory (the agent's sandbox).
"""
import json
import os

VAR_EXPORT = "{ ...$context, variables: { ...$context.variables, ...$output } }"
WORKFLOW_START_SET = (
    "${Object.entries($workflow.definition?.document?.metadata?.variables?.schema"
    "?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, "
    "[name]: def?.default }), {}) }"
)

broken = {
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
                                        # NOTE: the "switch" block is intentionally
                                        # absent. validateIfBranches requires an If
                                        # to have a switch child, so `uip api-workflow
                                        # validate` rejects this. Both branch blocks
                                        # below are present and correct; the fix is to
                                        # restore the switch routing score>=60 -> #Then,
                                        # default -> #Else.
                                        "metadata": {"displayName": "If"},
                                    }
                                },
                                {
                                    "If_1#Then": {
                                        "do": [
                                            {
                                                "Assign_Pass": {
                                                    "set": {"grade": "${'PASS'}"},
                                                    "export": {"as": VAR_EXPORT},
                                                    "metadata": {
                                                        "activityType": "Assign",
                                                        "displayName": "Set PASS",
                                                        "fullName": "Assign",
                                                        "isTransparent": False,
                                                    },
                                                }
                                            }
                                        ],
                                        "then": "exit",
                                    }
                                },
                                {
                                    "If_1#Else": {
                                        "do": [
                                            {
                                                "Assign_Fail": {
                                                    "set": {"grade": "${'FAIL'}"},
                                                    "export": {"as": VAR_EXPORT},
                                                    "metadata": {
                                                        "activityType": "Assign",
                                                        "displayName": "Set FAIL",
                                                        "fullName": "Assign",
                                                        "isTransparent": False,
                                                    },
                                                }
                                            }
                                        ],
                                        "then": "exit",
                                    }
                                },
                            ],
                            "export": {
                                "as": '{ ...$context, outputs: { ...$context?.outputs, "If_1": $output } }'
                            },
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
                            "export": {
                                "as": '{ ...$context, outputs: { ...$context?.outputs, "Response_1": $output } }'
                            },
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
    json.dump(broken, f, indent=2)
print(f"OK: seeded broken Workflow.json at {out}")
