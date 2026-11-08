"""Write specs/invoice_intake.json: accounts-payable invoice intake from an exported mailbox.

Shaped after the InvoiceIntake process in this repo's genome fixtures (tests/tasks/uipath-genome): unread AP mail, PDF attachments,
field extraction, a vendor check, an ERP posting queue, a failed folder and notifications. The scenarios are
built here and their answers computed by `run` from the rules the task's prompt states. Edit, then:

    python3 tests/tasks/uipath-rpa/offline/invoice_intake/specs/invoice_intake.py
"""
import json
import re
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEAD = "ap.lead@acme.example"


def message(sender, subject, status="Unread", date="2026-05-04"):
    return f"From: {sender}\r\nSubject: {subject}\r\nDate: {date}\r\nStatus: {status}\r\n\r\nPlease find our invoice attached.\r\n"


def invoice(vendor, number, total, extra=""):
    lines = [vendor, "123 Industrial Way", ""]
    if number is not None:
        lines.append(f"Invoice No: {number}")
    lines.append("Date: 2026-05-01")
    lines += ["", "Item | Qty | Amount", "Services | 1 | see total", extra, ""]
    if total is not None:
        lines.append(f"Total: {total} EUR")
    return "\n".join(lines) + "\n"


def vendors(rows):
    return "\n".join(["Vendor,CreditLimit", *(f"{v},{l}" for v, l in rows)]) + "\n"


def total_of(text):
    m = re.search(r"^Total:?\s*([\d,]+(?:\.\d+)?)", text, re.M)
    return None if m is None else Decimal(m.group(1).replace(",", ""))


def number_of(text):
    m = re.search(r"^Invoice No[:.]?\s*(\S+)", text, re.M)
    return None if m is None else m.group(1)


def money(d):
    return f"{d:.2f}"


def run(mailbox, vendor_csv):
    """The prompt's rules: the queue, the copies, the notifications, the counts and the warnings."""
    limits = {}
    for line in vendor_csv.splitlines()[1:]:
        if line.strip():
            v, limit = line.split(",")
            limits[v.strip().lower()] = (v.strip(), Decimal(limit.strip()))
    out = {"queue": [], "approved": {}, "failed": {}, "outbox": {}, "read": [], "counts": {"queued": 0, "rejected": 0, "missing": 0}, "warn": []}
    for mid in sorted({k.split("/")[0] for k in mailbox}):
        headers = dict(l.split(": ", 1) for l in mailbox[f"{mid}/message.txt"].split("\r\n\r\n")[0].split("\r\n"))
        if headers["Status"] != "Unread":
            continue
        pdfs = sorted(k.split("/", 1)[1] for k in mailbox if k.startswith(f"{mid}/") and k.lower().endswith(".pdf"))
        if not pdfs:
            out["counts"]["missing"] += 1
            out["outbox"][f"missing-{mid}.txt"] = [f"To: {headers['From']}", f"Subject: Missing attachment: {headers['Subject']}"]
        for name in pdfs:
            text = mailbox[f"{mid}/{name}"]
            vendor = next(l for l in text.splitlines() if l.strip()).strip()
            number, total = number_of(text), total_of(text)
            if number is None or total is None:
                reason = "Missing invoice number or total"
            elif vendor.lower() not in limits:
                reason = "Unknown vendor"
            elif total > limits[vendor.lower()][1]:
                reason = "Over credit limit"
            else:
                reason = None
            if reason is None:
                out["counts"]["queued"] += 1
                out["queue"].append(f"{number},{limits[vendor.lower()][0]},{money(total)},{mid}")
                out["approved"][f"{number}.pdf"] = text
            else:
                out["counts"]["rejected"] += 1
                base = name[: -len(".pdf")]
                out["failed"][f"{mid}-{name}"] = text
                out["outbox"][f"rejected-{mid}-{base}.txt"] = [f"To: {LEAD}", f"Subject: Rejected invoice {name}", reason]
                out["warn"].append(name)
        out["read"].append(mid)
    return out


def scenario(name, mailbox, vendor_csv, note):
    r = run(mailbox, vendor_csv)
    files = {f"mail/{k}": v for k, v in mailbox.items()}
    files["vendors.csv"] = vendor_csv
    expect = {"out/Posting/ERP_Queue.csv": {"lines": ["InvoiceNumber,Vendor,Total,MessageId", *r["queue"]]}}
    expect.update({f"out/Approved/{k}": v for k, v in r["approved"].items()})
    expect.update({f"out/Failed/{k}": v for k, v in r["failed"].items()})
    expect.update({f"out/Outbox/{k}": {"contains": v} for k, v in r["outbox"].items()})
    for mid in r["read"]:
        expect[f"mail/{mid}/message.txt"] = {"contains": ["Status: Read"]}
    for mid in sorted({k.split("/")[0] for k in mailbox}) :
        if mid not in r["read"]:
            expect[f"mail/{mid}/message.txt"] = mailbox[f"{mid}/message.txt"]
    s = {
        "name": name,
        "note": note,
        "files": files,
        "input": {"in_MailFolder": "${WORKDIR}/mail", "in_VendorsFile": "${WORKDIR}/vendors.csv", "in_OutputFolder": "${WORKDIR}/out"},
        "expect_outputs": {"out_Queued": r["counts"]["queued"], "out_Rejected": r["counts"]["rejected"], "out_MissingAttachment": r["counts"]["missing"]},
        "expect_files": expect,
        "expect_log_counts": [{"level": "Warn", "mentions": [w[: -len(".pdf")]], "count": 1} for w in r["warn"]],
    }
    # Only the prompt's own logging is graded: a warning per rejected invoice, naming it. A run may warn about
    # other things too (a message with no PDF, say), so no scenario forbids warnings.
    return s


