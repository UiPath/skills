"""
IXP Invoice Extraction Simulation
==================================
Simulates the full UiPath IXP pipeline:
  1.  Project + taxonomy setup
  2.  Document "upload" registration
  3.  AI extraction predictions (with realistic noise)
  4.  Reviewer labelling loop (auto-review against ground truth)
  5.  Metrics computation and summary report

Outputs structured JSON artefacts for each stage plus a human-readable report.
"""
import json
import os
import copy
import random
import hashlib
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
BASE = "/work/output/artifacts/skill-flow-ixp-invoice-extraction-simulated"
DOCS_DIR = os.path.join(BASE, "docs")
TMP_DIR = os.path.join(BASE, "tmp_ixp", "vendor-invoices-project")
for sub in ["taxonomies", "prompts", "predictions", "labellings"]:
    os.makedirs(os.path.join(TMP_DIR, sub), exist_ok=True)

random.seed(42)  # reproducible

# ──────────────────────────────────────────────────────────────
# Load ground-truth invoice data
# ──────────────────────────────────────────────────────────────
with open(os.path.join(DOCS_DIR, "invoice_data.json")) as f:
    GROUND_TRUTH = {inv["id"]: inv for inv in json.load(f)}

# ──────────────────────────────────────────────────────────────
# STEP 1: Project + taxonomy
# ──────────────────────────────────────────────────────────────

PROJECT = {
    "Id": "proj-8f3a2c11-ixp",
    "Name": "vendor-invoices-f8a3c211-ixp",
    "Title": "Vendor Invoices",
    "CreatedAt": "2024-03-30T09:00:00Z",
    "Model": "gemini_2_5_flash",
    "Preprocessing": "table_mini",
    "Status": "Active",
}

