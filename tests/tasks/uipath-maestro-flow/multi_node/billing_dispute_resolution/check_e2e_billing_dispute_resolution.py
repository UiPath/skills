#!/usr/bin/env python3
"""Effects check for BillingDisputeResolution.

Debugs the flow once against the live tenant and grades what the run did, read
from the debug trace, and what it returned, read among the declared outputs by
value. The prompt lets the agent choose the dispute submission's shape, so the
submission is built from the paths the flow reads off its input
(`flow_io_roles.map_inputs`) laid over a synonym-rich fallback for paths read
inside scripts. The invoice number is typed with stray spaces and in
lowercase, as the prompt warns customers do.

Both cases use rows the tenant's BillingDisputeERP really holds and the invoice
PDF that matches them, so the right outcome follows from the tenant's own
Billing Dispute SOP (§5.4 "Incorrect rate" compares the billed unitPrice with
the row's contractedRate; §7 sends $500-$5,000 to manager review and anything
without a variance to reject):

  overcharge  Invoice MCS-2026-04903, line 2 (DevOps Engineering), account
              ACCT-71044-AT: 90 hours billed at $290 against a contracted $235,
              so the customer is owed (290 - 235) x 90 = $4,950, which §7 sends
              to manager review and the prompt auto-approves. The run must
              extract the invoice (IxP), complete both lookups, POST through
              FinancialPostingFunction (whose live reply must cite the invoice
              number as the records hold it), run the writer, and return
              "Approved", "manager_review" or "credit", 4950, an explanation
              naming an SOP rule, and a plain-text email draft citing the
              invoice and that credit.

  reject      Invoice MCS-2026-04872, line 5 (Custom Integration Build), account
              ACCT-98201-NE: 14 hours billed at $185, and the ERP row's
              contractedRate is $185. No variance, so the run must complete
              without posting and without the writer, and return "Rejected",
              "reject", 0, an explanation naming an SOP rule, and
              "No resolution email drafted".

Both recommended actions count for the overcharge: the analyst picked
"manager_review" in one run and "credit" in the next for the same dispute
(round 3, 2026-11-18), and both lead to approval here. The analyst task grades
the SOP's band strictly.

Usage: check_e2e_billing_dispute_resolution.py overcharge|reject
"""
import os
import re
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _fail,
    _fail_with_capture,
    _get_ci,
    _load_flow,
    node_output_leaves,
    run_debug,
)

_HERE = os.path.dirname(os.path.abspath(__file__))
NO_EMAIL = "No resolution email drafted"
NAMES_A_RULE = re.compile(r"§|\bsection\s*\d|\bSOP\b", re.I)

CASES = {
    "overcharge": {
        "invoice": "MCS-2026-04903",
        "typed": " mcs-2026-04903  ",
        "account": "ACCT-71044-AT",
        "company": "Atlas Manufacturing Group",
        "line": {"number": 2, "description": "DevOps Engineering", "quantity": 90, "price": 290,
                 "amount": 26100, "reason": "Billed at $290/hour; our SOW AT-2026-008 contracts $235/hour"},
        "statement": "We were billed a higher hourly rate than our contract specifies.",
        "decision": "Approved",
        "actions": ("manager_review", "credit"),
        "credit": 4950,
    },
    "reject": {
        "invoice": "MCS-2026-04872",
        "typed": "  Mcs-2026-04872 ",
        "account": "ACCT-98201-NE",
        "company": "Northwind Electronics Corp.",
        "line": {"number": 5, "description": "Custom Integration Build", "quantity": 14, "price": 185,
                 "amount": 2590, "reason": "We believe the hourly rate is too high"},
        "statement": "The integration hourly rate looks higher than we expected.",
        "decision": "Rejected",
        "actions": ("reject",),
        "credit": 0,
    },
}


def line_item(case):
    """One disputed line, with every field under several common spellings."""
    li = CASES[case]["line"]
    number, qty, price, amount = li["number"], li["quantity"], li["price"], li["amount"]
    return {
        "lineNumber": number, "line": number, "lineNo": number, "line_number": number,
        "lineItemNumber": number, "lineId": number, "number": number,
        "quantity": qty, "qty": qty, "hours": qty, "units": qty, "billedQuantity": qty,
        "unitPrice": price, "unit_price": price, "price": price, "rate": price, "billedRate": price,
        "billedUnitPrice": price, "chargedPrice": price, "chargedUnitPrice": price, "hourlyRate": price,
        "amount": amount, "total": amount, "lineTotal": amount, "billedAmount": amount,
        "chargedAmount": amount, "totalAmount": amount,
        "description": li["description"], "reason": li["reason"],
    }


