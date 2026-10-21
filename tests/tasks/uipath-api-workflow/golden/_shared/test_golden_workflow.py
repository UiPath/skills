#!/usr/bin/env python3
"""Offline tests for golden_connectors.py's workflow side: choosing the project to grade,
its declared inputs and outputs, the connector calls that would change something, the
signed-in run, and walking an output's strings and records.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import golden_connectors as gc  # noqa: E402


def workflow(inputs=None, outputs=None, required=None):
    """A workflow declaring the {name: schema} inputs and outputs, with `required` inputs."""
    declared = {}
    if inputs is not None:
        document = {"type": "object", "properties": inputs}
        if required is not None:
            document["required"] = required
        declared["input"] = {"schema": {"format": "json", "document": document}}
    if outputs is not None:
        declared["output"] = {"schema": {"format": "json", "document": {"type": "object", "properties": outputs}}}
    return declared


class WorkflowTests(unittest.TestCase):
    def test_declared_inputs_and_outputs_keep_each_schema(self):
        declared = workflow(inputs={"epicKeys": {"type": "array"}, "x": 1}, outputs={"releaseNotes": {"type": "array"}})
        self.assertEqual(gc.declared_inputs(declared), {"epicKeys": {"type": "array"}, "x": {}})
        self.assertEqual(gc.declared_outputs(declared), {"releaseNotes": {"type": "array"}})
        self.assertEqual(gc.declared_inputs({}), {})
        self.assertEqual(gc.declared_outputs({}), {})

    def test_needed_inputs_are_required_and_have_no_default(self):
        declared = workflow(inputs={"daysAhead": {"type": "integer", "default": 30}, "ownerId": {"type": "string"},
                                    "dryRun": {"type": "boolean"}},
                            required=["daysAhead", "ownerId", "undeclared", 7])
        self.assertEqual(gc.needed_inputs(declared), ["ownerId", "undeclared"])
        self.assertEqual(gc.needed_inputs(workflow(inputs={"ownerId": {"type": "string"}})), [])
        self.assertEqual(gc.needed_inputs(workflow(inputs={"ownerId": {}}, required="ownerId")), [])

    def test_workflow_paths_leave_out_the_root_file_and_node_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("Workflow.json", "node_modules/pkg/Workflow.json", "B/Workflow.json", "A/Workflow.json"):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text("{}")
            self.assertEqual(gc.workflow_paths(tmp), [(root / "A/Workflow.json").resolve(),
                                                      (root / "B/Workflow.json").resolve()])

    def test_run_workflow_runs_signed_in(self):
        with mock.patch.object(gc, "run_row", return_value=(True, {}, None)) as run_row:
            gc.run_workflow("W.json", {"a": 1}, timeout=30)
        run_row.assert_called_once_with("W.json", {"a": 1}, timeout=30, no_auth=False)


class ChooseWorkflowTests(unittest.TestCase):
    def choose(self, projects):
        """The folder choose_workflow grades among {folder: workflow or text}, for a scenario
        whose input is `in` and whose output is `out`."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder, project in projects.items():
                (Path(tmp) / folder).mkdir()
                (Path(tmp) / folder / "Workflow.json").write_text(
                    project if isinstance(project, str) else json.dumps(project))
            chosen = gc.choose_workflow(lambda declared: "in" in gc.declared_inputs(declared),
                                        lambda declared: "out" in gc.declared_outputs(declared), tmp)
        return chosen.parent.name if chosen else None

    def test_a_project_that_fits_wins_over_a_helper_sorting_first(self):
        self.assertEqual(self.choose({"a-helper": workflow(outputs={"out": {}}),
                                      "b-real": workflow(inputs={"in": {}})}), "b-real")

    def test_a_tie_goes_to_the_project_declaring_the_output_then_to_path_order(self):
        self.assertEqual(self.choose({"a": workflow(inputs={"in": {}}),
                                      "b": workflow(inputs={"in": {}}, outputs={"out": {}}),
                                      "c": workflow(inputs={"in": {}}, outputs={"out": {}})}), "b")
        self.assertEqual(self.choose({"a": workflow(inputs={"in": {}}), "b": workflow(inputs={"in": {}})}), "a")

    def test_unreadable_and_non_object_workflows_never_fit(self):
        self.assertEqual(self.choose({"a": "{not json", "b": "[]", "c": workflow(inputs={"in": {}})}), "c")

    def test_without_a_fitting_project_the_first_is_graded_as_before(self):
        self.assertEqual(self.choose({"b": workflow(outputs={"out": {}}), "a": "{not json"}), "a")
        self.assertEqual(self.choose({"only": workflow()}), "only")
        self.assertIsNone(self.choose({}))


