#!/usr/bin/env python3
"""Invoice extractor with prompt-engineering and schema defects."""

from pathlib import Path

from lowcode_scaffold import (
    apply_agent,
    equality_evaluator,
    write_baseline_lowcode_agent,
    write_evals,
)

INVOICE_ALIASES = ", ".join(f"'{a}'" for a in [
    "Invoice No", "Invoice #", "Inv No", "Inv. No.", "Inv #", "Invoice Number", "Invoice Nr", "Inv Nr",
    "Bill No", "Bill #", "Document No", "Doc #", "Reference No", "Ref #", "Factura No",
])

SYSTEM = f"""You are an invoice extraction agent. You read invoice text and extract the invoice data.

Always respond in JSON.
Do not guess values.
Do not skip line items.
Do not include currency symbols in the total.
Never translate vendor names.
Never round amounts.
Do not add fields.
Write your response as a friendly paragraph that summarizes the invoice for the accounts payable clerk.

If the document says {INVOICE_ALIASES}, treat the value after it as the invoice number.

For tenant ACME-PROD-EU, send totals above 5000 EUR to the approver group AP-APPROVERS-WEST."""

USER = "Invoice text:\n{{input.document_text}}\n\nPurchase order: {{input.purchase_order}}"

INPUT_SCHEMA = {
    "type": "object",
    "properties": {"document_text": {"type": "string"}, "text": {"type": "string"}},
    "required": ["document_text"],
}

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string", "description": "Invoice number."},
        "vendor": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "country": {"type": "string"}},
        },
        "total": {"type": "number", "description": "Invoice total."},
        "currency": {"type": "string", "description": "ISO 4217 currency code."},
        "line_items": {"type": "array", "items": {"type": "object"}},
    },
}


def main() -> None:
    project = write_baseline_lowcode_agent(Path("ReviewSol"))
    apply_agent(project, system=SYSTEM, user=USER, input_schema=INPUT_SCHEMA, output_schema=OUTPUT_SCHEMA,
                settings={"temperature": 0, "maxTokens": 4096, "maxIterations": 3})
    write_evals(
        project,
        [equality_evaluator("Invoice exact match")],
        [
            {"name": f"inv{i}", "inputs": {"document_text": doc},
             "expectedOutput": {"invoice_number": num, "total": total, "currency": cur}}
            for i, (doc, num, total, cur) in enumerate([
                ("Invoice No INV-1001 Vendor: Contoso GmbH Total: 1,200.00 EUR", "INV-1001", 1200.0, "EUR"),
                ("Inv # 2002 Vendor: Fabrikam Ltd Total: 89.50 GBP", "2002", 89.5, "GBP"),
                ("Bill No B-77 Vendor: Northwind Inc Total: 15,000.00 USD", "B-77", 15000.0, "USD"),
                ("Factura No F-3 Vendor: Tailspin SA Total: 410.00 EUR", "F-3", 410.0, "EUR"),
                ("Reference No R-9 Vendor: Litware Total: 0.00 EUR", "R-9", 0.0, "EUR"),
            ])
        ],
    )
    print("Injected extractor prompt scenario")


if __name__ == "__main__":
    main()
