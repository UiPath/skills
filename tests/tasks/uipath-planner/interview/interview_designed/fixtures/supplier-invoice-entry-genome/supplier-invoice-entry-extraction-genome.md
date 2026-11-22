<!-- UIPATH-AUTOMATION-GENOME: component | This file is a build specification for one UiPath automation project.
     To build it, invoke the uipath-genome skill: it asks the configuration questions,
     then invokes the skills referenced in Build With. Do NOT execute these steps directly, and do NOT
     start from a Build With skill. To change it, invoke the uipath-planner skill. -->

# Genome: SupplierInvoiceEntry_Extraction

> An IXP extraction model that reads supplier, invoice number, invoice date, purchase order number and total from a supplier invoice PDF, in any supplier's layout, with a confidence for each field.

> **This is a UiPath automation blueprint.** Do not execute these steps directly. Build it with the **uipath-genome** skill, which hands each part to the skill listed in **Build With** below.

> Part of: [Supplier Invoice Entry](../supplier-invoice-entry-genome.md) — the extraction model that component 2 calls once per invoice, before the PO match.

## Overview

Every Contoso supplier sends its invoices in its own PDF layout, so the fields cannot be read from fixed positions. This model is the extraction step of supplier invoice entry. Given one supplier invoice PDF, it returns the five fields that AP needs to match and post the invoice, each with a confidence. The RPA process (component 2) sets aside any invoice with a field below its confidence threshold, so a wrong reading is never posted.

The model is new and reusable by other AP processes. It is built, trained and deployed before component 2, which calls it.

## Target Applications

| Application | Role | Notes |
|-------------|------|-------|
| Supplier invoice PDFs | Input source | One invoice per PDF; one layout per supplier; digital or scanned |

## Build With

| Step | Skill | Rationale |
|------|-------|-----------|
| Steps 1–3 | `uipath-ixp` | The SDD §9 places extraction in an IXP model because the input is semi-structured, with one layout per supplier. A template or rule extraction in the RPA project would need a template per supplier |

## Platform Dependencies

### Document Understanding

| Resource | Used by | Purpose |
|----------|---------|---------|
| IXP project and deployed model version, named per Configuration Question 1 | steps 1–3, called by component 2 | Field extraction from supplier invoice PDFs |

## Interface

- **Inputs:** one supplier invoice PDF, sent by component 2 (process genome Handoffs row 2).
- **Outputs:** Supplier: Text, InvoiceNumber: Text, InvoiceDate: Date, PONumber: Text, Total: Decimal, each with a confidence from 0 to 1. A field not found is returned empty with its confidence.
- **Side effects:** none.

## Configuration Questions

1. Which name does the IXP project and its deployment take, and which Orchestrator folder is the model deployed to? (setting; default: `SupplierInvoiceEntry_Extraction`, deployed to the process folder of component 2)

## Open Decisions

No open decisions.

## Workflow

1. **Trigger: called per invoice** — component 2 sends one invoice PDF to the deployed model.
2. **Extract the invoice fields** (input: the PDF; output: five fields with their confidences):
   a. Supplier — the supplier's name as printed on the invoice (the issuer, not Contoso).
   b. Invoice number — the supplier's own invoice number.
   c. Invoice date — the date of issue, returned as a date.
   d. PO number — the Contoso purchase order number the invoice cites.
   e. Total — the invoice total, returned as a decimal amount without currency symbol or thousands separators.
3. **Return the result** (input: the extracted values; output: the five fields and a confidence per field): return every field with its confidence. A field the model cannot find is returned empty, which component 2 sets aside as Unreadable.

The model is trained on supplier invoices covering each supplier layout in use, with the five fields above as its taxonomy (training documents: process D1).

## Business Rules

### Step 2: Extract the invoice fields
- The supplier is the party that issued the invoice, never Contoso as the addressee.
- Exactly one value per field per invoice: the invoice total, not a line or a subtotal; the invoice date, not a due or delivery date.

## Error Handling

No error handling: a failure stops the run.

## Transactional Shape

Not transactional: an IXP model; one invoice's extraction is called per item by component 2, which owns the item's lifecycle.

## Acceptance Criteria

1. Given a readable supplier invoice PDF, the model returns supplier, invoice number, invoice date, PO number and total, each with a confidence between 0 and 1.
2. Given invoices from at least 5 different supplier layouts, the five fields are correct on at least 95% of readable invoices (test data: process D1).
3. Given an invoice that does not cite a purchase order number, the PO number comes back empty or below the confidence threshold, never with another number from the page.
4. Given an invoice showing a due date and a delivery date beside the invoice date, the model returns the invoice date.
5. Given an invoice with subtotal, tax and total lines, the model returns the total as a decimal with no currency symbol.

## Complexity

simple

## Tags

accounts-payable, supplier-invoices, ixp, document-understanding, extraction
