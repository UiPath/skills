#!/usr/bin/env python3
"""Seed a deliberately BROKEN API workflow into the sandbox working dir.

The break (rule 7): the `If_1` switch routes its true branch to `If_1#Then`, but
that branch block is not defined — a dangling branch reference. `uip api-workflow
validate` must reject it. The agent's job is to diagnose from the validator output
and restore the missing `#Then` branch so validation passes, WITHOUT discarding the
score->grade PASS/FAIL intent.

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
                                # NOTE: the "If_1#Then" branch block is intentionally absent.
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
