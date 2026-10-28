#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import golden_connectors as gc  # noqa: E402


def workflow(inputs=None, outputs=None, required=None):
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


SFDC, JIRA = "uipath-salesforce-sfdc", "uipath-atlassian-jira"
CONNECTIONS = {"00000000-0000-4000-8000-0000000000a1": SFDC, "00000000-0000-4000-8000-0000000000a2": JIRA,
               "00000000-0000-4000-8000-0000000000a3": "uipath-microsoft-outlook365",
               "00000000-0000-4000-8000-0000000000a4": "uipath-salesforce-slack",
               "00000000-0000-4000-8000-0000000000a5": "uipath-uipath-airdk",
               "00000000-0000-4000-8000-0000000000a6": "uipath-openai-openai"}
CONNECTION = {connector: connection for connection, connector in CONNECTIONS.items()}


def call(connector, method, endpoint, kind="UiPath.IntSvc", connection=None):
    return {"call": kind, "with": {"connector": connector, "method": method, "endpoint": endpoint,
                                   "connectionId": connection or CONNECTION.get(connector.lower(), "missing")}}


def http(method, url, authentication="manual", **extra):
    request = {"authentication": authentication, "method": method, "url": url, **extra}
    return {"call": "UiPath.Http", "with": {"connector": "uipath-uipath-http", "connectionId": "ImplicitConnection",
                                            "method": "POST", "endpoint": "/http-request", "bodyParameters": request}}


def script(code):
    return {"run": {"script": {"language": "javascript", "code": code}}}


def effects(workflow, reads_from=SFDC, open_urls=()):
    return gc.side_effects(workflow, reads_from, CONNECTIONS, open_urls)


