#!/usr/bin/env python3
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_fakes import (  # noqa: E402
    CONTRACTS, EXPIRING_CONTRACTS, FIELD_LISTER, REMINDER_SENDER, TODAY, cc, fx, sandbox,
)


FIXTURE_CONNECTION = "0f0e0d0c-0000-4000-8000-000000000001"
OTHER_CONNECTION = "0f0e0d0c-0000-4000-8000-000000000002"
SLACK_CONNECTION = "0f0e0d0c-0000-4000-8000-000000000003"
OUTLOOK_CONNECTION = "0f0e0d0c-0000-4000-8000-000000000004"
CONNECTIONS = {FIXTURE_CONNECTION: fx.CONNECTOR, OTHER_CONNECTION: fx.CONNECTOR,
               SLACK_CONNECTION: "uipath-salesforce-slack", OUTLOOK_CONNECTION: "uipath-microsoft-outlook365"}
TASK = {"call": "UiPath.IntSvc", "with": {"connector": fx.CONNECTOR, "connectionId": FIXTURE_CONNECTION,
                                          "method": "POST", "endpoint": "/Task"}}
EMAIL = {"call": "UiPath.IntSvc", "with": {"connector": "uipath-microsoft-outlook365", "connectionId": OUTLOOK_CONNECTION,
                                           "method": "POST", "endpoint": "/send-mail-v2"}}


def switched(when, then=(), otherwise=(), then_exit=True):
    return {"If_1#Wrapper": {"do": [
        {"If_1": {"switch": [{"case": {"when": when, "then": "If_1#Then"}}, {"default": {"then": "If_1#Else"}}]}},
        {"If_1#Then": {"do": list(then), **({"then": "exit"} if then_exit else {})}},
        {"If_1#Else": {"do": list(otherwise), "then": "exit"}}]}}


def searching(*tasks, inputs=(), connection=FIXTURE_CONNECTION):
    search = {"call": "UiPath.IntSvc", "with": {"connector": fx.CONNECTOR, "connectionId": connection,
                                                "method": "POST", "endpoint": "/curated_soqlQuery"}}
    workflow = {"do": [{"Sequence_1": {"do": [{"SearchContracts_1": search}, *tasks]}}]}
    if inputs:
        workflow["input"] = {"schema": {"document": {"properties": {name: {"type": "boolean"} for name in inputs}}}}
    return json.dumps(workflow)


def bound_to(connection, then=None, switch=True):
    then = then or {"call": "UiPath.IntSvc", "with": {"connector": "uipath-salesforce-slack",
                                                      "connectionId": SLACK_CONNECTION, "method": "POST",
                                                      "endpoint": "/send_message_to_channel_v2"}}
    if not switch:
        return searching({"SendReminder_1": then}, connection=connection)
    return searching(switched("${$workflow.input.sendReminders}", [{"SendReminder_1": then}]),
                     inputs=["sendReminders"], connection=connection)


