#!/usr/bin/env python3
"""
Compare two IXP metrics snapshots: compute per-field F1 change and flag regressions.
Used after each improve-prompts iteration and to produce the final summary report.

Usage:
  python compare_metrics.py --baseline baseline.json --current current.json --taxonomy taxonomy.json
  python compare_metrics.py --baseline b.json --current c.json --taxonomy t.json --regression-threshold 0.1 --out delta.json

Inputs:
  --baseline              get-metrics JSON from before the iteration
  --current               get-metrics JSON from after the iteration
  --taxonomy              get-taxonomy JSON (for field_id → name mapping)
  --regression-threshold  F1 drop that counts as a regression (default: 0.1)
  --out                   write JSON results to this file (optional)

Output:
  Comparison table to stdout.
  Exit 0 if no regressions, exit 1 if any field regressed.
"""

import argparse
import json
import sys


def load_json(path):
    with open(path) as f:
        return json.load(f)


def build_field_map(taxonomy):
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


def extract_fields(data):
    """Return {field_id: metrics_dict} from a metrics Data object."""
    return {f["FieldId"]: f for f in data.get("Fields", [])}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", required=True, help="Baseline get-metrics JSON file")
    parser.add_argument("--current", required=True, help="Current get-metrics JSON file")
    parser.add_argument("--taxonomy", required=True, help="get-taxonomy JSON file")
    parser.add_argument("--regression-threshold", type=float, default=0.1,
                        help="F1 drop that counts as a regression (default: 0.1)")
    parser.add_argument("--out", help="Write JSON delta to this file")
    args = parser.parse_args()

    baseline_raw = load_json(args.baseline)
    current_raw = load_json(args.current)
    taxonomy_raw = load_json(args.taxonomy)

    b_data = baseline_raw.get("Data", baseline_raw)
    c_data = current_raw.get("Data", current_raw)

    for label, data in [("baseline", b_data), ("current", c_data)]:
        if data is None or (data.get("Metrics") is None and "Fields" not in data):
            print(f"ERROR: {label} metrics not available (model not validated).", file=sys.stderr)
            sys.exit(2)

    field_map = build_field_map(taxonomy_raw)
    b_fields = extract_fields(b_data)
    c_fields = extract_fields(c_data)

    all_ids = sorted(set(b_fields) | set(c_fields))

    rows = []
    for fid in all_ids:
        bf = b_fields.get(fid, {})
        cf = c_fields.get(fid, {})
        info = field_map.get(fid, {"name": fid, "group": bf.get("FieldGroup", cf.get("FieldGroup", "?"))})
        b_f1 = bf.get("F1", 0.0)
        c_f1 = cf.get("F1", 0.0)
        delta = c_f1 - b_f1
        regressed = delta < -args.regression_threshold
        rows.append({
            "field_id": fid,
            "field_name": info["name"],
            "group": info["group"],
            "baseline_f1": b_f1,
            "current_f1": c_f1,
            "delta": delta,
            "regressed": regressed,
        })

    rows.sort(key=lambda r: r["delta"])

    b_score = b_data.get("ProjectScore", "n/a")
    c_score = c_data.get("ProjectScore", "n/a")
    b_ver = b_data.get("ModelVersion", "n/a")
    c_ver = c_data.get("ModelVersion", "n/a")

    print(f"ModelVersion: {b_ver} → {c_ver}   ProjectScore: {b_score} → {c_score}")
    print()
    print(f"{'Field':<28} {'Group':<22} {'Baseline F1':>11} {'Current F1':>10} {'Change':>8}  {'Status'}")
    print("-" * 95)

    for r in rows:
        sign = "+" if r["delta"] > 0 else ""
        flag = "REGRESSION" if r["regressed"] else ("improved" if r["delta"] > 0 else "")
        print(
            f"{r['field_name']:<28} {r['group']:<22} {r['baseline_f1']:>11.3f} {r['current_f1']:>10.3f} "
            f"{sign}{r['delta']:>7.3f}  {flag}"
        )

    regressions = [r for r in rows if r["regressed"]]
    improved = [r for r in rows if r["delta"] > 0]
    print(f"\nSummary: {len(improved)} improved, {len(regressions)} regressed")

    if regressions:
        print("\nRegressed fields (roll back instructions):")
        for r in regressions:
            print(f"  {r['field_name']} ({r['group']}): {r['baseline_f1']:.3f} → {r['current_f1']:.3f}  (Δ {r['delta']:.3f})")

    if args.out:
        with open(args.out, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"\nJSON delta written to {args.out}")

    sys.exit(1 if regressions else 0)


if __name__ == "__main__":
    main()
