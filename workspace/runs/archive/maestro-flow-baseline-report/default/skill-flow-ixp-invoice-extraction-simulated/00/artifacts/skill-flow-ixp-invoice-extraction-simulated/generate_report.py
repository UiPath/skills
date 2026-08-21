"""
Generate the full human-readable IXP pipeline report from pipeline_state.json.
Produces:
  - report.txt  (plain-text, terminal-friendly)
  - report.json (structured summary for downstream use)
"""
import json
import os

BASE = "/work/output/artifacts/skill-flow-ixp-invoice-extraction-simulated"

with open(os.path.join(BASE, "pipeline_state.json")) as f:
    S = json.load(f)

project   = S["project"]
taxonomy  = S["taxonomy"]
documents = S["documents"]
preds     = S["predictions"]
labels    = S["labellings"]
metrics   = S["metrics"]

lines = []
def out(*args, **kw):
    lines.append(" ".join(str(a) for a in args))

DIVIDER = "═" * 72
DASH    = "─" * 72
THIN    = "·" * 72


# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
out(DIVIDER)
out("  UIPATH IXP — VENDOR INVOICE EXTRACTION PIPELINE")
out("  Simulated End-to-End Run  |  Anthropic Claude Code")
out(DIVIDER)
out()

# ══════════════════════════════════════════════════════════════════
# 1. PROJECT OVERVIEW
# ══════════════════════════════════════════════════════════════════
out("┌─  1. PROJECT OVERVIEW  " + "─" * 48)
out(f"│   Project Title  : {project['Title']}")
out(f"│   Project Name   : {project['Name']}")
out(f"│   Extraction Model : {project['Model']}")
out(f"│   Pre-processing   : {project['Preprocessing']}")
out(f"│   Documents        : {len(documents)}")
out(f"│   Created          : {project['CreatedAt']}")
out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 2. TAXONOMY
# ══════════════════════════════════════════════════════════════════
out("┌─  2. TAXONOMY — FIELD GROUPS & FIELDS  " + "─" * 31)
field_count = 0
for lg in taxonomy["label_groups"]:
    rep = "  [repeatable]" if lg["repeatable"] else ""
    out(f"│")
    out(f"│  ▸ {lg['name']}{rep}")
    out(f"│    Instructions: {lg['instructions'][:70]}...")
    for fld in lg["fields"]:
        type_name = next(
            (e["name"] for e in taxonomy["entity_defs"] if e["id"] == fld["type_id"]), fld["type_id"]
        )
        out(f"│      • {fld['name']:<28} [{type_name}]")
        field_count += 1
out(f"│")
out(f"│   Total: {len(taxonomy['label_groups'])} field groups  ·  {field_count} fields")
out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 3. DOCUMENT UPLOAD
# ══════════════════════════════════════════════════════════════════
out("┌─  3. DOCUMENT UPLOAD  " + "─" * 48)
for doc in documents:
    short_id = doc["DocumentId"][:12] + "..."
    out(f"│   [{short_id}]  {doc['Filename']}")
out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 4. EXTRACTION PREDICTIONS + REVIEW
# ══════════════════════════════════════════════════════════════════
out("┌─  4. EXTRACTION PREDICTIONS & REVIEW  " + "─" * 31)
out("│   For each document: IXP generates predictions → reviewer validates field-by-field")
out("│")

total_confirmed = 0
total_corrected = 0
total_missing   = 0
total_not_conf  = 0

