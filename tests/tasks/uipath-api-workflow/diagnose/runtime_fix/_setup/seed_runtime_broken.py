#!/usr/bin/env python3
"""Seed an API workflow that PASSES static validation but FAILS at runtime.

The break (rule 11): a ForEach declares `for.each: "currentItem"`, but the loop
body's accumulation Assign references the iterator as `currentItem` (no `$`)
instead of `$currentItem`. The executor binds the iterator as the global
`$currentItem` — the `$` is part of the identifier — so `currentItem` has no
binding and the run throws `currentItem is not defined`.

`uip api-workflow validate` reports Status: Valid (the fault is a runtime
expression binding, not a structural/schema fault). Only `uip api-workflow run`
surfaces it. Tests the runtime diagnose loop (run -> read error -> fix -> re-run),
which is distinct from the static validate loop in ../validate_fix.

The agent's job: diagnose from the run output and fix so the workflow sums the
`numbers` input and returns `total`, WITHOUT discarding the loop/aggregation intent.

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
                        "properties": {"total": {"type": "number", "default": 0}},
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
                "properties": {"numbers": {"type": "array"}},
                "title": "Inputs",
            },
        }
    },
    "output": {
        "schema": {
            "format": "json",
            "document": {
                "type": "object",
                "properties": {"total": {"type": "number"}},
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
                        "For_Each_1": {
                            "for": {
                                "each": "currentItem",
                                "at": "currentItemIndex",
                                "in": "${$workflow.input.numbers ?? []}",
                            },
                            "do": [
                                {
                                    "For_Each_1#Body": {
                                        "do": [
                                            {
                                                "Assign_Sum": {
                                                    # BUG (rule 11): iterator referenced as `currentItem`
                                                    # instead of `$currentItem` -> runtime ReferenceError.
                                                    "set": {
                                                        "total": "${$context.variables.total + currentItem}"
                                                    },
                                                    "export": {"as": VAR_EXPORT},
                                                    "metadata": {
                                                        "activityType": "Assign",
                                                        "displayName": "Accumulate",
                                                        "fullName": "Assign",
                                                        "isTransparent": False,
                                                    },
                                                }
                                            }
                                        ],
                                        "export": {"as": out_export("For_Each_1")},
                                    }
                                }
                            ],
                            "export": {"as": out_export("For_Each_1")},
                            "metadata": {
                                "activityType": "ForEach",
                                "displayName": "For Each",
                                "fullName": "ForEach",
                            },
                        }
                    },
                    {
                        "Response_1": {
                            "response": "${{ total: $context.variables.total }}",
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
    json.dump(broken, f, indent=2)
print(f"OK: seeded runtime-broken Workflow.json at {out}")
