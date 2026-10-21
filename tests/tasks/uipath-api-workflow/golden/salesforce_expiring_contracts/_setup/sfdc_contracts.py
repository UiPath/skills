#!/usr/bin/env python3
"""Salesforce fixture for the expiring-contracts golden scenario, created through the run
user's Integration Service connection.

`seed` (pre_run) creates one Account and four Contracts: two ending inside the scenario's
30-day window and two outside it (INSIDE_DAYS, OUTSIDE_DAYS from today). Each is activated,
so a workflow that keeps only Activated contracts still sees them; a contract the org will
not activate is a FixtureError, reported as INFRA, since that workflow would otherwise fail
for a fixture reason. They are recorded in STATE_FILE, with the EndDate Salesforce
computed and the Salesforce user who created them. The org can be shared, so the seed stops
as INFRA, creating nothing, while more than MAX_LEFTOVERS fixture accounts are left over.
`cleanup` (post_run) deletes this run's account and its contracts, then up to SWEEP_LIMIT
fixture accounts the same user created more than STALE_DAYS ago, left by runs that died
before their post_run. A fixture account is one named ACCOUNT_PREFIX and an 8-character
seed token, nothing else. check_contracts.py imports this module to add one more contract at
grading time.

Self-contained on purpose: pre_run and post_run run it from the agent's sandbox, where the
graders' golden/_shared helpers are not staged.

    python3 _setup/sfdc_contracts.py seed|cleanup
"""
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
    """The run user's one Enabled Salesforce connection: the one in their personal workspace
    (the unscoped listing the skill runs first), else the one across all folders when the
    workspace has no Enabled one or the tenant has no personal workspace. The fixture is
    written through it, so a workspace listing that fails for any other reason stops here."""
    for scope, where in (((), "in the personal workspace"), (("--all-folders",), "across all folders")):
        try:
            rows = _uip("is", "connections", "list", CONNECTOR, *scope, "--refresh")
        except FixtureError as exc:
            if scope or "personal workspace" not in str(exc).lower():
                raise
            continue
        rows = [row for row in rows or [] if str(_field(row, "ConnectorKey") or "").lower() == CONNECTOR]
        enabled = [row for row in rows if str(_field(row, "State") or "").lower() == "enabled"]
        if len(enabled) == 1:
            return str(_field(enabled[0], "Id"))
        if enabled:
            break
    raise FixtureError(f"expected one Enabled {CONNECTOR} connection {where}, found {len(enabled)} of {len(rows)}")


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


def fixture_accounts(conn, where=""):
    """The fixture accounts in the org matching the extra SOQL `where`, oldest first. Only
    exact fixture names count, so nothing another user named alike is ever touched."""
    rows = soql(conn, f"SELECT Id, Name FROM Account WHERE Name LIKE '{ACCOUNT_PREFIX} %'{where} "
                      "ORDER BY CreatedDate LIMIT 200")
    return [row for row in rows if FIXTURE_NAME.fullmatch(str(_field(row, "Name") or ""))]


def creator_of(conn, account_id):
    """Id of the Salesforce user who created `account_id`: the connection's user."""
    rows = soql(conn, f"SELECT Id, CreatedById FROM Account WHERE Id = '{account_id}'")
    creator = _field(rows[0], "CreatedById") if rows else None
    if not creator:
        raise FixtureError(f"cannot read who created Account {account_id}")
    return str(creator)


def add_contract(conn, account_id, token, days, today):
    """A contract on `account_id` ending `days` after `today`, activated. The account's
    cleanup also deletes one whose activation failed."""
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
    """FixtureError naming the fixture contracts Salesforce does not report as Activated."""
    inactive = [f"{c['label']} ({c.get('status') or 'no status'})" for c in contracts
                if str(c.get("status") or "").lower() != "activated"]
    if inactive:
        raise FixtureError("fixture contracts not Activated: " + ", ".join(inactive))


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
    """Never fails the task. Deletes through the connection the fixture was seeded through,
    and sweeps only what the same Salesforce user created; without STATE_FILE the run seeded
    nothing. What cannot be deleted is reported; a later run's sweep tries it again."""
    if not STATE_FILE.exists():
        print("cleanup: this run seeded nothing", file=sys.stderr)
        return 0
    try:
        state = load_state()
        conn, account_id = state["connection_id"], state["account_id"]
    except (FixtureError, KeyError) as exc:
        print(f"WARNING: cleanup skipped: {exc}", file=sys.stderr)
        return 0
    leftovers = []
    try:
        leftovers += remove_account(conn, account_id)
    except FixtureError as exc:
        leftovers.append(f"this run's fixture: {exc}")
    if state.get("created_by"):
        try:
            stale = fixture_accounts(conn, f" AND CreatedById = '{state['created_by']}' "
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
