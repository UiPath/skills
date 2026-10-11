#!/usr/bin/env python3
"""Offline tests for check_contracts.py's main flow, with Salesforce and the workflow
runner stubbed out: a correct workflow, a failing run and its retry, and a missing seed.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_fakes import CONTRACTS, TODAY, cc, fx, sandbox  # noqa: E402


class MainTests(unittest.TestCase):
    def run_main(self, workflow_text, answer, prepare=None):
        prepared = mock.patch.object(cc, "prepare", side_effect=prepare) if prepare else \
            mock.patch.object(cc, "prepare", return_value=CONTRACTS)
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

    def test_failed_run_is_retried_once_then_fails(self):
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (False, None, "run failed: bad SOQL"))
        self.assertIn("did not run", str(code))
        self.assertEqual(runner.call_count, 2)

    def test_missing_seed_is_infrastructure(self):
        code, log, runner = self.run_main(json.dumps({}), lambda *a, **k: (True, [], None),
                                          prepare=fx.FixtureError("no readable .golden/sfdc_fixture.json"))
        self.assertEqual(code, cc.INFRA_EXIT)
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
