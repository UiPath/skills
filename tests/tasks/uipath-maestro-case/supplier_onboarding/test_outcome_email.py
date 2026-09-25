#!/usr/bin/env python3
"""The three findings `check_outcome_email.py` can report, each driven to its branch.

It was the one checker `mutate.py` never covered: it has no entry in that script's
CLASSES and had no test class, so all three of its `problems.append` sites could be
removed with nothing going red. The mailbox read and the ExternalId lookup are the only
calls that need the tenant, and both are module-level functions, so both are replaced.
"""
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).parent


def load():
    """A fresh copy of the module, so one test's stubs never reach another's."""
    spec = importlib.util.spec_from_file_location(
        "outcome_email_under_test", HERE / "check_outcome_email.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OutcomeEmailTests(unittest.TestCase):
    def run_with(self, runs, external, messages):
        """Run `main()` in a scratch directory and return (exit code, stderr text)."""
        module = load()
        module.POLL_ATTEMPTS = 1
        module.POLL_SLEEP = 0
        module.external_id = external
        module.sent_messages = lambda: messages
        with tempfile.TemporaryDirectory() as workdir:
            module.RUN_STATE = pathlib.Path(workdir) / ".supplier-onboarding-run.json"
            module.RUN_STATE.write_text(json.dumps({"runs": runs}), encoding="utf-8")
            import contextlib
            import io
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                code = module.main()
            return code, err.getvalue()

    def test_a_sending_route_with_no_external_id_is_a_finding(self):
        code, err = self.run_with(
            [{"route": "onboard", "instance_id": "i-1", "folder_key": "f"}],
            lambda instance_id, folder_key: ("", "the instance record carries no ExternalId"),
            [],
        )
        self.assertEqual(code, 1)
        self.assertIn("has no usable ExternalId", err)

    def test_a_route_that_should_send_nothing_is_not_failed_for_a_missing_id(self):
        code, err = self.run_with(
            [{"route": "onboard", "instance_id": "i-1", "folder_key": "f"},
             {"route": "withdraw", "instance_id": "i-2", "folder_key": "f"}],
            lambda instance_id, folder_key: (
                ("tok-1", "") if instance_id == "i-1" else ("", "no ExternalId")),
            [{"subject": "Supplier application tok-1", "sentDateTime": "now"}],
        )
        self.assertEqual(code, 0, err)
        self.assertNotIn("withdraw", err)

    def test_a_missing_notification_is_a_finding(self):
        code, err = self.run_with(
            [{"route": "onboard", "instance_id": "i-1", "folder_key": "f"}],
            lambda instance_id, folder_key: ("tok-1", ""),
            [],
        )
        self.assertEqual(code, 1)
        self.assertIn("0 of 1 buyer notification(s)", err)
        self.assertIn("saveAsDraft", err)

    def test_an_extra_notification_is_a_finding(self):
        code, err = self.run_with(
            [{"route": "onboard", "instance_id": "i-1", "folder_key": "f"}],
            lambda instance_id, folder_key: ("tok-1", ""),
            [{"subject": "Supplier application tok-1"},
             {"subject": "Supplier application tok-1 again"}],
        )
        self.assertEqual(code, 1)
        self.assertIn("the phase was entered again", err)

    def test_the_sendback_route_wants_two(self):
        """`sendback` re-enters 'Buyer review', so one message is short, not correct."""
        code, err = self.run_with(
            [{"route": "sendback", "instance_id": "i-1", "folder_key": "f"}],
            lambda instance_id, folder_key: ("tok-1", ""),
            [{"subject": "Supplier application tok-1"}],
        )
        self.assertEqual(code, 1)
        self.assertIn("1 of 2 buyer notification(s)", err)


if __name__ == "__main__":
    unittest.main()
