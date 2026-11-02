#!/usr/bin/env python3
"""Enforce the EVFX- fixture contract (tests/tasks/uipath-test/fixtures/README.md).

Two invariants, both of which the 2026-08-05 nightly violated:

1. **Sole ownership** — an EVFX- fixture name may be referenced by exactly one
   task file. Two tasks touching one mutable fixture is how execution_rerun
   destroyed the history flaky_tests_analysis reads.
2. **Namespace discipline** — a task may only reference EVFX- names whose
   namespace segment matches its own, so a task cannot quietly reach into a
   sibling's fixtures.

Exit 1 on violation. Runs from any directory:

    python3 tests/tasks/uipath-test/fixtures/check-collisions.py
"""
import re
import sys
from pathlib import Path

# The task directory is this script's parent — resolved from __file__ so the
# check runs from any working directory, not just the repo root.
TASK_DIR = Path(__file__).resolve().parent.parent
EVFX = re.compile(r"EVFX-[A-Z]+(?:-[A-Za-z0-9]+)*")

# Namespace segment -> the single task file allowed to own it.
OWNERS = {
    "SCHEDSMOKE": "schedule_list_smoke.yaml",
    "SCHEDLC": "schedule_lifecycle_e2e.yaml",
    "RERUN": "execution_rerun_failed_integration.yaml",
    "FLAKY": "flaky_tests_analysis.yaml",
    "SIGNOFF": "release_signoff_wait_report_e2e.yaml",
    "ORG": "organize_testcases_into_testsets.yaml",
    "READY": "integration_release_readiness_qa_lead.yaml",
    "JUNIT": "test_report_junit_export.yaml",
    "SCAFFOLD": "project_scaffold_build.yaml",
    "CURATE": "testset_curation_by_label_build.yaml",
    "SCHEMA": "customfield_schema_multiscope_build.yaml",
    "CFIELD": "customfield_definition_crud_smoke.yaml",
    "TRIAGE": "failed_run_triage_diagnose.yaml",
    "TCLOG": "testcaselog_override_integration.yaml",
    "TCLOGRD": "testcaselog_read_smoke.yaml",
    "TCLOGMR": "testcaselog_manual_record_e2e.yaml",
    "PERMPRE": "project_permissions_preflight_smoke.yaml",
    "PERMAT": "project_permissions_access_integration.yaml",
    "DEFECT": "defect_lifecycle_smoke.yaml",
    "DEFTRACE": "defect_traceability_integration.yaml",
    "DEFFLOW": "defect_full_lifecycle_e2e.yaml",
    "MANUAL": "manual_execution_record_integration.yaml",
    "REPORT": "reporting_date_backdate_integration.yaml",
    "EXLIST": "executions_list_smoke.yaml",
    "PSET": "project_settings_smoke.yaml",
    "RUNPKG": "run_package_ci_smoke.yaml",
    "RUNPKGFAIL": "run_package_failing_smoke.yaml",
    "DPTC": "project_default_testcases_smoke.yaml",
    "PARAM": "testcase_parameters_bulk_add_smoke.yaml",
    "PARAMEDIT": "testcase_parameters_edit_integration.yaml",
    "PARAMLIFE": "testcase_parameters_lifecycle_e2e.yaml",
    "PARAMASK": "testcase_parameters_ask_first_integration.yaml",
    "AIGEN": "requirement_ai_generate_smoke.yaml",
    "AIEVAL": "requirement_ai_evaluate_smoke.yaml",
    "AIDEL": "requirement_ai_obsolete_smoke.yaml",
    "AIBLOCK": "requirement_ai_blocked_inputs_smoke.yaml",
    "ATTUP": "attachment_upload_smoke.yaml",
    "ATTDL": "attachment_download_integration.yaml",
    "ATTASK": "attachment_overwrite_ask_integration.yaml",
    "ATTLIFE": "attachment_lifecycle_e2e.yaml",
    "TSCLONE": "testset_clone_smoke.yaml",
    "TSORDER": "testset_order_integration.yaml",
    "TSASK": "testset_settings_ask_integration.yaml",
    "TSLIFE": "testset_lifecycle_e2e.yaml",
    "TCCLONE": "testcase_clone_smoke.yaml",
    "TCBULK": "testcase_bulk_create_integration.yaml",
    "TCLOOK": "testcase_lookup_integration.yaml",
    "TCINV": "testcase_inventory_lookup_smoke.yaml",
    "TCLIFE": "testcase_lifecycle_e2e.yaml",
    "FXEXP": "testcases_export_smoke.yaml",
    "FXJOB": "export_job_download_integration.yaml",
    "FXASK": "export_overwrite_ask_integration.yaml",
    "FXLAB": "testcases_export_by_label_e2e.yaml",
    "FXRPT": "report_export_integration.yaml",
    "MXEXP": "project_export_smoke.yaml",
    "MXASK": "project_import_ask_integration.yaml",
    "MXLIFE": "project_migration_e2e.yaml",
    "PERF": "perf_scenario_cleanup_smoke.yaml",
    "PERFSET": "perf_scenario_setup_integration.yaml",
    "PERFDRY": "perf_scenario_dryrun_e2e.yaml",
    "PROMPT": "prompts_create_smoke.yaml",
    "PROMPTSET": "prompts_library_setup_integration.yaml",
    "PERFHIST": "perf_scenario_history_integration.yaml",
}


def main() -> int:
    if not TASK_DIR.is_dir():
        print(f"error: {TASK_DIR} not found", file=sys.stderr)
        return 2

    refs: dict[str, set[str]] = {}
    errors: list[str] = []

    # rglob, not glob: tasks may sit in nested leaf directories, and a
    # non-recursive scan would report the contract as valid while silently
    # ignoring a collision introduced by a nested task.
    for path in sorted(TASK_DIR.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        for name in set(EVFX.findall(text)):
            refs.setdefault(name, set()).add(path.name)

            ns = name.split("-")[1]
            owner = OWNERS.get(ns)
            if owner is None:
                errors.append(
                    f"{path.name}: references {name}, but namespace "
                    f"EVFX-{ns}-* has no declared owner. Add it to OWNERS "
                    f"and to tests/tasks/uipath-test/fixtures/README.md."
                )
            elif owner != path.name:
                errors.append(
                    f"{path.name}: references {name}, which belongs to "
                    f"{owner}. A task may only use its own namespace."
                )

    for name, files in sorted(refs.items()):
        if len(files) > 1:
            errors.append(
                f"{name} is referenced by {len(files)} tasks "
                f"({', '.join(sorted(files))}). An EVFX- fixture must have "
                f"exactly one owner."
            )

    if errors:
        print("EVFX fixture contract violations:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nSee tests/tasks/uipath-test/fixtures/README.md for the contract.",
            file=sys.stderr,
        )
        return 1

    print(f"EVFX fixture contract OK — {len(refs)} fixture names, no collisions.")
    for name, files in sorted(refs.items()):
        print(f"  {name:24s} {next(iter(files))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