class MainTests(unittest.TestCase):
    def run_main(self, workflow_text, answer, prepare=None):
        prepared = mock.patch.object(cc, "prepare", side_effect=prepare) if prepare else \
            mock.patch.object(cc, "prepare", return_value=(FIXTURE_CONNECTION, CONTRACTS))
        with sandbox(workflow_text), prepared, mock.patch.object(cc, "connection_map", return_value=CONNECTIONS), \
                mock.patch.object(cc, "run_workflow", side_effect=answer) as runner, \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                code = cc.main(TODAY)
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue() + err.getvalue(), runner

    def test_correct_workflow_passes(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertEqual(runner.call_args.args[1], {})

    def test_the_project_listing_contracts_is_graded_beside_helper_projects(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        projects = {"contract-fields": FIELD_LISTER, "expiring-contracts": EXPIRING_CONTRACTS,
                    "send-reminders": REMINDER_SENDER}
        code, log, runner = self.run_main(projects, lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertIn(f"OK: {os.path.join('expiring-contracts', 'Workflow.json')}:", log)
        self.assertEqual(runner.call_args.args[1], {"daysAhead": 30})

    def test_failed_run_is_retried_once_then_fails(self):
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (False, None, "run failed: bad SOQL"))
        self.assertIn("did not run", str(code))
        self.assertNotIn("bad SOQL", str(code))
        self.assertEqual(runner.call_count, 2)

    def test_a_run_that_timed_out_is_not_retried(self):
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (False, None, "run timed out"))
        self.assertIn("did not run with inputs {}: run timed out", str(code))
        self.assertEqual(runner.call_count, 1)

    def test_a_connection_listing_that_fails_is_infrastructure(self):
        with sandbox(json.dumps({})), mock.patch.object(cc, "prepare", return_value=(FIXTURE_CONNECTION, CONTRACTS)), \
                mock.patch.object(cc, "connection_map", side_effect=cc.InfraError("listing failed")), \
                mock.patch.object(cc, "run_workflow") as runner, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cc.main(TODAY), cc.INFRA_EXIT)
        runner.assert_not_called()

    def test_missing_seed_is_infrastructure(self):
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (True, [], None),
                                          prepare=fx.FixtureError("no readable .golden/sfdc_fixture.json"))
        self.assertEqual(code, cc.INFRA_EXIT)
        runner.assert_not_called()

    def test_a_workflow_on_another_salesforce_connection_is_infrastructure(self):
        code, log, runner = self.run_main(bound_to(OTHER_CONNECTION), lambda *a, **k: (True, [], None))
        self.assertEqual(code, cc.INFRA_EXIT)
        self.assertIn(f"{OTHER_CONNECTION}, not {FIXTURE_CONNECTION}", log)
        runner.assert_not_called()

    def test_a_workflow_on_the_fixture_connection_is_graded_whatever_else_it_binds(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        code, log, runner = self.run_main(bound_to(FIXTURE_CONNECTION.upper()), lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertEqual(runner.call_args.args[1], {"sendReminders": False})

    def test_a_workflow_that_writes_or_sends_on_every_run_fails_without_a_run(self):
        for workflow in (bound_to(FIXTURE_CONNECTION, switch=False), bound_to(FIXTURE_CONNECTION, TASK, False)):
            with self.subTest(workflow=workflow):
                code, log, runner = self.run_main(workflow, lambda *a, **k: (True, [], None))
                self.assertIn("would write to Salesforce or send something (SendReminder_1 (", str(code))
                runner.assert_not_called()

    def test_a_switch_covers_the_salesforce_write_its_if_routes_around(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        code, log, runner = self.run_main(bound_to(FIXTURE_CONNECTION, TASK), lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertEqual(runner.call_args.args[1], {"sendReminders": False})

    def test_a_switch_does_not_cover_a_write_outside_its_if(self):
        workflow = searching(switched("${$workflow.input.sendReminders}", [{"SendReminder_1": EMAIL}]),
                             {"LogReminder_1": TASK}, inputs=["sendReminders"])
        code, log, runner = self.run_main(workflow, lambda *a, **k: (True, [], None))
        self.assertIn(f"send something (LogReminder_1 ({fx.CONNECTOR} POST /Task)),", str(code))
        runner.assert_not_called()

    def test_a_declared_switch_that_no_condition_reads_covers_nothing(self):
        for name in ("dryRun", "includePreviewText", "isTestModeDisabled"):
            with self.subTest(name=name):
                code, log, runner = self.run_main(searching({"CloseContract_1": TASK}, inputs=[name]),
                                                  lambda *a, **k: (True, [], None))
                self.assertIn("(CloseContract_1 (", str(code))
                runner.assert_not_called()

    def test_a_switch_gets_the_value_its_condition_needs_whatever_its_name(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        for when, name, value in (("${!$workflow.input.skipEmails}", "skipEmails", True),
                                  ("${$workflow.input.dryRun === false}", "dryRun", True),
                                  ("${$workflow.input.isTestModeDisabled}", "isTestModeDisabled", False)):
            with self.subTest(when=when):
                workflow = searching(switched(when, [{"SendReminder_1": EMAIL}]), inputs=[name])
                code, log, runner = self.run_main(workflow, lambda *a, **k: (True, good, None))
                self.assertEqual(code, 0, log)
                self.assertEqual(runner.call_args.args[1], {name: value})

    def test_a_script_that_posts_counts_and_a_switch_covers_it_inside_its_if(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        post = {"run": {"script": {"language": "javascript", "code": "await fetch('https://hooks.slack.com/x');"}}}
        code, log, runner = self.run_main(searching({"Post_1": post}), lambda *a, **k: (True, good, None))
        self.assertIn("(Post_1 (JavaScript using fetch))", str(code))
        runner.assert_not_called()
        switched_post = searching(switched("${$workflow.input.notify}", [{"Post_1": post}]), inputs=["notify"])
        code, log, runner = self.run_main(switched_post, lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertEqual(runner.call_args.args[1], {"notify": False})

    def test_a_branch_that_falls_through_into_the_write_is_not_run(self):
        workflow = searching(switched("${$workflow.input.dryRun}", [{"Log_1": {"set": {}}}], [{"Close_1": TASK}],
                                      then_exit=False), inputs=["dryRun"])
        code, log, runner = self.run_main(workflow, lambda *a, **k: (True, [], None))
        self.assertIn("(Close_1 (", str(code))
        runner.assert_not_called()

    def test_a_required_boolean_no_condition_needs_is_passed_false(self):
        good = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        workflow = json.loads(searching(inputs=["includeDrafts"]))
        workflow["input"]["schema"]["document"]["required"] = ["includeDrafts"]
        code, log, runner = self.run_main(json.dumps(workflow), lambda *a, **k: (True, good, None))
        self.assertEqual(code, 0, log)
        self.assertEqual(runner.call_args.args[1], {"includeDrafts": False})

    def test_a_connection_the_tenant_does_not_list_fails_without_a_run(self):
        code, log, runner = self.run_main(bound_to("<REPLACE_WITH_VENDOR_CONNECTION_UUID>"),
                                          lambda *a, **k: (False, None, "run failed: no such connection"))
        self.assertIn("(SearchContracts_1 (uipath-salesforce-sfdc POST /curated_soqlQuery through an unlisted "
                      "connection)", str(code))
        runner.assert_not_called()

    def test_an_activity_naming_one_connector_on_another_s_connection_fails_without_a_run(self):
        disguised = {"call": "UiPath.IntSvc", "with": {"connector": "uipath-uipath-airdk", "method": "DELETE",
                                                       "connectionId": FIXTURE_CONNECTION, "endpoint": "/Contract/x"}}
        code, log, runner = self.run_main(searching({"Summarize_1": disguised}), lambda *a, **k: (True, [], None))
        self.assertIn("through a uipath-salesforce-sfdc connection", str(code))
        runner.assert_not_called()

    def test_a_script_that_rewrites_a_switch_leaves_the_write_reachable(self):
        rewrite = {"run": {"script": {"language": "javascript", "code": "$workflow.input.sendReminders = true;"}}}
        workflow = json.loads(bound_to(FIXTURE_CONNECTION, TASK))
        workflow["do"][0]["Sequence_1"]["do"].insert(1, {"Rewrite_1": rewrite})
        code, log, runner = self.run_main(json.dumps(workflow), lambda *a, **k: (True, [], None))
        self.assertIn("(SendReminder_1 (", str(code))
        runner.assert_not_called()


class PrepareTests(unittest.TestCase):
    def prepare(self, statuses, verified=(FIXTURE_CONNECTION, "001AAAAAAAAAAAAAAA", None)):
        state = {"connection_id": FIXTURE_CONNECTION, "account_id": "001AAAAAAAAAAAAAAA", "token": "0a1b2c3d",
                 "contracts": []}
        described = [{**c, "status": status} for c, status in zip(CONTRACTS, statuses)]
        verify = {"side_effect": verified} if isinstance(verified, Exception) else {"return_value": verified}
        with mock.patch.object(fx, "load_state", return_value=state), mock.patch.object(fx, "save_state"), \
                mock.patch.object(fx, "verify_fixture", **verify), \
                mock.patch.object(fx, "add_contract", return_value=CONTRACTS[4]) as add, \
                mock.patch.object(fx, "describe", return_value=described):
            try:
                return cc.prepare(TODAY)
            except fx.FixtureError as exc:
                if not isinstance(verified, Exception):
                    raise
                return exc, add

    def test_returns_the_connection_and_contracts_once_every_one_is_activated(self):
        connection, contracts = self.prepare(["Activated"] * len(CONTRACTS))
        self.assertEqual(connection, FIXTURE_CONNECTION)
        self.assertEqual(len(contracts), len(CONTRACTS))

    def test_a_state_file_that_no_longer_names_the_fixture_adds_nothing(self):
        exc, add = self.prepare(["Activated"] * len(CONTRACTS), fx.FixtureError("not the fixture account"))
        self.assertIn("not the fixture account", str(exc))
        add.assert_not_called()

    def test_a_contract_that_is_not_activated_is_infrastructure(self):
        statuses = ["Activated"] * len(CONTRACTS)
        statuses[1] = "Draft"
        with self.assertRaises(fx.FixtureError) as raised:
            self.prepare(statuses)
        self.assertIn(f"{CONTRACTS[1]['label']} (Draft)", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
