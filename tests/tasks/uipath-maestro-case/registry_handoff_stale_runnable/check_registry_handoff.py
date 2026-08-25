import json
from pathlib import Path


# Correct resolution expected AFTER the stale cache is discarded and re-resolved from the
# current SDD's portable names.
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
# Names the STAGED stale cache used; they must NOT survive into the fresh audit or tasks.md.
STALE_QUERIES = ("LegacyPostingFunction", "PreviousEmailDrafter")
STALE_IDENTITIES = ("stale-api-0000", "stale-agent-0000")
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


entries = load_json(Path("tasks/registry-resolved.json"))
assert isinstance(entries, list), "registry-resolved.json must be a list"
assert len(entries) == len(EXPECTED), (
    f"expected one fresh audit entry per SDD task, got {len(entries)}"
)

cache_root = Path.home() / ".uip" / "case-resources"
tasks_text = Path("tasks/tasks.md").read_text(encoding="utf-8")

for name, expected in EXPECTED.items():
    matching = [e for e in entries if str(e.get("searchQuery", "")).strip() == name]
    assert len(matching) == 1, (
        f"expected one fresh audit entry for {name}, got {len(matching)} "
        "(stale entry not replaced from the current SDD?)"
    )
    entry = matching[0]
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

    cache = load_json(cache_root / expected["cache_file"])
    exact_matches = [
        r for r in cache
        if str(r.get("name", "")).strip().casefold() == name.casefold()
    ]
    assert exact_matches, f"test precondition failed: no live registry match for {name}"
    cache_keys = {str(r.get("entityKey")) for r in exact_matches}

    # registry-resolved.json records a normalized shape; compare on stable identity
    # (name + entityKey), never deep-equality against the raw cache object.
    recorded = entry.get("matches") or []
    assert recorded, f"{name} audit recorded no matches"
    # The skill's discovery search is substring-based, so `matches` may carry near-name
    # candidates (e.g. a `<name>V2` sibling) alongside the exact hit. Correctness is proven
    # by `selected` below (exact-name + live entityKey); here we only require the exact-name
    # match to be PRESENT among the recorded candidates, not that every candidate is exact.
    assert any(
        str(m.get("name", "")).strip().casefold() == name.casefold() for m in recorded
    ), f"{name} audit recorded no exact-name match"

    selected = entry.get("selected")
    assert isinstance(selected, dict), f"missing selected result for {name}"
    assert (
        str(selected.get("name", "")).strip().casefold() == name.casefold()
        and str(selected.get("entityKey")) in cache_keys
    ), f"selected result for {name} is not a live exact-name cache entry (stale entry not re-resolved?)"
    # never carry the stale cached identity forward
    assert str(selected.get("entityKey")) not in STALE_IDENTITIES, (
        f"{name} kept the STALE cached identity instead of re-resolving from the SDD"
    )
    # multi-match disambiguation: canonical resource, not an ephemeral debug-solution deploy.
    # The audit shape varies run to run — folder/type may be flat (folder/folderType) or
    # nested (folders[0].fullyQualifiedName/.type), so read from whichever is present.
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

# The stale names must be gone as *selections* — no entry may still search for or resolve
# to them. They MAY still appear in a `rationale` line explaining what was discarded (that
# is correct, informative behavior), so do NOT blanket-substring-search the audit or tasks.md.
for stale in STALE_QUERIES:
    assert not any(str(e.get("searchQuery", "")).strip() == stale for e in entries), (
        f"stale audit entry {stale} was not replaced from the current SDD"
    )
    assert not any(
        isinstance(e.get("selected"), dict)
        and str(e["selected"].get("name", "")).strip() == stale
        for e in entries
    ), f"a task still SELECTED the stale resource {stale}"

assert "Post Invoice" in tasks_text
assert "Draft Notification" in tasks_text
