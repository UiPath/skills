#!/usr/bin/env python3
"""
Diagnose IXP fields: join metrics with taxonomy, classify each field as
SKIP / OK / REFINE and label the problem type (PRECISION / RECALL / BOTH).

Usage:
  python diagnose_fields.py --metrics metrics.json --taxonomy taxonomy.json
  python diagnose_fields.py --metrics metrics.json --taxonomy taxonomy.json --threshold 0.8 --json

Inputs:
  --metrics    Path to `uip ixp projects get-metrics --output json` output file
  --taxonomy   Path to `uip ixp projects get-taxonomy --output json` output file
  --threshold  F1 below which a field is a REFINE target (default: 0.7)
  --json       Also emit results as JSON to stdout (in addition to the table)

Output:
  Prints a diagnosis table to stdout.
  Field groups are shown first, then per-field rows.
  Exit 0 always (this is a read-only analysis tool).
"""

import argparse
import json
import sys


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_field_map(taxonomy):
    """Return {field_id: {name, group}} from taxonomy Data.dataset."""
    dataset = taxonomy.get("Data", taxonomy).get("dataset", taxonomy)
    mapping = {}
    for lg in dataset.get("label_groups", []):
        for ld in lg.get("label_defs", []):
            group_name = ld.get("name", "")
            for field in ld.get("field_defs", []):
                fid = field.get("field_id") or field.get("id")
                if fid:
                    mapping[fid] = {"name": field.get("name", fid), "group": group_name}
    return mapping


def classify_field(f1, precision, recall, documents, threshold):
    if documents == 0 and f1 == 0:
        return "SKIP", "-"
    if documents < 1:
        return "SKIP", "-"
    if f1 >= threshold:
        return "OK", "-"
    if precision < recall - 0.1:
        return "REFINE", "PRECISION"
    if recall < precision - 0.1:
        return "REFINE", "RECALL"
    return "REFINE", "BOTH"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics", required=True, help="get-metrics JSON output file")
    parser.add_argument("--taxonomy", required=True, help="get-taxonomy JSON output file")
    parser.add_argument("--threshold", type=float, default=0.7, help="F1 threshold for REFINE (default: 0.7)")
    parser.add_argument("--json", action="store_true", help="also emit JSON results")
    args = parser.parse_args()

    metrics_raw = load_json(args.metrics)
    taxonomy_raw = load_json(args.taxonomy)

    data = metrics_raw.get("Data", metrics_raw)

    if data is None or data.get("Metrics") is None and "Fields" not in data:
        print("ERROR: Metrics not available yet (model not validated or no trained model).", file=sys.stderr)
        sys.exit(1)

    field_map = build_field_map(taxonomy_raw)

    # --- Field groups ---
    groups = data.get("FieldGroups", [])
    # --- Per-field ---
    fields = data.get("Fields", [])

    project_score = data.get("ProjectScore", "n/a")
    model_version = data.get("ModelVersion", "n/a")
    validated_docs = data.get("ValidatedDocuments", "n/a")

    print(f"Model version: {model_version}  |  ProjectScore: {project_score}  |  ValidatedDocuments: {validated_docs}")
    print()

    # Groups table
    print("Field Groups")
    print(f"{'Group':<30} {'F1':>6} {'Prec':>6} {'Recall':>6} {'Docs':>5}")
    print("-" * 60)
    for g in sorted(groups, key=lambda x: x.get("F1", 1.0)):
        print(f"{g.get('FieldGroup','?'):<30} {g.get('F1',0):>6.3f} {g.get('Precision',0):>6.3f} {g.get('Recall',0):>6.3f} {g.get('Documents',0):>5}")
    print()

    # Per-field diagnosis
    results = []
    for f in fields:
        fid = f.get("FieldId", "")
        info = field_map.get(fid, {"name": fid, "group": f.get("FieldGroup", "?")})
        f1 = f.get("F1", 0.0)
        precision = f.get("Precision", 0.0)
        recall = f.get("Recall", 0.0)
        documents = f.get("Documents", 0)
        action, problem = classify_field(f1, precision, recall, documents, args.threshold)
        results.append({
            "field_id": fid,
            "field_name": info["name"],
            "group": info["group"],
            "f1": f1,
            "precision": precision,
            "recall": recall,
            "documents": documents,
            "action": action,
            "problem_type": problem,
        })

    results.sort(key=lambda x: (x["action"] != "REFINE", x["f1"]))

    print(f"Per-Field Diagnosis  (threshold F1 < {args.threshold})")
    print(f"{'Field':<28} {'Group':<22} {'F1':>6} {'Prec':>6} {'Rec':>6} {'Docs':>5} {'Action':<8} {'Problem'}")
    print("-" * 100)
    for r in results:
        print(
            f"{r['field_name']:<28} {r['group']:<22} {r['f1']:>6.3f} {r['precision']:>6.3f} "
            f"{r['recall']:>6.3f} {r['documents']:>5} {r['action']:<8} {r['problem_type']}"
        )

    refine_count = sum(1 for r in results if r["action"] == "REFINE")
    print(f"\nSummary: {refine_count} field(s) need REFINE, "
          f"{sum(1 for r in results if r['action'] == 'OK')} OK, "
          f"{sum(1 for r in results if r['action'] == 'SKIP')} SKIP")

    if args.json:
        print("\n--- JSON ---")
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