class SideEffectTests(unittest.TestCase):
    def test_side_effect_tasks_finds_activities_at_any_depth_and_returns_them(self):
        email = call("uipath-microsoft-outlook365", "POST", "/SendMailV2")
        nested = {"do": [{"Sequence_1": {"do": [
            {"Query_1": call("Uipath-Salesforce-Sfdc", "post", "/curated_soqlQuery")},
            {"Try_1": {"try": [{"Email_1": email}], "catch": {"do": []}}},
        ]}}]}
        self.assertEqual(gc.side_effect_tasks(nested, SFDC, CONNECTIONS),
                         [("Email_1 (uipath-microsoft-outlook365 POST /SendMailV2)", email)])
        self.assertEqual(effects({"Bad_1": {"call": "UiPath.IntSvc", "with": "x"}}),
                         ["Bad_1 (UiPath.IntSvc through an unlisted connection)"])

    def test_reads_of_the_scenario_connector_and_text_generation_have_no_side_effects(self):
        reads = {"do": [{"Soql_1": call(SFDC, "POST", "/curated_soqlQuery")}, {"Get_1": call(SFDC, "GET", "/Contract")},
                        {"Sosl_1": call(SFDC, "POST", "/parameterizedSearch_POST")},
                        {"Llm_1": call("uipath-uipath-airdk", "POST", "/v1/llmCall")},
                        {"Chat_1": call("uipath-openai-openai", "POST", "/v2/chat/completion")}]}
        self.assertEqual(effects(reads), [])
        searches = {"do": [{"Search_1": call(JIRA, "GET", "/search")}, {"Jql_1": call(JIRA, "POST", "/search")},
                           {"Fields_1": call(JIRA, "GET", "/search_issues_with_fields")}]}
        self.assertEqual(effects(searches, JIRA), [])

    def test_a_model_connector_counts_beyond_text_generation(self):
        workflow = {"do": [{"Index_1": call("uipath-uipath-airdk", "POST", "/update_index")},
                           {"Search_1": call("uipath-uipath-airdk", "POST", "/v2/webSearch")},
                           {"Users_1": call("uipath-openai-openai", "GET", "/organizationUsers")},
                           {"Get_1": call("uipath-uipath-airdk", "GET", "/v1/llmCall")}]}
        self.assertEqual(effects(workflow), ["Get_1 (uipath-uipath-airdk GET /v1/llmCall)",
                                             "Index_1 (uipath-uipath-airdk POST /update_index)",
                                             "Search_1 (uipath-uipath-airdk POST /v2/webSearch)",
                                             "Users_1 (uipath-openai-openai GET /organizationUsers)"])

    def test_a_call_counts_unless_its_connection_belongs_to_the_connector_it_names(self):
        workflow = {"do": [
            {"Model_1": call("uipath-uipath-airdk", "DELETE", "/Contract/x", connection=CONNECTION[SFDC])},
            {"Read_1": call(SFDC, "GET", "/Contract", connection="00000000-0000-4000-8000-0000000000ff")},
            {"Implicit_1": call(SFDC, "GET", "/Contract", connection="ImplicitConnection")},
            {"Upper_1": call(SFDC, "GET", "/Contract", connection=CONNECTION[SFDC].upper())}]}
        self.assertEqual(effects(workflow),
                         ["Implicit_1 (uipath-salesforce-sfdc GET /Contract through an unlisted connection)",
                          f"Model_1 (uipath-uipath-airdk DELETE /Contract/x through a {SFDC} connection)",
                          "Read_1 (uipath-salesforce-sfdc GET /Contract through an unlisted connection)"])

    def test_a_trigger_reads_only_on_the_scenario_connector(self):
        def trigger(connector, connection=None):
            return {"call": "UiPath.IntSvcEvent", "with": {"connector": connector, "eventType": "UPDATED",
                                                           "connectionId": connection or CONNECTION[connector]}}

        workflow = {"do": [{"Updated_1": trigger(SFDC)}, {"Clicked_1": trigger("uipath-salesforce-slack")},
                           {"Foreign_1": trigger(SFDC, CONNECTION[JIRA])}]}
        self.assertEqual(effects(workflow), ["Clicked_1 (uipath-salesforce-slack trigger)",
                                             f"Foreign_1 ({SFDC} trigger through a {JIRA} connection)"])

    def test_a_read_is_a_get_or_a_known_search_never_an_endpoint_that_mentions_one(self):
        query = "/Contract/${$context.outputs.curated_soqlQuery_1.content[0].Id}"
        for method, endpoint in (("DELETE", "/jobs/query/{id}"), ("PATCH", query), ("POST", "/research_notes__c"),
                                 ("POST", "/Contract?query=x"), ("POST", "/create_query_job"),
                                 ("PUT", "/curated_soqlQuery"), ("POST", "/curated_soqlQuery/x")):
            with self.subTest(method=method, endpoint=endpoint):
                self.assertEqual(effects({"Write_1": call(SFDC, method, endpoint)}),
                                 [f"Write_1 ({SFDC} {method} {endpoint})"])
        self.assertEqual(effects({"Fields_1": call(JIRA, "POST", "/search_issues_with_fields")}, JIRA),
                         [f"Fields_1 ({JIRA} POST /search_issues_with_fields)"])

    def test_an_http_request_counts_unless_it_goes_straight_to_an_open_url(self):
        open_urls = ("https://api.example.com/facts/",)
        workflow = {"do": [{"Fact_1": http("GET", "https://api.example.com/facts/random")},
                           {"Post_1": http("POST", "https://api.example.com/facts/${$workflow.input.kind}")},
                           {"Other_1": http("GET", "https://api.example.com/factsheet")},
                           {"Host_1": http("GET", "https://api.example.com.example.net/facts/x")},
                           {"Url_1": http("GET", "${$workflow.input.factsUrl}")},
                           {"Upper_1": http("GET", "HTTPS://API.EXAMPLE.COM/facts/x")}]}
        self.assertEqual(effects(workflow, open_urls=open_urls),
                         ["Host_1 (HTTP GET https://api.example.com.example.net/facts/x)",
                          "Other_1 (HTTP GET https://api.example.com/factsheet)",
                          "Upper_1 (HTTP GET HTTPS://API.EXAMPLE.COM/facts/x)",
                          "Url_1 (HTTP GET ${$workflow.input.factsUrl})"])
        self.assertEqual(effects({"Fact_1": http("GET", "https://api.example.com/facts/random")}),
                         ["Fact_1 (HTTP GET https://api.example.com/facts/random)"])

    def test_an_http_request_through_a_connector_or_reshaped_always_counts(self):
        reshaped = http("GET", "https://api.example.com/facts/x")
        reshaped["with"].update(connectionId=CONNECTION[SFDC], method="DELETE", endpoint="/Contract/x")
        workflow = {"do": [
            {"Read_1": http("GET", "/services/data/v60.0/query?q=x", "connector", targetConnector=SFDC)},
            {"Bare_1": http("GET", "/services/data", "connector")},
            {"Reshaped_1": reshaped}]}
        self.assertEqual(effects(workflow, open_urls=("https://api.example.com/facts/",)),
                         ["Bare_1 (HTTP GET /services/data through a connector)",
                          "Read_1 (HTTP GET /services/data/v60.0/query?q=x through a connector)",
                          "Reshaped_1 (HTTP GET https://api.example.com/facts/x through a connector)"])

    def test_the_simple_http_form_other_calls_emit_and_run_count_unless_they_only_script(self):
        workflow = {"do": [
            {"Get_1": {"call": "http", "with": {"method": "get", "endpoint": {"uri": "https://api.example.com/x"}}}},
            {"Hook_1": {"call": "http", "with": {"method": "post", "endpoint": "https://hooks.slack.com/services/x"}}},
            {"Job_1": {"call": "UiPath.StartJob", "with": {}}},
            {"Emit_1": {"emit": {"event": {"with": {"type": "x"}}}}},
            {"Shell_1": {"run": {"shell": {"command": "curl"}}}},
            {"Js_1": script("return 1")}]}
        self.assertEqual(effects(workflow),
                         ["Emit_1 (emit)", "Get_1 (HTTP GET https://api.example.com/x)",
                          "Hook_1 (HTTP POST https://hooks.slack.com/services/x)", "Job_1 (call UiPath.StartJob)",
                          "Shell_1 (run shell)"])
        self.assertEqual(effects({"Get_1": workflow["do"][0]["Get_1"]}, open_urls=("https://api.example.com/",)), [])

    def test_javascript_that_reaches_the_network_or_the_machine_counts(self):
        workflow = {"do": [
            {"Notify_1": script("await fetch('https://hooks.slack.com/services/x', {method: 'POST'}); return 1;")},
            {"Module_1": script("const https = require('https'); return typeof https.request;")},
            {"Assign_1": {"set": {"platform": "${process.platform}"}}},
            {"Sneaky_1": script("return (() => {}).constructor('return globalThis')();")},
            {"Lookup_1": script("return [].filter['constructor']('return this')()['fe' + 'tch'];")},
            {"Global_1": script("return this['fe' + 'tch'] && window.location && self.origin;")},
            {"Listed_1": {"set": {"items": ["${1}", ["${fetch('https://hooks.zapier.com/x')}"]]}}},
            {"Export_1": {"set": {}, "export": {"as": "{ ...$context, sent: fetch('https://example.com') }"}}},
            {"Prompt_1": script("return 'Fetch the closed tickets and process them; return JSON with this exact shape. "
                                "Leave out the maintenance window. Describe the change itself.';")},
            {"Shape_1": script("return $context.outputs.query_1.content.map(c => ({ id: c.Id, ends: c.EndDate }));")},
            {"Label_1": {"set": {"note": "fetch(this) is not code here"}}}]}
        self.assertEqual(effects(workflow),
                         ["Assign_1 (JavaScript using process)", "Export_1 (JavaScript using fetch)",
                          "Global_1 (JavaScript using a computed property name, self, this, window)",
                          "Listed_1 (JavaScript using fetch)",
                          "Lookup_1 (JavaScript using a computed property name, constructor)",
                          "Module_1 (JavaScript using require)", "Notify_1 (JavaScript using fetch)",
                          "Sneaky_1 (JavaScript using constructor, globalThis)"])
        found = dict(gc.side_effect_tasks(workflow, SFDC, CONNECTIONS))
        self.assertIs(found["Notify_1 (JavaScript using fetch)"], workflow["do"][0]["Notify_1"]["run"]["script"])

    def test_javascript_that_reaches_out_without_calling_by_name_counts(self):
        for code, name in (("return (0, require)('os').hostname();", "require"),
                           ("return require.call(null, 'os');", "require"),
                           ("return module['require']('os');", "module, require"),
                           ("const d = Object.getOwnPropertyDescriptor(x, 'y'); return d;", "getOwnPropertyDescriptor"),
                           ("return Reflect.get(x, 'y');", "Reflect"),
                           ("return x['\\x63onstructor'];", "constructor"),
                           ("with (o) { return 1; }", "with"),
                           ("return arguments.length;", "arguments")):
            with self.subTest(code=code):
                self.assertEqual(effects({"do": [{"Js_1": script(code)}]}), [f"Js_1 (JavaScript using {name})"])

    def test_javascript_the_grader_cannot_read_counts(self):
        for code in ("\\u0072equire('os')", "const a = {} / 1;", "return `${x`;", "return 'open;", "x = 1 /* open",
                     "of / 2 / 1"):
            with self.subTest(code=code):
                self.assertEqual(effects({"do": [{"Js_1": script(code)}]}), ["Js_1 (JavaScript the grader cannot read)"])
        self.assertEqual(effects({"do": [{"Set_1": {"set": {"n": "${ (}"}}}]}), ["Set_1 (JavaScript the grader cannot read)"])
        self.assertEqual(effects({"do": [{"Set_1": {"input": {"from": "require('os')"}}}]}),
                         ["Set_1 (JavaScript using require)"])

    def test_script_arguments_are_read_even_when_their_quotes_are_escaped_twice(self):
        def task(arguments):
            return {"do": [{"Js_1": {"run": {"script": {"language": "javascript", "code": "return 1;",
                                                        "arguments": arguments}}}}]}

        standard = '${{ "$context": $context, "$workflow": $workflow, "$input": $input }}'
        self.assertEqual(effects(task(standard)), [])
        self.assertEqual(effects(task(standard.replace('"', '\\"'))), [])
        self.assertEqual(effects(task('${{ \\"os\\": require(\\"os\\") }}')), ["Js_1 (JavaScript using require)"])

    def test_text_with_several_expressions_is_read_expression_by_expression(self):
        subject = "${$context.outputs.q.content[0].Name} ends on ${$context.outputs.q.content[0].EndDate}"
        self.assertEqual(effects({"do": [{"Set_1": {"set": {"subject": subject}}}]}), [])
        self.assertEqual(effects({"do": [{"Set_1": {"set": {"subject": "${a} and ${process.env.X}"}}}]}),
                         ["Set_1 (JavaScript using process)"])

    def test_comments_strings_and_regexes_hide_no_code(self):
        for code in ("// don't\nrequire('os')", "// note require('os')", "/* it's */ require('os')",
                     "if (x) /'/.test(y); require('os'); y = '/';", "x = `${'`'}${require('os')}`;"):
            with self.subTest(code=code):
                self.assertEqual(effects({"do": [{"Js_1": script(code)}]}), ["Js_1 (JavaScript using require)"])
        for code in ("return s.replace(/\\s+/g, ' ').split(/,\\s*/);", "return (a - b) / 86400000 / 2;",
                     "return x.return / 2;", "return `Hello ${name}, process ${n} items`;",
                     "// process each window\nreturn 1;"):
            with self.subTest(code=code):
                self.assertEqual(effects({"do": [{"Js_1": script(code)}]}), [])

    def test_writes_and_other_connectors_are_side_effects(self):
        workflow = {"do": [{"Task_1": call(SFDC, "POST", "/Task")}, {"Close_1": call(SFDC, "PATCH", "/Contract")},
                           {"Slack_1": call("uipath-salesforce-slack", "POST", "/send_message_to_channel_v2")},
                           {"Search_1": call("uipath-atlassian-jira", "GET", "/search")}]}
        self.assertEqual(effects(workflow),
                         [f"Close_1 ({SFDC} PATCH /Contract)",
                          "Search_1 (uipath-atlassian-jira GET /search)",
                          "Slack_1 (uipath-salesforce-slack POST /send_message_to_channel_v2)",
                          f"Task_1 ({SFDC} POST /Task)"])

    def test_connection_map_lists_every_folder(self):
        rows = [{"Id": "00000000-0000-4000-8000-0000000000A1", "ConnectorKey": "Uipath-Salesforce-Sfdc"},
                {"Id": None, "ConnectorKey": JIRA}]
        with mock.patch.object(gc, "data", return_value=rows) as listed:
            self.assertEqual(gc.connection_map(), {"00000000-0000-4000-8000-0000000000a1": SFDC})
        self.assertIn("--all-folders", listed.call_args.args)

    def test_brief_keeps_only_fixed_text_and_the_error_code(self):
        self.assertEqual(gc.brief("run timed out"), "run timed out")
        self.assertEqual(gc.brief('run failed: {"Result": "Failure", "ErrorCode": "RunFailed", "Message": "token x"}'),
                         "run failed (RunFailed)")
        self.assertEqual(gc.brief("non-JSON CLI output (exit 1): secret"), "run failed")


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
