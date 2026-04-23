#!/usr/bin/env python3
"""Clause-first compliance check runner.

Reads an extracted `.uipolicy` pack directory plus a JSON file of cached
`get-by-user` CLI responses, produces the JSON audit report, renders the
HTML report from the skill's template, and prints the terminal summary.

Inputs are all data — no network calls, no `uip` shellouts. The caller is
responsible for:
  1. Verifying `uip login` (preflight)
  2. Unzipping the pack
  3. Calling `uip admin aops-policy deployment get-by-user` once per unique
     (licenseType, productIdentifier) pair and concatenating the full CLI
     responses into the cache file (see --cli-cache format below).

Invocation:

    python3 run-compliance-check.py \
      --pack-dir      /tmp/pack/extracted \
      --cli-cache     /tmp/cli-cache.json \
      --tenant-id     "$UIPATH_TENANT_ID" \
      --tenant-name   "$UIPATH_TENANT_NAME" \
      --out-dir       .

Defaults for --reference and --template point at the skill's assets/, so
they can be omitted when the script is run from its installed location.

Exit codes:
  0  report generated (drift is not a failure)
  2  usage / missing inputs
  3  walker could not produce a report (malformed pack, cache mismatch)
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REFERENCE = SCRIPT_DIR.parent / "uipath_policy_reference_classified.json"
DEFAULT_TEMPLATE  = SCRIPT_DIR.parent / "templates" / "compliance-report-template.html"

# --- CLI cache file format -------------------------------------------------
# {
#   "NoLicense|AITrustLayer": { ...full "Data" object from `uip ... get-by-user` ... },
#   ...
# }
# i.e. a dict keyed by "{licenseType}|{productIdentifier}" whose values are
# exactly the `Data` subtree of the successful CLI response. A value of `null`
# means the CLI returned 204 / no policy applied.

# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--pack-dir", required=True, type=Path, help="Extracted pack directory")
    p.add_argument("--cli-cache", required=True, type=Path, help="Cached CLI responses (JSON)")
    p.add_argument("--tenant-id", required=True)
    p.add_argument("--tenant-name", required=True)
    p.add_argument("--out-dir", default=".", type=Path)
    p.add_argument("--reference", default=DEFAULT_REFERENCE, type=Path)
    p.add_argument("--template",  default=DEFAULT_TEMPLATE,  type=Path)
    p.add_argument("--pack-source", default="", help="Display string for how the pack was obtained")
    return p.parse_args()


# --- Helpers ---------------------------------------------------------------

def load_json(path: Path) -> object:
    with path.open() as fh:
        return json.load(fh)


def lookup_ref(ref: dict, product: str, path: str) -> dict | None:
    """Resolve `<product>.<dotted.path>` to its reference node, honoring `fields` / `item_schema`."""
    node = ref.get(product)
    if node is None:
        return None
    for seg in path.split("."):
        if isinstance(node, dict) and seg in node:
            node = node[seg]
        elif isinstance(node, dict) and isinstance(node.get("fields"), dict) and seg in node["fields"]:
            node = node["fields"][seg]
        elif isinstance(node, dict) and isinstance(node.get("item_schema"), dict) and seg in node["item_schema"]:
            node = node["item_schema"][seg]
        else:
            return None
    return node if isinstance(node, dict) else None


def json_path(obj: object, dotted: str) -> object:
    if obj is None:
        return None
    cur = obj
    for seg in dotted.split("."):
        if isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return None
    return cur


def deep_equal(a: object, b: object) -> bool:
    # Arrays of objects keyed by `identifier` (AITL pii-entity-table quirk).
    if isinstance(a, list) and isinstance(b, list) and a and isinstance(a[0], dict) and "identifier" in a[0]:
        ai = {x.get("identifier"): x for x in a if isinstance(x, dict)}
        bi = {x.get("identifier"): x for x in b if isinstance(x, dict)}
        if set(ai) != set(bi):
            return False
        return all(deep_equal(ai[k], bi[k]) for k in ai)
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return False
        return all(deep_equal(a[k], b[k]) for k in a)
    return a == b


def h(v: object) -> str:
    return html.escape("" if v is None else str(v))


def fmt_val(v: object) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[array]"
    if isinstance(v, dict):
        return h(json.dumps(v))
    return h(v)


# --- Walk ------------------------------------------------------------------

def walk(pack_dir: Path, cli_cache: dict, ref: dict) -> tuple[list[dict], dict, dict]:
    manifest   = load_json(pack_dir / "manifest.json")
    clause_map = load_json(pack_dir / "clause-map.json")

    policy_cache: dict[str, dict] = {}

    def load_policy(rel: str) -> dict:
        if rel not in policy_cache:
            policy_cache[rel] = load_json(pack_dir / rel)
        return policy_cache[rel]

    clauses: list[dict] = []
    cli_calls_expected: set[str] = set()

    for clause in clause_map.get("clauses", []):
        result = {
            "clauseId": clause["id"],
            "name": clause.get("name", ""),
            "category": clause.get("category"),
            "obligationLevel": clause.get("obligationLevel") or ("Mandatory" if clause.get("mandatory") else "Optional"),
            "status": "unknown",
            "contributions": [],
        }

        for contrib in clause.get("contributions", []):
            policy = load_policy(contrib["uipolicyFile"])
            prod_id = (policy.get("policy") or {}).get("productIdentifier")
            access_kind = (policy.get("accessPolicy") or {}).get("accessPolicyType")
            kind = policy.get("policyKind", "product")

            if kind != "product" or prod_id != "AITrustLayer":
                result["contributions"].append({
                    "product": prod_id or access_kind,
                    "status": "skipped",
                    "reason": "out-of-version-scope",
                    "properties": [],
                })
                continue

            license_type = policy["policy"]["licenseTypeIdentifier"]
            key = f"{license_type}|{prod_id}"
            cli_calls_expected.add(key)

            if key not in cli_cache:
                raise SystemExit(f"cache miss for {key}: caller must pre-fetch get-by-user")
            live = cli_cache[key]
            live_data = (live or {}).get("data") if isinstance(live, dict) else None

            properties = []
            expected_fd = policy.get("formData", {}) or {}
            for prop_path in contrib.get("properties", []):
                expected = json_path(expected_fd, prop_path)
                actual = json_path(live_data, prop_path)
                properties.append({
                    "path": prop_path,
                    "expected": expected,
                    "actual": actual,
                    "match": deep_equal(expected, actual),
                })

            result["contributions"].append({
                "product": prod_id,
                "status": "checked",
                "effectivePolicyName": (live or {}).get("policy-name"),
                "effectiveDeployment": (live or {}).get("deployment"),
                "properties": properties,
            })

        # Aggregate
        checked = [c for c in result["contributions"] if c["status"] == "checked"]
        if any(any(not p["match"] for p in c["properties"]) for c in checked):
            result["status"] = "drifted"
        elif checked:
            result["status"] = "compliant"
        else:
            result["status"] = "skipped"
        clauses.append(result)

    return clauses, manifest, clause_map


# --- Reports ---------------------------------------------------------------

def build_summary(clauses: list[dict]) -> dict:
    return {
        "totalClauses": len(clauses),
        "compliant":    sum(1 for c in clauses if c["status"] == "compliant"),
        "drifted":      sum(1 for c in clauses if c["status"] == "drifted"),
        "skippedPolicies": sum(1 for c in clauses if c["status"] == "skipped"),
    }


def overall_status(clauses: list[dict], summary: dict) -> tuple[str, str]:
    total = summary["totalClauses"]
    if total == 0:
        return "Compliant", "badge-pass"
    if summary["compliant"] == total:
        return "Compliant", "badge-pass"
    mandatory_drifted = any(
        c["obligationLevel"] in ("Mandatory", "ConditionalMandatory") and c["status"] == "drifted"
        for c in clauses
    )
    if summary["drifted"] == total or mandatory_drifted:
        return "Non-Compliant", "badge-fail"
    return "Partially Compliant", "badge-partial"


def render_html(template: str, report: dict, ref: dict) -> str:
    clauses = report["clauses"]
    summary = report["summary"]
    total   = summary["totalClauses"]
    ov_status, ov_badge = overall_status(clauses, summary)

    status_rank = {"drifted": 0, "compliant": 1, "skipped": 2}
    obl_rank    = {"Mandatory": 0, "ConditionalMandatory": 1, "Recommended": 2, "Optional": 3}
    obl_tag = {
        "Mandatory": "tag-mandatory",
        "ConditionalMandatory": "tag-conditional",
        "Recommended": "tag-recommended",
        "Optional": "tag-optional",
    }
    pill = {
        "compliant": ("pill-compliant", "Compliant"),
        "drifted":   ("pill-drifted", "Drifted"),
        "skipped":   ("pill-skipped", "Skipped"),
    }
    ordered = sorted(
        clauses,
        key=lambda c: (status_rank.get(c["status"], 9), obl_rank.get(c["obligationLevel"], 9), c["clauseId"]),
    )

    def drift_prop_count(c: dict) -> int:
        return sum(1 for ctr in c["contributions"] for p in ctr.get("properties", []) if not p.get("match", True))

    clause_rows: list[str] = []
    for c in ordered:
        pcls, pt = pill.get(c["status"], ("pill-skipped", c["status"]))
        dc = drift_prop_count(c)
        clause_rows.append(
            f'      <tr>'
            f'<td><span class="clause-id">{h(c["clauseId"])}</span></td>'
            f'<td><div class="clause-name">{h(c["name"])}</div>'
            f'<div class="clause-category">{h(c.get("category") or "")}</div></td>'
            f'<td><span class="obligation-tag {obl_tag.get(c["obligationLevel"], "tag-optional")}">'
            f'{h(c["obligationLevel"])}</span></td>'
            f'<td><span class="status-pill {pcls}">{pt}</span></td>'
            f'<td><span class="drift-count">{dc if dc else ""}</span></td>'
            f'</tr>'
        )
    CLAUSE_ROWS = "\n".join(clause_rows)

    drift_blocks: list[str] = []
    for c in [x for x in ordered if x["status"] == "drifted"]:
        prop_rows: list[str] = []
        for ctr in c["contributions"]:
            product = ctr.get("product") or "AITrustLayer"
            for p in ctr.get("properties", []):
                mcls, micon = ("val-match", "&#x2713;") if p["match"] else ("val-mismatch", "&#x2717;")
                node = lookup_ref(ref, product, p["path"])
                if node and node.get("description"):
                    label = f'<div class="control-desc">{h(node["description"])}</div>'
                else:
                    label = f'<div class="control-desc"><code>{h(p["path"])}</code></div>'
                prop_rows.append(
                    f'      <tr><td>{label}</td>'
                    f'<td><span class="val-expected">{fmt_val(p["expected"])}</span></td>'
                    f'<td><span class="val-actual">{fmt_val(p["actual"])}</span></td>'
                    f'<td><span class="{mcls}">{micon}</span></td></tr>'
                )
        drift_blocks.append(
            '<div class="drift-detail">'
            '<div class="drift-detail-header">'
            f'<span class="clause-id">{h(c["clauseId"])}</span>'
            f'<span class="clause-name">{h(c["name"])}</span>'
            '</div>'
            '<table><thead><tr><th>Control</th><th>Expected</th><th>Actual</th>'
            '<th style="width:70px">Match</th></tr></thead>'
            f'<tbody>{chr(10).join(prop_rows)}</tbody></table></div>'
        )
    DRIFT_DETAILS = "\n".join(drift_blocks) if drift_blocks else '<p class="empty-note">No drifted clauses.</p>'

    skipped = report.get("skippedPolicies") or []
    if skipped:
        items = "\n".join(
            f'    <li><code>{h(s["file"])}</code> — {h(s["product"])} ({h(s["reason"])})</li>'
            for s in skipped
        )
        SKIPPED_BLOCK = (
            '<div class="skipped-policies">'
            '<h2 style="margin-top:0">Skipped Policies</h2>'
            '<p class="empty-note">The following policy files were recorded but not diffed (out of V1 scope):</p>'
            f'<ul>{items}</ul></div>'
        )
    else:
        SKIPPED_BLOCK = ""

    def pct(n: int, t: int) -> str:
        return str(round(n / t * 100)) if t else "0"

    scalars = {
        "PACK_NAME":           h(report["pack"]["packName"]),
        "PACK_VERSION":        h(report["pack"]["version"]),
        "TENANT_NAME":         h(report["target"]["tenantName"]),
        "GENERATED_AT":        datetime.fromisoformat(report["generatedAt"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC"),
        "OVERALL_STATUS":      ov_status,
        "OVERALL_BADGE_CLASS": ov_badge,
        "TOTAL_CLAUSES":       str(total),
        "COMPLIANT_COUNT":     str(summary["compliant"]),
        "DRIFTED_COUNT":       str(summary["drifted"]),
        "COMPLIANT_PCT":       pct(summary["compliant"], total),
        "DRIFTED_PCT":         pct(summary["drifted"], total),
    }

    out = template
    out = out.replace("<!-- {{CLAUSE_ROWS}} -->", CLAUSE_ROWS)
    out = out.replace("<!-- {{DRIFT_DETAILS}} -->", DRIFT_DETAILS)
    out = out.replace("<!-- {{SKIPPED_POLICIES_BLOCK}} -->", SKIPPED_BLOCK)
    for k, v in scalars.items():
        out = out.replace("{{" + k + "}}", v)

    leftover = re.findall(r"\{\{[A-Z0-9_]+\}\}", out)
    if leftover:
        raise SystemExit(f"template has unsubstituted placeholders: {sorted(set(leftover))}")
    return out


def terminal_summary(report: dict) -> str:
    clauses = report["clauses"]
    summary = report["summary"]
    ov_status, _ = overall_status(clauses, summary)

    status_rank = {"drifted": 0, "compliant": 1, "skipped": 2}
    obl_rank    = {"Mandatory": 0, "ConditionalMandatory": 1, "Recommended": 2, "Optional": 3}
    ordered = sorted(
        clauses,
        key=lambda c: (status_rank.get(c["status"], 9), obl_rank.get(c["obligationLevel"], 9), c["clauseId"]),
    )
    glyph = {"compliant": "✓", "drifted": "✗", "skipped": "·"}

    def drift_prop_count(c: dict) -> int:
        return sum(1 for ctr in c["contributions"] for p in ctr.get("properties", []) if not p.get("match", True))

    lines = []
    lines.append(f'Compliance Check: {report["pack"]["packName"]} v{report["pack"]["version"]} → tenant {report["target"]["tenantName"]}')
    lines.append(f"Overall: {ov_status}")
    lines.append("")
    for c in ordered:
        g = glyph.get(c["status"], "·")
        ext = f" ({drift_prop_count(c)} properties)" if c["status"] == "drifted" else ""
        lines.append(f'  {g} {c["clauseId"]:<12}{c["name"]:<58}{c["status"]}{ext}')
    lines.append("")
    lines.append(f'Result: {summary["compliant"]}/{summary["totalClauses"]} compliant, {summary["drifted"]} drifted')
    return "\n".join(lines)


# --- Main ------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    try:
        cli_cache = load_json(args.cli_cache)
        ref       = load_json(args.reference)
        template  = args.template.read_text()
    except FileNotFoundError as exc:
        print(f"error: missing input: {exc}", file=sys.stderr)
        return 2

    clauses, manifest, _clause_map = walk(args.pack_dir, cli_cache, ref)
    summary = build_summary(clauses)

    # Effective deployment + policy name come from the first checked contribution
    effective_policy = None
    effective_deployment = None
    for c in clauses:
        for ctr in c["contributions"]:
            if ctr["status"] == "checked":
                effective_policy = ctr.get("effectivePolicyName")
                effective_deployment = ctr.get("effectiveDeployment")
                break
        if effective_policy:
            break

    skipped_policies = []
    seen_skipped: set[str] = set()
    for c in clauses:
        for ctr in c["contributions"]:
            if ctr["status"] == "skipped":
                key = f'{ctr.get("product")}'
                if key in seen_skipped:
                    continue
                seen_skipped.add(key)
                skipped_policies.append({
                    "product": ctr.get("product"),
                    "reason":  ctr.get("reason", "out-of-version-scope"),
                })
    summary["skippedPolicies"] = len(skipped_policies)

    pack_id = manifest.get("packId") or "pack"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    report = {
        "reportKind":   "compliance-check",
        "schemaVersion": "1.0.0",
        "generatedAt":   datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "pack": {
            "packId":   manifest.get("packId"),
            "packName": manifest.get("packName"),
            "version":  manifest.get("version"),
            "source":   args.pack_source,
        },
        "target": {
            "tenantName":          args.tenant_name,
            "tenantId":            args.tenant_id,
            "effectivePolicyName": effective_policy,
            "effectiveDeployment": effective_deployment,
        },
        "summary":         summary,
        "clauses":         clauses,
        "skippedPolicies": skipped_policies,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"compliance-report-{pack_id}-{timestamp}.json"
    html_path = args.out_dir / f"compliance-report-{pack_id}-{timestamp}.html"
    json_path.write_text(json.dumps(report, indent=2))
    html_path.write_text(render_html(template, report, ref))

    print(terminal_summary(report))
    print("")
    print(f"Reports:")
    print(f"  {json_path}")
    print(f"  {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