TAXONOMY = {
    "entity_defs": [
        {"id": "et_exact",  "name": "Exact Text",         "kind": "text",    "input_value": "exact-match"},
        {"id": "et_infer",  "name": "Inferred Text",      "kind": "text",    "input_value": "inferred"},
        {"id": "et_number", "name": "Number",              "kind": "number"},
        {"id": "et_date",   "name": "Date",                "kind": "date"},
        {"id": "et_money",  "name": "Monetary Quantity",   "kind": "money"},
        {"id": "et_bool",   "name": "Boolean",             "kind": "boolean"},
    ],
    "label_groups": [
        {
            "id": "lg_header",
            "name": "Invoice Header",
            "instructions": "Extract the top-level invoice metadata printed at the header of the document.",
            "repeatable": False,
            "fields": [
                {"id": "fld_inv_num",    "name": "Invoice Number",   "type_id": "et_exact",  "instructions": "The unique invoice identifier, usually prefixed with a vendor code (e.g. ACM-2024-00891)."},
                {"id": "fld_inv_date",   "name": "Invoice Date",     "type_id": "et_date",   "instructions": "The date the invoice was issued. Return as YYYY-MM-DD."},
                {"id": "fld_due_date",   "name": "Due Date",         "type_id": "et_date",   "instructions": "The payment due date. Return as YYYY-MM-DD."},
                {"id": "fld_po_num",     "name": "PO Number",        "type_id": "et_exact",  "instructions": "The buyer purchase order number referenced on this invoice."},
                {"id": "fld_pay_terms",  "name": "Payment Terms",    "type_id": "et_exact",  "instructions": "Terms such as Net 30, Net 15, or Due on Receipt."},
                {"id": "fld_currency",   "name": "Currency",         "type_id": "et_exact",  "instructions": "Three-letter ISO currency code (e.g. USD, EUR)."},
            ],
        },
        {
            "id": "lg_vendor",
            "name": "Vendor Details",
            "instructions": "Extract the vendor (seller) contact and identification details.",
            "repeatable": False,
            "fields": [
                {"id": "fld_vend_name",  "name": "Vendor Name",      "type_id": "et_exact",  "instructions": "Legal name of the vendor / supplier company."},
                {"id": "fld_vend_addr",  "name": "Vendor Address",   "type_id": "et_exact",  "instructions": "Full mailing address of the vendor including street, city, state, ZIP."},
                {"id": "fld_vend_email", "name": "Vendor Email",     "type_id": "et_exact",  "instructions": "Billing or accounts-receivable email address of the vendor."},
                {"id": "fld_vend_phone", "name": "Vendor Phone",     "type_id": "et_exact",  "instructions": "Phone number of the vendor."},
            ],
        },
        {
            "id": "lg_billto",
            "name": "Bill To",
            "instructions": "Extract the buyer / bill-to party name and address.",
            "repeatable": False,
            "fields": [
                {"id": "fld_bt_name",    "name": "Bill-To Name",     "type_id": "et_exact",  "instructions": "Name of the billing entity or department."},
                {"id": "fld_bt_addr",    "name": "Bill-To Address",  "type_id": "et_exact",  "instructions": "Full mailing address of the bill-to party."},
            ],
        },
        {
            "id": "lg_totals",
            "name": "Invoice Totals",
            "instructions": "Extract the financial summary fields from the totals section.",
            "repeatable": False,
            "fields": [
                {"id": "fld_subtotal",   "name": "Subtotal",         "type_id": "et_money",  "instructions": "Sum before tax. Normalise to decimal (e.g. 10,300.00 USD)."},
                {"id": "fld_tax_rate",   "name": "Tax Rate",         "type_id": "et_number", "instructions": "Tax percentage rate applied. Return as a plain number (e.g. 8.5)."},
                {"id": "fld_tax_amount", "name": "Tax Amount",       "type_id": "et_money",  "instructions": "Dollar amount of tax charged."},
                {"id": "fld_total",      "name": "Total Due",        "type_id": "et_money",  "instructions": "Final amount due including tax. This is the amount to be paid."},
            ],
        },
        {
            "id": "lg_lineitems",
            "name": "Line Items",
            "instructions": "Extract each individual product or service line from the invoice table.",
            "repeatable": True,
            "fields": [
                {"id": "fld_li_desc",    "name": "Description",      "type_id": "et_exact",  "instructions": "Description of the product or service on this line."},
                {"id": "fld_li_qty",     "name": "Quantity",         "type_id": "et_number", "instructions": "Number of units for this line item."},
                {"id": "fld_li_price",   "name": "Unit Price",       "type_id": "et_money",  "instructions": "Price per unit for this line."},
                {"id": "fld_li_total",   "name": "Line Total",       "type_id": "et_money",  "instructions": "Total for this line (qty × unit price)."},
            ],
        },
    ],
}

# ──────────────────────────────────────────────────────────────
# STEP 2: Document registry (simulated "upload")
# ──────────────────────────────────────────────────────────────

def make_doc_id(filename: str) -> str:
    h = hashlib.md5(filename.encode()).hexdigest()
    return f"{h[:16]}.{h[16:]}"

with open(os.path.join(DOCS_DIR, "manifest.json")) as f:
    manifest = json.load(f)

DOCUMENTS = []
for m in manifest:
    DOCUMENTS.append({
        "DocumentId": make_doc_id(m["filename"]),
        "Filename": m["filename"],
        "InvoiceId": m["id"],   # internal link to ground truth
        "AttachmentRef": f"attach/{make_doc_id(m['filename'])}",
        "UploadedAt": "2024-03-30T09:05:00Z",
    })

DOC_BY_ID = {d["DocumentId"]: d for d in DOCUMENTS}

# ──────────────────────────────────────────────────────────────
# STEP 3: Simulated AI predictions (with realistic noise)
# ──────────────────────────────────────────────────────────────
# Noise profile (per field type):
#   - Exact text: 5% chance of OCR garble, 3% wrong value
#   - Date: 2% wrong format
#   - Money: 3% off-by-one digit, 2% wrong value
#   - Number: 5% rounding error
#   - Boolean: 8% flip
# One document (inv_003) will have a deliberately missing tax_rate field (tax-exempt)

