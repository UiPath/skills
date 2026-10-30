#!/usr/bin/env python3
import calendar
import datetime
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path

CONNECTOR = "uipath-salesforce-sfdc"
STATE_FILE = Path(".golden/sfdc_fixture.json")
ACCOUNT_PREFIX = "Golden expiring contracts"
FIXTURE_NAME = re.compile(rf"{re.escape(ACCOUNT_PREFIX)} [0-9a-f]{{8}}")
TOKEN = re.compile(r"[0-9a-f]{8}")
SALESFORCE_ID = re.compile(r"[0-9A-Za-z]{15}(?:[0-9A-Za-z]{3})?")
CONNECTION_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE)
INSIDE_DAYS = (5, 25)
OUTSIDE_DAYS = (45, -3)
GRADING_DAYS = 12
WINDOW_DAYS = 30
STALE_DAYS = 2
MAX_LEFTOVERS = 24
SWEEP_LIMIT = 5
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
    rows = _uip("is", "connections", "list", CONNECTOR, "--refresh")
    rows = [row for row in rows or [] if str(_field(row, "ConnectorKey") or "").lower() == CONNECTOR]
    enabled = [row for row in rows if str(_field(row, "State") or "").lower() == "enabled"]
    if len(enabled) != 1:
        raise FixtureError(f"expected one Enabled {CONNECTOR} connection in the personal workspace, "
                           f"found {len(enabled)} of {len(rows)}")
    return str(_field(enabled[0], "Id"))


def add_months(day, months):
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def start_for(end_day):
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


def fixture_accounts(conn, where=""):
    rows = soql(conn, f"SELECT Id, Name FROM Account WHERE Name LIKE '{ACCOUNT_PREFIX} %'{where} "
                      "ORDER BY CreatedDate LIMIT 200")
    return [row for row in rows if FIXTURE_NAME.fullmatch(str(_field(row, "Name") or ""))]


def creator_of(conn, account_id):
    rows = soql(conn, f"SELECT Id, CreatedById FROM Account WHERE Id = '{account_id}'")
    creator = _field(rows[0], "CreatedById") if rows else None
    if not creator:
        raise FixtureError(f"cannot read who created Account {account_id}")
    return str(creator)


def add_contract(conn, account_id, token, days, today):
    label = f"{ACCOUNT_PREFIX} {token} {days:+d}d"
    end = today + datetime.timedelta(days=days)
    contract_id = create(conn, "Contract", {"AccountId": account_id, "StartDate": start_for(end).isoformat(),
                                            "ContractTerm": 1, "Status": "Draft", "Description": label})
    try:
        update(conn, "Contract", contract_id, {"Status": "Activated"})
    except FixtureError as exc:
        raise FixtureError(f"{label} was not activated; the connection's user must be able to activate "
                           f"Contracts ({exc})") from exc
    return {"id": contract_id, "label": label, "days": days}


def require_activated(contracts):
    inactive = [f"{c['label']} ({c.get('status') or 'no status'})" for c in contracts
                if str(c.get("status") or "").lower() != "activated"]
    if inactive:
        raise FixtureError("fixture contracts not Activated: " + ", ".join(inactive))


def describe(conn, state):
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


def verify_fixture(state):
    if not isinstance(state, dict):
        raise FixtureError(f"{STATE_FILE} does not hold a fixture record")
    conn = str(state.get("connection_id") or "")
    account_id = str(state.get("account_id") or "")
    token = str(state.get("token") or "")
    creator = state.get("created_by")
    if not (CONNECTION_ID.fullmatch(conn) and SALESFORCE_ID.fullmatch(account_id) and TOKEN.fullmatch(token)
            and (creator is None or SALESFORCE_ID.fullmatch(str(creator)))):
        raise FixtureError(f"{STATE_FILE} no longer holds a connection id, account id, token and creator")
    rows = soql(conn, f"SELECT Id, Name, CreatedById FROM Account WHERE Id = '{account_id}'")
    if not rows or _field(rows[0], "Name") != f"{ACCOUNT_PREFIX} {token}":
        raise FixtureError(f"Account {account_id} is not the fixture account '{ACCOUNT_PREFIX} {token}'")
    if creator is not None and str(_field(rows[0], "CreatedById") or "")[:15] != creator[:15]:
        raise FixtureError(f"Account {account_id} was not created by the fixture's Salesforce user")
    return conn, account_id, creator


def seed(today=None):
    today = today or datetime.date.today()
    token = uuid.uuid4().hex[:8]
    conn = connection_id()
    leftovers = fixture_accounts(conn)
    if len(leftovers) > MAX_LEFTOVERS:
        raise FixtureError(f"{len(leftovers)} fixture accounts are already in the org, so cleanup is not deleting "
                           f"them; delete the Accounts named '{ACCOUNT_PREFIX} <token>' before seeding more")
    account_id = create(conn, "Account", {"Name": f"{ACCOUNT_PREFIX} {token}"})
    state = {"connection_id": conn, "account_id": account_id, "token": token, "seeded_on": today.isoformat(),
             "contracts": []}
    save_state(state)
    state["created_by"] = creator_of(conn, account_id)
    save_state(state)
    for days in (*INSIDE_DAYS, *OUTSIDE_DAYS):
        state["contracts"].append(add_contract(conn, account_id, token, days, today))
        save_state(state)
    describe(conn, state)
    save_state(state)
    for contract in state["contracts"]:
        print(f"{contract['label']}: {contract['id']} ends {contract.get('end_date')} ({contract.get('status')})")
    require_activated(state["contracts"])


def remove_account(conn, account_id):
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
    if not STATE_FILE.exists():
        print("cleanup: this run seeded nothing", file=sys.stderr)
        return 0
    try:
        conn, account_id, creator = verify_fixture(load_state())
    except FixtureError as exc:
        print(f"WARNING: cleanup skipped, nothing deleted: {exc}", file=sys.stderr)
        return 0
    leftovers = []
    try:
        leftovers += remove_account(conn, account_id)
    except FixtureError as exc:
        leftovers.append(f"this run's fixture: {exc}")
    if creator:
        try:
            stale = fixture_accounts(conn, f" AND CreatedById = '{creator}' "
                                           f"AND CreatedDate < LAST_N_DAYS:{STALE_DAYS}")
            for row in stale[:SWEEP_LIMIT]:
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