for doc in documents:
    doc_id = doc["DocumentId"]
    lab    = labels[doc_id]
    pred   = preds[doc_id]
    inv_id = doc["Filename"]

    nc = lab["not_confirmed"]
    co = lab["corrected"]
    mi = lab["missing"]
    cf = lab["confirmed"]

    # Don't double-count corrected (they're in confirmed too)
    confirmed_only = [c for c in cf if c["field_id"] not in {x["field_id"] for x in co}]
    total_confirmed += len(cf)
    total_corrected += len(co)
    total_missing   += len(mi)
    total_not_conf  += len(nc)

    out(f"│  ┌─ Document: {doc['Filename']}")
    out(f"│  │  Doc ID : {doc_id[:18]}...")
    out(f"│  │")

    # Build verdict table
    out(f"│  │  {'Field':<35} {'Verdict':<16} Notes")
    out(f"│  │  {'─'*35} {'─'*16} {'─'*18}")

    for pred_label in pred["Labels"]:
        group = pred_label["Name"]
        occ   = pred_label["Occurrence"]
        occ_str = f" (occ {occ})" if pred_label["Name"] == "Line Items" else ""

        for fld in pred_label["Fields"]:
            fid       = fld["FieldId"]
            predicted = fld["FormattedValue"]
            fname     = f"{fld['FieldName']}{occ_str}"

            is_corrected = any(c["field_id"] == fid and c["occurrence"] == occ for c in co)
            is_missing   = any(m["field_id"] == fid and m["occurrence"] == occ for m in mi)
            is_nc        = any(n["field_id"] == fid and n["occurrence"] == occ for n in nc)
            is_confirmed = any(c["field_id"] == fid and c["occurrence"] == occ for c in cf) and not is_nc

            if is_missing:
                note = "(absent from document)"
                verdict = "MISSING"
            elif is_corrected:
                corr_entry = next(c for c in co if c["field_id"] == fid and c["occurrence"] == occ)
                note = f'OCR: "{predicted}" → "{corr_entry["corrected"]}"'
                verdict = "CORRECTED"
            elif is_nc:
                nc_entry = next(n for n in nc if n["field_id"] == fid and n["occurrence"] == occ)
                note = f'pred="{predicted[:28]}" actual="{str(nc_entry.get("actual","?"))[:20]}"'
                verdict = "NOT CONFIRMED"
            elif is_confirmed:
                note = f'"{predicted[:35]}"'
                verdict = "CONFIRMED"
            else:
                note = ""
                verdict = "—"

            fname_short = fname[:34]
            out(f"│  │  {fname_short:<35} {verdict:<16} {note[:50]}")

    out(f"│  │")
    out(f"│  │  Summary: {len(cf)} confirmed  ·  {len(co)} corrected  ·  {len(mi)} missing  ·  {len(nc)} not-confirmed")
    out(f"│  └{'─'*69}")
    out("│")

out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 5. METRICS
# ══════════════════════════════════════════════════════════════════
out("┌─  5. EXTRACTION METRICS  " + "─" * 45)
out(f"│   Model Version    : v{metrics['ModelVersion']}  (trained {metrics['TrainedTime']})")
out(f"│   Validated Docs   : {metrics['ValidatedDocuments']}")
out(f"│   Overall F1       : {metrics['ProjectScore']:.4f}   [{metrics['ProjectScoreQuality']}]")
out("│")
out("│   Per Field Group:")
out(f"│   {'Field Group':<28} {'F1':>6}  {'Prec':>6}  {'Recall':>6}  {'TP':>4} {'FP':>4} {'FN':>4}")
out(f"│   {'─'*28} {'─'*6}  {'─'*6}  {'─'*6}  {'─'*4} {'─'*4} {'─'*4}")
for g in metrics["FieldGroups"]:
    bar_len = int(g["F1"] * 20)
    bar = "█" * bar_len + "░" * (20 - bar_len)
    out(f"│   {g['FieldGroup']:<28} {g['F1']:>6.4f}  {g['Precision']:>6.4f}  {g['Recall']:>6.4f}  "
        f"{g['TP']:>4} {g['FP']:>4} {g['FN']:>4}  {bar}")
out("│")
out("│   Per Field (sorted lowest F1 first):")
out(f"│   {'Field Name':<28} {'Group':<22} {'F1':>6}  {'Prec':>6}  {'Recall':>6}  Annot")
out(f"│   {'─'*28} {'─'*22} {'─'*6}  {'─'*6}  {'─'*6}  {'─'*5}")
for fld in metrics["Fields"]:
    grp_short = fld["FieldGroup"][:21]
    out(f"│   {fld['FieldName']:<28} {grp_short:<22} {fld['F1']:>6.4f}  {fld['Precision']:>6.4f}  "
        f"{fld['Recall']:>6.4f}  {fld['Annotations']:>5}")
out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 6. LABELLING SUMMARY
# ══════════════════════════════════════════════════════════════════
out("┌─  6. LABELLING SUMMARY  " + "─" * 46)
out(f"│   Documents processed : {len(documents)}")
out(f"│   Fields confirmed    : {total_confirmed:>4}  (exact matches + OCR corrections)")
out(f"│   OCR corrections     : {total_corrected:>4}  (right location, garbled characters)")
out(f"│   Marked missing      : {total_missing:>4}  (genuinely absent from document)")
out(f"│   Not confirmed       : {total_not_conf:>4}  (wrong value — left unannotated for retraining)")
out("│")

