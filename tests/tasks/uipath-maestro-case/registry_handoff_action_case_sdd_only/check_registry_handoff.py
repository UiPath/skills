import json
import re
from pathlib import Path


ACTION_RESOURCE = "PortableReviewActionProbeQ91"
CASE_RESOURCE = "PortableChildCaseProbeQ91"
RESOLVED_ACTION = "purchaseorderapp-1782974854"
RESOLVED_DISPLAY_NAME = "Resolved App Review"
DISPLAY_NAMES = (RESOLVED_DISPLAY_NAME, "Review Request", "Launch Follow-up")
STAGE = "Review and Follow-up"
STALE_QUERIES = ("SimpleApprovalApp", "LegacyReviewApp", "LegacyFollowUpCase")
REQUIRED_KEYS = {
    "stage",
    "task",
    "taskType",
    "cacheFile",
    "searchQuery",
    "matches",
    "selected",
    "rationale",
}

EXPECTED = {
    ACTION_RESOURCE: {
        "task": "Review Request",
        "task_type": "action",
        "cache_file": "action-apps-index.json",
        "name_field": "deploymentTitle",
        "id_field": "id",
        "resolved": False,
    },
    CASE_RESOURCE: {
        "task": "Launch Follow-up",
        "task_type": "case-management",
        "cache_file": "caseManagement-index.json",
        "name_field": "name",
        "id_field": "entityKey",
        "resolved": False,
    },
    RESOLVED_ACTION: {
        "task": RESOLVED_DISPLAY_NAME,
        "task_type": "action",
        "cache_file": "action-apps-index.json",
        "name_field": "deploymentTitle",
        "id_field": "id",
        "resolved": True,
    },
}


registry_path = Path("tasks/registry-resolved.json")
tasks_path = Path("tasks/tasks.md")

entries = json.loads(registry_path.read_text(encoding="utf-8"))
assert isinstance(entries, list), "registry-resolved.json must be a list"
assert len(entries) == len(EXPECTED), (
    f"expected one corrected audit entry per SDD task, got {len(entries)}"
)

cache_root = Path.home() / ".uip" / "case-resources"
resolved_entry = None

for resource_name, expected in EXPECTED.items():
    matching_entries = [
        entry for entry in entries if str(entry.get("searchQuery", "")).strip() == resource_name
    ]
    assert len(matching_entries) == 1, (
        f"expected one registry audit entry for {resource_name}, got {len(matching_entries)}"
    )
    entry = matching_entries[0]
    assert REQUIRED_KEYS <= entry.keys(), (
        f"{resource_name} audit entry is missing {sorted(REQUIRED_KEYS - entry.keys())}"
    )
    assert str(entry.get("rationale", "")).strip(), (
        f"{resource_name} audit entry has no selection rationale"
    )
    assert entry.get("stage") == STAGE, (
        f"{resource_name} audit entry is associated with stage {entry.get('stage')!r}"
    )
    assert entry.get("task") == expected["task"], (
        f"{resource_name} audit entry is associated with task {entry.get('task')!r}"
    )
    assert entry.get("taskType") == expected["task_type"], (
        f"{resource_name} used taskType {entry.get('taskType')!r}"
    )
    assert entry.get("cacheFile") == expected["cache_file"], (
        f"{resource_name} did not record cacheFile {expected['cache_file']}"
    )

    cache = json.loads((cache_root / expected["cache_file"]).read_text(encoding="utf-8"))
    name_field = expected["name_field"]
    id_field = expected["id_field"]
    exact_matches = [
        item
        for item in cache
        if str(item.get(name_field, "")).strip().casefold() == resource_name.casefold()
    ]
    recorded = entry.get("matches") or []
    selected = entry.get("selected")

    if expected["resolved"]:
        assert exact_matches, f"test precondition failed: no live {resource_name} Action App"
        cache_ids = {str(m.get(id_field)) for m in exact_matches}
        # registry-resolved.json records a normalized/trimmed audit shape, not the raw cache
        # object — compare on stable identity (name + id), never deep-equality.
        assert recorded, f"{resource_name} audit recorded no matches"
        assert all(
            str(m.get(name_field, "")).strip().casefold() == resource_name.casefold()
            for m in recorded
        ), f"{resource_name} audit recorded a non-exact-name match"
        assert (
            isinstance(selected, dict)
            and str(selected.get(name_field, "")).strip().casefold() == resource_name.casefold()
            and str(selected.get(id_field)) in cache_ids
        ), f"{resource_name} selected is not a live exact-name cache entry"
        resolved_entry = selected
    else:
        assert exact_matches == [], (
            f"test precondition failed: probe resource {resource_name} unexpectedly exists"
        )
        assert recorded == [], (
            f"missing resource {resource_name} must record no matches"
        )
        assert selected in (None, {}), (
            f"missing resource {resource_name} must not have a selected result"
        )

for stale_query in STALE_QUERIES:
    assert not any(
        str(entry.get("searchQuery", "")).strip() == stale_query for entry in entries
    ), f"stale registry selection {stale_query} was not replaced from the current SDD"

for display_name in DISPLAY_NAMES:
    assert not any(str(entry.get("searchQuery", "")).strip() == display_name for entry in entries), (
        f"registry lookup incorrectly substituted task display name {display_name}"
    )

tasks_text = tasks_path.read_text(encoding="utf-8")
assert ACTION_RESOURCE in tasks_text, "action placeholder lost its Action App title"
assert CASE_RESOURCE in tasks_text, "case placeholder lost its Child Case name"
assert "action-app" in tasks_text.lower(), "action unresolved marker is missing"
assert "case-management" in tasks_text.lower(), "case-management task is missing"

assert resolved_entry is not None
resolved_folder = resolved_entry.get("deploymentFolder", {}).get("fullyQualifiedName", "")
resolved_id = resolved_entry.get("id")
assert resolved_folder, "resolved Action App cache entry has no deployment folder"
assert resolved_id, "resolved Action App cache entry has no id"

heading = re.search(
    rf'(?ms)^## T\d+: Add action task "{re.escape(RESOLVED_DISPLAY_NAME)}".*?(?=^## T\d+:|\Z)',
    tasks_text,
)
assert heading, f"tasks.md omitted resolved action task {RESOLVED_DISPLAY_NAME}"
resolved_body = heading.group(0)
assert re.search(rf'(?m)^- name:\s*["\']?{re.escape(RESOLVED_ACTION)}["\']?\s*$', resolved_body), (
    "resolved Action task omitted its selected name binding"
)
assert re.search(rf'(?m)^- folder-path:\s*["\']?{re.escape(resolved_folder)}["\']?\s*$', resolved_body), (
    "resolved Action task omitted its selected folder-path binding"
)
assert re.search(rf'(?m)^- taskTypeId:\s*["\']?{re.escape(resolved_id)}["\']?\s*$', resolved_body), (
    "resolved Action task did not retain the selected Action App id"
)

assert not Path(ACTION_RESOURCE).exists(), "an Action App sibling directory was created"
assert not Path(CASE_RESOURCE).exists(), "a child-case sibling directory was created"
