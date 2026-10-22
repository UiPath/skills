#!/usr/bin/env python3
"""Offline tests for check_contracts.py's main flow, with Salesforce and the workflow
runner stubbed out: a correct workflow, one beside helper projects, a failing run and its
retry, a missing seed, a workflow bound to another Salesforce connection, one that would
write or send on every run, and fixture contracts that are not Activated.

Run: python3 -m unittest discover -s <this directory>
"""
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


def bound_to(connection, then=None, switch=True):
    """A workflow that searches Salesforce through `connection`, then by default posts to
    Slack through another connection unless its `sendReminders` input is false."""
    search = {"call": "UiPath.IntSvc", "with": {"connector": fx.CONNECTOR, "connectionId": connection,
                                                "method": "POST", "endpoint": "/curated_soqlQuery"}}
    then = then or {"call": "UiPath.IntSvc", "with": {"connector": "uipath-salesforce-slack",
                                                      "connectionId": OTHER_CONNECTION, "method": "POST",
                                                      "endpoint": "/send_message_to_channel_v2"}}
    workflow = {"do": [{"Sequence_1": {"do": [{"SearchContracts_1": search}, {"SendReminder_1": then}]}}]}
    if switch:
        workflow["input"] = {"schema": {"document": {"properties": {"sendReminders": {"type": "boolean"}}}}}
    return json.dumps(workflow)


class MainTests(unittest.TestCase):
    def run_main(self, workflow_text, answer, prepare=None):
        prepared = mock.patch.object(cc, "prepare", side_effect=prepare) if prepare else \
            mock.patch.object(cc, "prepare", return_value=(FIXTURE_CONNECTION, CONTRACTS))
        with sandbox(workflow_text), prepared, \
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
        self.assertEqual(runner.call_count, 2)

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
        task = {"call": "UiPath.IntSvc", "with": {"connector": fx.CONNECTOR, "connectionId": FIXTURE_CONNECTION,
                                                  "method": "POST", "endpoint": "/Task"}}
        for workflow in (bound_to(FIXTURE_CONNECTION, switch=False), bound_to(FIXTURE_CONNECTION, task, False)):
            with self.subTest(workflow=workflow):
                code, log, runner = self.run_main(workflow, lambda *a, **k: (True, [], None))
                self.assertIn("would write to Salesforce or send something on every run (SendReminder_1 (", str(code))
                runner.assert_not_called()

    def test_a_placeholder_connection_is_left_to_fail_the_run(self):
        code, log, runner = self.run_main(bound_to("<REPLACE_WITH_VENDOR_CONNECTION_UUID>"),
                                          lambda *a, **k: (False, None, "run failed: no such connection"))
        self.assertIn("did not run", str(code))
        runner.assert_called()


class PrepareTests(unittest.TestCase):
    def prepare(self, statuses):
        state = {"connection_id": "conn", "account_id": "001ACC", "token": "t0k3n", "contracts": []}
        described = [{**c, "status": status} for c, status in zip(CONTRACTS, statuses)]
        with mock.patch.object(fx, "load_state", return_value=state), mock.patch.object(fx, "save_state"), \
                mock.patch.object(fx, "add_contract", return_value=CONTRACTS[4]), \
                mock.patch.object(fx, "describe", return_value=described):
            return cc.prepare(TODAY)

    def test_returns_the_connection_and_contracts_once_every_one_is_activated(self):
        connection, contracts = self.prepare(["Activated"] * len(CONTRACTS))
        self.assertEqual(connection, "conn")
        self.assertEqual(len(contracts), len(CONTRACTS))

    def test_a_contract_that_is_not_activated_is_infrastructure(self):
        statuses = ["Activated"] * len(CONTRACTS)
        statuses[1] = "Draft"
        with self.assertRaises(fx.FixtureError) as raised:
            self.prepare(statuses)
        self.assertIn(f"{CONTRACTS[1]['label']} (Draft)", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
