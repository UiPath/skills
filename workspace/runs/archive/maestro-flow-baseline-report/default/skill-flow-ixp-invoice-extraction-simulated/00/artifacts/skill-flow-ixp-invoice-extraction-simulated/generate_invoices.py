"""
Generate realistic mock vendor invoices as PDFs for IXP simulation.
Creates 5 diverse invoices with different vendors, layouts, and complexity levels.
"""
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas

INVOICES = [
    {
        "id": "inv_001",
        "filename": "invoice_acme_tech_001.pdf",
        "vendor_name": "Acme Technology Solutions Inc.",
        "vendor_address": "450 Silicon Valley Blvd, Suite 200\nSan Jose, CA 95110",
        "vendor_email": "billing@acmetech.com",
        "vendor_phone": "+1 (408) 555-0192",
        "bill_to_name": "GlobalCorp Procurement",
        "bill_to_address": "1200 Corporate Plaza, Floor 8\nNew York, NY 10001",
        "invoice_number": "ACM-2024-00891",
        "invoice_date": "2024-03-15",
        "due_date": "2024-04-14",
        "po_number": "PO-GC-44720",
        "payment_terms": "Net 30",
        "currency": "USD",
        "line_items": [
            {"description": "Enterprise SaaS License — Q2 2024", "qty": 50, "unit_price": 120.00, "total": 6000.00},
            {"description": "Professional Services — System Integration", "qty": 8, "unit_price": 250.00, "total": 2000.00},
            {"description": "24/7 Premium Support Package", "qty": 1, "unit_price": 1500.00, "total": 1500.00},
            {"description": "On-site Training (2 days)", "qty": 2, "unit_price": 400.00, "total": 800.00},
        ],
        "subtotal": 10300.00,
        "tax_rate": 8.5,
        "tax_amount": 875.50,
        "total": 11175.50,
        "notes": "Please reference invoice number in payment. Wire transfer preferred.",
    },
    {
        "id": "inv_002",
        "filename": "invoice_summit_supplies_002.pdf",
        "vendor_name": "Summit Office Supplies Ltd.",
        "vendor_address": "88 Commerce Street\nChicago, IL 60601",
        "vendor_email": "accounts@summitsupplies.com",
        "vendor_phone": "+1 (312) 555-7834",
        "bill_to_name": "GlobalCorp Facilities",
        "bill_to_address": "1200 Corporate Plaza\nNew York, NY 10001",
        "invoice_number": "SOS-INV-20240312",
        "invoice_date": "2024-03-12",
        "due_date": "2024-03-27",
        "po_number": "PO-GC-44650",
        "payment_terms": "Net 15",
        "currency": "USD",
        "line_items": [
            {"description": "A4 Copy Paper (Case of 10 reams)", "qty": 20, "unit_price": 42.50, "total": 850.00},
            {"description": "Ergonomic Office Chair — Model EX500", "qty": 5, "unit_price": 389.00, "total": 1945.00},
            {"description": "Standing Desk Converter", "qty": 3, "unit_price": 215.00, "total": 645.00},
            {"description": "Monitor Arm Dual Mount", "qty": 5, "unit_price": 89.99, "total": 449.95},
            {"description": "USB-C Hub 7-port", "qty": 10, "unit_price": 34.99, "total": 349.90},
        ],
        "subtotal": 4239.85,
        "tax_rate": 10.25,
        "tax_amount": 434.59,
        "total": 4674.44,
        "notes": "Delivery within 5-7 business days. Shipping included.",
    },
    {
        "id": "inv_003",
        "filename": "invoice_rapid_logistics_003.pdf",
        "vendor_name": "Rapid Logistics & Freight Co.",
        "vendor_address": "7200 Industrial Park Way\nDallas, TX 75201",
        "vendor_email": "invoices@rapidlogistics.com",
        "vendor_phone": "+1 (214) 555-3301",
        "bill_to_name": "GlobalCorp Operations",
        "bill_to_address": "500 Warehouse Drive\nElizabeth, NJ 07201",
        "invoice_number": "RL-2024-8847",
        "invoice_date": "2024-03-20",
        "due_date": "2024-04-19",
        "po_number": "PO-GC-44801",
        "payment_terms": "Net 30",
        "currency": "USD",
        "line_items": [
            {"description": "Freight Shipment — Chicago to Newark (FTL)", "qty": 1, "unit_price": 3200.00, "total": 3200.00},
            {"description": "Hazmat Handling Surcharge", "qty": 1, "unit_price": 450.00, "total": 450.00},
            {"description": "Fuel Surcharge (18% of base freight)", "qty": 1, "unit_price": 576.00, "total": 576.00},
            {"description": "Liftgate Service", "qty": 1, "unit_price": 125.00, "total": 125.00},
        ],
        "subtotal": 4351.00,
        "tax_rate": 0.0,
        "tax_amount": 0.00,
        "total": 4351.00,
        "notes": "Freight services are tax-exempt per TX Code 151.335. Bill of Lading: BOL-2024-88471.",
    },
    {
        "id": "inv_004",
        "filename": "invoice_cloudwave_004.pdf",
        "vendor_name": "CloudWave Infrastructure LLC",
        "vendor_address": "1 Cloud Campus Drive\nSeattle, WA 98101",
        "vendor_email": "billing@cloudwave.io",
        "vendor_phone": "+1 (206) 555-9020",
        "bill_to_name": "GlobalCorp IT Department",
        "bill_to_address": "1200 Corporate Plaza, Floor 12\nNew York, NY 10001",
        "invoice_number": "CW-0029541",
        "invoice_date": "2024-03-01",
        "due_date": "2024-03-31",
        "po_number": "PO-GC-44501",
        "payment_terms": "Due on Receipt",
        "currency": "USD",
        "line_items": [
            {"description": "Cloud Compute — 500 vCPU-hours", "qty": 500, "unit_price": 0.096, "total": 48.00},
            {"description": "Cloud Storage — 50 TB (March 2024)", "qty": 50, "unit_price": 23.00, "total": 1150.00},
            {"description": "Data Transfer Egress — 12 TB", "qty": 12, "unit_price": 90.00, "total": 1080.00},
            {"description": "Managed Kubernetes Service (3 clusters)", "qty": 3, "unit_price": 150.00, "total": 450.00},
            {"description": "CDN Bandwidth — 8 TB", "qty": 8, "unit_price": 85.00, "total": 680.00},
            {"description": "DDoS Protection — Enterprise Tier", "qty": 1, "unit_price": 500.00, "total": 500.00},
        ],
        "subtotal": 3908.00,
        "tax_rate": 10.1,
        "tax_amount": 394.71,
        "total": 4302.71,
        "notes": "Usage-based billing. Detailed usage report attached. Auto-pay enabled.",
    },
    {
        "id": "inv_005",
        "filename": "invoice_meridian_consulting_005.pdf",
        "vendor_name": "Meridian Business Consulting Group",
        "vendor_address": "333 Madison Avenue, 22nd Floor\nNew York, NY 10017",
        "vendor_email": "finance@meridianconsulting.com",
        "vendor_phone": "+1 (212) 555-4400",
        "bill_to_name": "GlobalCorp Executive Office",
        "bill_to_address": "1200 Corporate Plaza, Floor 20\nNew York, NY 10001",
        "invoice_number": "MCG-2024-Q1-047",
        "invoice_date": "2024-03-29",
        "due_date": "2024-04-28",
        "po_number": "PO-GC-44900",
        "payment_terms": "Net 30",
        "currency": "USD",
        "line_items": [
            {"description": "Strategic Planning Workshops (Week of March 11)", "qty": 3, "unit_price": 4500.00, "total": 13500.00},
            {"description": "Market Analysis Report — APAC Expansion", "qty": 1, "unit_price": 8000.00, "total": 8000.00},
            {"description": "Executive Coaching Sessions — 12 hours", "qty": 12, "unit_price": 600.00, "total": 7200.00},
            {"description": "Travel & Expenses (receipts attached)", "qty": 1, "unit_price": 2340.75, "total": 2340.75},
        ],
        "subtotal": 31040.75,
        "tax_rate": 8.875,
        "tax_amount": 2754.87,
        "total": 33795.62,
        "notes": "Engagement: GlobalCorp Q1 2024 Strategy Initiative. SOW ref: MCG-SOW-2024-003. Net 30 from invoice date.",
    },
]