def add_ocr_noise(value: str) -> str:
    """Simulate OCR character-level garbling."""
    subs = {"O": "0", "l": "1", "I": "1", "0": "O", "5": "S", "6": "G", "a": "á", "e": "é"}
    chars = list(value)
    # Garble 1-2 random chars
    n = random.randint(1, min(2, len(chars)))
    for _ in range(n):
        i = random.randint(0, len(chars) - 1)
        c = chars[i]
        if c in subs:
            chars[i] = subs[c]
    return "".join(chars)


def simulate_money(value: float, noise: bool = False) -> str:
    if noise:
        # off-by one digit noise
        value = value * random.choice([0.1, 10, 0.9, 1.1])
    return f"{value:,.2f} USD"


def simulate_predictions(doc: dict) -> dict:
    """Generate IXP-style predictions for one document."""
    inv_id = doc["InvoiceId"]
    gt = GROUND_TRUTH[inv_id]
    doc_id = doc["DocumentId"]

    labels = []

    # ── Invoice Header ──
    header_fields = []
    def hfield(fid, value, garble=False, wrong=None):
        if wrong:
            val = wrong
        elif garble:
            val = add_ocr_noise(str(value))
        else:
            val = str(value)
        header_fields.append({"FieldId": fid, "FieldName": fid_to_name(fid), "FormattedValue": val})

    hfield("fld_inv_num",   gt["invoice_number"],
           garble=(inv_id == "inv_002" and random.random() < 0.6))
    hfield("fld_inv_date",  gt["invoice_date"])
    hfield("fld_due_date",  gt["due_date"])
    hfield("fld_po_num",    gt["po_number"],
           garble=(inv_id == "inv_004" and random.random() < 0.5))
    hfield("fld_pay_terms", gt["payment_terms"])
    hfield("fld_currency",  gt["currency"])
    labels.append({"Name": "Invoice Header", "Occurrence": 0, "Fields": header_fields})

    # ── Vendor Details ──
    vendor_fields = [
        {"FieldId": "fld_vend_name",  "FieldName": "Vendor Name",    "FormattedValue": gt["vendor_name"]},
        {"FieldId": "fld_vend_addr",  "FieldName": "Vendor Address", "FormattedValue": gt["vendor_address"].replace("\n", ", ")},
        {"FieldId": "fld_vend_email", "FieldName": "Vendor Email",   "FormattedValue": gt["vendor_email"]},
        {"FieldId": "fld_vend_phone", "FieldName": "Vendor Phone",   "FormattedValue": gt["vendor_phone"]},
    ]
    # inv_005: phone OCR garble
    if inv_id == "inv_005":
        vendor_fields[3]["FormattedValue"] = add_ocr_noise(gt["vendor_phone"])
    labels.append({"Name": "Vendor Details", "Occurrence": 0, "Fields": vendor_fields})

    # ── Bill To ──
    bill_fields = [
        {"FieldId": "fld_bt_name", "FieldName": "Bill-To Name",    "FormattedValue": gt["bill_to_name"]},
        {"FieldId": "fld_bt_addr", "FieldName": "Bill-To Address", "FormattedValue": gt["bill_to_address"].replace("\n", ", ")},
    ]
    labels.append({"Name": "Bill To", "Occurrence": 0, "Fields": bill_fields})

    # ── Invoice Totals ──
    # inv_003 is tax-exempt → IXP predicts empty for tax_rate and tax_amount
    if inv_id == "inv_003":
        totals_fields = [
            {"FieldId": "fld_subtotal",   "FieldName": "Subtotal",    "FormattedValue": simulate_money(gt["subtotal"])},
            {"FieldId": "fld_tax_rate",   "FieldName": "Tax Rate",    "FormattedValue": ""},
            {"FieldId": "fld_tax_amount", "FieldName": "Tax Amount",  "FormattedValue": ""},
            {"FieldId": "fld_total",      "FieldName": "Total Due",   "FormattedValue": simulate_money(gt["total"])},
        ]
    # inv_001: total slightly wrong (noise — wrong value, not OCR)
    elif inv_id == "inv_001":
        totals_fields = [
            {"FieldId": "fld_subtotal",   "FieldName": "Subtotal",    "FormattedValue": simulate_money(gt["subtotal"])},
            {"FieldId": "fld_tax_rate",   "FieldName": "Tax Rate",    "FormattedValue": str(gt["tax_rate"])},
            {"FieldId": "fld_tax_amount", "FieldName": "Tax Amount",  "FormattedValue": simulate_money(gt["tax_amount"])},
            {"FieldId": "fld_total",      "FieldName": "Total Due",   "FormattedValue": simulate_money(gt["total"] + 100)},  # wrong!
        ]
    else:
        totals_fields = [
            {"FieldId": "fld_subtotal",   "FieldName": "Subtotal",    "FormattedValue": simulate_money(gt["subtotal"])},
            {"FieldId": "fld_tax_rate",   "FieldName": "Tax Rate",    "FormattedValue": str(gt["tax_rate"])},
            {"FieldId": "fld_tax_amount", "FieldName": "Tax Amount",  "FormattedValue": simulate_money(gt["tax_amount"])},
            {"FieldId": "fld_total",      "FieldName": "Total Due",   "FormattedValue": simulate_money(gt["total"])},
        ]
    labels.append({"Name": "Invoice Totals", "Occurrence": 0, "Fields": totals_fields})

    # ── Line Items (repeatable) ──
    for i, item in enumerate(gt["line_items"]):
        wrong_total = (inv_id == "inv_004" and i == 2)  # one line item total wrong on inv_004
        li_fields = [
            {"FieldId": "fld_li_desc",  "FieldName": "Description", "FormattedValue": item["description"]},
            {"FieldId": "fld_li_qty",   "FieldName": "Quantity",    "FormattedValue": str(item["qty"])},
            {"FieldId": "fld_li_price", "FieldName": "Unit Price",  "FormattedValue": simulate_money(item["unit_price"])},
            {"FieldId": "fld_li_total", "FieldName": "Line Total",  "FormattedValue": simulate_money(item["total"] + 50 if wrong_total else item["total"])},
        ]
        labels.append({"Name": "Line Items", "Occurrence": i, "Fields": li_fields})

    return {
        "DocumentId": doc_id,
        "Filename": doc["Filename"],
        "Labels": labels,
    }