def call(connector, method, endpoint, kind="UiPath.IntSvc"):
    return {"call": kind, "with": {"connector": connector, "method": method, "endpoint": endpoint}}


class SideEffectTests(unittest.TestCase):
    def test_connector_calls_lists_every_integration_service_activity_by_name(self):
        nested = {"do": [{"Sequence_1": {"do": [
            {"Query_1": call("Uipath-Salesforce-Sfdc", "post", "/curated_soqlQuery")},
            {"Try_1": {"try": {"do": [{"Email_1": call("uipath-microsoft-outlook365", "POST", "/SendMailV2")}]}}},
            {"Http_1": call("uipath-uipath-http", "POST", "/http-request", kind="UiPath.Http")},
        ]}}]}
        self.assertEqual(gc.connector_calls(nested),
                         [("Email_1", "uipath-microsoft-outlook365", "POST", "/SendMailV2"),
                          ("Query_1", "uipath-salesforce-sfdc", "POST", "/curated_soqlQuery")])
        self.assertEqual(gc.connector_calls({"call": "UiPath.IntSvc", "with": "not an object"}), [])

    def test_reads_of_the_scenario_connector_and_model_calls_have_no_side_effects(self):
        sfdc, jira = "uipath-salesforce-sfdc", "uipath-atlassian-jira"
        reads = {"do": [{"Soql_1": call(sfdc, "POST", "/curated_soqlQuery")}, {"Get_1": call(sfdc, "GET", "/Contract")},
                        {"Llm_1": call("uipath-uipath-airdk", "POST", "/v1/llmCall")},
                        {"Chat_1": call("uipath-openai-openai", "POST", "/v2/chat/completion")}]}
        self.assertEqual(gc.side_effects(reads, sfdc), [])
        searches = {"do": [{"Search_1": call(jira, "GET", "/search")},
                           {"Jql_1": call(jira, "POST", "/search_issues_with_fields")}]}
        self.assertEqual(gc.side_effects(searches, jira), [])

    def test_writes_and_other_connectors_are_side_effects(self):
        sfdc = "uipath-salesforce-sfdc"
        workflow = {"do": [{"Task_1": call(sfdc, "POST", "/Task")}, {"Close_1": call(sfdc, "PATCH", "/Contract")},
                           {"Slack_1": call("uipath-salesforce-slack", "POST", "/send_message_to_channel_v2")},
                           {"Search_1": call("uipath-atlassian-jira", "GET", "/search")}]}
        self.assertEqual(gc.side_effects(workflow, sfdc),
                         [f"Close_1 ({sfdc} PATCH /Contract)",
                          "Search_1 (uipath-atlassian-jira GET /search)",
                          "Slack_1 (uipath-salesforce-slack POST /send_message_to_channel_v2)",
                          f"Task_1 ({sfdc} POST /Task)"])


class OutputWalkTests(unittest.TestCase):
    def test_collects_keys_values_and_json_held_in_strings(self):
        raw = {"notes": '[{"summary": "CSV export"}]', "count": 2}
        found = gc.strings_in(raw)
        self.assertIn("notes", found)
        self.assertIn("summary", found)
        self.assertIn("CSV export", found)

    def test_decode_json_string_only_returns_containers(self):
        self.assertEqual(gc.decode_json_string(' {"a": 1}'), {"a": 1})
        self.assertIsNone(gc.decode_json_string('"text"'))
        self.assertIsNone(gc.decode_json_string("[not json"))

    def test_dicts_in_walks_nested_lists(self):
        self.assertEqual([d["k"] for d in gc.dicts_in({"k": 1, "items": [{"k": 2}, [{"k": 3}]]})], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
