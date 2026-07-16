import json
from pathlib import Path


EXPECTED = {
    "FinancialPostingFunction": {
        "task": "Post Invoice",
        "task_type": "api-workflow",
        "cache_file": "api-index.json",
    },
    "EmailDrafter": {
        "task": "Draft Notification",
        "task_type": "agent",
        "cache_file": "agent-index.json",
    },
}
STAGE = "Resolve Resources"
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


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


registry_path = Path("tasks/registry-resolved.json")
entries = load_json(registry_path)
assert isinstance(entries, list), "registry-resolved.json must be a list"
assert len(entries) == len(EXPECTED), (
    f"expected one fresh audit entry per SDD task, got {len(entries)}"
)

cache_root = Path.home() / ".uip" / "case-resources"
tasks_text = Path("tasks/tasks.md").read_text(encoding="utf-8")

for name, expected in EXPECTED.items():
    matching_entries = [
        entry
        for entry in entries
        if str(entry.get("searchQuery", "")).strip() == name
    ]
    assert len(matching_entries) == 1, (
        f"expected one registry audit entry for {name}, got {len(matching_entries)}"
    )
    entry = matching_entries[0]
    assert REQUIRED_KEYS <= entry.keys(), (
        f"{name} audit entry is missing {sorted(REQUIRED_KEYS - entry.keys())}"
    )
    assert str(entry.get("rationale", "")).strip(), (
        f"{name} audit entry has no selection rationale"
    )
    assert entry.get("stage") == STAGE, (
        f"{name} audit entry is associated with stage {entry.get('stage')!r}"
    )
    assert entry.get("task") == expected["task"], (
        f"{name} audit entry is associated with task {entry.get('task')!r}"
    )
    assert entry.get("taskType") == expected["task_type"], (
        f"{name} used taskType {entry.get('taskType')!r}"
    )
    assert entry.get("cacheFile") == expected["cache_file"], (
        f"{name} did not record cacheFile {expected['cache_file']}"
    )

    selected = entry.get("selected")
    assert isinstance(selected, dict), f"missing selected result for {name}"
    assert selected.get("name") == name, f"selected the wrong resource for {name}"

    cached_resources = load_json(cache_root / expected["cache_file"])
    exact_matches = [
        resource
        for resource in cached_resources
        if str(resource.get("name", "")).strip().casefold() == name.casefold()
    ]
    assert exact_matches, f"test precondition failed: no live registry match for {name}"
    cache_keys = {str(r.get("entityKey")) for r in exact_matches}

    # registry-resolved.json records a NORMALIZED audit shape (flat `folder`, derived
    # `entitySubType`/`folderType`), not the raw cache object (`folders[]` array + extra
    # fields) — so compare on stable identity (name + entityKey), never deep-equality.
    # Also tolerant of ephemeral debug-deploy churn: we require the SELECTED entry to be a
    # live exact-name match and every recorded candidate to be exact-name, not a byte-for-
    # byte copy of the whole cache set.
    recorded = entry.get("matches") or []
    assert recorded, f"{name} audit recorded no matches"
    assert all(
        str(m.get("name", "")).strip().casefold() == name.casefold() for m in recorded
    ), f"{name} audit recorded a non-exact-name match"
    assert isinstance(selected, dict), f"missing selected result for {name}"
    assert (
        str(selected.get("name", "")).strip().casefold() == name.casefold()
        and str(selected.get("entityKey")) in cache_keys
    ), f"selected result for {name} is not a live exact-name cache entry"

    # Multi-match disambiguation: when several exact-name copies exist (e.g. ephemeral
    # debug-solution deploys of the same resource), the resolver must select the canonical
    # resource, NOT a debug copy. The audit shape varies run to run — folder/type may be
    # flat (folder/folderType) or nested (folders[0].fullyQualifiedName/.type).
    fol = selected.get("folders") or []
    sel_folder = str(
        selected.get("folder") or (fol[0].get("fullyQualifiedName") if fol else "")
    ).casefold()
    sel_ftype = str(
        selected.get("folderType") or (fol[0].get("type") if fol else "")
    ).casefold()
    assert sel_ftype != "debugsolution" and "debug_" not in sel_folder, (
        f"{name} resolved to an ephemeral debug-solution deploy "
        f"({sel_folder!r}); expected the canonical resource"
    )

    assert name in tasks_text, f"tasks.md omitted resource name {name}"

assert "Post Invoice" in tasks_text
assert "Draft Notification" in tasks_text
