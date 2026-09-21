"""Seed a Slack-trigger API workflow project whose trigger listens to C_OLD.

Shaped after what Studio Web writes for a CuratedTrigger: the trigger is the
first activity after WorkflowStart, and bindings_v2.json carries the matching
EventTrigger entry. Both name the OLD channel, so the task is only complete
when both have moved to the new one.
"""

import json
import os

PROJECT = "SlackAlert"
OLD_CHANNEL = "C_OLD_CHANNEL_ID"
CONNECTION = "00000000-0000-4000-8000-000000000001"

os.makedirs(PROJECT, exist_ok=True)

configuration = json.dumps(
    {
        "essentialConfiguration": {
            "connectorVersion": "",
            "executionType": None,
            "scriptRef": None,
            "customFieldsRequestDetails": None,
            "instanceParameters": {
                "connectorKey": "uipath-salesforce-slack",
                "objectName": "button",
                "activityType": "CuratedTrigger",
                "version": "1.0.0",
                "eventOperation": "BUTTON_CLICKED",
                "eventMode": "webhooks",
                "supportsStreaming": False,
            },
            "objectName": "button",
            "packageVersion": "1.0.0",
            "httpMethod": None,
            "path": None,
            "filter": None,
        }
    }
)

workflow = {
    "document": {
        "dsl": "1.0.0",
        "name": "Workflow",
        "tags": {},
        "version": "0.0.1",
        "namespace": "default",
        "metadata": {"variables": []},
    },
    "do": [
        {
            "Sequence_1": {
                "do": [
                    {
                        "WorkflowStart": {
                            "set": "${ { ...Object.entries($workflow.definition?.document?.metadata?.variables?.schema?.document?.properties || {}).reduce((acc, [name, def]) => ({ ...acc, [name]: def?.default }), {}), ...($workflow.input || {}) } }",
                            "output": {"as": "${$input}"},
                            "export": {
                                "as": "{ ...$context, variables: { ...$context.variables, ...$output } }"
                            },
                            "metadata": {
                                "activityType": "Assign",
                                "displayName": "Workflow start",
                                "fullName": "Assign",
                                "isTransparent": True,
                            },
                        }
                    },
                    {
                        "Button_Clicked_1": {
                            "call": "UiPath.IntSvcEvent",
                            "with": {
                                "connector": "uipath-salesforce-slack",
                                "connectionId": CONNECTION,
                                "connectionResourceId": CONNECTION,
                                "eventParameters": {"channel_id": OLD_CHANNEL},
                                "objectName": "button",
                                "eventType": "BUTTON_CLICKED",
                                "eventMode": "webhooks",
                                "filterExpression": f"(channel_id == '{OLD_CHANNEL}')",
                            },
                            "export": {
                                "as": '{ ...$context, outputs: { ...$context?.outputs, "button_1": $output } }'
                            },
                            "metadata": {
                                "activityType": "Connector",
                                "fullName": "Connector",
                                "displayName": "Button Clicked",
                                "uiPathActivityTypeId": "00000000-0000-4000-8000-0000000000a1",
                                "configuration": configuration,
                            },
                        }
                    },
                    {
                        "Response_1": {
                            "response": "${{ clicked: $context.outputs.button_1?.content }}",
                            "markJobAsFailed": False,
                            "then": "end",
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

bindings = {
    "version": "2.0",
    "resources": [
        {
            "resource": "EventTrigger",
            "key": CONNECTION,
            "activityId": "Button_Clicked_1",
            "activityDisplayName": "Button Clicked",
            "value": {
                "ConnectionId": {"defaultValue": CONNECTION, "isExpression": False}
            },
            "metadata": {
                "UseConnectionService": "true",
                "Connector": "uipath-salesforce-slack",
                "ActivityName": "Button Clicked",
                "BindingsVersion": "2.2",
                "ObjectName": "button",
                "Operation": "BUTTON_CLICKED",
                "FilterExpression": f"(channel_id == '{OLD_CHANNEL}')",
                "SolutionsSupport": "true",
            },
        }
    ],
}

with open(f"{PROJECT}/Workflow.json", "w") as handle:
    json.dump(workflow, handle, indent=2)

with open(f"{PROJECT}/bindings_v2.json", "w") as handle:
    json.dump(bindings, handle, indent=2)

with open(f"{PROJECT}/project.uiproj", "w") as handle:
    json.dump(
        {
            "ProjectType": "Api",
            "Name": PROJECT,
            "Description": None,
            "MainFile": "Workflow.json",
        },
        handle,
        indent=2,
    )

with open(f"{PROJECT}/entry-points.json", "w") as handle:
    json.dump(
        {
            "$schema": "https://cloud.uipath.com/draft/2024-12/entry-point",
            "$id": "entry-points.json",
            "entryPoints": [
                {
                    "filePath": "content/Workflow.json",
                    "uniqueId": "00000000-0000-4000-8000-0000000000e1",
                    "type": "Api",
                    "input": None,
                    "output": None,
                }
            ],
        },
        handle,
        indent=2,
    )

print(f"Seeded {PROJECT} listening to {OLD_CHANNEL}")
