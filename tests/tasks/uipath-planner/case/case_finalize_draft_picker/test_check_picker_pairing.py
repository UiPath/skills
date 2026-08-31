#!/usr/bin/env python3
"""Behavioral tests for the manual stage-picker pairing grader."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CHECKER = Path(__file__).parent / "check_picker_pairing.py"
PRIMARY_STAGES = ("Document Collection", "Vendor Approval")


def run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class PickerPairingCheckerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_sdd(
        self,
        exposed_by: tuple[str, ...],
        *,
        noncompleting: tuple[str, ...] = (),
        duplicate_completion: tuple[str, ...] = (),
    ) -> None:
        primary_blocks = []
        for index, stage_name in enumerate(PRIMARY_STAGES, 1):
            exit_type = "wait-for-user" if stage_name in exposed_by else "exit-only"
            marks_complete = "No" if stage_name in noncompleting else "Yes"
            duplicate_row = (
                "\n| required-tasks-completed | — | exit-only | Yes |"
                if stage_name in duplicate_completion
                else ""
            )
            primary_blocks.append(
                f"""### Stage {index}: {stage_name}

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|---|---|---|---|
| required-tasks-completed | — | {exit_type} | {marks_complete} |{duplicate_row}
"""
            )
        text = "# SDD — VendorOnboarding\n\n" + "\n".join(primary_blocks) + """
### Secondary Stage: Compliance Hold

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|---|---|---|
| user-selected-stage | — | Yes |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|---|---|---|---|
| required-tasks-completed | — | return-to-origin | Yes |
"""
        (self.workdir / "sdd.md").write_text(text, encoding="utf-8")

    def test_accepts_picker_exposure_from_every_primary_stage(self) -> None:
        self.write_sdd(PRIMARY_STAGES)
        result = run(self.workdir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_picker_exposure_from_only_one_primary_stage(self) -> None:
        self.write_sdd(("Document Collection",))
        result = run(self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Vendor Approval", result.stdout + result.stderr)

    def test_rejects_noncompleting_wait_for_user_exit(self) -> None:
        self.write_sdd(PRIMARY_STAGES, noncompleting=("Vendor Approval",))
        result = run(self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Vendor Approval", result.stdout + result.stderr)

    def test_rejects_duplicate_completion_exit_instead_of_replacement(self) -> None:
        self.write_sdd(PRIMARY_STAGES, duplicate_completion=("Document Collection",))
        result = run(self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Document Collection", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
