#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).with_name("build-bpmn.py")
SPEC = importlib.util.spec_from_file_location("build_bpmn", SCRIPT)
assert SPEC and SPEC.loader
build_bpmn = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_bpmn)


def guard_variables() -> list[dict[str, object]]:
    return [
        {"id": "Var_JiraAvailable", "name": "jiraAvailable"},
        {"id": "Var_Severity", "name": "severity"},
    ]


class BuildBpmnTests(unittest.TestCase):
    def test_error_guard_reference_constraint_is_backward_compatible(
        self,
    ) -> None:
        build_bpmn.validate_error_guard_reference_constraints(
            {},
            {"End_JiraUnavailable": "=js:true"},
            guard_variables(),
        )

    def test_error_guard_accepts_required_semantic_variable_names(
        self,
    ) -> None:
        build_bpmn.validate_error_guard_reference_constraints(
            {
                "End_JiraUnavailable": [
                    "jiraAvailable",
                    "severity",
                ]
            },
            {
                "End_JiraUnavailable": (
                    "=js:vars.Var_JiraAvailable === false && "
                    "(vars.Var_Severity === 'Sev1' || "
                    "vars.Var_Severity === 'Sev2')"
                )
            },
            guard_variables(),
        )

    def test_error_guard_rejects_missing_availability_reference(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'jiraAvailable'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {
                    "End_JiraUnavailable": [
                        "jiraAvailable",
                        "severity",
                    ]
                },
                {
                    "End_JiraUnavailable": (
                        "=js:vars.Var_Severity === 'Sev1' || "
                        "vars.Var_Severity === 'Sev2'"
                    )
                },
                guard_variables(),
            )

    def test_error_guard_rejects_route_proxy_for_severity(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {
                    "End_JiraUnavailable": [
                        "jiraAvailable",
                        "severity",
                    ]
                },
                {
                    "End_JiraUnavailable": (
                        "=js:vars.Var_JiraAvailable === false && "
                        "(vars.Var_Route === 'ExistingIssue' || "
                        "vars.Var_Route === 'NewEscalation')"
                    )
                },
                guard_variables()
                + [{"id": "Var_Route", "name": "route"}],
            )

    def test_error_guard_rejects_unknown_error_end(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"names unknown error ends: \['End_Other'\]",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_Other": ["severity"]},
                {"End_JiraUnavailable": "=js:true"},
                guard_variables(),
            )

    def test_error_guard_rejects_unknown_variable(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "references unknown variable 'missing'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["missing"]},
                {"End_JiraUnavailable": "=js:true"},
                guard_variables(),
            )

    def test_error_guard_rejects_ambiguous_variable_name(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "references ambiguous variable name 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["severity"]},
                {"End_JiraUnavailable": "=js:vars.Var_Severity"},
                guard_variables()
                + [{"id": "Var_SeverityScoped", "name": "severity"}],
            )

    def test_error_guard_rejects_longer_identifier_prefix(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["severity"]},
                {
                    "End_JiraUnavailable": (
                        "=js:vars.Var_SeverityBackup === 'Sev1'"
                    )
                },
                guard_variables()
                + [
                    {
                        "id": "Var_SeverityBackup",
                        "name": "severityBackup",
                    }
                ],
            )

    def test_error_guard_rejects_reference_inside_string(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["severity"]},
                {
                    "End_JiraUnavailable": (
                        '=js:"vars.Var_Severity" && '
                        "!vars.Var_JiraAvailable"
                    )
                },
                guard_variables(),
            )

    def test_error_guard_rejects_reference_inside_comment(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["severity"]},
                {
                    "End_JiraUnavailable": (
                        "=js:!vars.Var_JiraAvailable "
                        "/* vars.Var_Severity */"
                    )
                },
                guard_variables(),
            )

    def test_error_guard_rejects_reference_inside_regex(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'severity'",
        ):
            build_bpmn.validate_error_guard_reference_constraints(
                {"End_JiraUnavailable": ["severity"]},
                {
                    "End_JiraUnavailable": (
                        r"=js:/vars\.Var_Severity/.test('x') && "
                        "!vars.Var_JiraAvailable"
                    )
                },
                guard_variables(),
            )

    def test_error_end_rejects_null_matching_boundary(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "matching boundary for error end End_Error is required",
        ):
            build_bpmn.validate_matching_error_boundary(
                {"id": "End_Error", "errorRef": "Error_Backend"},
                None,
                {},
                {"End_Error": "Sub_Assess"},
            )

    def test_accepts_connected_nested_execution_scopes(self) -> None:
        build_bpmn.validate_scope_execution_paths(
            {
                "nodes": [
                    {"kind": "startEvent", "id": "Start_Main"},
                    {
                        "kind": "subProcess",
                        "id": "Sub_Assess",
                        "nodes": [
                            {"kind": "startEvent", "id": "Start_Assess"},
                            {"kind": "task", "id": "Task_Assess"},
                            {"kind": "endEvent", "id": "End_Assess"},
                        ],
                        "flows": [
                            {
                                "id": "Flow_Assess_Task",
                                "source": "Start_Assess",
                                "target": "Task_Assess",
                            },
                            {
                                "id": "Flow_Task_EndAssess",
                                "source": "Task_Assess",
                                "target": "End_Assess",
                            },
                        ],
                    },
                    {"kind": "endEvent", "id": "End_Main"},
                ],
                "flows": [
                    {
                        "id": "Flow_Start_Sub",
                        "source": "Start_Main",
                        "target": "Sub_Assess",
                    },
                    {
                        "id": "Flow_Sub_End",
                        "source": "Sub_Assess",
                        "target": "End_Main",
                    },
                ],
            }
        )

    def test_rejects_subprocess_start_without_outgoing_flow(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "start event Start_Assess in scope Sub_Assess needs exactly "
            "one outgoing flow; found 0",
        ):
            build_bpmn.validate_scope_execution_paths(
                {
                    "nodes": [
                        {"kind": "startEvent", "id": "Start_Main"},
                        {
                            "kind": "subProcess",
                            "id": "Sub_Assess",
                            "nodes": [
                                {
                                    "kind": "startEvent",
                                    "id": "Start_Assess",
                                },
                                {"kind": "task", "id": "Task_Assess"},
                                {"kind": "endEvent", "id": "End_Assess"},
                            ],
                            "flows": [
                                {
                                    "id": "Flow_Task_EndAssess",
                                    "source": "Task_Assess",
                                    "target": "End_Assess",
                                }
                            ],
                        },
                        {"kind": "endEvent", "id": "End_Main"},
                    ],
                    "flows": [
                        {
                            "id": "Flow_Start_Sub",
                            "source": "Start_Main",
                            "target": "Sub_Assess",
                        },
                        {
                            "id": "Flow_Sub_End",
                            "source": "Sub_Assess",
                            "target": "End_Main",
                        },
                    ],
                }
            )

    def test_rejects_unreachable_node_in_scope(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            r"scope process has nodes unreachable .*\['Task_Orphan'\]",
        ):
            build_bpmn.validate_scope_execution_paths(
                {
                    "nodes": [
                        {"kind": "startEvent", "id": "Start_Main"},
                        {"kind": "endEvent", "id": "End_Main"},
                        {"kind": "task", "id": "Task_Orphan"},
                    ],
                    "flows": [
                        {
                            "id": "Flow_Start_End",
                            "source": "Start_Main",
                            "target": "End_Main",
                        }
                    ],
                }
            )

    def test_rejects_flow_crossing_execution_scope(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "scope Sub_Assess flow Flow_Escape must connect nodes in that "
            "same scope",
        ):
            build_bpmn.validate_scope_execution_paths(
                {
                    "nodes": [
                        {"kind": "startEvent", "id": "Start_Main"},
                        {
                            "kind": "subProcess",
                            "id": "Sub_Assess",
                            "nodes": [
                                {
                                    "kind": "startEvent",
                                    "id": "Start_Assess",
                                }
                            ],
                            "flows": [
                                {
                                    "id": "Flow_Escape",
                                    "source": "Start_Assess",
                                    "target": "End_Main",
                                }
                            ],
                        },
                        {"kind": "endEvent", "id": "End_Main"},
                    ],
                    "flows": [
                        {
                            "id": "Flow_Start_Sub",
                            "source": "Start_Main",
                            "target": "Sub_Assess",
                        },
                        {
                            "id": "Flow_Sub_End",
                            "source": "Sub_Assess",
                            "target": "End_Main",
                        },
                    ],
                }
            )

    def test_accepts_complete_diverging_exclusive_gateway(self) -> None:
        build_bpmn.validate_diverging_exclusive_gateways(
            [
                {
                    "kind": "exclusiveGateway",
                    "id": "Gateway_Route",
                    "default": "Flow_Default",
                }
            ],
            [
                {
                    "id": "Flow_Guarded",
                    "source": "Gateway_Route",
                    "target": "Task_Guarded",
                    "condition": "=vars.Var_Enabled == true",
                },
                {
                    "id": "Flow_Default",
                    "source": "Gateway_Route",
                    "target": "Task_Default",
                },
            ],
        )

    def test_rejects_diverging_exclusive_gateway_without_default(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "needs an explicit default flow"
        ):
            build_bpmn.validate_diverging_exclusive_gateways(
                [
                    {
                        "kind": "exclusiveGateway",
                        "id": "Gateway_Route",
                    }
                ],
                [
                    {
                        "id": "Flow_One",
                        "source": "Gateway_Route",
                        "target": "Task_One",
                        "condition": "=vars.Var_Route == 1",
                    },
                    {
                        "id": "Flow_Two",
                        "source": "Gateway_Route",
                        "target": "Task_Two",
                        "condition": "=vars.Var_Route == 2",
                    },
                ],
            )

    def test_accepts_script_scoped_error_variable(self) -> None:
        scripts = {
            "Task_Normalize": {
                "mapping": {
                    "outputs": [
                        {
                            "name": "Error",
                            "type": "jsonSchema",
                            "var": "Var_NormalizeError",
                            "source": "=Error",
                        }
                    ]
                }
            }
        }
        variables = [
            {
                "direction": "internal",
                "id": "Var_NormalizeError",
                "name": "Error",
                "type": "jsonSchema",
                "elementId": "Task_Normalize",
            }
        ]

        build_bpmn.validate_script_error_bindings(scripts, variables)

    def test_rejects_unscoped_script_error_variable(self) -> None:
        scripts = {
            "Task_Normalize": {
                "mapping": {
                    "outputs": [
                        {
                            "name": "Error",
                            "type": "jsonSchema",
                            "var": "Var_NormalizeError",
                            "source": "=Error",
                        }
                    ]
                }
            }
        }
        variables = [
            {
                "direction": "internal",
                "id": "Var_NormalizeError",
                "name": "normalizeError",
                "type": "object",
            }
        ]

        with self.assertRaisesRegex(
            ValueError, "matching elementId"
        ):
            build_bpmn.validate_script_error_bindings(scripts, variables)

    def test_accepts_complete_v3_script_runtime_contract(self) -> None:
        scripts = {
            "Task_Normalize": {
                "scriptVersion": "v3",
                "mapping": {
                    "serviceType": "BPMN.Variables",
                    "outputs": [
                        {
                            "name": "scriptResponse",
                            "type": "object",
                            "var": "Var_NormalizeResponse",
                            "source": "=result.response",
                        },
                        {
                            "name": "Error",
                            "type": "jsonSchema",
                            "var": "Var_NormalizeError",
                            "source": "=Error",
                        },
                    ],
                },
            }
        }
        variables = [
            {
                "direction": "internal",
                "id": "Var_NormalizeResponse",
                "name": "normalizeResponse",
                "type": "object",
            },
            {
                "direction": "internal",
                "id": "Var_NormalizeError",
                "name": "Error",
                "type": "jsonSchema",
                "elementId": "Task_Normalize",
            },
        ]

        build_bpmn.validate_script_runtime_contracts(scripts, variables)

    def test_rejects_script_without_standard_response_output(self) -> None:
        scripts = {
            "Task_Normalize": {
                "mapping": {
                    "serviceType": "BPMN.Variables",
                    "outputs": [
                        {
                            "name": "normalizedTier",
                            "type": "string",
                            "var": "Var_NormalizedTier",
                            "source": "=result.response.normalizedTier",
                        },
                        {
                            "name": "Error",
                            "type": "jsonSchema",
                            "var": "Var_NormalizeError",
                            "source": "=Error",
                        },
                    ],
                }
            }
        }
        variables = [
            {
                "direction": "internal",
                "id": "Var_NormalizedTier",
                "name": "normalizedTier",
                "type": "string",
            },
            {
                "direction": "internal",
                "id": "Var_NormalizeError",
                "name": "Error",
                "type": "jsonSchema",
                "elementId": "Task_Normalize",
            },
        ]

        with self.assertRaisesRegex(
            ValueError, "exactly one scriptResponse output"
        ):
            build_bpmn.validate_script_runtime_contracts(
                scripts, variables
            )

    def test_rejects_runtime_reference_by_variable_name(self) -> None:
        process = {
            "variables": [
                {
                    "direction": "input",
                    "id": "Var_Request",
                    "name": "request",
                    "type": "string",
                }
            ],
            "nodes": [
                {
                    "kind": "scriptTask",
                    "id": "Task_Normalize",
                    "mapping": {
                        "inputs": [
                            {
                                "name": "args",
                                "body": '{"request":"=vars.request"}',
                            }
                        ]
                    },
                }
            ],
            "flows": [],
        }

        with self.assertRaisesRegex(
            ValueError,
            r"use its stable id 'vars\.Var_Request'",
        ):
            build_bpmn.validate_stable_variable_references(process)

    def test_accepts_runtime_reference_by_stable_variable_id(self) -> None:
        process = {
            "variables": [
                {
                    "direction": "input",
                    "id": "Var_Request",
                    "name": "request",
                    "type": "string",
                }
            ],
            "nodes": [
                {
                    "kind": "scriptTask",
                    "id": "Task_Normalize",
                    "mapping": {
                        "inputs": [
                            {
                                "name": "args",
                                "body": '{"request":"=vars.Var_Request"}',
                            }
                        ]
                    },
                }
            ],
            "flows": [],
        }

        build_bpmn.validate_stable_variable_references(process)

    def test_script_constraint_accepts_stable_reference_in_script_body(
        self,
    ) -> None:
        script = {
            "mapping": {
                "inputs": [
                    {
                        "name": "args",
                        "body": {
                            "vars": "=vars",
                            "metadata": "=metadata",
                        },
                    }
                ]
            },
            "script": "return vars.Var_Request;",
        }

        self.assertTrue(
            build_bpmn.script_references_stable_variable(
                script,
                "Var_Request",
            )
        )

    def test_script_constraint_rejects_name_only_reference(self) -> None:
        script = {
            "mapping": {
                "inputs": [
                    {
                        "name": "args",
                        "body": {
                            "vars": "=vars",
                            "metadata": "=metadata",
                        },
                    }
                ]
            },
            "script": "return vars.request;",
        }

        self.assertFalse(
            build_bpmn.script_references_stable_variable(
                script,
                "Var_Request",
            )
        )

    def test_public_bridge_rejects_duplicate_semantic_name(self) -> None:
        node = {
            "id": "Start_Main",
            "mapping": {
                "serviceType": "BPMN.Variables",
                "version": "v1",
                "outputs": [
                    {
                        "name": "request",
                        "type": "string",
                        "var": "Var_Request",
                        "source": "=vars.input_Var_Request",
                    }
                ],
            },
        }

        with self.assertRaisesRegex(
            ValueError,
            r"duplicates output names \['request'\]",
        ):
            build_bpmn.merge_bridge_mapping(
                node,
                [
                    {
                        "name": "request",
                        "type": "string",
                        "var": "input_Var_Request",
                        "source": "=vars.input_input_Var_Request",
                    }
                ],
            )

    def test_public_bridge_allows_distinct_initialization(self) -> None:
        node = {
            "id": "Start_Main",
            "mapping": {
                "serviceType": "BPMN.Variables",
                "version": "v1",
                "outputs": [
                    {
                        "name": "initialized",
                        "type": "boolean",
                        "var": "Var_Initialized",
                        "source": "=true",
                    }
                ],
            },
        }

        build_bpmn.merge_bridge_mapping(
            node,
            [
                {
                    "name": "request",
                    "type": "string",
                    "var": "Var_Request",
                    "source": "=vars.input_Var_Request",
                }
            ],
        )

        self.assertEqual(
            [
                item["name"]
                for item in node["mapping"]["outputs"]
            ],
            ["initialized", "request"],
        )

    def test_rejects_json_boolean_mapping_source_before_type_is_lost(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "task"))
        mapping = {
            "serviceType": "BPMN.Variables",
            "outputs": [
                {
                    "name": "approved",
                    "type": "boolean",
                    "var": "Var_Approved",
                    "source": True,
                }
            ],
        }

        with self.assertRaisesRegex(
            ValueError, "source must be a string"
        ):
            build_bpmn.add_mapping(node, mapping)

    def test_rejects_bare_literal_for_non_string_mapping_output(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "task"))
        mapping = {
            "serviceType": "BPMN.Variables",
            "outputs": [
                {
                    "name": "approved",
                    "type": "boolean",
                    "var": "Var_Approved",
                    "source": "true",
                }
            ],
        }

        with self.assertRaisesRegex(
            ValueError, "must be a typed '=' expression"
        ):
            build_bpmn.add_mapping(node, mapping)

    def test_accepts_typed_boolean_mapping_expression(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "task"))
        build_bpmn.add_mapping(
            node,
            {
                "serviceType": "BPMN.Variables",
                "outputs": [
                    {
                        "name": "approved",
                        "type": "boolean",
                        "var": "Var_Approved",
                        "source": "=true",
                    }
                ],
            },
        )

        output = node.find(".//uipath:output", build_bpmn.NS)
        self.assertIsNotNone(output)
        self.assertEqual(output.attrib["source"], "=true")

    def test_serializes_runtime_mapping_body_as_value_attribute(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "scriptTask"))
        build_bpmn.add_mapping(
            node,
            {
                "serviceType": "BPMN.Variables",
                "context": [
                    {
                        "name": "inputSchema",
                        "type": "jsonSchema",
                        "body": {"type": "object"},
                    }
                ],
                "inputs": [
                    {
                        "name": "args",
                        "type": "json",
                        "target": "bodyField",
                        "body": {"vars": "=vars", "metadata": "=metadata"},
                    }
                ],
            },
            script_version="v3",
        )

        input_el = node.find(".//uipath:input", build_bpmn.NS)
        self.assertIsNotNone(input_el)
        self.assertEqual(
            input_el.attrib["value"],
            '{"vars":"=vars","metadata":"=metadata"}',
        )
        self.assertIsNone(input_el.text)
        schema = node.find(
            ".//uipath:context/uipath:inputSchema",
            build_bpmn.NS,
        )
        self.assertIsNotNone(schema)
        self.assertEqual(schema.attrib["type"], "jsonSchema")
        self.assertEqual(schema.text, '{"type":"object"}')
        self.assertIsNotNone(
            node.find(".//uipath:scriptVersion", build_bpmn.NS)
        )

    def test_loop_item_is_optional_for_root_marker(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "scriptTask"))
        build_bpmn.add_loop(
            node,
            {
                "sequential": True,
                "collection": "=vars.Var_Items",
            },
        )

        loop = node.find(
            ".//uipath:loopCharacteristics",
            build_bpmn.NS,
        )
        self.assertIsNotNone(loop)
        self.assertEqual(loop.attrib["version"], "v1")
        self.assertEqual(loop.attrib["inputCollection"], "=vars.Var_Items")
        self.assertNotIn("inputElement", loop.attrib)

    def test_task_loop_rejects_input_element_alias(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "scriptTask"))
        with self.assertRaisesRegex(
            ValueError,
            "task-level multi-instance loops must omit item",
        ):
            build_bpmn.add_loop(
                node,
                {
                    "sequential": True,
                    "collection": "=vars.Var_Items",
                    "item": "item",
                },
            )

    def test_subprocess_loop_requires_iterator_depth_binding(self) -> None:
        node = ET.Element(build_bpmn.q("bpmn", "subProcess"))
        with self.assertRaisesRegex(
            ValueError,
            "multi-instance subprocess loops require",
        ):
            build_bpmn.add_loop(
                node,
                {
                    "sequential": True,
                    "collection": "=vars.Var_Items",
                },
            )
        build_bpmn.add_loop(
            node,
            {
                "sequential": True,
                "collection": "=vars.Var_Items",
                "item": "iterator[0]",
            },
        )
        loop = node.find(
            ".//uipath:loopCharacteristics",
            build_bpmn.NS,
        )
        self.assertIsNotNone(loop)
        self.assertEqual(loop.attrib["inputElement"], "iterator[0]")

    def test_nested_error_loop_mapping_and_metadata(self) -> None:
        spec = {
            "project": {
                "name": "Complex",
                "bpmnFile": "Complex.bpmn",
                "startId": "Start_Main",
                "entryPointId": "Entry_Main",
            },
            "errors": [
                {
                    "id": "Error_Backend",
                    "name": "Backend",
                    "errorCode": "Backend",
                }
            ],
            "process": {
                "id": "Process_Complex",
                "variables": [
                    {
                        "direction": "input",
                        "id": "Var_Items",
                        "name": "items",
                        "type": "array",
                    },
                    {
                        "direction": "output",
                        "id": "Var_Result",
                        "name": "result",
                        "type": "string",
                    },
                    {
                        "direction": "internal",
                        "id": "Var_Working",
                        "name": "working",
                        "type": "string",
                    },
                ],
                "nodes": [
                    {"kind": "startEvent", "id": "Start_Main"},
                    {
                        "kind": "subProcess",
                        "id": "Sub_Assess",
                        "nodes": [
                            {"kind": "startEvent", "id": "Start_Assess"},
                            {
                                "kind": "exclusiveGateway",
                                "id": "Gateway_Check",
                                "default": "Flow_Check_End",
                            },
                            {
                                "kind": "endEvent",
                                "id": "End_Error",
                                "errorRef": "Error_Backend",
                            },
                            {"kind": "endEvent", "id": "End_Assess"},
                        ],
                        "flows": [
                            {
                                "id": "Flow_Assess_Check",
                                "source": "Start_Assess",
                                "target": "Gateway_Check",
                            },
                            {
                                "id": "Flow_Check_Error",
                                "source": "Gateway_Check",
                                "target": "End_Error",
                                "condition": "=js:!vars.Var_Working",
                            },
                            {
                                "id": "Flow_Check_End",
                                "source": "Gateway_Check",
                                "target": "End_Assess",
                            },
                        ],
                    },
                    {
                        "kind": "boundaryEvent",
                        "id": "Boundary_Backend",
                        "attachedTo": "Sub_Assess",
                        "errorRef": "Error_Backend",
                    },
                    {
                        "kind": "task",
                        "id": "Task_Items",
                        "loop": {
                            "sequential": True,
                            "collection": "=vars.Var_Items",
                        },
                        "mapping": {
                            "serviceType": "BPMN.Variables",
                            "outputs": [
                                {
                                    "name": "result",
                                    "type": "string",
                                    "var": "result",
                                    "source": "=iterator.item.name",
                                }
                            ],
                        },
                    },
                    {"kind": "endEvent", "id": "End_Main"},
                ],
                "flows": [
                    {
                        "id": "Flow_Start_Assess",
                        "source": "Start_Main",
                        "target": "Sub_Assess",
                    },
                    {
                        "id": "Flow_Assess_Items",
                        "source": "Sub_Assess",
                        "target": "Task_Items",
                    },
                    {
                        "id": "Flow_Boundary_Items",
                        "source": "Boundary_Backend",
                        "target": "Task_Items",
                    },
                    {
                        "id": "Flow_Items_End",
                        "source": "Task_Items",
                        "target": "End_Main",
                    },
                ],
            },
            "constraints": {
                "publicInputs": ["items"],
                "publicOutputs": ["result"],
                "internalVariables": ["working"],
                "scriptTasks": {
                    "exact": 0,
                    "allowedIds": [],
                    "allowedOutputsById": {},
                    "requiredInputReferencesById": {},
                },
                "errorEnds": {
                    "singleGuardedIncoming": True,
                    "allowedIds": ["End_Error"],
                    "matchingBoundaryById": {
                        "End_Error": "Boundary_Backend",
                    },
                    "forbidUntypedBoundaries": True,
                    "requiredGuardReferencesById": {
                        "End_Error": ["working"],
                    },
                },
                "decisionPhases": {
                    "Sub_Assess": {
                        "minDivergingExclusiveGateways": 1,
                    }
                },
                "rootTopology": {
                    "exactStartEvents": 1,
                    "exactEndEvents": 1,
                },
                "requiredReachability": [
                    {
                        "sources": ["Sub_Assess", "Boundary_Backend"],
                        "target": "Task_Items",
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "Complex"
            bpmn_path = build_bpmn.build(spec, project)
            root = ET.parse(bpmn_path).getroot()

            ns = build_bpmn.NS
            entry_point = root.find(
                ".//bpmn:startEvent/bpmn:extensionElements/uipath:entryPointId",
                ns,
            )
            self.assertIsNotNone(entry_point)
            self.assertEqual(entry_point.attrib["value"], "Entry_Main")
            scripts = root.findall(".//bpmn:scriptTask", ns)
            self.assertEqual(scripts, [])
            self.assertEqual(
                len(root.findall(".//bpmn:errorEventDefinition", ns)), 2
            )
            loops = root.findall(
                ".//bpmn:multiInstanceLoopCharacteristics", ns
            )
            self.assertEqual(len(loops), 1)
            self.assertEqual(loops[0].attrib["isSequential"], "true")
            output = root.find(
                ".//bpmn:task[@id='Task_Items']"
                "/bpmn:extensionElements/uipath:mapping/uipath:output",
                ns,
            )
            self.assertIsNotNone(output)
            self.assertEqual(output.attrib["var"], "Var_Result")

            process = root.find(".//bpmn:process", ns)
            self.assertIsNotNone(process)
            self.assertEqual(process.attrib["isExecutable"], "false")
            migration = process.find(
                "./bpmn:extensionElements/uipath:migrationVersion",
                ns,
            )
            self.assertIsNotNone(migration)
            self.assertEqual(migration.attrib["version"], "15")

            declarations = process.findall(
                "./bpmn:extensionElements/uipath:variables/*",
                ns,
            )
            declaration_ids = {item.attrib["id"] for item in declarations}
            self.assertEqual(
                declaration_ids,
                {
                    "input_Var_Items",
                    "Var_Items",
                    "output_Var_Result",
                    "Var_Result",
                    "Var_Working",
                },
            )
            start_bridge = root.find(
                ".//bpmn:startEvent[@id='Start_Main']"
                "/bpmn:extensionElements/uipath:mapping/uipath:output",
                ns,
            )
            self.assertIsNotNone(start_bridge)
            self.assertEqual(start_bridge.attrib["var"], "Var_Items")
            self.assertEqual(
                start_bridge.attrib["source"],
                "=vars.input_Var_Items",
            )
            end_bridge = root.find(
                ".//bpmn:endEvent[@id='End_Main']"
                "/bpmn:extensionElements/uipath:mapping/uipath:output",
                ns,
            )
            self.assertIsNotNone(end_bridge)
            self.assertEqual(end_bridge.attrib["var"], "output_Var_Result")
            self.assertEqual(end_bridge.attrib["source"], "=vars.Var_Result")

            nodes = build_bpmn.collect_nodes(
                {
                    "nodes": spec["process"]["nodes"],
                    "flows": spec["process"]["flows"],
                }
            )
            shapes = root.findall(".//bpmndi:BPMNShape", ns)
            self.assertEqual(len(shapes), len(nodes))
            bounds_by_node = {
                shape.attrib["bpmnElement"]: {
                    key: float(value)
                    for key, value in shape.find(
                        "dc:Bounds",
                        ns,
                    ).attrib.items()
                }
                for shape in shapes
            }
            subprocess_bounds = bounds_by_node["Sub_Assess"]
            for child_id in (
                "Start_Assess",
                "Gateway_Check",
                "End_Error",
                "End_Assess",
            ):
                child_bounds = bounds_by_node[child_id]
                self.assertGreaterEqual(
                    child_bounds["x"],
                    subprocess_bounds["x"],
                )
                self.assertGreaterEqual(
                    child_bounds["y"],
                    subprocess_bounds["y"],
                )
                self.assertLessEqual(
                    child_bounds["x"] + child_bounds["width"],
                    subprocess_bounds["x"] + subprocess_bounds["width"],
                )
                self.assertLessEqual(
                    child_bounds["y"] + child_bounds["height"],
                    subprocess_bounds["y"] + subprocess_bounds["height"],
                )

            boundary_bounds = bounds_by_node["Boundary_Backend"]
            self.assertGreaterEqual(
                boundary_bounds["x"],
                subprocess_bounds["x"],
            )
            self.assertLessEqual(
                boundary_bounds["x"] + boundary_bounds["width"],
                subprocess_bounds["x"] + subprocess_bounds["width"],
            )
            self.assertLess(
                boundary_bounds["y"],
                subprocess_bounds["y"] + subprocess_bounds["height"],
            )
            self.assertGreater(
                boundary_bounds["y"] + boundary_bounds["height"],
                subprocess_bounds["y"] + subprocess_bounds["height"],
            )
            flows = build_bpmn.collect_flows(
                {
                    "nodes": spec["process"]["nodes"],
                    "flows": spec["process"]["flows"],
                }
            )
            edges = root.findall(".//bpmndi:BPMNEdge", ns)
            self.assertEqual(len(edges), len(flows))

            entry_points = json.loads(
                (project / "entry-points.json").read_text(encoding="utf-8")
            )
            entry = entry_points["entryPoints"][0]
            self.assertEqual(entry["id"], "Entry_Main")
            self.assertIn("items", entry["inputSchema"]["properties"])
            self.assertIn("result", entry["outputSchema"]["properties"])
            self.assertNotIn("working", entry["inputSchema"]["properties"])
            self.assertNotIn("working", entry["outputSchema"]["properties"])

        spec["process"]["nodes"][1]["flows"][1]["condition"] = "=js:true"
        with self.assertRaisesRegex(
            ValueError,
            "does not reference required variable 'working'",
        ):
            build_bpmn.validate_constraints(spec)

    def test_rejects_underdeveloped_visible_decision_phase(self) -> None:
        spec = {
            "project": {
                "name": "Decisions",
                "startId": "Start_Main",
                "entryPointId": "Entry_Main",
            },
            "process": {
                "id": "Process_Decisions",
                "variables": [],
                "nodes": [
                    {"kind": "startEvent", "id": "Start_Main"},
                    {
                        "kind": "subProcess",
                        "id": "Sub_Assess",
                        "nodes": [
                            {"kind": "startEvent", "id": "Start_Assess"},
                            {
                                "kind": "exclusiveGateway",
                                "id": "Gateway_One",
                                "default": "Flow_Gateway_No",
                            },
                            {"kind": "endEvent", "id": "End_Yes"},
                            {"kind": "endEvent", "id": "End_No"},
                        ],
                        "flows": [
                            {
                                "id": "Flow_Start_Gateway",
                                "source": "Start_Assess",
                                "target": "Gateway_One",
                            },
                            {
                                "id": "Flow_Gateway_Yes",
                                "source": "Gateway_One",
                                "target": "End_Yes",
                                "condition": "=js:vars.flag",
                            },
                            {
                                "id": "Flow_Gateway_No",
                                "source": "Gateway_One",
                                "target": "End_No",
                            },
                        ],
                    },
                    {"kind": "endEvent", "id": "End_Main"},
                ],
                "flows": [
                    {
                        "id": "Flow_Start_Assess",
                        "source": "Start_Main",
                        "target": "Sub_Assess",
                    },
                    {
                        "id": "Flow_Assess_End",
                        "source": "Sub_Assess",
                        "target": "End_Main",
                    },
                ],
            },
            "constraints": {
                "publicInputs": [],
                "publicOutputs": [],
                "internalVariables": [],
                "scriptTasks": {
                    "exact": 0,
                    "allowedIds": [],
                    "allowedOutputsById": {},
                    "requiredInputReferencesById": {},
                },
                "errorEnds": {
                    "singleGuardedIncoming": True,
                    "allowedIds": [],
                    "matchingBoundaryById": {},
                    "forbidUntypedBoundaries": True,
                },
                "decisionPhases": {
                    "Sub_Assess": {
                        "minDivergingExclusiveGateways": 2,
                    }
                },
                "rootTopology": {
                    "exactStartEvents": 1,
                    "exactEndEvents": 1,
                },
                "requiredReachability": [],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                ValueError,
                "requires at least 2 diverging exclusive gateways, found 1",
            ):
                build_bpmn.build(spec, Path(directory) / "Decisions")


if __name__ == "__main__":
    unittest.main()