def build_invoice_pdf(inv: dict, output_dir: str) -> str:
    """Render a single invoice dict to a PDF file. Returns the output path."""
    out_path = os.path.join(output_dir, inv["filename"])

    doc = SimpleDocTemplate(
        out_path,
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontSize = 9

    h1 = ParagraphStyle("h1", fontSize=22, leading=26, textColor=colors.HexColor("#1a3a5c"), spaceAfter=2)
    h2 = ParagraphStyle("h2", fontSize=11, leading=14, textColor=colors.HexColor("#1a3a5c"), spaceBefore=10, spaceAfter=4)
    small = ParagraphStyle("small", fontSize=8, leading=11, textColor=colors.HexColor("#555555"))
    right_align = ParagraphStyle("right", fontSize=9, alignment=TA_RIGHT)
    bold = ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold")
    note_style = ParagraphStyle("note", fontSize=8, textColor=colors.HexColor("#666666"), leading=11)

    story = []

    # ── Header row: vendor info left, INVOICE label right ──
    header_data = [
        [
            Paragraph(f"<b>{inv['vendor_name']}</b>", ParagraphStyle("vn", fontSize=13, textColor=colors.HexColor("#1a3a5c"))),
            Paragraph("INVOICE", h1),
        ],
        [
            Paragraph(inv["vendor_address"].replace("\n", "<br/>") +
                      f"<br/>{inv['vendor_email']}<br/>{inv['vendor_phone']}", small),
            Paragraph(
                f"<b>Invoice #:</b>  {inv['invoice_number']}<br/>"
                f"<b>Invoice Date:</b>  {inv['invoice_date']}<br/>"
                f"<b>Due Date:</b>  {inv['due_date']}<br/>"
                f"<b>PO Number:</b>  {inv['po_number']}",
                ParagraphStyle("meta", fontSize=9, alignment=TA_RIGHT, leading=14)
            ),
        ],
    ]
    header_tbl = Table(header_data, colWidths=[3.8 * inch, 3.4 * inch])
    header_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3a5c"), spaceAfter=10))

    # ── Bill-To ──
    bill_data = [
        [
            Paragraph("<b>BILL TO</b>", ParagraphStyle("lbl", fontSize=8, textColor=colors.HexColor("#888888"))),
            Paragraph("<b>PAYMENT TERMS</b>", ParagraphStyle("lbl", fontSize=8, textColor=colors.HexColor("#888888"))),
            Paragraph("<b>CURRENCY</b>", ParagraphStyle("lbl", fontSize=8, textColor=colors.HexColor("#888888"))),
        ],
        [
            Paragraph(f"<b>{inv['bill_to_name']}</b><br/>" + inv["bill_to_address"].replace("\n", "<br/>"), small),
            Paragraph(inv["payment_terms"], bold),
            Paragraph(inv["currency"], bold),
        ],
    ]
    bill_tbl = Table(bill_data, colWidths=[4.0 * inch, 1.8 * inch, 1.4 * inch])
    bill_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, colors.HexColor("#cccccc")),
    ]))
    story.append(bill_tbl)
    story.append(Spacer(1, 12))

    # ── Line items table ──
    story.append(Paragraph("LINE ITEMS", ParagraphStyle("lbl", fontSize=8, textColor=colors.HexColor("#888888"), spaceBefore=4, spaceAfter=4)))

    li_header = ["Description", "Qty", "Unit Price", "Amount"]
    li_rows = [li_header]
    for item in inv["line_items"]:
        li_rows.append([
            item["description"],
            str(item["qty"]),
            f"${item['unit_price']:,.2f}",
            f"${item['total']:,.2f}",
        ])

    li_tbl = Table(li_rows, colWidths=[4.2 * inch, 0.6 * inch, 1.1 * inch, 1.3 * inch])
    li_style = TableStyle([
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (-1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # Data rows
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, 0), 0, colors.white),
    ])
    li_tbl.setStyle(li_style)
    story.append(li_tbl)
    story.append(Spacer(1, 8))

    # ── Totals ──
    totals_rows = [
        ["", "Subtotal:", f"${inv['subtotal']:,.2f}"],
    ]
    if inv["tax_rate"] > 0:
        totals_rows.append(["", f"Tax ({inv['tax_rate']}%):", f"${inv['tax_amount']:,.2f}"])
    else:
        totals_rows.append(["", "Tax:", "Exempt"])
    totals_rows.append(["", "TOTAL DUE:", f"${inv['total']:,.2f}"])

    totals_tbl = Table(totals_rows, colWidths=[3.6 * inch, 1.9 * inch, 1.7 * inch])
    totals_tbl.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("FONTNAME", (1, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (1, -1), (-1, -1), 11),
        ("TEXTCOLOR", (1, -1), (-1, -1), colors.HexColor("#1a3a5c")),
        ("LINEABOVE", (1, -1), (-1, -1), 1, colors.HexColor("#1a3a5c")),
        ("BACKGROUND", (1, -1), (-1, -1), colors.HexColor("#eef3f8")),
    ]))
    story.append(totals_tbl)

    # ── Notes ──
    if inv.get("notes"):
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=6))
        story.append(Paragraph("<b>Notes:</b>", ParagraphStyle("nb", fontSize=8, textColor=colors.HexColor("#555555"), spaceAfter=2)))
        story.append(Paragraph(inv["notes"], note_style))

    # ── Footer ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=4))
    story.append(Paragraph(
        f"Thank you for your business. Questions? Contact {inv['vendor_email']} · {inv['vendor_phone']}",
        ParagraphStyle("footer", fontSize=7.5, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)
    ))

    doc.build(story)
    return out_path


def main():
    base = "/work/output/artifacts/skill-flow-ixp-invoice-extraction-simulated"
    docs_dir = os.path.join(base, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    manifest = []
    for inv in INVOICES:
        path = build_invoice_pdf(inv, docs_dir)
        size = os.path.getsize(path)
        manifest.append({
            "id": inv["id"],
            "filename": inv["filename"],
            "path": path,
            "size_bytes": size,
            "vendor_name": inv["vendor_name"],
            "invoice_number": inv["invoice_number"],
            "invoice_date": inv["invoice_date"],
            "due_date": inv["due_date"],
            "total": inv["total"],
            "currency": inv["currency"],
        })
        print(f"  ✓  {inv['filename']}  ({size:,} bytes)")

    manifest_path = os.path.join(base, "docs", "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Also save full invoice data for simulation use
    data_path = os.path.join(base, "docs", "invoice_data.json")
    with open(data_path, "w") as f:
        json.dump(INVOICES, f, indent=2)

    print(f"\n  {len(manifest)} invoices generated → {docs_dir}/")
    print(f"  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