out("│   OCR Corrections Applied:")
for doc_id, lab in labels.items():
    for corr in lab["corrected"]:
        doc = DOC_BY_ID = next(d for d in documents if d["DocumentId"] == doc_id)
        out(f"│     • {doc['Filename']}")
        out(f"│       {corr['name']}: \"{corr['predicted']}\" → \"{corr['corrected']}\"")

if total_missing > 0:
    out("│")
    out("│   Fields Marked Missing:")
    for doc_id, lab in labels.items():
        for m in lab["missing"]:
            doc = next(d for d in documents if d["DocumentId"] == doc_id)
            out(f"│     • {doc['Filename']}  ·  {m['name']}")

if total_not_conf > 0:
    out("│")
    out("│   Not Confirmed (wrong predictions — prompt improvement needed):")
    for doc_id, lab in labels.items():
        for nc in lab["not_confirmed"]:
            doc = next(d for d in documents if d["DocumentId"] == doc_id)
            out(f"│     • {doc['Filename']}")
            out(f"│       {nc['name']}: predicted=\"{str(nc.get('predicted',''))[:40]}\"  actual=\"{str(nc.get('actual',''))[:35]}\"")
            out(f"│       Reason: {nc.get('reason','')}")

out("└" + "─" * 71)
out()

# ══════════════════════════════════════════════════════════════════
# 7. NEXT STEPS
# ══════════════════════════════════════════════════════════════════
out("┌─  7. NEXT STEPS  " + "─" * 53)
out("│")
if total_not_conf > 0:
    out(f"│   ① IMPROVE PROMPTS  — {total_not_conf} field(s) were not confirmed.")
    out("│     Run 'uip ixp fields update-prompts' with tighter instructions for:")
    for doc_id, lab in labels.items():
        for nc in set((n["name"], n["group"]) for n in lab["not_confirmed"]):
            out(f"│       · {nc[1]} > {nc[0]}")
    out("│     Wait ~2 min for retrain, then re-review predictions.")
    out("│")
out("│   ② PUBLISH MODEL")
out(f"│     uip ixp projects publish {project['Name']} --tag live --output json")
out("│")
out("│   ③ DEPLOY TO ORCHESTRATOR FOLDER")
out("│     In-product step — bind the published model to a folder/environment.")
out("│     See: https://docs.uipath.com/ixp/automation-cloud/latest/user-guide/building-and-deploying-models")
out("│")
out("│   ④ CONSUME IN A WORKFLOW OR MAESTRO FLOW")
out("│     Reference the deployed model from an UiPath automation, robot, or")
out("│     Maestro Flow to process invoices automatically end-to-end.")
out("└" + "─" * 71)
out()

report_text = "\n".join(lines)

# Write report.txt
report_path = os.path.join(BASE, "report.txt")
with open(report_path, "w") as f:
    f.write(report_text)

# Write structured report.json
report_json = {
    "project": project,
    "documents": [{"id": d["DocumentId"], "filename": d["Filename"]} for d in documents],
    "taxonomy_summary": {
        "field_groups": len(taxonomy["label_groups"]),
        "total_fields": sum(len(lg["fields"]) for lg in taxonomy["label_groups"]),
        "groups": [{"name": lg["name"], "repeatable": lg["repeatable"], "field_count": len(lg["fields"])} for lg in taxonomy["label_groups"]],
    },
    "labelling_summary": {
        "documents_processed": len(documents),
        "total_confirmed": total_confirmed,
        "ocr_corrections": total_corrected,
        "marked_missing": total_missing,
        "not_confirmed": total_not_conf,
    },
    "metrics": {
        "model_version": metrics["ModelVersion"],
        "project_score": metrics["ProjectScore"],
        "quality": metrics["ProjectScoreQuality"],
        "validated_documents": metrics["ValidatedDocuments"],
        "field_groups": metrics["FieldGroups"],
    },
}
with open(os.path.join(BASE, "report.json"), "w") as f:
    json.dump(report_json, f, indent=2)

print(report_text)
print(f"\n  Report saved → {report_path}")
print(f"  JSON summary → {BASE}/report.json")
