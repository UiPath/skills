"""Unit tests for skills/uipath-activity-migrator/scripts/summarize-sarif.mjs.

Placement note. This file first lived at tests/scripts/summarize-sarif.test.mjs, written for
Node's test runner and registered in `npm run skills:test`, where CI runs it on every pull
request. It was moved here on 2026-10-02 so that it stays under the skill's own CODEOWNERS
instead of the repository root's. Nothing in CI runs it from here yet: to enforce it again,
add a job to .github/workflows/test-helpers.yml that runs
`pytest tests/tasks/uipath-activity-migrator/_shared/ -v`, or move it back to tests/scripts.

Run locally from the repository root (needs pytest and node):
    python -m pytest tests/tasks/uipath-activity-migrator/_shared -q

Each test writes a minimal SARIF 2.1.0 log to a temp folder and runs the summarizer on it.
The cases come from real migrator logs: the tool's SARIF library omits `level` when it equals
the default, so every warning arrives with no level; the --ignore-missing-dependencies path
reports the restore rule at warning level; a requested UIAutomation version below the tool's
minimum is raised to it; a project already on the target reports "Using existing project
version".
"""

import json
import re
import subprocess

from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[4] / "skills" / "uipath-activity-migrator" / "scripts" / "summarize-sarif.mjs"


