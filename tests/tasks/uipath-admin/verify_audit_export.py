#!/usr/bin/env python3
"""Verify a real `uip admin audit <scope> export` artifact on disk.

Replaces the export tasks' command-string matching with assertions on what the
export actually produced:

  regex                              -> what is actually graded here
  --output-path <requested folder>    -> the artifact exists at the destination
                                         the user asked for
  --file-format csv / json default    -> the artifact has the requested SHAPE
                                         (one merged .csv vs a folder of day
                                         files) — not merely the flag spelling
  (nothing)                           -> the name/layout is CLI-generated, so the
                                         file was produced by a real export

The generated-name check is the "a real export ran" signal: only the CLI produces
`audit_<from>_<to>_<generatedAt>`, so a hand-written placeholder file at the right
path does not pass. When a task credits moving the generated output to the
requested name (`AUDIT_ALLOW_FLAT`), the day-file naming convention
(`<YYYY-MM-DD>.json`) carries that signal instead.

Deep mode (`AUDIT_DEEP=1`, the artifact-verify tier) adds record-level schema
assertions and, for CSV, a spreadsheet-formula-injection guard: the CLI must
prefix any cell starting with `= + - @` (or TAB/CR) with a single quote, so a
regression that stops neutralizing those is caught on a real artifact rather than
only in a unit test.

Env:
  AUDIT_BASE_DIR    directory the user asked the export to be saved in
  AUDIT_FORMAT      json | csv
  AUDIT_DEEP        1 to add record-level schema + CSV-injection assertions
  AUDIT_ALLOW_FLAT  1 to also accept the generated output moved to the base dir
  AUDIT_MIN_DAYS    minimum number of whole UTC days the export must cover
  AUDIT_EXPECT_SCOPE  org | tenant — grade scope from the records themselves:
                      org-scope exports are not attached to a tenant and carry an
                      empty TenantId, tenant-scope exports always populate it.
                      Catches a wrong-scope export, which matching the word `org`
                      in the command never could.

An empty window is a legitimate outcome — the long-term store lags the live
`events` endpoint by up to ~48h, so recent days come back empty by design. All
assertions here are therefore structural, never "at least N events".

Logging is PII-safe: audit records carry actor emails and client IPs, so failures
report file names, counts, column/key NAMES and row indexes — never a cell or
field value.
"""

import csv
import glob
import json
import logging
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared"))
from audit_helpers import (  # noqa: E402  (path set above)
    LTS_SIGNATURE,
    env_flag,
    env_int,
    env_str,
    fail,
    keys_of,
    ok,
    parse_ts,
)

logging.basicConfig(level=logging.INFO, format="verify_audit_export: %(message)s")
logger = logging.getLogger(__name__)

# LTS-schema columns/keys every exported audit record carries.
REQUIRED_LTS = ("Identifier", "DateCreatedUtc", "OrganizationId", "ActorId",
                "Action", "Source", "Category")
# The CLI's generated output name: audit_<from>_<to>_<generatedAt>.
GENERATED_NAME = re.compile(r"^audit_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})_")
# Day-wise file the json export writes inside the generated folder.
DAY_FILE = re.compile(r"^\d{4}-\d{2}-\d{2}.*\.json$")
# Cells a spreadsheet would evaluate as a formula unless neutralized.
FORMULA_LEAD = ("=", "+", "-", "@", "\t", "\r")


def check_window_from_name(name, min_days):
    """Grade the exported window from the CLI-generated name, not from the data.

    The generated name carries the requested bounds
    (`audit_<from>_<to>_<generatedAt>`), so the window is checkable even when the
    export is empty — which it legitimately is for a recent window, since the
    long-term store lags the live endpoint by up to ~48h. Counting day files
    instead would flake exactly when the tenant is quiet.
    """
    if min_days is None:
        return
    match = GENERATED_NAME.match(name)
    if not match:
        logger.info("output name is not CLI-generated — cannot grade the window from it")
        return
    start, end = (parse_ts(match.group(1)), parse_ts(match.group(2)))
    if start is None or end is None:
        logger.info("could not parse the window out of %r — skipping the span assertion", name)
        return
    span = (end - start).days + 1  # both bounds are whole-day inclusive
    if span < min_days:
        fail(
            f"the export covers {span} whole UTC day(s) ({match.group(1)}..{match.group(2)}) but "
            f"the request needs at least {min_days} — the window was narrower than asked"
        )
    logger.info("window spans %d whole UTC day(s) — meets the %d-day minimum", span, min_days)