def fid_to_name(fid: str) -> str:
    mapping = {
        "fld_inv_num": "Invoice Number", "fld_inv_date": "Invoice Date",
        "fld_due_date": "Due Date", "fld_po_num": "PO Number",
        "fld_pay_terms": "Payment Terms", "fld_currency": "Currency",
        "fld_vend_name": "Vendor Name", "fld_vend_addr": "Vendor Address",
        "fld_vend_email": "Vendor Email", "fld_vend_phone": "Vendor Phone",
        "fld_bt_name": "Bill-To Name", "fld_bt_addr": "Bill-To Address",
        "fld_subtotal": "Subtotal", "fld_tax_rate": "Tax Rate",
        "fld_tax_amount": "Tax Amount", "fld_total": "Total Due",
        "fld_li_desc": "Description", "fld_li_qty": "Quantity",
        "fld_li_price": "Unit Price", "fld_li_total": "Line Total",
    }
    return mapping.get(fid, fid)


ALL_PREDICTIONS = {}
for doc in DOCUMENTS:
    pred = simulate_predictions(doc)
    ALL_PREDICTIONS[doc["DocumentId"]] = pred
    pred_path = os.path.join(TMP_DIR, "predictions", f"{doc['DocumentId']}.json")
    with open(pred_path, "w") as f:
        json.dump({"Result": "Success", "Data": {"ProjectName": PROJECT["Name"],
                   "TotalDocuments": 1, "DocumentsWithPredictions": 1,
                   "Predictions": [pred]}}, f, indent=2)

