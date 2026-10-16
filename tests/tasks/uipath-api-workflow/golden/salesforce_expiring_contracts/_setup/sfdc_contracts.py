#!/usr/bin/env python3
"""Salesforce fixture for the expiring-contracts golden scenario, created through the run
user's Integration Service connection.

`seed` (pre_run) creates one Account and four Contracts: two ending inside the scenario's
30-day window and two outside it (INSIDE_DAYS, OUTSIDE_DAYS from today). Each is activated
when the org allows it, so a workflow that keeps only Activated contracts still sees them.
They are recorded in STATE_FILE, with the EndDate Salesforce computed. `cleanup`
(post_run) deletes what STATE_FILE lists, then fixture accounts older than STALE_DAYS left
by runs that died before their post_run. check_contracts.py imports this module to add one
more contract at grading time.

Self-contained on purpose: pre_run and post_run run it from the agent's sandbox, where the
graders' golden/_shared helpers are not staged.

    python3 _setup/sfdc_contracts.py seed|cleanup
"""
import calendar
import datetime
import json
import subprocess
import sys
import uuid
from pathlib import Path

CONNECTOR = "uipath-salesforce-sfdc"
STATE_FILE = Path(".golden/sfdc_fixture.json")
ACCOUNT_PREFIX = "Golden expiring contracts"
INSIDE_DAYS = (5, 25)
OUTSIDE_DAYS = (45, -3)
GRADING_DAYS = 12
WINDOW_DAYS = 30
STALE_DAYS = 2
INFRA_EXIT = 3


class FixtureError(Exception):
    pass


def _field(record, name):
    if not isinstance(record, dict):
        return None
    for key, value in record.items():
        if key.lower() == name.lower():
            return value
    return None


def _uip(*args, timeout=90):
    """`Data` of `uip <args> --output json`, or FixtureError naming the call."""
    label = " ".join(args[:5])
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FixtureError(f"uip {label}: {type(exc).__name__}") from exc
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise FixtureError(f"uip {label} printed no JSON (exit {proc.returncode})") from exc
    if not isinstance(envelope, dict) or envelope.get("Result") != "Success":
        detail = {k: _field(envelope, k) for k in ("ErrorCode", "Message")} if isinstance(envelope, dict) else envelope
        raise FixtureError(f"uip {label} failed: {json.dumps(detail)[:300]}")
    return envelope.get("Data")


def connection_id():
    """The one Enabled Salesforce connection the run user can list, across folders."""
    rows = _uip("is", "connections", "list", CONNECTOR, "--all-folders", "--refresh")
    rows = [row for row in rows or [] if str(_field(row, "ConnectorKey") or "").lower() == CONNECTOR]
    enabled = [row for row in rows if str(_field(row, "State") or "").lower() == "enabled"]
    if len(enabled) != 1:
        raise FixtureError(f"expected one Enabled {CONNECTOR} connection, found {len(enabled)} of {len(rows)}")
    return str(_field(enabled[0], "Id"))


def add_months(day, months):
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def start_for(end_day):
    """The StartDate of a one-month contract that Salesforce ends on `end_day` (it computes
    EndDate = StartDate + ContractTerm months - 1 day). Month-end clamping can move the end
    a day; the EndDate actually stored is read back instead of trusted."""
    return add_months(end_day + datetime.timedelta(days=1), -1)


def _id_query(sobject, record_id):
    return json.dumps({f"{sobject[0].lower()}{sobject[1:]}Id": record_id})


def create(conn, sobject, body):
    created = _uip("is", "resources", "run", "create", CONNECTOR, sobject, "--connection-id", conn,
                   "--body", json.dumps(body))
    record_id = _field(created, "Id")
    if not record_id:
        raise FixtureError(f"{sobject} created without an id: {json.dumps(created)[:200]}")
    return str(record_id)


def update(conn, sobject, record_id, body):
    _uip("is", "resources", "run", "update", CONNECTOR, sobject, "--connection-id", conn,
         "--query", _id_query(sobject, record_id), "--body", json.dumps(body))


def delete(conn, sobject, record_id):
    _uip("is", "resources", "run", "delete", CONNECTOR, sobject, "--connection-id", conn,
         "--query", _id_query(sobject, record_id), "--yes")


def soql(conn, query):
    found = _uip("is", "resources", "run", "create", CONNECTOR, "curated_soqlQuery", "--connection-id", conn,
                 "--body", json.dumps({"query": query}))
    if isinstance(found, dict):
        found = _field(found, "records") or _field(found, "items") or [found]
    return [row for row in found or [] if _field(row, "Id")]


