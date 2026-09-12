#!/usr/bin/env python3
"""Offline tests for the child-case cleanup.

The rule this file exists to keep: the cleanup must never cancel an instance of the package
this run itself drove. It once did. An instance record names no solution — `ReleaseName` is
absent and `PackageId` is a bare GUID — so a filter written against a name matched nothing,
treated every instance as a foreign child case, and cancelled the run's own case mid-flight.
Worse, it runs in post_run, after grading, so the damage read as the case having faulted.

Run: python3 -m unittest test_cleanup_child_cases
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import cleanup_child_cases as C  # noqa: E402

OURS = "a62ac5bd-803f-407f-a82b-6b0e014304d7"
CHILD = "f1f1f1f1-0000-0000-0000-000000000000"
MINE = "4bb5ef74-e1a3-4133-ae05-f310f4c30bf7"
THEIRS = "9999aaaa-0000-0000-0000-000000000000"


def instance(instance_id: str, package: str, status: str = "Running",
             created: str = "2026-08-31T01:02:23Z") -> dict:
    # Shaped like a real `instance list` row: no ReleaseName, PackageId a bare GUID.
    return {"InstanceId": instance_id, "PackageId": package, "LatestRunStatus": status,
            "CreatedTimeUtc": created, "FolderKey": "30b98ad6-522a-4630-85d5-5eb625387f2b"}


class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.addCleanup(os.chdir, self.cwd)
        Path("build.uipx").write_text("", encoding="utf-8")
        os.utime("build.uipx", (0, 0))          # epoch, so every instance is newer
        Path(f".{C.RUN_STATE}").write_text(json.dumps({"instance_id": MINE}), encoding="utf-8")
        self.cancelled: list[str] = []

    def fake_uip(self, rows):
        def _uip(args, timeout=120):
            if args[:4] == ["maestro", "case", "instance", "list"]:
                return {"Data": rows}
            if args[:4] == ["maestro", "case", "instance", "cancel"]:
                self.cancelled.append(args[4])
                return {"Result": "Success"}
            return {}
        return _uip

    def test_spares_an_instance_of_this_runs_own_package(self):
        rows = [instance(MINE, OURS), instance(THEIRS, OURS)]
        with mock.patch.object(C, "uip", self.fake_uip(rows)):
            C.main()
        self.assertEqual(self.cancelled, [], "cancelled an instance of the run's own package")

    def test_cancels_a_live_child_case(self):
        rows = [instance(MINE, OURS), instance("child-1", CHILD)]
        with mock.patch.object(C, "uip", self.fake_uip(rows)):
            C.main()
        self.assertEqual(self.cancelled, ["child-1"])

    def test_leaves_a_finished_child_case_alone(self):
        rows = [instance(MINE, OURS), instance("child-1", CHILD, status="Completed")]
        with mock.patch.object(C, "uip", self.fake_uip(rows)):
            C.main()
        self.assertEqual(self.cancelled, [])

    def test_does_nothing_when_this_runs_package_is_unknown(self):
        # No handover file: the run's own package cannot be identified, so nothing is eligible.
        # Guessing here is what cancelled a live case.
        Path(f".{C.RUN_STATE}").unlink()
        rows = [instance("child-1", CHILD)]
        with mock.patch.object(C, "uip", self.fake_uip(rows)):
            C.main()
        self.assertEqual(self.cancelled, [])

    def test_leaves_instances_older_than_this_run_alone(self):
        os.utime("build.uipx", (1_800_000_000, 1_800_000_000))   # 2027, after every row
        rows = [instance(MINE, OURS), instance("child-1", CHILD)]
        with mock.patch.object(C, "uip", self.fake_uip(rows)):
            C.main()
        self.assertEqual(self.cancelled, [])


if __name__ == "__main__":
    unittest.main()
