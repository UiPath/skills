#!/usr/bin/env python3
"""Verify the agent's saved `uip admin audit <scope> events` result by outcome.

Replaces command-string matching with assertions on the retrieved data. Each
assertion targets the *meaning* the old regex was standing in for:

  regex                          -> what is actually graded here
  --from-date/--to-date present   -> no returned event is older than the window
  --limit N                       -> the returned count does not exceed N
  --limit >200                    -> more than one server page came back
  --status Failure                -> every returned event is a failure
  org vs tenant scope             -> org events carry no TenantId, tenant events do
  (nothing)                       -> the records are really from THIS tenant

Scope is graded from an intrinsic property of the records rather than from the
command: tenant-scope events always carry a populated `TenantId`, while org-scope
events are not attached to a tenant and omit the field. The backend enforces this
at read time (org queries filter on `isnull(TenantId)`), so it cannot be faked by
writing a different flag.

Anti-forgery: the harness independently re-queries the tenant and requires the
saved records to share its OrganizationId. `OrganizationId` is stable regardless
of window or paging, so this corroborates provenance without being sensitive to
events arriving between the agent's call and this one.

Window checks are deliberately generous (a grace margin on each side). The point
is to catch an *unbounded* query that drags in months of history, not to police
an agent's boundary arithmetic — the old criterion only checked that the flags
were present at all.

Env (AUDIT_FILE and AUDIT_SCOPE required; the rest opt in to an assertion):
  AUDIT_FILE                  path the agent saved the JSON to
  AUDIT_SCOPE                 org | tenant
  AUDIT_WINDOW_DAYS           no event older than this many days (+ grace)
  AUDIT_MAX_COUNT             returned count must not exceed this
  AUDIT_MIN_COUNT             returned count must reach this, capped by what the
                              tenant actually holds (self-calibrating)
  AUDIT_STATUS                Success | Failure — every event must match
  AUDIT_MAX_DISTINCT_SOURCES  the query was narrowed: at most N distinct sources
  AUDIT_ALLOW_EMPTY           0 to require at least one event (default 1)
  AUDIT_LIVE_ARGS             extra flags the harness must add to its own
                              corroborating query so it asks the same question
                              (e.g. "--status=Failure"). Author-supplied only —
                              never agent text — and passed as an explicit argv
                              list, never through a shell.
  AUDIT_CORROBORATE_EMPTY     0 when the request is narrowed in a way the harness
                              cannot reproduce (a source/target-filtered
                              investigation), so an empty result passes without a
                              live comparison. Default 1.

Logging is PII-safe: counts, key names, category labels and truncated ids only —
never an actor email, actor name, client IP, or EventDetails value.
"""

import datetime
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared"))
from audit_helpers import (  # noqa: E402  (path set above)
    EVENT_SIGNATURE,
    env_flag,
    env_int,
    env_str,
    event_timestamp,
    fail,
    field,
    find_records,
    gid,
    keys_of,
    live_query,
    ok,
    status_of,
    unwrap,
    load_saved,
)

logging.basicConfig(level=logging.INFO, format="verify_audit_events: %(message)s")
logger = logging.getLogger(__name__)

# Slack on each end of the requested window. Agents resolve "the last 7 days"
# against the real clock and may round to whole days or pad the upper bound to
# the start of tomorrow; neither is the failure this check exists to catch.
LOWER_GRACE_DAYS = 2
UPPER_GRACE_DAYS = 2
# The server clamps a single events call to 200 records, so a returned count
# above this proves the CLI paginated internally rather than the agent
# hand-rolling a cursor loop.
SERVER_PAGE_CAP = 200


def window_args(days):
    """Bounds so the harness's corroborating query covers the same window.

    Without this, comparing an agent's windowed result against an unbounded read
    would compare two different questions: a tenant that was quiet for the last
    24h but busy last week would make a correct empty result look like a failed
    retrieval. The upper bound is nudged slightly into the future so events
    arriving during the run are not excluded.
    """
    if days is None:
        return []
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    start = now - datetime.timedelta(days=days)
    end = now + datetime.timedelta(minutes=5)
    return [
        "--from-date", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "--to-date", end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    ]