def check_record_scope(records, expected):
    """Grade org-vs-tenant from exported records, not from the command text.

    Silent on an empty window: the long-term store lags by up to ~48h, so a
    recent window can legitimately export nothing, and there is then no evidence
    either way. Saying so beats inventing a verdict.
    """
    if not expected or not records:
        if expected:
            logger.info("export produced no records — skipping the scope assertion")
        return
    with_tenant = [r for r in records if str(r.get("TenantId") or r.get("tenantId") or "").strip()]
    if expected == "org":
        if with_tenant:
            fail(
                f"{len(with_tenant)}/{len(records)} exported records carry a TenantId — this is a "
                "TENANT-scope export, but the request was for ORG scope"
            )
        logger.info(
            "scope assertion passed: none of the %d exported records carry a TenantId, as "
            "org-scope events do not", len(records),
        )
        return
    if not with_tenant:
        fail(
            f"none of the {len(records)} exported records carry a TenantId — this looks like an "
            "ORG-scope export, but the request was for TENANT scope"
        )
    logger.info(
        "scope assertion passed: %d/%d exported records carry a TenantId, as tenant-scope "
        "events do", len(with_tenant), len(records),
    )


def check_csv_scope(header, rows, expected):
    """Same scope assertion for a CSV artifact, without printing any cell."""
    if not expected or "TenantId" not in header:
        if expected:
            logger.info("no TenantId column in the CSV — skipping the scope assertion")
        return
    index = header.index("TenantId")
    values = [row[index].strip() for row in rows if len(row) > index]
    if not values:
        logger.info("CSV has no data rows — skipping the scope assertion")
        return
    populated = [v for v in values if v]
    if expected == "org" and populated:
        fail(
            f"{len(populated)}/{len(values)} exported rows populate TenantId — this is a "
            "TENANT-scope export, but the request was for ORG scope"
        )
    if expected == "tenant" and not populated:
        fail(
            f"none of the {len(values)} exported rows populate TenantId — this looks like an "
            "ORG-scope export, but the request was for TENANT scope"
        )
    logger.info("scope assertion passed: CSV rows are consistent with %s scope", expected)


def require_base_dir(base):
    if not os.path.isdir(base):
        siblings = sorted(p for p in glob.glob("*") if os.path.isdir(p))[:10]
        fail(
            f"the export destination {base!r} does not exist — the export did not land where "
            f"the user asked; directories present={siblings}"
        )


def resolve_json_output(base, allow_flat):
    """Return (directory holding day files, description) for a json export."""
    generated = sorted(
        p for p in glob.glob(os.path.join(base, "audit_*"))
        if os.path.isdir(p) and GENERATED_NAME.match(os.path.basename(p))
    )
    if len(generated) > 1:
        fail(
            f"expected ONE generated export folder under {base!r}, found {len(generated)}: "
            f"{[os.path.basename(p) for p in generated]} — repeated exports collided"
        )
    if generated:
        return generated[0], f"generated folder {os.path.basename(generated[0])!r}"
    if allow_flat:
        # The task credits moving the generated folder to the requested name, so
        # the CLI-produced signal is the day-file naming instead.
        day_files = [f for f in os.listdir(base) if DAY_FILE.match(f)]
        if day_files:
            return base, f"day files placed directly in {base!r}"
        nested = sorted(p for p in glob.glob(os.path.join(base, "*")) if os.path.isdir(p))
        for candidate in nested:
            if any(DAY_FILE.match(f) for f in os.listdir(candidate)):
                return candidate, f"day files under {os.path.basename(candidate)!r}"
    present = sorted(os.listdir(base))[:12]
    fail(
        f"no CLI-generated json export found under {base!r} — expected an "
        f"'audit_<from>_<to>_<generatedAt>' folder"
        + (" or day-wise <YYYY-MM-DD>.json files" if allow_flat else "")
        + f"; contents={present}"
    )


def check_json_export(base, deep, allow_flat, min_days):
    directory, described = resolve_json_output(base, allow_flat)
    check_window_from_name(os.path.basename(directory), min_days)
    day_files = sorted(f for f in os.listdir(directory) if f.endswith(".json"))
    misnamed = [f for f in day_files if not DAY_FILE.match(f)]
    if misnamed:
        # Nested-ZIP entries are flattened to <inner>_<outer>.json, so tolerate a
        # suffix, but the leading calendar day must be there.
        fail(
            f"{len(misnamed)} file(s) in {described} are not day-wise exports "
            f"(expected <YYYY-MM-DD>.json): {misnamed[:6]}"
        )
    if not day_files:
        # A window whose days are all inside the long-term store's ~48h lag writes
        # no day files at all. The CLI-generated output itself is the evidence the
        # export ran; asserting a file count here would flake on a quiet tenant.
        ok(f"{described} exists but holds no per-day files — the requested window is "
           "entirely inside the long-term store's lag; structural assertion holds")
        return

    total = 0
    sample = None
    # Bounded sample for the scope assertion — a wrong-scope export is wrong in
    # every record, so a few hundred is ample and keeps memory flat on a big window.
    scope_sample = []
    for name in day_files:
        path = os.path.join(directory, name)
        try:
            with open(path, encoding="utf-8-sig") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            fail(f"{name} is not valid JSON (line {exc.lineno}) — the export wrote a corrupt day file")
        if not isinstance(payload, list):
            fail(f"{name} is not a JSON array (got {type(payload).__name__}) — wrong export shape")
        total += len(payload)
        if sample is None and payload and isinstance(payload[0], dict):
            sample = payload[0]
        if len(scope_sample) < 300:
            scope_sample.extend(r for r in payload if isinstance(r, dict))

    if sample is None:
        # Every day empty: real for a window inside the long-term store's lag.
        ok(f"{described}: {len(day_files)} day file(s), all empty JSON arrays — "
           "structural assertion holds for an idle window")
        return
    if deep:
        missing = [key for key in REQUIRED_LTS if key not in sample]
        if missing:
            fail(
                f"exported event is missing LTS-schema keys {missing}; "
                f"keys present={keys_of(sample)}"
            )
    check_record_scope(scope_sample, env_str("AUDIT_EXPECT_SCOPE"))
    ok(f"{described}: {len(day_files)} day file(s), {total} event(s), "
       f"{'LTS schema verified' if deep else 'structure verified'}")


