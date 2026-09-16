import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import registry_audit_entries  # noqa: E402


def g(obj, *names, default=None):
    """Case-insensitive key read.

    `selected` and `matches[]` are registry cache entries copied through by the agent,
    and `uip maestro case registry search` returns PascalCase (`Name`, `EntityKey`)
    while the skill's own examples show camelCase. SKILL.md Rule 9 pins the ledger's
    OUTER keys and says nothing about the shape inside them, so both spellings are
    legal and runs alternate: suite7 wrote `name`, suite8 wrote `Name`, and asserting
    on one spelling failed a correct resolution. Read either.
    """
    if not isinstance(obj, dict):
        return default
    lowered = {str(k).casefold(): v for k, v in obj.items()}
    for n in names:
        v = lowered.get(str(n).casefold())
        if v is not None:
            return v
    return default


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


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


registry_path = Path("tasks/registry-resolved.json")
entries = load_json(registry_path)
entries = registry_audit_entries(entries)
assert len(entries) == len(EXPECTED), (
    f"expected one fresh audit entry per SDD task, got {len(entries)}"
)

cache_root = Path.home() / ".uip" / "case-resources"

for name, expected in EXPECTED.items():
    matching_entries = [
        entry
        for entry in entries
        if str(entry.get("searchQuery") or entry.get("resolvedResource") or "").strip()
        == name
    ]
    assert len(matching_entries) == 1, (
        f"expected one registry audit entry for {name}, got {len(matching_entries)}"
    )
    entry = matching_entries[0]
    if "stage" in entry:
        assert entry["stage"] == STAGE, (
            f"{name} audit entry is associated with stage {entry['stage']!r}"
        )
    task_name = entry.get("task") or entry.get("taskName")
    assert task_name == expected["task"], (
        f"{name} audit entry is associated with task {task_name!r}"
    )
    assert entry.get("taskType") == expected["task_type"], (
        f"{name} used taskType {entry.get('taskType')!r}"
    )
    if "cacheFile" in entry:
        assert entry["cacheFile"] == expected["cache_file"], (
            f"{name} did not record cacheFile {expected['cache_file']}"
        )
    assert str(entry.get("rationale") or "").strip() or isinstance(
        entry.get("resolution"), dict
    ), f"{name} audit entry has no resolution evidence"

    selected = entry.get("selected") or entry.get("resourceIdentity")
    assert isinstance(selected, dict), f"missing selected result for {name}"
    # `selected` is the registry cache entry copied through, and `registry search` returns
    # PascalCase (`Name`), while the skill's own examples show camelCase. SKILL.md Rule 9
    # pins the ledger's OUTER keys and says nothing about the shape inside `selected`, so
    # both spellings are legal and runs alternate between them: suite7 wrote `name`,
    # suite8 wrote `Name` and this assertion failed a correct resolution. Accept either.
    selected_name = (
        g(selected, "name")
        or entry.get("resolvedResource")
    )
    assert selected_name == name, (
        f"selected the wrong resource for {name}: got {selected_name!r} "
        f"(selected keys: {sorted(selected)[:8]})"
    )

    cached_resources = load_json(cache_root / expected["cache_file"])
    exact_matches = [
        resource
        for resource in cached_resources
        if str(g(resource, "name", default="")).strip().casefold() == name.casefold()
    ]
    assert exact_matches, f"test precondition failed: no live registry match for {name}"
    cache_keys = {str(g(r, "entityKey")) for r in exact_matches}

    # registry-resolved.json records a NORMALIZED audit shape (flat `folder`, derived
    # `entitySubType`/`folderType`), not the raw cache object (`folders[]` array + extra
    # fields) — so compare on stable identity (name + entityKey), never deep-equality.
    # Also tolerant of ephemeral debug-deploy churn: we require the SELECTED entry to be a
    # live exact-name match and every recorded candidate to be exact-name, not a byte-for-
    # byte copy of the whole cache set.
    recorded = entry.get("matches")
    if recorded is not None:
        assert recorded, f"{name} audit recorded no matches"
        # The skill's discovery search is substring-based, so `matches` may carry
        # near-name candidates alongside the exact hit. Correctness is proven by
        # `selected`; here we only require the exact-name match to be present.
        assert any(
            str(g(m, "name", default="")).strip().casefold() == name.casefold()
            for m in recorded
        ), f"{name} audit recorded no exact-name match"
    assert (
        str(selected_name).strip().casefold() == name.casefold()
        and str(g(selected, "entityKey")) in cache_keys
    ), f"selected result for {name} is not a live exact-name cache entry"

    # Multi-match disambiguation: when several exact-name copies exist (e.g. ephemeral
    # debug-solution deploys of the same resource), the resolver must select the canonical
    # resource, NOT a debug copy. The audit shape varies run to run — folder/type may be
    # flat (folder/folderType) or nested (folders[0].fullyQualifiedName/.type).
    fol = g(selected, "folders") or []
    sel_folder = str(
        g(selected, "folder", "folderPath")
        or entry.get("folderPath")
        or (g(fol[0], "fullyQualifiedName") if fol else "")
    ).casefold()
    sel_ftype = str(
        g(selected, "folderType", "organizationUnitType")
        or (g(fol[0], "type") if fol else "")
    ).casefold()
    assert sel_ftype != "debugsolution" and "debug_" not in sel_folder, (
        f"{name} resolved to an ephemeral debug-solution deploy "
        f"({sel_folder!r}); expected the canonical resource"
    )