def live_extra_args():
    """Filter flags the harness adds so its query matches the agent's request.

    Without this, corroborating a filtered request against an UNfiltered read
    would compare two different questions — e.g. a status-filtered task that
    legitimately returns nothing would look like a failed retrieval merely
    because the tenant has unfiltered events. Values come from the task YAML the
    author writes, and reach `run_cli` as separate argv entries.
    """
    raw = env_str("AUDIT_LIVE_ARGS")
    return raw.split() if raw else []


def live_organization_id(scope):
    """OrganizationId as seen by the harness, or None when unobtainable.

    Deliberately unbounded — any recent event is a valid provenance anchor, and
    reusing the task's window would leave us without one whenever that window is
    quiet.
    """
    data = live_query(scope, "events", ["--limit", "5"])
    if not data or str(field(data, "Result")).lower() != "success":
        return None
    records = find_records(unwrap(data), EVENT_SIGNATURE) or []
    for record in records:
        org_id = field(record, "OrganizationId")
        if org_id:
            return str(org_id)
    return None


def check_provenance(records, scope):
    """Require the saved records to belong to the tenant the harness can see."""
    saved_orgs = {str(field(r, "OrganizationId")) for r in records if field(r, "OrganizationId")}
    if not saved_orgs:
        fail(
            "saved events carry no OrganizationId — cannot corroborate that they came "
            f"from this tenant; record keys={keys_of(records[0])}"
        )
    live_org = live_organization_id(scope)
    if live_org is None:
        # No anchor available (the tenant returned no events at all, or the read
        # failed). Say so rather than implying the data was corroborated.
        logger.info("no live OrganizationId anchor available — provenance not corroborated")
        return
    if live_org not in saved_orgs:
        fail(
            f"saved events are not from this tenant: their OrganizationId "
            f"({', '.join(sorted(gid(o) for o in saved_orgs))}) does not include the one the "
            f"harness reads back ({gid(live_org)})"
        )
    logger.info("provenance corroborated against live OrganizationId %s", gid(live_org))


def check_scope(records, scope):
    """Grade org-vs-tenant from the records themselves.

    Tenant-scope events always carry a populated TenantId. Org-scope events are
    not attached to any tenant and, in practice, omit the field entirely rather
    than returning null — so ABSENCE is the org signature and is treated as
    confirmation, not as a reason to skip. An earlier version skipped whenever the
    field was missing, which silently turned the assertion into a no-op for every
    org-scope task; the check only has teeth if the org case asserts something.
    """
    with_tenant = [r for r in records if field(r, "TenantId")]
    if scope == "tenant":
        if not with_tenant:
            fail(
                f"none of the {len(records)} saved events carry a populated TenantId — these "
                "look like ORG-scope events, but the request was for TENANT scope"
            )
        logger.info(
            "intrinsic scope check passed: %d/%d events carry a TenantId, as tenant-scope "
            "events do", len(with_tenant), len(records),
        )
        return
    if with_tenant:
        fail(
            f"{len(with_tenant)}/{len(records)} saved events carry a populated TenantId — these "
            "are TENANT-scope events, but the request was for ORG scope"
        )
    logger.info(
        "intrinsic scope check passed: none of the %d events carry a TenantId, as org-scope "
        "events do not", len(records),
    )