def resolve_csv_output(base, allow_flat):
    generated = sorted(
        p for p in glob.glob(os.path.join(base, "audit_*.csv"))
        if os.path.isfile(p) and GENERATED_NAME.match(os.path.basename(p))
    )
    if len(generated) > 1:
        fail(
            f"expected ONE generated .csv under {base!r}, found {len(generated)}: "
            f"{[os.path.basename(p) for p in generated]}"
        )
    if generated:
        return generated[0]
    if allow_flat:
        any_csv = sorted(p for p in glob.glob(os.path.join(base, "*.csv")) if os.path.isfile(p))
        if len(any_csv) == 1:
            return any_csv[0]
        if len(any_csv) > 1:
            fail(f"expected ONE .csv under {base!r}, found {[os.path.basename(p) for p in any_csv]}")
    present = sorted(os.listdir(base))[:12]
    fail(
        f"no CLI-generated .csv found under {base!r} — expected "
        f"'audit_<from>_<to>_<generatedAt>.csv'; contents={present}. A folder of per-day JSON "
        "here would mean the CSV format was not selected."
    )


def check_csv_export(base, deep, min_days=None):
    path = resolve_csv_output(base, env_flag("AUDIT_ALLOW_FLAT"))
    check_window_from_name(os.path.basename(path), min_days)
    # A json export must NOT also be present — that would mean the requested
    # single-CSV shape was not what the agent actually produced.
    stray = [p for p in glob.glob(os.path.join(base, "audit_*")) if os.path.isdir(p)]
    if stray:
        fail(
            f"the CSV export is accompanied by a json export folder "
            f"{[os.path.basename(p) for p in stray]} — the requested single-CSV shape is ambiguous"
        )
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    except OSError as exc:
        fail(f"{os.path.basename(path)} could not be read ({exc.__class__.__name__})")
    if not rows:
        fail(f"{os.path.basename(path)} is empty — a valid export always writes a header row")

    header = rows[0]
    missing = [column for column in REQUIRED_LTS if column not in header]
    if missing:
        fail(
            f"CSV header is missing LTS-schema columns {missing}; "
            f"columns present={sorted(header)[:14]}"
        )
    for index, row in enumerate(rows[1:], start=1):
        if len(row) != len(header):
            fail(
                f"CSV row {index} has {len(row)} columns but the header has {len(header)} — "
                "rows are misaligned with the shared header"
            )

    if deep:
        # Formula-injection guard on a real artifact: the exporter must neutralize
        # any cell a spreadsheet would evaluate. Report the location only, never
        # the cell contents.
        for index, row in enumerate(rows[1:], start=1):
            for column, cell in zip(header, row):
                if cell[:1] in FORMULA_LEAD:
                    fail(
                        f"CSV cell at row {index}, column {column!r} begins with an "
                        "un-neutralized spreadsheet formula character — the export must prefix "
                        "such values with a single quote (formula-injection regression)"
                    )
        logger.info("formula-injection guard passed across %d data row(s)", len(rows) - 1)

    check_csv_scope(header, rows[1:], env_str("AUDIT_EXPECT_SCOPE"))
    ok(f"{os.path.basename(path)}: {len(header)} columns, {len(rows) - 1} data row(s), "
       f"{'LTS schema + injection guard verified' if deep else 'structure verified'}")


def main():
    base = env_str("AUDIT_BASE_DIR")
    fmt = (env_str("AUDIT_FORMAT") or "json").lower()
    if not base:
        fail("internal: AUDIT_BASE_DIR is required")
    if fmt not in ("json", "csv"):
        fail(f"internal: AUDIT_FORMAT must be json or csv, got {fmt!r}")

    require_base_dir(base)
    deep = env_flag("AUDIT_DEEP")
    if fmt == "json":
        check_json_export(base, deep, env_flag("AUDIT_ALLOW_FLAT"), env_int("AUDIT_MIN_DAYS"))
    else:
        check_csv_export(base, deep, env_int("AUDIT_MIN_DAYS"))


main()