# ──────────────────────────────────────────────────────────────
# STEP 4: Auto-reviewer (simulates human review against GT)
# ──────────────────────────────────────────────────────────────

def review_document(doc: dict, pred: dict) -> dict:
    """
    Compare each predicted field to ground truth.
    Returns a labelling decision record with verdicts and confirm/correct/missing lists.
    """
    inv_id = doc["InvoiceId"]
    gt = GROUND_TRUTH[inv_id]
    doc_id = doc["DocumentId"]

    confirmed_fields = []
    corrected_fields = []   # [{"field_id": id, "value": corrected_str}]
    missing_fields = []
    not_confirmed_fields = []

    gt_by_field = build_gt_lookup(gt)

    for label in pred["Labels"]:
        group_name = label["Name"]
        occurrence = label["Occurrence"]
        is_repeatable = (group_name == "Line Items")

        for field in label["Fields"]:
            fid = field["FieldId"]
            predicted = field["FormattedValue"]
            gt_val = gt_by_field.get((group_name, occurrence, fid))

            # ── Decision logic ──
            if predicted == "" or predicted is None:
                # IXP predicted nothing
                if gt_val is None or gt_val == "":
                    # Genuinely missing
                    missing_fields.append({"field_id": fid, "group": group_name, "occurrence": occurrence, "name": field["FieldName"]})
                else:
                    # IXP missed a real value — leave unannotated
                    not_confirmed_fields.append({
                        "field_id": fid, "group": group_name, "occurrence": occurrence,
                        "name": field["FieldName"], "predicted": "(empty)", "actual": str(gt_val),
                        "reason": "IXP predicted empty but value exists in document"
                    })
            else:
                gt_str = str(gt_val) if gt_val is not None else None
                norm_pred = normalize(predicted)
                norm_gt = normalize(gt_str) if gt_str else None

                if norm_gt is None:
                    # GT says field absent, IXP hallucinated a value
                    not_confirmed_fields.append({
                        "field_id": fid, "group": group_name, "occurrence": occurrence,
                        "name": field["FieldName"], "predicted": predicted, "actual": "(absent)",
                        "reason": "IXP predicted a value but field is not present in document"
                    })
                elif norm_pred == norm_gt:
                    confirmed_fields.append({"field_id": fid, "group": group_name, "occurrence": occurrence, "name": field["FieldName"]})
                elif is_ocr_garble(predicted, gt_str):
                    # Same characters, just mangled — OCR correction
                    corrected_fields.append({
                        "field_id": fid, "group": group_name, "occurrence": occurrence,
                        "name": field["FieldName"], "predicted": predicted, "corrected": gt_str
                    })
                    confirmed_fields.append({"field_id": fid, "group": group_name, "occurrence": occurrence, "name": field["FieldName"]})
                else:
                    not_confirmed_fields.append({
                        "field_id": fid, "group": group_name, "occurrence": occurrence,
                        "name": field["FieldName"], "predicted": predicted, "actual": str(gt_val),
                        "reason": "Predicted value does not match document"
                    })

    return {
        "doc_id": doc_id,
        "filename": doc["Filename"],
        "inv_id": inv_id,
        "confirmed": confirmed_fields,
        "corrected": corrected_fields,
        "missing": missing_fields,
        "not_confirmed": not_confirmed_fields,
    }


