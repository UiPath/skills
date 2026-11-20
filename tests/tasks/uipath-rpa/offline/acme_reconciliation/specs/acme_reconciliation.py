"""Write specs/acme_reconciliation.json: the ACME work-item reconciliation, from System 1 and System 3 exports.

The scenarios are built here, and their expected results computed by `run` from the rules the task's prompt
states, so the data and the answers cannot drift apart. Edit this file, then:

    python3 tests/tasks/uipath-rpa/offline/acme_reconciliation/specs/acme_reconciliation.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEADER = "WIID,Description,Type,Status,Date"


def config(item_type="WI1", retries=1, consecutive=3, blank_lines=False):
    lines = ["Name,Value", f"WorkItemType,{item_type}", f"MaxRetryNumber,{retries}", f"MaxConsecutiveSystemExceptions,{consecutive}"]
    if blank_lines:
        lines = [lines[0], "", lines[1], lines[2], "", lines[3], ""]
    return "\n".join(lines) + "\n"


def page(rows):
    return "\n".join([HEADER, *(",".join(r) for r in rows)]) + "\n"


def detail(wiid, account, amount, item_type="WI1"):
    lines = [f"Work Item: {wiid}", f"Type: {item_type}", "", "Account Information", "Client Name: Ana Ionescu"]
    if account is not None:
        lines.append(f"Account Number: {account}")
    lines.append(f"Amount: {amount}")
    return "\r\n".join(lines) + "\r\n"


def statement(account, transactions):
    lines = [f"ACME System 3 - Account {account}", "Date | Description | Amount", ""]
    lines += [f"{d} | {desc} | {amt}" for d, desc, amt in transactions]
    return "\n".join(lines) + "\n"


def digits(text):
    return "".join(c for c in text if c.isdigit())


def run(files, cfg):
    """The rules of the prompt: what Updates.csv holds, the counts, the logs, and whether the job faults."""
    settings = dict(line.split(",", 1) for line in cfg.splitlines()[1:] if line.strip())
    retries, limit = int(settings["MaxRetryNumber"]), int(settings["MaxConsecutiveSystemExceptions"])
    items, n = [], 1
    while f"System1/WorkItems_{n}.csv" in files:
        for line in files[f"System1/WorkItems_{n}.csv"].splitlines()[1:]:
            if line.strip():
                wiid, _, kind, status, _ = line.split(",")
                if kind == settings["WorkItemType"] and status == "Open":
                    items.append(wiid)
        n += 1
    updates, counts, warns, errors, consecutive, fault = [], {"Completed": 0, "Rejected": 0, "Failed": 0}, {}, {}, 0, None
    for wiid in items:
        attempt = 0
        while True:
            outcome = process(files, wiid)
            if outcome[0] != "System":
                consecutive = 0
                updates.append(f"{wiid},{outcome[0]},{outcome[1]}")
                counts[outcome[0]] += 1
                if outcome[0] == "Rejected":
                    warns[wiid] = warns.get(wiid, 0) + 1
                break
            errors[wiid] = errors.get(wiid, 0) + 1
            consecutive += 1
            if consecutive >= limit:
                fault = consecutive
                break
            if attempt == retries:
                counts["Failed"] += 1
                break
            attempt += 1
        if fault is not None:
            break
    return updates, counts, warns, errors, fault


def process(files, wiid):
    page_ = files.get(f"System1/WorkItem_{wiid}.txt")
    if page_ is None:
        return ("System",)
    lines = page_.splitlines()
    account = next(l.split(": ", 1)[1] for l in lines if l.startswith("Account Number: "))
    amount = digits(next(l.split(": ", 1)[1] for l in lines if l.startswith("Amount: ")))
    if amount == "":
        return ("Rejected", "Invalid account amount")
    stmt = files.get(f"System3/{account}.txt")
    if stmt is None:
        return ("System",)
    amounts = []
    for l in stmt.splitlines():
        parts = [p.strip() for p in l.split("|")]
        if len(parts) == 3 and len(parts[0]) == 10 and parts[0][4] == "-" and parts[0][7] == "-" and parts[0].replace("-", "").isdigit():
            amounts.append(int(parts[2].replace(",", "")))
    if not amounts:
        return ("Rejected", "No transactions")
    return ("Completed", f"Difference: {abs(int(amount) - sum(amounts))}")


def scenario(name, files, cfg, existing_updates=None, note=None):
    files = {k.replace("${CFG}", ""): v for k, v in files.items()}
    data = {f"data/{k}": v for k, v in files.items()}
    data["config/Config.csv"] = cfg
    if existing_updates is not None:
        data["data/System1/Updates.csv"] = existing_updates
    updates, counts, warns, errors, fault = run(files, cfg)
    lines = (existing_updates.splitlines() if existing_updates else ["WIID,Status,Comment"]) + updates
    s = {
        "name": name,
        "files": data,
        "input": {"in_DataFolder": "${WORKDIR}/data", "in_ConfigFile": "${WORKDIR}/config/Config.csv"},
        "expect_files": {"data/System1/Updates.csv": {"lines": [l for l in lines if l.strip()]}},
    }
    if note:
        s["note"] = note
    if fault is None:
        s["expect_outputs"] = {"out_Completed": counts["Completed"], "out_Rejected": counts["Rejected"], "out_Failed": counts["Failed"]}
    else:
        s["expect_state"] = "Faulted"
        s["expect_fault"] = {"mentions": [str(fault)]}
    s["expect_log_counts"] = [{"level": "Warn", "mentions": [w], "count": c} for w, c in warns.items()]
    s["expect_log_counts"] += [{"level": "Error", "mentions": [w], "count": c} for w, c in errors.items()]
    # Warnings are the prompt's word for business exceptions only, so a run may log others (a summary of a
    # failed item, say); what it must not do is warn about a rejected item more than once, or not at all.
    if not errors:
        s.setdefault("expect_not_logged", []).append({"level": "Error"})
    return s


def good(wiid, account, s1, txs, item_type="WI1"):
    return {f"System1/WorkItem_{wiid}.txt": detail(wiid, account, s1, item_type), f"System3/{account}.txt": statement(account, txs)}


SCENARIOS = [
    scenario(
        "pages-and-filters",
        {
            "System1/WorkItems_1.csv": page([
                ["300101", "Client reconciliation", "WI1", "Open", "2026-03-02"],
                ["300102", "Calculate client security hash", "WI2", "Open", "2026-03-02"],
                ["300103", "Client reconciliation", "WI1", "Completed", "2026-03-03"],
                ["300104", "Client reconciliation", "WI1", "Open", "2026-03-03"],
            ]),
            "System1/WorkItems_2.csv": page([
                ["300105", "Client reconciliation", "WI1", "Open", "2026-03-04"],
                ["300106", "Client reconciliation", "WI1", "Pending", "2026-03-05"],
            ]),
            # Page 3 is missing, so the list ends at page 2 and page 4 is never read.
            "System1/WorkItems_4.csv": page([["300199", "Client reconciliation", "WI1", "Open", "2026-03-09"]]),
            **good("300101", "AC-71001", "$12,345", [("2026-02-03", "Opening balance", "10,000"), ("2026-02-11", "Card payment", "-1,250"), ("2026-02-20", "Transfer in", "3,100")]),
            **good("300104", "AC-71004", "$980", [("2026-02-01", "Opening balance", "1000"), ("2026-02-15", "Fee", "-20")]),
            **good("300105", "AC-71005", "$2,000,000", [("2026-01-05", "Opening balance", "1,999,000"), ("2026-01-30", "Interest", "1,500")]),
            **good("300199", "AC-71099", "$1", [("2026-03-01", "Opening balance", "1")]),
        },
        config(),
        note="Only open WI1 items, in page order; the pages end where the numbering breaks.",
    ),
    scenario(
        "configured-type-and-existing-updates",
        {
            "System1/WorkItems_1.csv": page([
                ["400201", "Calculate client security hash", "WI2", "Open", "2026-04-01"],
                ["400202", "Client reconciliation", "WI1", "Open", "2026-04-01"],
                ["400203", "Calculate client security hash", "WI2", "Open", "2026-04-02"],
            ]),
            **good("400201", "AC-82001", "$5,500", [("2026-03-01", "Opening balance", "6,000"), ("2026-03-09", "Withdrawal", "-700")], "WI2"),
            **good("400203", "AC-82003", "$0", [("2026-03-01", "Opening balance", "0")], "WI2"),
        },
        config(item_type="WI2", blank_lines=True),
        existing_updates="WIID,Status,Comment\n399999,Completed,Difference: 0\n",
        note="The type comes from the config, which has blank lines; an existing Updates.csv is added to.",
    ),
    scenario(
        "business-exceptions-are-rejected",
        {
            "System1/WorkItems_1.csv": page([
                ["500301", "Client reconciliation", "WI1", "Open", "2026-05-01"],
                ["500302", "Client reconciliation", "WI1", "Open", "2026-05-01"],
                ["500303", "Client reconciliation", "WI1", "Open", "2026-05-02"],
            ]),
            "System1/WorkItem_500301.txt": detail("500301", "AC-93001", "n/a"),
            "System3/AC-93001.txt": statement("AC-93001", [("2026-04-01", "Opening balance", "100")]),
            **good("500302", "AC-93002", "$250", []),
            **good("500303", "AC-93003", "$4,321", [("2026-04-01", "Opening balance", "4,000"), ("2026-04-17", "Deposit", "300")]),
        },
        config(retries=2),
        note="An amount with no digits and a statement with no transactions are rejected, never retried.",
    ),
    scenario(
        "system-exceptions-are-retried",
        {
            "System1/WorkItems_1.csv": page([
                ["600401", "Client reconciliation", "WI1", "Open", "2026-06-01"],
                ["600402", "Client reconciliation", "WI1", "Open", "2026-06-01"],
                ["600403", "Client reconciliation", "WI1", "Open", "2026-06-02"],
            ]),
            "System1/WorkItem_600401.txt": detail("600401", "AC-04001", "$700"),
            **good("600403", "AC-04003", "$1,000", [("2026-05-01", "Opening balance", "1,200"), ("2026-05-02", "Payment", "-150")]),
        },
        config(retries=2, consecutive=10),
        note="A missing statement and a missing detail page are tried three times each, then the item has failed.",
    ),
    scenario(
        "consecutive-system-exceptions-stop-the-run",
        {
            "System1/WorkItems_1.csv": page([
                ["700501", "Client reconciliation", "WI1", "Open", "2026-07-01"],
                ["700502", "Client reconciliation", "WI1", "Open", "2026-07-01"],
                ["700503", "Client reconciliation", "WI1", "Open", "2026-07-02"],
                ["700504", "Client reconciliation", "WI1", "Open", "2026-07-02"],
                ["700505", "Client reconciliation", "WI1", "Open", "2026-07-03"],
            ]),
            **good("700502", "AC-05002", "$10", [("2026-06-01", "Opening balance", "15")]),
            **good("700505", "AC-05005", "$10", [("2026-06-01", "Opening balance", "10")]),
        },
        config(retries=1, consecutive=3),
        note="700501 fails twice, 700502 resets the count, 700503 fails twice and 700504 once: the third in a row stops the run.",
    ),
    scenario(
        "no-retries",
        {
            "System1/WorkItems_1.csv": page([
                ["800601", "Client reconciliation", "WI1", "Open", "2026-08-01"],
                ["800602", "Client reconciliation", "WI1", "Open", "2026-08-01"],
            ]),
            **good("800602", "AC-06002", "$99", [("2026-07-01", "Opening balance", "100")]),
        },
        config(retries=0, consecutive=5),
        note="With MaxRetryNumber 0 a failing item is tried once.",
    ),
]

SPEC = {
    "task": "acme_reconciliation",
    "band": "real-world",
    "candidate": "Main.xaml",
    "reference": "../../../../../fixtures/uipath-rpa-offline-solutions/acme_reconciliation/Main.xaml",
    "contract": {
        "arguments": [
            {"name": "in_DataFolder", "direction": "In", "type": "System.String"},
            {"name": "in_ConfigFile", "direction": "In", "type": "System.String"},
            {"name": "out_Completed", "direction": "Out", "type": "System.Int32"},
            {"name": "out_Rejected", "direction": "Out", "type": "System.Int32"},
            {"name": "out_Failed", "direction": "Out", "type": "System.Int32"},
        ],
        "required_activity_types": ["System.Activities.Statements.StateMachine", "UiPath.Core.Activities.InvokeWorkflowFile"],
        "forbidden_activity_types": ["UiPath.Core.Activities.InvokeCode"],
    },
    "pass_threshold": 1.0,
    "scenarios": SCENARIOS,
}

(HERE / "acme_reconciliation.json").write_text(json.dumps(SPEC, indent=1) + "\n")
for s in SCENARIOS:
    print(s["name"], s.get("expect_outputs") or s.get("expect_fault"), s["expect_files"]["data/System1/Updates.csv"]["lines"][1:])