def check_window(records, days):
    """No returned event may predate the requested window (plus grace)."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    # Agents express windows as whole UTC days (`--from-date 2026-06-25`), so the
    # floor is midnight of the earliest allowed day — not the current time-of-day
    # N days back. Comparing a whole-day window against a time-of-day floor
    # rejects events from the morning of the boundary day, which is boundary
    # arithmetic the agent got right, not the unbounded query this check exists
    # to catch.
    floor_day = (now - datetime.timedelta(days=days + LOWER_GRACE_DAYS)).date()
    floor = datetime.datetime(floor_day.year, floor_day.month, floor_day.day)
    ceiling = now + datetime.timedelta(days=UPPER_GRACE_DAYS)
    stamped = [(r, event_timestamp(r)) for r in records]
    undated = [r for r, ts in stamped if ts is None]
    if undated and len(undated) == len(stamped):
        fail(
            "no saved event carries a parseable timestamp — cannot confirm the query was "
            f"time-bounded; record keys={keys_of(records[0])}"
        )
    too_old = [ts for _, ts in stamped if ts is not None and ts < floor]
    too_new = [ts for _, ts in stamped if ts is not None and ts > ceiling]
    if too_old:
        # Report how far past the boundary, not the timestamp itself: CreatedOn is
        # a field value from an audit record, and this module's contract is that
        # only counts, key names and truncated ids reach the log.
        overshoot = (floor - min(too_old)).days
        fail(
            f"query was not bounded to the requested {days}-day window: {len(too_old)} event(s) "
            f"predate it, the oldest by {overshoot} day(s) beyond a floor that already includes "
            f"{LOWER_GRACE_DAYS}d of grace"
        )
    if too_new:
        fail(
            f"{len(too_new)} saved event(s) are dated after the window's upper bound "
            f"{ceiling.isoformat()}Z — the payload is not a real result for this window"
        )
    if undated:
        logger.info("%d/%d saved events had no parseable timestamp", len(undated), len(stamped))
    logger.info("all dated events fall inside the %d-day window (+grace)", days)


def check_min_count(records, requested_min, scope, days):
    """Require `requested_min` events, capped by what the tenant actually holds.

    Self-calibrating so the assertion tests the agent, not the tenant's activity
    level: the harness asks for the same volume itself and lowers the bar to what
    came back. On a quiet org this degrades to "match what is really there".
    """
    args = ["--limit", str(requested_min), *window_args(days), *live_extra_args()]
    data = live_query(scope, "events", args)
    live_count = None
    if data and str(field(data, "Result")).lower() == "success":
        live = find_records(unwrap(data), EVENT_SIGNATURE)
        live_count = len(live) if live is not None else None
    if live_count is None:
        logger.info("could not measure live volume — skipping the minimum-count assertion")
        return
    # The harness measures volume AFTER the agent's query, and this tenant is
    # shared: concurrent tasks in the same run emit audit events, so the live
    # count can only have grown. Demanding parity would fail the agent for events
    # that did not exist when it looked. Allow headroom for that drift — the
    # assertion is about a truncated retrieval, not an exact match.
    drift_allowance = max(5, live_count // 20)
    effective = min(requested_min, live_count - drift_allowance)
    if len(records) < effective:
        fail(
            f"saved only {len(records)} events; the tenant returns {live_count} for the same "
            f"request, so at least {effective} were expected (allowing {drift_allowance} for "
            "events created during the run) — the retrieval was truncated"
        )
    # The >200 case: a single server call cannot exceed the page cap, so crossing
    # it proves pagination happened. Only assertable when the tenant is
    # comfortably above the cap — right at it, the agent could legitimately come
    # back with exactly one full page.
    if requested_min > SERVER_PAGE_CAP:
        if live_count >= SERVER_PAGE_CAP + 25:
            if len(records) <= SERVER_PAGE_CAP:
                fail(
                    f"saved {len(records)} events — at or below the {SERVER_PAGE_CAP}-record "
                    f"server page cap even though the tenant can return {live_count}; the "
                    "request did not paginate past a single page"
                )
            logger.info(
                "pagination confirmed: %d events exceeds the %d-record server page cap",
                len(records), SERVER_PAGE_CAP,
            )
        else:
            logger.info(
                "tenant holds only %d events for this window — too close to the %d-record page "
                "cap to assert pagination", live_count, SERVER_PAGE_CAP,
            )
    logger.info("count %d meets the effective minimum %d (live volume %d)",
                len(records), effective, live_count)


def main():
    path = env_str("AUDIT_FILE")
    scope = env_str("AUDIT_SCOPE")
    if not path or scope not in ("org", "tenant"):
        fail("internal: AUDIT_FILE and AUDIT_SCOPE (org|tenant) are required")

    payload = unwrap(load_saved(path))
    records = find_records(payload, EVENT_SIGNATURE)
    if records is None:
        fail(
            f"{path!r} holds no audit-events collection (no list of records carrying "
            f"{list(EVENT_SIGNATURE)}); top-level keys={keys_of(payload)}"
        )

    days = env_int("AUDIT_WINDOW_DAYS")
    allow_empty = env_flag("AUDIT_ALLOW_EMPTY", default=True)
    if not records:
        if not allow_empty:
            fail(f"{path!r} holds zero events, but this task requires at least one")
        if not env_flag("AUDIT_CORROBORATE_EMPTY", default=True):
            # The request was narrowed in a way the harness cannot reproduce, so
            # there is nothing to compare against. Say that plainly rather than
            # implying an empty result was corroborated.
            ok(f"{path!r} holds zero events — a legitimate outcome for a narrowed "
               "investigation query; not corroborated against a live comparison")
            return
        # A quiet window is a real outcome. Ask the tenant the SAME question —
        # same scope, same window, same filters — so "saved nothing" cannot mask
        # a failed retrieval, and a genuinely idle window cannot fail.
        data = live_query(scope, "events", ["--limit", "50", *window_args(days), *live_extra_args()])
        if data and str(field(data, "Result")).lower() == "success":
            live = find_records(unwrap(data), EVENT_SIGNATURE) or []
            if live:
                fail(
                    f"{path!r} holds zero events, but the same query returns {len(live)} at "
                    f"{scope} scope — the retrieval failed rather than the window being quiet"
                )
        ok(f"{scope} events window is genuinely empty on this tenant — retrieval corroborated")
        return

    sample = records[0]
    for required in ("Id", "EventType", "EventSource"):
        if field(sample, required) is None:
            fail(f"event record missing {required}; keys={keys_of(sample)}")

    check_provenance(records, scope)
    check_scope(records, scope)

    if days is not None:
        check_window(records, days)

    max_count = env_int("AUDIT_MAX_COUNT")
    if max_count is not None and len(records) > max_count:
        fail(
            f"saved {len(records)} events but the request capped the result at {max_count} — "
            "the returned volume was not limited as asked"
        )

    wanted_status = env_str("AUDIT_STATUS")
    if wanted_status:
        expected = wanted_status.strip().lower()
        statuses = [status_of(r) for r in records]
        if all(s is None for s in statuses):
            fail(
                "no saved event carries a readable Status — cannot confirm the status filter; "
                f"record keys={keys_of(sample)}"
            )
        offenders = [s for s in statuses if s is not None and s != expected]
        if offenders:
            counts = {value: offenders.count(value) for value in set(offenders)}
            fail(
                f"status filter was not applied: {len(offenders)}/{len(records)} saved events "
                f"are not {expected!r} (found {counts})"
            )
        logger.info("all %d saved events have status %s", len(records), expected)

    max_sources = env_int("AUDIT_MAX_DISTINCT_SOURCES")
    # Only meaningful on a result large enough for breadth to indicate an
    # unfiltered scan. `--search <term>` is a legitimate server-side narrowing
    # flag whose small result set can still span several sources, and penalizing
    # that would grade the agent's choice of filter rather than whether it
    # narrowed at all.
    if max_sources is not None and len(records) > 10:
        # Source names are catalog labels ("Folders", "Identity"), not PII.
        distinct = sorted({str(field(r, "EventSource")) for r in records if field(r, "EventSource")})
        if len(distinct) > max_sources:
            fail(
                f"the query was not narrowed server-side: saved events span {len(distinct)} "
                f"distinct sources {distinct[:6]} (expected at most {max_sources}) — looks like "
                "an unfiltered scan rather than a source/target-filtered query"
            )
        logger.info("narrowing confirmed: %d distinct source(s) %s", len(distinct), distinct)

    min_count = env_int("AUDIT_MIN_COUNT")
    if min_count is not None:
        check_min_count(records, min_count, scope, days)

    ok(
        f"{len(records)} {scope}-scope audit events verified from the live tenant "
        f"(schema, provenance, scope"
        + (f", {days}d window" if days is not None else "")
        + (f", <={max_count}" if max_count is not None else "")
        + (f", status={wanted_status}" if wanted_status else "")
        + ")"
    )


main()
