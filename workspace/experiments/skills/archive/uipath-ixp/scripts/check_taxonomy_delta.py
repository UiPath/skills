#!/usr/bin/env python3
"""
Verify that a taxonomy update did not lose any fields from any label_def.
Run after every `uip ixp fields update-prompts` or `groups update-prompts` call.

Usage:
  python check_taxonomy_delta.py --old old_taxonomy.json --new new_taxonomy.json

Inputs:
  --old   Taxonomy JSON saved before the update (get-taxonomy output)
  --new   Taxonomy JSON saved after the update (get-taxonomy output)

Output:
  Per-group pass/fail table to stdout.
  Exit 0 if no groups lost fields.
  Exit 1 if any group has fewer fields than before (STOP — taxonomy corrupted).
"""

import argparse
import json
import sys


def load_json(path):
    with open(path) as f:
        return json.load(f)


def extract_groups(taxonomy):
    """Return {group_name: [field_names]} from taxonomy Data.dataset."""
    dataset = taxonomy.get("Data", taxonomy).get("dataset", taxonomy)
    groups = {}
    for lg in dataset.get("label_groups", []):
        for ld in lg.get("label_defs", []):
            name = ld.get("name", "")
            fields = [f.get("name", f.get("field_id", "?")) for f in ld.get("field_defs", [])]
            groups[name] = fields
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--old", required=True, help="Taxonomy JSON before the update")
    parser.add_argument("--new", required=True, help="Taxonomy JSON after the update")
    args = parser.parse_args()

    old_groups = extract_groups(load_json(args.old))
    new_groups = extract_groups(load_json(args.new))

    all_names = sorted(set(old_groups) | set(new_groups))
    problems = []

    print(f"{'Group':<30} {'Old fields':>10} {'New fields':>10} {'Status'}")
    print("-" * 65)

    for name in all_names:
        old_fields = old_groups.get(name, [])
        new_fields = new_groups.get(name, [])
        old_count = len(old_fields)
        new_count = len(new_fields)
        missing = set(old_fields) - set(new_fields)

        if name not in new_groups:
            status = "MISSING GROUP"
            problems.append(f"Group '{name}' disappeared entirely")
        elif missing:
            status = f"LOST {len(missing)} field(s)"
            problems.append(f"Group '{name}' lost: {', '.join(sorted(missing))}")
        elif new_count < old_count:
            status = f"FEWER FIELDS ({old_count} → {new_count})"
            problems.append(f"Group '{name}': field count dropped {old_count} → {new_count}")
        else:
            added = new_count - old_count
            status = f"OK{f'  (+{added} added)' if added else ''}"

        print(f"{name:<30} {old_count:>10} {new_count:>10}  {status}")

    print()
    if problems:
        print("TAXONOMY CORRUPTED — stop the workflow immediately:")
        for p in problems:
            print(f"  {p}")
        print("\nRestore using the previous taxonomy version and re-run `fields update-prompts`.")
        sys.exit(1)
    else:
        print("Taxonomy OK — no fields lost.")


if __name__ == "__main__":
    main()