VENDORS = vendors([("Contoso Ltd", "5000"), ("Fabrikam GmbH", "12,000.00".replace(",", "")), ("Northwind Traders", "800")])

SCENARIOS = [
    scenario(
        "approved-invoices-are-queued",
        {
            "M-001/message.txt": message("billing@contoso.example", "Invoice INV-1001"),
            "M-001/INV-1001.pdf": invoice("Contoso Ltd", "INV-1001", "1,250.50"),
            "M-002/message.txt": message("ar@fabrikam.example", "May invoices"),
            "M-002/fab-77.pdf": invoice("Fabrikam GmbH", "FB-77", "9,999.99"),
            "M-002/fab-78.pdf": invoice("  fabrikam gmbh", "FB-78", "10.00"),
            "M-002/terms.docx": "not an invoice\n",
            "M-003/message.txt": message("billing@contoso.example", "Invoice INV-0999", status="Read"),
            "M-003/INV-0999.pdf": invoice("Contoso Ltd", "INV-0999", "100.00"),
        },
        VENDORS,
        "Unread mail only, every PDF of a message in name order, vendors matched ignoring case and spaces.",
    ),
    scenario(
        "rejections-go-to-failed-and-the-lead",
        {
            "M-010/message.txt": message("sales@unknown.example", "Invoice 55"),
            "M-010/inv-55.pdf": invoice("Unknown Supplies", "U-55", "40.00"),
            "M-011/message.txt": message("ar@northwind.example", "Invoice NW-9"),
            "M-011/nw-9.pdf": invoice("Northwind Traders", "NW-9", "800.01"),
            "M-012/message.txt": message("ar@northwind.example", "Invoice NW-10"),
            "M-012/nw-10.pdf": invoice("Northwind Traders", "NW-10", "800.00"),
            "M-013/message.txt": message("billing@contoso.example", "Invoice"),
            "M-013/scan.pdf": invoice("Contoso Ltd", None, "75.00"),
        },
        VENDORS,
        "An unknown vendor, a total over the limit, and a missing invoice number are rejected; exactly the limit is fine.",
    ),
    scenario(
        "missing-attachments-ask-the-sender",
        {
            "M-020/message.txt": message("billing@contoso.example", "Invoice INV-2001 (resend)"),
            "M-021/message.txt": message("ar@fabrikam.example", "Statement"),
            "M-021/statement.xlsx": "not a pdf\n",
            "M-022/message.txt": message("billing@contoso.example", "Invoice INV-2002"),
            "M-022/INV-2002.PDF": invoice("Contoso Ltd", "INV-2002", "5,000"),
        },
        VENDORS,
        "A message with no PDF gets a note back to its sender; the extension is matched ignoring case.",
    ),
    scenario(
        "an-empty-mailbox",
        {
            "M-030/message.txt": message("billing@contoso.example", "Old invoice", status="Read"),
        },
        VENDORS,
        "Nothing unread: an empty queue with its header, and nothing marked read.",
    ),
]

SPEC = {
    "task": "invoice_intake",
    "band": "real-world",
    "candidate": "Main.xaml",
    "reference": "../reference/Main.xaml",
    "contract": {
        "arguments": [
            {"name": "in_MailFolder", "direction": "In", "type": "System.String"},
            {"name": "in_VendorsFile", "direction": "In", "type": "System.String"},
            {"name": "in_OutputFolder", "direction": "In", "type": "System.String"},
            {"name": "out_Queued", "direction": "Out", "type": "System.Int32"},
            {"name": "out_Rejected", "direction": "Out", "type": "System.Int32"},
            {"name": "out_MissingAttachment", "direction": "Out", "type": "System.Int32"},
        ],
        "required_activity_types": ["UiPath.Core.Activities.InvokeWorkflowFile"],
        "forbidden_activity_types": ["UiPath.Core.Activities.InvokeCode"],
    },
    "pass_threshold": 1.0,
    "scenarios": SCENARIOS,
}

(HERE / "invoice_intake.json").write_text(json.dumps(SPEC, indent=1) + "\n")
for s in SCENARIOS:
    print(s["name"], s["expect_outputs"], s["expect_files"]["out/Posting/ERP_Queue.csv"]["lines"][1:], sorted(k for k in s["expect_files"] if "Outbox" in k or "Failed" in k))