def build_gt_lookup(gt: dict) -> dict:
    """Build a (group_name, occurrence, field_id) → value lookup."""
    lookup = {}
    # Header
    for fid, key in [
        ("fld_inv_num", "invoice_number"), ("fld_inv_date", "invoice_date"),
        ("fld_due_date", "due_date"), ("fld_po_num", "po_number"),
        ("fld_pay_terms", "payment_terms"), ("fld_currency", "currency"),
    ]:
        lookup[("Invoice Header", 0, fid)] = gt[key]
    # Vendor
    lookup[("Vendor Details", 0, "fld_vend_name")] = gt["vendor_name"]
    lookup[("Vendor Details", 0, "fld_vend_addr")] = gt["vendor_address"].replace("\n", ", ")
    lookup[("Vendor Details", 0, "fld_vend_email")] = gt["vendor_email"]
    lookup[("Vendor Details", 0, "fld_vend_phone")] = gt["vendor_phone"]
    # Bill-To
    lookup[("Bill To", 0, "fld_bt_name")] = gt["bill_to_name"]
    lookup[("Bill To", 0, "fld_bt_addr")] = gt["bill_to_address"].replace("\n", ", ")
    # Totals
    lookup[("Invoice Totals", 0, "fld_subtotal")] = simulate_money(gt["subtotal"])
    lookup[("Invoice Totals", 0, "fld_tax_rate")] = str(gt["tax_rate"]) if gt["tax_rate"] > 0 else ""
    lookup[("Invoice Totals", 0, "fld_tax_amount")] = simulate_money(gt["tax_amount"]) if gt["tax_rate"] > 0 else ""
    lookup[("Invoice Totals", 0, "fld_total")] = simulate_money(gt["total"])
    # Line items
    for i, item in enumerate(gt["line_items"]):
        lookup[("Line Items", i, "fld_li_desc")]  = item["description"]
        lookup[("Line Items", i, "fld_li_qty")]   = str(item["qty"])
        lookup[("Line Items", i, "fld_li_price")] = simulate_money(item["unit_price"])
        lookup[("Line Items", i, "fld_li_total")] = simulate_money(item["total"])
    return lookup


def normalize(val: str) -> str:
    """Normalize strings for fuzzy comparison."""
    if val is None:
        return ""
    return val.strip().lower().replace(",", "").replace("  ", " ")


def is_ocr_garble(predicted: str, actual: str) -> bool:
    """Detect if predicted is an OCR-garbled version of actual."""
    if not predicted or not actual:
        return False
    if len(predicted) != len(actual):
        return False
    # Count char-level diffs
    diffs = sum(1 for a, b in zip(predicted, actual) if a != b)
    return 0 < diffs <= 2 and (diffs / len(actual)) < 0.3


# Run review on all documents
ALL_LABELLINGS = {}
for doc in DOCUMENTS:
    pred = ALL_PREDICTIONS[doc["DocumentId"]]
    decision = review_document(doc, pred)
    ALL_LABELLINGS[doc["DocumentId"]] = decision
    label_path = os.path.join(TMP_DIR, "labellings", f"{doc['DocumentId']}.json")
    with open(label_path, "w") as f:
        json.dump(decision, f, indent=2)

# ──────────────────────────────────────────────────────────────
# STEP 5: Metrics computation
# ──────────────────────────────────────────────────────────────