def add_contract(conn, account_id, token, days, today):
    """A contract on `account_id` ending `days` after `today`, activated if the org lets
    this user activate it."""
    label = f"{ACCOUNT_PREFIX} {token} {days:+d}d"
    end = today + datetime.timedelta(days=days)
    contract_id = create(conn, "Contract", {"AccountId": account_id, "StartDate": start_for(end).isoformat(),
                                            "ContractTerm": 1, "Status": "Draft", "Description": label})
    try:
        update(conn, "Contract", contract_id, {"Status": "Activated"})
    except FixtureError as exc:
        print(f"WARNING: {label} stays Draft: {exc}", file=sys.stderr)
    return {"id": contract_id, "label": label, "days": days}


def describe(conn, state):
    """state["contracts"] with each one's ContractNumber, EndDate and Status from Salesforce."""
    rows = soql(conn, "SELECT Id, ContractNumber, EndDate, Status FROM Contract "
                      f"WHERE AccountId = '{state['account_id']}'")
    live = {str(_field(row, "Id"))[:15]: row for row in rows}
    for contract in state["contracts"]:
        row = live.get(contract["id"][:15])
        if row:
            contract.update(number=_field(row, "ContractNumber"), end_date=_field(row, "EndDate"),
                            status=_field(row, "Status"))
    return state["contracts"]


def load_state(path=STATE_FILE):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise FixtureError(f"no readable {path}: did pre_run seed the fixture? ({exc})") from exc


def save_state(state, path=STATE_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))


def seed(today=None):
    today = today or datetime.date.today()
    token = uuid.uuid4().hex[:8]
    conn = connection_id()
    account_id = create(conn, "Account", {"Name": f"{ACCOUNT_PREFIX} {token}"})
    state = {"connection_id": conn, "account_id": account_id, "token": token, "seeded_on": today.isoformat(),
             "contracts": []}
    save_state(state)
    for days in (*INSIDE_DAYS, *OUTSIDE_DAYS):
        state["contracts"].append(add_contract(conn, account_id, token, days, today))
        save_state(state)
    describe(conn, state)
    save_state(state)
    for contract in state["contracts"]:
        print(f"{contract['label']}: {contract['id']} ends {contract.get('end_date')} ({contract.get('status')})")


def remove_account(conn, account_id):
    """Delete the account's contracts, moving an activated one back to Draft when Salesforce
    refuses to delete it, then the account. Returns what could not be deleted."""
    leftovers = []
    for row in soql(conn, f"SELECT Id FROM Contract WHERE AccountId = '{account_id}'"):
        contract_id = str(_field(row, "Id"))
        try:
            delete(conn, "Contract", contract_id)
        except FixtureError:
            try:
                update(conn, "Contract", contract_id, {"Status": "Draft"})
                delete(conn, "Contract", contract_id)
            except FixtureError as exc:
                leftovers.append(f"Contract {contract_id}: {exc}")
    try:
        delete(conn, "Account", account_id)
    except FixtureError as exc:
        leftovers.append(f"Account {account_id}: {exc}")
    return leftovers


def cleanup():
    """Never fails the task. What cannot be deleted is reported; the next run's stale
    sweep tries it again."""
    try:
        conn = connection_id()
    except FixtureError as exc:
        print(f"WARNING: cleanup skipped: {exc}", file=sys.stderr)
        return 0
    leftovers = []
    if STATE_FILE.exists():
        try:
            leftovers += remove_account(conn, load_state()["account_id"])
        except (FixtureError, KeyError) as exc:
            leftovers.append(f"this run's fixture: {exc}")
    try:
        stale = soql(conn, f"SELECT Id FROM Account WHERE Name LIKE '{ACCOUNT_PREFIX} %' "
                           f"AND CreatedDate < LAST_N_DAYS:{STALE_DAYS}")
        for row in stale:
            leftovers += remove_account(conn, str(_field(row, "Id")))
    except FixtureError as exc:
        leftovers.append(f"stale sweep: {exc}")
    for line in leftovers:
        print(f"WARNING: not deleted: {line}", file=sys.stderr)
    return 0


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args == ["seed"]:
        try:
            seed()
        except FixtureError as exc:
            print(f"INFRA: the Salesforce fixture was not seeded: {exc}", file=sys.stderr)
            return INFRA_EXIT
        return 0
    if args == ["cleanup"]:
        return cleanup()
    print("usage: sfdc_contracts.py seed|cleanup", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
