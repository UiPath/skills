"""Verify the full publish/tag/unpublish lifecycle from saved list-models snapshots.

ModelVersion numbers are dynamic (each retrain increments them), so we assert
RELATIVE wire-effects, not fixed numbers. `list-models` Data carries:
  - Tags[]:   {Name, Version}      — which version each named tag points to
  - Models[]: {Version, Pinned}    — Pinned = currently published

Each file may be the full CLI response (root has `Data`) or the unwrapped payload
(root IS the data), so we accept either shape.

Snapshots (saved by the agent after each step):
  models_tagged.json           after: staging->v1, live->v2
  models_after_move.json       after: live moved onto v1
  models_after_untag.json      after: tags removed from v1 (still published)
  models_after_unpublish.json  after: v2 unpublished (still trained/listed)
"""
import json
import sys


def load_snapshot(path):
    d = json.load(open(path))
    return d.get("Data", d)


def get_tag_version(snapshot, tag_name):
    hits = [t["Version"] for t in snapshot["Tags"] if t["Name"] == tag_name]
    return hits[0] if hits else None


def count_tags_on(snapshot, version):
    return len([t for t in snapshot["Tags"] if t["Version"] == version])


def is_published(snapshot, version):
    return any(m["Version"] == version and m.get("Pinned") for m in snapshot["Models"])


def is_listed(snapshot, version):
    return any(m["Version"] == version for m in snapshot["Models"])


tagged = load_snapshot("models_tagged.json")
moved = load_snapshot("models_after_move.json")
untagged = load_snapshot("models_after_untag.json")
unpublished = load_snapshot("models_after_unpublish.json")

v1 = get_tag_version(tagged, "staging")   # first version (staging)
v2 = get_tag_version(tagged, "live")      # second version (live)

checks = {
    "tagging: staging and live point to two different versions":
        v1 is not None and v2 is not None and v1 != v2,
    "move: live now points to the staging version (v1)":
        get_tag_version(moved, "live") == v1,
    "untag: version 1 has exactly 0 tags left, and stays published":
        count_tags_on(untagged, v1) == 0 and is_published(untagged, v1),
    "unpublish: v2 is no longer published but still trained/listed":
        (not is_published(unpublished, v2)) and is_listed(unpublished, v2),
}

for name, ok in checks.items():
    print(("PASS" if ok else "FAIL"), "-", name)

sys.exit(0 if all(checks.values()) else 1)
