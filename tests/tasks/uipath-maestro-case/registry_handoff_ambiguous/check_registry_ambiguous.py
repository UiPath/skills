"""An ambiguous resource name is settled by the user's pick, never by position.

The SDD names its API workflow "API Workflow" with no folder. On the tenant that
name belongs to several resources, and `sdd resolve` reports it `ambiguous`.
The registry cache lists them in the order the tenant registered them, so the
first is whichever was deployed earliest — not a property of the resource.

The simulated user picks the candidate in TARGET_FOLDER, which sits in the
MIDDLE of the cache order — neither first nor last, so no positional heuristic
("first", "newest", "last") can reach it. That separates three behaviours that
otherwise all look plausible:

  * picked by position (the retired "first exact-name match" rule) -> wrong resource
  * left a placeholder although the user answered                  -> no resource
  * asked, and bound exactly the chosen candidate                  -> pass
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import registry_audit_entries  # noqa: E402

NAME = "API Workflow"
TASK = "Record Outcome"
STAGE = "Resolve Resources"
TARGET_FOLDER = "Shared/uipath-maestro-case/NameToAgeFixed"
CACHE = Path.home() / ".uip" / "case-resources" / "api-index.json"


def ci(obj, *names):
    """Case-insensitive read: raw cache entries are camelCase, `registry search` PascalCase."""
    if not isinstance(obj, dict):
        return None
    low = {str(k).casefold(): v for k, v in obj.items()}
    for n in names:
        if low.get(n.casefold()) is not None:
            return low[n.casefold()]
    return None


def folder_of(resource):
    folders = ci(resource, "folders") or []
    if folders and isinstance(folders[0], dict):
        return ci(folders[0], "fullyQualifiedName")
    return ci(resource, "folder")


# --- environment preconditions: failing these is a tenant gap, not a skill bug ---
cache = json.loads(CACHE.read_text(encoding="utf-8"))
exact = [r for r in cache if str(ci(r, "name") or "").strip().casefold() == NAME.casefold()]
assert len(exact) >= 2, (
    f"test precondition failed: {len(exact)} live '{NAME}' resource(s) — nothing is ambiguous"
)
targets = [r for r in exact if folder_of(r) == TARGET_FOLDER]
assert targets, f"test precondition failed: no live '{NAME}' in {TARGET_FOLDER}"
position = exact.index(targets[0])
assert 0 < position < len(exact) - 1, (
    f"test precondition failed: the target is at position {position} of {len(exact)} in cache "
    f"order; at either end a positional pick (first, or last/newest) would pass — move "
    f"TARGET_FOLDER to a middle candidate"
)
target_key = str(ci(targets[0], "entityKey"))
first_key = str(ci(exact[0], "entityKey"))
first_folder = folder_of(exact[0])
last_key = str(ci(exact[-1], "entityKey"))

# --- the behaviour ---
entries = registry_audit_entries(
    json.loads(Path("tasks/registry-resolved.json").read_text(encoding="utf-8"))
)
matching = [e for e in entries if str(e.get("searchQuery") or "").strip() == NAME]
assert len(matching) == 1, f"expected one audit entry for '{NAME}', got {len(matching)}"
entry = matching[0]
assert entry.get("task") == TASK, f"'{NAME}' is associated with task {entry.get('task')!r}"
if "stage" in entry:
    assert entry["stage"] == STAGE, f"'{NAME}' is associated with stage {entry['stage']!r}"

recorded = entry.get("matches") or []
recorded_exact = [
    m for m in recorded if str(ci(m, "name") or "").strip().casefold() == NAME.casefold()
]
assert len(recorded_exact) >= 2, (
    f"the audit recorded {len(recorded_exact)} exact-name candidate(s); an ambiguous "
    f"resource must keep every candidate so the choice is reviewable"
)

selected = entry.get("selected")
assert isinstance(selected, dict) and selected, (
    f"'{NAME}' was left unresolved although the user was available to choose — "
    f"the gate must ask which candidate is meant"
)
selected_key = str(ci(selected, "entityKey"))
assert selected_key != first_key, (
    f"'{NAME}' was settled by position: it bound the first registered candidate "
    f"({first_folder}), not the one the user chose"
)
assert selected_key != last_key, (
    f"'{NAME}' was settled by position: it bound the last registered candidate "
    f"({folder_of(exact[-1])}), not the one the user chose"
)
assert selected_key == target_key, (
    f"'{NAME}' bound {selected_key} ({folder_of(selected)}); the user chose {TARGET_FOLDER}"
)