def submission_fallback(case):
    """A dispute submission readable under the common spellings of each field."""
    c = CASES[case]
    lines = [line_item(case)]
    account, invoice = c["account"], c["typed"]
    return {
        "accountNumber": account, "accountNo": account, "account_number": account, "accountId": account,
        "account": account, "customerAccountNumber": account, "customerAccount": account,
        "acctNumber": account,
        "customer": {"accountNumber": account, "accountNo": account, "account": account, "id": account,
                     "number": account, "name": c["company"], "companyName": c["company"]},
        "customerName": c["company"], "companyName": c["company"],
        "invoiceNumber": invoice, "invoiceNo": invoice, "invoice_number": invoice, "invoiceId": invoice,
        "invoiceRef": invoice,
        "invoice": {"invoiceNumber": invoice, "number": invoice, "invoiceNo": invoice, "id": invoice},
        "disputedLines": lines, "disputedLineItems": lines, "disputed_lines": lines, "lineItems": lines,
        "lines": lines, "items": lines, "disputedItems": lines, "disputes": lines,
        "dispute": {"disputedLineItems": lines, "disputedLines": lines, "lineItems": lines, "lines": lines,
                    "items": lines, "type": "pricing", "description": c["statement"],
                    "customerStatement": c["statement"]},
        "description": c["statement"], "reason": c["statement"], "customerStatement": c["statement"],
    }


def submission_roles(case):
    """The submission's parts, for leaf paths the flow reads off its input."""
    c = CASES[case]
    return {
        "account number": {"value": c["account"], "keywords": [
            "accountnumber", "accountno", "accountid", "acctno", "acctnumber", "account", "acct"]},
        "invoice number": {"value": c["typed"], "keywords": [
            "invoicenumber", "invoiceno", "invoiceid", "invoiceref", "invoicenum"]},
        "disputed lines": {"value": [line_item(case)], "keywords": ["lineitems", "lines", "items", "disputes"]},
    }


LINE_ROLES = ("disputed line number", "billed quantity", "billed unit price")


def scalar_roles(case):
    """The submission spread over separate inputs."""
    li = CASES[case]["line"]
    roles = {k: v for k, v in submission_roles(case).items() if k != "disputed lines"}
    roles["invoice number"]["keywords"] = roles["invoice number"]["keywords"] + ["invoice"]
    roles["account number"]["keywords"] = roles["account number"]["keywords"] + ["customer"]
    roles.update({
        "disputed line number": {"value": li["number"], "keywords": ["linenumber", "lineno", "line"]},
        "billed quantity": {"value": li["quantity"], "keywords": ["quantity", "qty", "hours"]},
        "billed unit price": {"value": li["price"], "keywords": ["unitprice", "price", "rate"]},
    })
    return roles


def invoice_pdf(case):
    return os.path.join(_HERE, f"invoice-{CASES[case]['invoice']}.pdf")


def build_inputs(flow, case):
    """(inputs, attachments) for the debug run, or a clear failure naming what had no input."""
    declared_in = io.declared(flow, "in")
    kinds = {v["id"]: str(v.get("type") or "").lower() for v in declared_in}
    if "file" not in kinds.values():
        _fail(io.unmapped_error(flow, ["the invoice PDF (a file input)"]))
    if any(k in ("object", "jsonschema") for k in kinds.values()):
        inputs, attachments, _ = io.map_inputs(
            flow, submission_roles(case), object_fallback=submission_fallback(case), file_path=invoice_pdf(case)
        )
        return inputs, attachments
    arrays = [i for i, k in kinds.items() if k == "array"]
    scalars = {"variables": {"globals": [v for v in declared_in if v["id"] not in arrays]}}
    inputs, attachments, unmapped = io.map_inputs(
        scalars, scalar_roles(case), object_fallback=None, file_path=invoice_pdf(case)
    )
    if arrays:
        inputs[arrays[0]] = [line_item(case)]
        unmapped = [r for r in unmapped if r not in LINE_ROLES]
    if problem := io.unmapped_error(flow, unmapped, inputs):
        _fail(problem)
    return inputs, attachments


def _ids_of(flow, sub):
    return {n["id"] for n in flow.get("nodes") or [] if sub in str(n.get("type", ""))}


def _agent_ids(flow):
    """Inline agents and existing tenant agents (`uipath.core.agent.<key>`)."""
    return _ids_of(flow, "uipath.agent.autonomous") | _ids_of(flow, "uipath.core.agent.")