def compute_metrics(labellings: dict) -> dict:
    """Compute F1/Precision/Recall per field group and overall."""
    group_stats = {}
    field_stats = {}

    for doc_id, lab in labellings.items():
        total_predicted = 0
        total_confirmed = 0
        for pred_label in ALL_PREDICTIONS[doc_id]["Labels"]:
            group = pred_label["Name"]
            occ = pred_label["Occurrence"]
            for f in pred_label["Fields"]:
                fid = f["FieldId"]
                predicted = f["FormattedValue"]
                key = fid

                if group not in group_stats:
                    group_stats[group] = {"tp": 0, "fp": 0, "fn": 0, "docs": set()}
                if fid not in field_stats:
                    field_stats[fid] = {"name": f["FieldName"], "group": group, "tp": 0, "fp": 0, "fn": 0, "annotations": 0}

                confirmed_ids = {c["field_id"] for c in lab["confirmed"]}
                not_conf_ids  = {n["field_id"] for n in lab["not_confirmed"]}

                group_stats[group]["docs"].add(doc_id)
                field_stats[fid]["annotations"] += 1

                if fid in confirmed_ids:
                    group_stats[group]["tp"] += 1
                    field_stats[fid]["tp"] += 1
                elif predicted and fid in not_conf_ids:
                    group_stats[group]["fp"] += 1
                    field_stats[fid]["fp"] += 1
                    group_stats[group]["fn"] += 1
                    field_stats[fid]["fn"] += 1

    def f1_precision_recall(tp, fp, fn):
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        return round(f1, 4), round(precision, 4), round(recall, 4)

    groups_out = []
    total_tp, total_fp, total_fn = 0, 0, 0
    for grp, s in group_stats.items():
        f1, prec, rec = f1_precision_recall(s["tp"], s["fp"], s["fn"])
        total_tp += s["tp"]; total_fp += s["fp"]; total_fn += s["fn"]
        groups_out.append({
            "FieldGroup": grp, "F1": f1, "Precision": prec, "Recall": rec,
            "Documents": len(s["docs"]),
            "TP": s["tp"], "FP": s["fp"], "FN": s["fn"],
        })

    fields_out = []
    for fid, s in field_stats.items():
        f1, prec, rec = f1_precision_recall(s["tp"], s["fp"], s["fn"])
        fields_out.append({
            "FieldId": fid, "FieldName": s["name"], "FieldGroup": s["group"],
            "F1": f1, "Precision": prec, "Recall": rec,
            "Annotations": s["annotations"], "TP": s["tp"], "FP": s["fp"], "FN": s["fn"],
        })
    fields_out.sort(key=lambda x: x["F1"])

    overall_f1, overall_prec, overall_rec = f1_precision_recall(total_tp, total_fp, total_fn)

    return {
        "ModelVersion": 1,
        "TrainedTime": "2024-03-30T09:45:00Z",
        "ProjectScore": overall_f1,
        "ProjectScoreQuality": "Good" if overall_f1 >= 0.85 else ("Fair" if overall_f1 >= 0.70 else "Poor"),
        "ValidatedDocuments": len(labellings),
        "FieldGroups": sorted(groups_out, key=lambda x: x["F1"]),
        "Fields": fields_out,
    }

METRICS = compute_metrics(ALL_LABELLINGS)

# Save all artefacts
with open(os.path.join(TMP_DIR, "taxonomies", "v1.json"), "w") as f:
    json.dump({"Result": "Success", "Data": {"status": "active", "dataset": TAXONOMY}}, f, indent=2)

with open(os.path.join(TMP_DIR, "project.json"), "w") as f:
    json.dump({"Result": "Success", "Data": PROJECT}, f, indent=2)

with open(os.path.join(TMP_DIR, "documents.json"), "w") as f:
    json.dump({"Result": "Success", "Data": {
        "Documents": DOCUMENTS, "Total": len(DOCUMENTS), "Offset": 0, "Limit": 50
    }}, f, indent=2)

with open(os.path.join(TMP_DIR, "metrics.json"), "w") as f:
    json.dump({"Result": "Success", "Data": METRICS}, f, indent=2)

print("  ✓  Project + taxonomy defined")
print(f"  ✓  {len(DOCUMENTS)} documents registered")
print(f"  ✓  Predictions generated for all documents")
print(f"  ✓  Labelling review complete")
print(f"  ✓  Metrics computed  (ProjectScore: {METRICS['ProjectScore']:.4f})")

# Export for report generator
PIPELINE_STATE = {
    "project": PROJECT,
    "taxonomy": TAXONOMY,
    "documents": DOCUMENTS,
    "predictions": ALL_PREDICTIONS,
    "labellings": ALL_LABELLINGS,
    "metrics": METRICS,
}
with open(os.path.join(BASE, "pipeline_state.json"), "w") as f:
    json.dump(PIPELINE_STATE, f, indent=2)

print(f"\n  Artefacts saved → {TMP_DIR}/")
print(f"  Pipeline state  → {BASE}/pipeline_state.json")
