"""Round-trip check for the taxonomy lifecycle.

The test auto-suggests a taxonomy, snapshots it (taxonomy_initial.json), then adds
a field group and a series of edits, and finally deletes that group. Since every
edit was confined to the added group, the final taxonomy must match the initial
suggested one.

Compares STRUCTURE only — group names + each field's (name, kind, instructions) —
sorted, so ordering and volatile metadata (ids, timestamps, version) don't matter.

Each file may be the full get-taxonomy response (root has Data.dataset), the Data
object, or the unwrapped dataset — all accepted.
"""
import json
import sys


def load_dataset(path):
    d = json.load(open(path))
    d = d.get("Data", d)        # full response -> Data; else unchanged
    return d.get("dataset", d)  # Data -> dataset; else already the dataset


def extract_structure(ds):
    groups = []
    for group in ds.get("label_groups", []):
        for ld in group.get("label_defs", []):
            fields = sorted(
                (f.get("name"), f.get("kind"), f.get("instructions", ""))
                for f in ld.get("moon_form", [])
            )
            groups.append((ld.get("name"), ld.get("instructions", ""), tuple(fields)))
    return sorted(groups)


initial = extract_structure(load_dataset("taxonomy_initial.json"))
final = extract_structure(load_dataset("taxonomy_final.json"))

if initial == final:
    print("PASS - taxonomy round-trip: final matches the initial auto-suggested taxonomy")
    sys.exit(0)

print("FAIL - taxonomy changed across the add/delete round-trip")
print("initial groups:", [g[0] for g in initial])
print("final groups:  ", [g[0] for g in final])
sys.exit(1)