def _downstream(flow, starts):
    adj = {}
    for e in flow.get("edges") or []:
        adj.setdefault(e.get("sourceNodeId"), []).append(e.get("targetNodeId"))
    seen, stack = set(), list(starts)
    while stack:
        for y in adj.get(stack.pop(), ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def _executed_ids(payload, *, completed=False):
    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    return {
        _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId")
        for e in els
        if not completed or str(_get_ci(e, "status", "Status")).lower() == "completed"
    }


def _completed(flow, payload, sub):
    return _ids_of(flow, sub) & _executed_ids(payload, completed=True)


def _amount_spellings(amount):
    spellings = {f"{amount:.2f}", f"{amount:,.2f}"}
    if float(amount).is_integer():
        spellings |= {str(int(amount)), f"{int(amount):,}"}
    return spellings


def check_results(case, outs, *, email):
    """Decision, action, credit and explanation by value; `email` grades the draft output."""
    c = CASES[case]
    if not io.find_out(outs, io.equals_exact(c["decision"])):
        _fail_with_capture(f"no declared output is the decision {c['decision']!r}: {outs}")
    actions = [a for a in c["actions"] if io.find_out(outs, io.equals_exact(a))]
    if not actions:
        _fail_with_capture(f"no declared output is the recommended action {' or '.join(map(repr, c['actions']))}: {outs}")
    if not io.find_out(outs, io.equals_number(c["credit"], 0.005)):
        _fail_with_capture(f"no declared output is the credit amount {c['credit']}: {outs}")
    print(f"OK: decision {c['decision']!r}, recommended action {actions[0]!r}, credit {c['credit']}")

    email_ids = email(outs)
    explanations = [t for k, (_t, v) in outs.items() if k not in email_ids for t in io.texts(v)
                    if len(t.split()) >= 5]
    if not any(NAMES_A_RULE.search(t) for t in explanations):
        _fail_with_capture(f"no returned explanation names an SOP rule (§, section or SOP): {explanations}")
    print("OK: the explanation names an SOP rule")


def check_overcharge(flow, payload):
    c = CASES["overcharge"]
    invoice, credit = c["invoice"], c["credit"]
    if not _completed(flow, payload, "uipath.ixp"):
        _fail_with_capture("the IxP extraction did not complete")
    reads = set()
    for hint in ENTITY_QUERY_HINTS:
        reads |= _completed(flow, payload, hint)
    if len(reads) < 2:
        _fail_with_capture(f"expected the ERP and CRM lookups to complete, completed reads: {sorted(reads)}")
    print("OK: IxP extraction and both lookups completed")

    posted = _completed(flow, payload, "uipath.core.api-workflow")
    if not posted:
        _fail_with_capture("FinancialPostingFunction did not complete: a valid overcharge was not posted")
    # The deployed function echoes the invoice it was sent ("Credit memo posted
    # successfully. Invoice: '<n>'. …"), so its live reply proves which invoice
    # the flow posted, and that the typed number was cleaned up first.
    replies = node_output_leaves(payload, posted)
    if not any(invoice in r for r in replies):
        _fail_with_capture(f"FinancialPostingFunction's reply does not cite {invoice}: {sorted(replies)[:5]}")
    print(f"OK: FinancialPostingFunction completed ({sorted(posted)}) and replied for {invoice}")

    writers = _agent_ids(flow) & _downstream(flow, posted)
    if not writers & _executed_ids(payload, completed=True):
        _fail_with_capture("the writer agent after posting did not complete: no email was drafted")
    print(f"OK: writer agent completed ({sorted(writers)})")

    def email(outs):
        drafts = [k for k, (_t, v) in outs.items() if isinstance(v, str) and invoice in v
                  and any(s in v for s in _amount_spellings(credit))]
        if not drafts:
            _fail_with_capture(f"no declared output is a plain-text email citing {invoice} and the credit of {credit}: {outs}")
        print(f"OK: the email draft ({drafts}) cites {invoice} and the credit")
        return set(drafts)

    outs = io.out_values(flow, payload)
    print(f"outputs: { {k: v for k, (_t, v) in outs.items()} }")
    check_results("overcharge", outs, email=email)


def check_reject(flow, payload):
    api = _ids_of(flow, "uipath.core.api-workflow")
    executed = _executed_ids(payload)
    if api & executed:
        _fail_with_capture(f"FinancialPostingFunction ran ({sorted(api & executed)}) for a line billed exactly at contract")
    print("OK: nothing was posted")

    writers = _agent_ids(flow) & _downstream(flow, api)
    if writers & executed:
        _fail_with_capture(f"the writer agent ran ({sorted(writers & executed)}): an email was drafted")
    print("OK: the writer did not run")

    def email(outs):
        placeholder = io.find_out(outs, io.equals_exact(NO_EMAIL))
        if not placeholder:
            _fail_with_capture(f"no declared output is {NO_EMAIL!r}: {outs}")
        print(f"OK: {NO_EMAIL!r} returned ({placeholder})")
        return set(placeholder)

    outs = io.out_values(flow, payload)
    print(f"outputs: { {k: v for k, (_t, v) in outs.items()} }")
    check_results("reject", outs, email=email)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(CASES)}")
    case = sys.argv[1]
    flow = _load_flow("**/project.uiproj")
    inputs, attachments = build_inputs(flow, case)
    print(f"debug inputs: {inputs} attachments: {attachments}")
    payload = run_debug(inputs=inputs, attachments=attachments, timeout=840)
    (check_overcharge if case == "overcharge" else check_reject)(flow, payload)


if __name__ == "__main__":
    main()
