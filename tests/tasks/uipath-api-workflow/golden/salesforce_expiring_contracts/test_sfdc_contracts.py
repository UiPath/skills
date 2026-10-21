#!/usr/bin/env python3
"""Offline tests for _setup/sfdc_contracts.py, with Salesforce stubbed out: the contract
dates, the SOQL and delete calls, which accounts count as fixture accounts, seeding
(including contracts that are not activated and too many leftovers), and cleanup with its
sweep of stale fixture accounts.

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


class ConnectionTests(unittest.TestCase):
    @staticmethod
    def row(connection, state="Enabled"):
        return {"Id": connection, "ConnectorKey": fx.CONNECTOR, "State": state}

    def lookup(self, workspace, all_folders, scopes=None):
        def answer(*args, **kwargs):
            in_all = "--all-folders" in args
            if scopes is not None:
                scopes.append("all folders" if in_all else "workspace")
            rows = all_folders if in_all else workspace
            if isinstance(rows, Exception):
                raise rows
            return rows

        with mock.patch.object(fx, "_uip", side_effect=answer):
            return fx.connection_id()

    def test_the_personal_workspace_connection_wins_over_other_folders(self):
        self.assertEqual(self.lookup([self.row("mine")], [self.row("mine"), self.row("theirs")]), "mine")

    def test_falls_back_to_all_folders_when_the_workspace_has_none_or_the_tenant_has_no_workspace(self):
        self.assertEqual(self.lookup([self.row("old", "Failed")], [self.row("shared")]), "shared")
        no_workspace = fx.FixtureError('uip is connections list failed: {"Message": "Personal workspace not available"}')
        self.assertEqual(self.lookup(no_workspace, [self.row("shared")]), "shared")

    def test_a_workspace_listing_that_fails_otherwise_stops_before_any_shared_folder(self):
        scopes = []
        with self.assertRaisesRegex(fx.FixtureError, "timed out"):
            self.lookup(fx.FixtureError("uip is connections list timed out"), [self.row("shared")], scopes)
        self.assertEqual(scopes, ["workspace"])

    def test_several_in_the_deciding_scope_is_infrastructure(self):
        with self.assertRaisesRegex(fx.FixtureError, "in the personal workspace, found 2 of 2"):
            self.lookup([self.row("a"), self.row("b")], [self.row("c")])
        with self.assertRaisesRegex(fx.FixtureError, "across all folders, found 2 of 2"):
            self.lookup([], [self.row("mine"), self.row("theirs")])

    def test_none_anywhere_or_an_all_folders_failure_is_infrastructure(self):
        with self.assertRaisesRegex(fx.FixtureError, "across all folders, found 0 of 0"):
            self.lookup([], [])
        with self.assertRaisesRegex(fx.FixtureError, "all folders down"):
            self.lookup([], fx.FixtureError("all folders down"))


def accounts(*names):
    return [{"Id": f"001A{i}", "Name": name} for i, name in enumerate(names)]


class FixtureAccountTests(unittest.TestCase):
    def test_only_exact_fixture_names_count(self):
        rows = accounts(f"{fx.ACCOUNT_PREFIX} 0a1b2c3d", f"{fx.ACCOUNT_PREFIX} renewals",
                        f"{fx.ACCOUNT_PREFIX} 0A1B2C3D", f"{fx.ACCOUNT_PREFIX} 0a1b2c3d copy", "Acme")
        with mock.patch.object(fx, "soql", return_value=rows) as soql:
            self.assertEqual([r["Name"] for r in fx.fixture_accounts("conn", " AND CreatedById = '005U'")],
                             [f"{fx.ACCOUNT_PREFIX} 0a1b2c3d"])
        query = soql.call_args.args[1]
        self.assertIn(f"Name LIKE '{fx.ACCOUNT_PREFIX} %' AND CreatedById = '005U' ORDER BY CreatedDate", query)

    def test_creator_of_reads_the_account_creator(self):
        with mock.patch.object(fx, "soql", return_value=[{"Id": "001ACC", "CreatedById": "005U"}]):
            self.assertEqual(fx.creator_of("conn", "001ACC"), "005U")
        with mock.patch.object(fx, "soql", return_value=[]), self.assertRaises(fx.FixtureError):
            fx.creator_of("conn", "001ACC")


class SeedTests(unittest.TestCase):
    @contextlib.contextmanager
    def seeding(self, created, live=(), update=None, leftovers=()):
        """A sandbox where Salesforce creates the `created` ids in turn, reads `live` contracts
        back, and holds the `leftovers` fixture accounts. Yields the create mock."""
        ids = iter(created)
        with sandbox(), mock.patch.object(fx, "connection_id", return_value="conn"), \
                mock.patch.object(fx, "fixture_accounts", return_value=list(leftovers)), \
                mock.patch.object(fx, "creator_of", return_value="005U"), \
                mock.patch.object(fx, "create", side_effect=lambda *a, **k: next(ids)) as create, \
                mock.patch.object(fx, "update", side_effect=update), \
                mock.patch.object(fx, "soql", return_value=list(live)), \
                contextlib.redirect_stdout(io.StringIO()):
            yield create

    def test_seed_records_every_contract_with_its_live_end_date_and_its_creator(self):
        live = [{"Id": f"800C{i}", "ContractNumber": f"0000010{i}", "EndDate": "2026-10-13", "Status": "Activated"}
                for i in range(1, 5)]
        with self.seeding(["001ACC", "800C1", "800C2", "800C3", "800C4"], live):
            fx.seed(TODAY)
            state = fx.load_state()
        self.assertEqual((state["account_id"], state["created_by"]), ("001ACC", "005U"))
        self.assertEqual([c["days"] for c in state["contracts"]], [*fx.INSIDE_DAYS, *fx.OUTSIDE_DAYS])
        self.assertTrue(all(c["end_date"] and c["number"] for c in state["contracts"]))

    def test_a_contract_the_org_will_not_activate_stops_the_seed_as_infrastructure(self):
        with self.seeding(["001ACC", "800C1"], update=fx.FixtureError("INSUFFICIENT_ACCESS")), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(fx.main(["seed"]), fx.INFRA_EXIT)
            state = fx.load_state()
        self.assertIn("was not activated", err.getvalue())
        self.assertEqual(state["account_id"], "001ACC")

    def test_a_contract_that_reads_back_as_draft_stops_the_seed_as_infrastructure(self):
        live = [{"Id": f"800C{i}", "ContractNumber": f"0000010{i}", "EndDate": "2026-10-13",
                 "Status": "Draft" if i == 2 else "Activated"} for i in range(1, 5)]
        with self.seeding(["001ACC", "800C1", "800C2", "800C3", "800C4"], live), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(fx.main(["seed"]), fx.INFRA_EXIT)
        self.assertIn(f"+{fx.INSIDE_DAYS[1]}d (Draft)", err.getvalue())

    def test_too_many_leftover_fixture_accounts_stop_the_seed_before_it_creates_anything(self):
        leftovers = accounts(*[f"{fx.ACCOUNT_PREFIX} {i:08x}" for i in range(fx.MAX_LEFTOVERS + 1)])
        with self.seeding(["001ACC"], leftovers=leftovers) as create, \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(fx.main(["seed"]), fx.INFRA_EXIT)
            self.assertFalse(fx.STATE_FILE.exists())
        create.assert_not_called()
        self.assertIn(f"{fx.MAX_LEFTOVERS + 1} fixture accounts are already in the org", err.getvalue())


class CleanupTests(unittest.TestCase):
    def clean(self, state, stale=(), removed=None):
        """(exit code, stderr, removed accounts, sweep SOQL or None) of cleanup with `state` in
        STATE_FILE (none when None), `stale` the leftover fixture accounts."""
        removed = [] if removed is None else removed
        sweeps = []

        def remove_account(conn, account_id):
            removed.append((conn, account_id))
            return []

        def fixture_accounts(conn, where=""):
            sweeps.append(where)
            return list(stale)

        with sandbox(), mock.patch.object(fx, "connection_id", side_effect=AssertionError("no listing")), \
                mock.patch.object(fx, "remove_account", side_effect=remove_account), \
                mock.patch.object(fx, "fixture_accounts", side_effect=fixture_accounts), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            if state is not None:
                fx.save_state(state)
            code = fx.cleanup()
        return code, err.getvalue(), removed, sweeps[0] if sweeps else None

    def test_without_a_seed_nothing_is_deleted(self):
        code, err, removed, sweep = self.clean(None)
        self.assertEqual((code, removed, sweep), (0, [], None))
        self.assertIn("seeded nothing", err)

    def test_deletes_this_run_then_sweeps_a_few_stale_accounts_of_the_same_user_through_the_seed_connection(self):
        stale = accounts(*[f"{fx.ACCOUNT_PREFIX} {i:08x}" for i in range(fx.SWEEP_LIMIT + 3)])
        code, _, removed, sweep = self.clean({"connection_id": "seeded", "account_id": "001ACC", "created_by": "005U"},
                                             stale)
        self.assertEqual(code, 0)
        self.assertEqual(removed, [("seeded", "001ACC")] + [("seeded", row["Id"]) for row in stale[:fx.SWEEP_LIMIT]])
        self.assertEqual(sweep, f" AND CreatedById = '005U' AND CreatedDate < LAST_N_DAYS:{fx.STALE_DAYS}")

    def test_without_the_creator_only_this_run_is_deleted(self):
        _, _, removed, sweep = self.clean({"connection_id": "seeded", "account_id": "001ACC"},
                                          accounts(f"{fx.ACCOUNT_PREFIX} 0a1b2c3d"))
        self.assertEqual((removed, sweep), ([("seeded", "001ACC")], None))

    def test_cleanup_never_fails_the_task(self):
        code, err, removed, _ = self.clean({"account_id": "001ACC"})
        self.assertEqual((code, removed), (0, []))
        self.assertIn("cleanup skipped", err)

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
