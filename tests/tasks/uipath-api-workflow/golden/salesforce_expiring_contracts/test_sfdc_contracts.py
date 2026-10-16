#!/usr/bin/env python3
"""Offline tests for _setup/sfdc_contracts.py, with Salesforce stubbed out: the contract
dates, the SOQL and delete calls, seeding, and cleanup.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import datetime
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_fakes import TODAY, fx, sandbox  # noqa: E402


class DateTests(unittest.TestCase):
    def test_start_for_ends_a_one_month_contract_on_the_day(self):
        for end in (datetime.date(2026, 10, 13), datetime.date(2027, 1, 1), datetime.date(2026, 3, 1)):
            start = fx.start_for(end)
            self.assertEqual(fx.add_months(start, 1) - datetime.timedelta(days=1), end)

    def test_add_months_clamps_to_the_month_end(self):
        self.assertEqual(fx.add_months(datetime.date(2026, 3, 31), -1), datetime.date(2026, 2, 28))
        self.assertEqual(fx.add_months(datetime.date(2026, 12, 15), 1), datetime.date(2027, 1, 15))

    def test_seed_offsets_sit_well_inside_and_outside_the_window(self):
        for days in (*fx.INSIDE_DAYS, fx.GRADING_DAYS):
            self.assertTrue(2 <= days <= fx.WINDOW_DAYS - 2)
        for days in fx.OUTSIDE_DAYS:
            self.assertTrue(days < -1 or days > fx.WINDOW_DAYS + 2)


class CallTests(unittest.TestCase):
    def test_soql_accepts_a_list_or_a_records_wrapper(self):
        rows = [{"Id": "1"}, {"Id": "2"}]
        for payload in (rows, {"records": rows}, {"Records": rows}):
            with mock.patch.object(fx, "_uip", return_value=payload):
                self.assertEqual([r["Id"] for r in fx.soql("conn", "SELECT Id FROM Contract")], ["1", "2"])
        with mock.patch.object(fx, "_uip", return_value={}):
            self.assertEqual(fx.soql("conn", "SELECT Id FROM Contract"), [])

    def test_delete_passes_the_path_id_and_confirms(self):
        with mock.patch.object(fx, "_uip") as uip:
            fx.delete("conn", "Contract", "800X")
        args = uip.call_args.args
        self.assertEqual(json.loads(args[args.index("--query") + 1]), {"contractId": "800X"})
        self.assertIn("--yes", args)


class SeedAndCleanupTests(unittest.TestCase):
    def test_seed_records_every_contract_with_its_live_end_date(self):
        created = iter(["001ACC", "800C1", "800C2", "800C3", "800C4"])
        live = [{"Id": f"800C{i}", "ContractNumber": f"0000010{i}", "EndDate": "2026-10-13", "Status": "Activated"}
                for i in range(1, 5)]
        with sandbox(), mock.patch.object(fx, "connection_id", return_value="conn"), \
                mock.patch.object(fx, "create", side_effect=lambda *a, **k: next(created)), \
                mock.patch.object(fx, "update"), mock.patch.object(fx, "soql", return_value=live), \
                contextlib.redirect_stdout(io.StringIO()):
            fx.seed(TODAY)
            state = fx.load_state()
        self.assertEqual(state["account_id"], "001ACC")
        self.assertEqual([c["days"] for c in state["contracts"]], [*fx.INSIDE_DAYS, *fx.OUTSIDE_DAYS])
        self.assertTrue(all(c["end_date"] and c["number"] for c in state["contracts"]))

    def test_cleanup_never_fails_the_task(self):
        with sandbox(), mock.patch.object(fx, "connection_id", side_effect=fx.FixtureError("no connection")), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(fx.cleanup(), 0)
        self.assertIn("cleanup skipped", err.getvalue())

    def test_activated_contract_goes_back_to_draft_before_delete(self):
        calls = []

        def delete(conn, sobject, record_id):
            calls.append(("delete", sobject, record_id))
            if sobject == "Contract" and ("update", "Contract", record_id) not in calls:
                raise fx.FixtureError("cannot delete an activated contract")

        def update(conn, sobject, record_id, body):
            calls.append(("update", sobject, record_id))

        with mock.patch.object(fx, "soql", return_value=[{"Id": "800C1"}]), \
                mock.patch.object(fx, "delete", side_effect=delete), mock.patch.object(fx, "update", side_effect=update):
            self.assertEqual(fx.remove_account("conn", "001ACC"), [])
        self.assertEqual(calls[-1], ("delete", "Account", "001ACC"))


if __name__ == "__main__":
    unittest.main()