def sarif(tmp_path, results, rules=None):
    """Write a minimal SARIF 2.1.0 log holding `results`; return its path."""
    file = tmp_path / "analyze-latest.sarif"
    log = {"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "UiPath.Upgrade", "rules": rules or []}}, "results": results}]}
    file.write_text(json.dumps(log), encoding="utf-8")
    return file


def at(uri):
    return {"locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}}}]}


def result(rule_id, text, **extra):
    return {"ruleId": rule_id, "message": {"text": text}, **extra}


# A completed run always carries a validation result; without one the status is `unknown`.
VALIDATED = result("WORKFLOW-VALIDATION-SUCCESS", "Workflow validation passed with no errors.", level="note", **at("Main.xaml"))


def summarize(file, *flags):
    run = subprocess.run(["node", str(SCRIPT), str(file), *flags], capture_output=True, text=True, encoding="utf-8")
    assert run.returncode == 0, run.stderr
    return run.stdout


def summary(file):
    return json.loads(summarize(file, "--json"))


def test_result_without_level_is_a_warning_and_a_validation_issue_lands_in_needs_attention(tmp_path):
    j = summary(sarif(tmp_path, [VALIDATED, result("WORKFLOW-VALIDATION-ISSUE", "Validation error: You must provide a value for Connection", **at("Main.xaml"))]))
    assert j["totals"]["warning"] == 1
    assert j["status"] == "partial"
    assert j["attention"]["total"] == 1
    assert "WORKFLOW-VALIDATION-ISSUE" in ";".join(j["attention"]["items"][0]["reasons"])


def test_restore_error_with_no_file_is_a_blocker_and_fails_the_run(tmp_path):
    j = summary(sarif(tmp_path, [result("RESTORE-MISSING-PACKAGE", "Package 'Acme.Internal.Helpers' version '1.0.0' not found in any source.", level="error")]))
    assert j["status"] == "failed"
    assert len(j["blockers"]) == 1
    assert j["attention"]["total"] == 0


def test_restore_rule_without_level_is_a_needs_attention_item_not_a_blocker(tmp_path):
    j = summary(sarif(tmp_path, [VALIDATED, result("RESTORE-MISSING-PACKAGE", "Package 'Acme.Internal.Helpers' version '1.0.0' not found in any source.")]))
    assert j["status"] == "partial"
    assert j["blockers"] == []
    assert j["attention"]["total"] == 1
    assert j["attention"]["items"][0]["reasons"][0] == "RESTORE-MISSING-PACKAGE"


def test_version_raised_to_the_tool_minimum_is_on_the_packages_line_and_does_not_make_the_run_partial(tmp_path):
    file = sarif(tmp_path, [
        VALIDATED,
        result("UIAUTOMATION-PACKAGE-UPGRADE", "Cannot use version '25.10.5' for 'UiPath.UIAutomation.Activities'. Minimum required version is '25.10.21'. Using minimum version."),
        result("UIAUTOMATION-PACKAGE-UPGRADE", "Updated package 'UiPath.UIAutomation.Activities' from '24.10.19' to '25.10.21'.", level="note"),
    ])
    j = summary(file)
    assert j["status"] == "success"
    assert j["totals"]["warning"] == 1
    assert j["effectiveVersions"]["UiPath.UIAutomation.Activities"] == {"requested": "25.10.5", "minimum": "25.10.21", "from": "24.10.19", "to": "25.10.21"}
    assert re.search(r"Packages: UiPath\.UIAutomation\.Activities 24\.10\.19 → 25\.10\.21 \(requested 25\.10\.5, raised to the tool minimum 25\.10\.21\)", summarize(file))


def test_project_already_on_the_target_version_is_reported_as_unchanged(tmp_path):
    file = sarif(tmp_path, [VALIDATED, result("UIAUTOMATION-PACKAGE-UPGRADE", "Using existing project version '25.10.22' for 'UiPath.UIAutomation.Activities'.Update is not needed.", level="note")])
    assert summary(file)["effectiveVersions"]["UiPath.UIAutomation.Activities"] == {"from": "25.10.22", "to": "25.10.22", "unchanged": True}
    assert re.search(r"Packages: UiPath\.UIAutomation\.Activities 25\.10\.22 \(unchanged\)", summarize(file))


def test_whole_step_failure_at_warning_level_is_a_needs_attention_item(tmp_path):
    # Rule WARNING with no file: the step threw as a whole and the run went on without it. Without an attention item
    # a report would promote the run to success on an empty list and hide the skipped step.
    j = summary(sarif(tmp_path, [VALIDATED, result("WARNING", "Step failed: UiAutomationActivitiesStep - Object reference not set to an instance of an object.")]))
    assert j["status"] == "partial"
    assert len(j["stepFailures"]) == 1
    assert j["attention"]["total"] == 1
    assert j["attention"]["items"][0]["reasons"] == ["step failed"]


def test_workflow_scoped_uia_result_above_note_level_is_a_needs_attention_item(tmp_path):
    j = summary(sarif(tmp_path, [VALIDATED, result("UIAUTOMATION-WORKFLOW-MIGRATION-WARNING-UnsupportedShape", "Main.xaml - the workflow uses a construct the migrator does not handle.", **at("Main.xaml"))]))
    assert j["status"] == "partial"
    assert j["attention"]["total"] == 1
    assert j["attention"]["items"][0]["reasons"] == ["UnsupportedShape"]


def test_raise_warning_without_the_updated_note_prints_requested_once(tmp_path):
    file = sarif(tmp_path, [VALIDATED, result("UIAUTOMATION-PACKAGE-UPGRADE", "Cannot use version '25.10.5' for 'UiPath.UIAutomation.Activities'. Minimum required version is '25.10.21'. Using minimum version.")])
    line = next(l for l in summarize(file).splitlines() if l.startswith("Packages:"))
    assert line == "Packages: UiPath.UIAutomation.Activities requested 25.10.5, raised to the tool minimum 25.10.21"
    assert line.count("requested") == 1


def test_package_message_no_shape_parses_stays_on_the_packages_line_verbatim(tmp_path):
    file = sarif(tmp_path, [
        VALIDATED,
        result("UIAUTOMATION-PACKAGE-UPGRADE", "Updated package 'UiPath.UIAutomation.Activities' from '24.10.19' to '26.10.4'.", level="note"),
        result("OFFICE365-PACKAGE-MIGRATION", "Added UiPath.MicrosoftOffice365.Activities package dependency to the project.", level="note"),
    ])
    assert re.search(r"Packages: UiPath\.UIAutomation\.Activities 24\.10\.19 → 26\.10\.4; Added UiPath\.MicrosoftOffice365\.Activities package dependency to the project\.", summarize(file))

# The Microsoft.Activities.Extensions extension reports one …-SUCCESS per rewritten activity, one UNSUPPORTED-… error per
# unsupported activity type (the activity is named only in the message; the workflow is then copied unchanged), one
# namespace note per file and two package notes without a file. Shapes from a 25.10.1 run on Studio's test project.
def test_microsoft_activities_results_count_as_migrated_and_unsupported_types_need_attention(tmp_path):
    j = summary(sarif(tmp_path, [
        VALIDATED,
        result("MICROSOFT-ACTIVITY-MIGRATION-SUCCESS", "Replaced Microsoft Activity 'AddToDictionary`2' with InvokeCode in workflow: DictAct.xaml", level="note", **at("DictAct.xaml")),
        result("MICROSOFT-ACTIVITY-MIGRATION-SUCCESS", "Replaced Microsoft Activity 'ClearDictionary`2' with InvokeCode in workflow: DictAct.xaml", level="note", **at("DictAct.xaml")),
        result("MICROSOFT-ACTIVITY-MIGRATION-SUCCESS", "Replaced Microsoft Activity 'RemoveFromDictionary`2' with InvokeCode in workflow: DictActInt.xaml", level="note", **at("DictActInt.xaml")),
        result("MICROSOFT-NAMESPACE-UPDATE", "Updated namespace from 'clr-namespace:Microsoft.Activities.Extensions.Statements;assembly=Microsoft.Activities.Extensions' to 'clr-namespace:Microsoft.Activities.Extensions.Statements;assembly=UiPath.Upgrade.MicrosoftActivitiesExtensions'", level="note", **at("DictAct.xaml")),
        result("UNSUPPORTED-MICROSOFT-ACTIVITY", "Found 1 instance(s) of unsupported activity GetInstanceId", level="error", **at("Main.xaml")),
        result("UNSUPPORTED-MICROSOFT-ACTIVITY", "Found 1 instance(s) of unsupported activity LoadAssembly", level="error", **at("Main.xaml")),
        result("MICROSOFT-ACTIVITIES-EXTENSIONS-PACKAGE-REMOVAL", "Removed Microsoft.Activities.Extensions package from project dependencies", level="note"),
        result("ADD-OR-UPDATE-UIPATH-SYSTEM", "Updated UiPath.System.Activities package version from [24.10.7] to 25.10.3", level="note"),
    ]))
    assert j["totals"]["migrated"] == 3
    assert j["status"] == "partial"
    assert j["totals"]["leftClassic"] == 0
    assert j["attention"]["total"] == 2
    assert {a["activity"] for a in j["attention"]["items"]} == {"GetInstanceId", "LoadAssembly"}
    assert any("Removed Microsoft.Activities.Extensions" in p for p in j["packages"])
    assert any("UiPath.System.Activities" in p for p in j["packages"])
    assert "outside the known families" not in summarize(sarif(tmp_path, [VALIDATED, result("MICROSOFT-ACTIVITY-MIGRATION-SUCCESS", "Replaced Microsoft Activity 'GetFromDictionary`2' with InvokeCode in workflow: DictAct.xaml", level="note", **at("DictAct.xaml"))]))


def test_microsoft_activities_run_with_only_rewrites_is_a_success(tmp_path):
    j = summary(sarif(tmp_path, [
        VALIDATED,
        result("MICROSOFT-ACTIVITY-MIGRATION-SUCCESS", "Replaced Microsoft Activity 'AddToDictionary`2' with InvokeCode in workflow: DictAct.xaml", level="note", **at("DictAct.xaml")),
        result("MICROSOFT-ACTIVITIES-EXTENSIONS-PACKAGE-REMOVAL", "Removed Microsoft.Activities.Extensions package from project dependencies", level="note"),
    ]))
    assert j["status"] == "success"
    assert j["totals"]["migrated"] == 1
    assert j["attention"]["total"] == 0

# Mail and GSuite runs carry a config-load note and an extension summary line without a level or a file. Both are
# project-level information: known rules, no finding, no effect on the status.
def test_mail_config_load_and_general_reporting_are_known_rules_and_do_not_affect_the_status(tmp_path):
    file = sarif(tmp_path, [
        VALIDATED,
        result("LOAD-USER-CONFIGURATION", "Successfully loaded user configuration.", level="note"),
        result("GENERAL-REPORTING", "Migration completed: 12 successful, 2 partially successful, 0 failed."),
    ])
    assert "outside the known families" not in summarize(file)
    assert summary(file)["status"] == "success"

# Mail/GSuite outcome levels as measured on 25.10.1: a rewritten activity with a caveat arrives at note level with the
# [PostMigration Action Required] prefix and counts as migrated AND as needing attention; an unsupported activity type
# arrives at error level, is not migrated, and lands under needs attention (left classic is a UIA-only count).
def test_productivity_action_required_note_counts_as_migrated_and_attention_and_error_as_not_migrated(tmp_path):
    j = summary(sarif(tmp_path, [
        VALIDATED,
        result("SEND-OUTLOOK-MAIL-ACTIVITY-MIGRATION", "Successfully migrated activity `Send` to `Migrated Send`.", level="note", **at("Send.xaml")),
        result("GET-OUTLOOK-MAIL-MESSAGES-ACTIVITY-MIGRATION", "[PostMigration Action Required]: Filter migration is not currently supported and should be manually migrated.", level="note", **at("Get.xaml")),
        result("OUTLOOK-MAIL-MESSAGES-TRIGGER-ACTIVITY-MIGRATION", "[PostMigration Action Required]: Migration of 'OutlookMailMessagesTrigger' is currently not supported.", level="error", **at("Trigger.xaml")),
    ]))
    assert j["totals"]["migrated"] == 2
    assert j["totals"]["leftClassic"] == 0
    assert j["attention"]["total"] == 2
    assert j["status"] == "partial"

