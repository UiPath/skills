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

The generated-name check is the "a real export ran" signal, and it is the ONLY
anti-forgery lever in this tier (unlike the sources/events verifiers, nothing here
re-queries the tenant): only the CLI produces `audit_<from>_<to>_<generatedAt>`, so
a hand-written placeholder at the right path does not pass.

An earlier revision also accepted the generated output *moved* to the requested
folder, on the theory that day-file naming (`<YYYY-MM-DD>.json`) carried the same
signal. It does not — `touch 2026-07-27.json` satisfied it, which made every
export smoke forgeable. That allowance is gone: `--output-path` already takes a
base directory, so passing the folder the user named is the natural correct
behavior, and a cross-agent run confirmed claude, codex and gemini all do exactly
that. Requiring the generated name is both stronger and simpler.

Deep mode (`AUDIT_DEEP=1`, the artifact-verify tier) adds record-level schema
assertions and, for CSV, a spreadsheet-formula-injection guard: the CLI must
prefix any cell starting with `= + - @` (or TAB/CR) with a single quote, so a
regression that stops neutralizing those is caught on a real artifact rather than
only in a unit test.

Env:
  AUDIT_BASE_DIR    directory the user asked the export to be saved in
  AUDIT_FORMAT      json | csv
  AUDIT_DEEP        1 to add record-level schema + CSV-injection assertions
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

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_shared")
)
sys.path.insert(0, _shared_root)
from audit_helpers import (  # noqa: E402  (path set above)
    LTS_SIGNATURE,
    env_flag,
    env_int,
    env_str,
    fail,
    field,
    keys_of,
    ok,
    parse_ts,
    wait_for,
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
    with_tenant = [r for r in records if str(field(r, "TenantId") or "").strip()]
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
    # Waited on rather than checked once: an agent may drive the export through a
    # background runner and end its turn before the CLI finishes writing. The
    # assertion is that the export produced the artifact, not that it beat the
    # turn boundary.
    if not wait_for(lambda: os.path.isdir(base)):
        siblings = sorted(p for p in glob.glob("*") if os.path.isdir(p))[:10]
        fail(
            f"the export destination {base!r} does not exist — the export did not land where "
            f"the user asked; directories present={siblings}"
        )


def newest(paths):
    """Most recent of several generated outputs.

    An agent that self-corrects — exports, notices the wrong format or window,
    re-exports — legitimately leaves more than one generated output behind. The
    last one written is its answer; failing on the presence of an earlier attempt
    would punish the retry rather than the result.
    """
    return max(paths, key=os.path.getmtime)


def _generated_dirs(base):
    return sorted(
        p for p in glob.glob(os.path.join(base, "audit_*"))
        if os.path.isdir(p) and GENERATED_NAME.match(os.path.basename(p))
    )


def resolve_json_output(base):
    """Return (directory holding day files, description) for a json export."""
    generated = wait_for(lambda: _generated_dirs(base) or None) or []
    if not generated:
        present = sorted(os.listdir(base))[:12]
        fail(
            f"no CLI-generated json export found under {base!r} — expected an "
            f"'audit_<from>_<to>_<generatedAt>' folder; contents={present}"
        )
    if len(generated) > 1:
        chosen = newest(generated)
        logger.info(
            "%d generated export folders present (agent retried); grading the newest %r",
            len(generated), os.path.basename(chosen),
        )
    else:
        chosen = generated[0]
    return chosen, f"generated folder {os.path.basename(chosen)!r}"


def check_json_export(base, deep, min_days, expect_scope=None):
    directory, described = resolve_json_output(base)
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
    check_record_scope(scope_sample, expect_scope)
    ok(f"{described}: {len(day_files)} day file(s), {total} event(s), "
       f"{'LTS schema verified' if deep else 'structure verified'}")


def _generated_csvs(base):
    return sorted(
        p for p in glob.glob(os.path.join(base, "audit_*.csv"))
        if os.path.isfile(p) and GENERATED_NAME.match(os.path.basename(p))
    )


def resolve_csv_output(base):
    generated = wait_for(lambda: _generated_csvs(base) or None) or []
    if not generated:
        present = sorted(os.listdir(base))[:12]
        fail(
            f"no CLI-generated .csv found under {base!r} — expected "
            f"'audit_<from>_<to>_<generatedAt>.csv'; contents={present}. A folder of per-day JSON "
            "here would mean the CSV format was not selected."
        )
    if len(generated) > 1:
        chosen = newest(generated)
        logger.info(
            "%d generated .csv files present (agent retried); grading the newest %r",
            len(generated), os.path.basename(chosen),
        )
        return chosen
    return generated[0]


def check_csv_export(base, deep, min_days=None, expect_scope=None):
    # `resolve_csv_output` already fails when no generated .csv exists, which is
    # what "the CSV format was not selected" looks like on disk. A json folder
    # sitting alongside a real .csv is a self-corrected retry, not a wrong answer,
    # so its presence is not itself a failure.
    path = resolve_csv_output(base)
    check_window_from_name(os.path.basename(path), min_days)
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

    check_csv_scope(header, rows[1:], expect_scope)
    ok(f"{os.path.basename(path)}: {len(header)} columns, {len(rows) - 1} data row(s), "
       f"{'LTS schema + injection guard verified' if deep else 'structure verified'}")


def main():
    base = env_str("AUDIT_BASE_DIR")
    fmt = (env_str("AUDIT_FORMAT") or "json").lower()
    if not base:
        fail("internal: AUDIT_BASE_DIR is required")
    if fmt not in ("json", "csv"):
        fail(f"internal: AUDIT_FORMAT must be json or csv, got {fmt!r}")
    # Validated rather than compared loosely: a typo like `Tenant` would silently
    # match neither branch, disarming the scope assertion while still reporting
    # success. A misconfigured check is worse than no check.
    expect_scope = env_str("AUDIT_EXPECT_SCOPE")
    if expect_scope is not None:
        expect_scope = expect_scope.lower()
        if expect_scope not in ("org", "tenant"):
            fail(f"internal: AUDIT_EXPECT_SCOPE must be org or tenant, got {expect_scope!r}")

    require_base_dir(base)
    deep = env_flag("AUDIT_DEEP")
    min_days = env_int("AUDIT_MIN_DAYS")
    if fmt == "json":
        check_json_export(base, deep, min_days, expect_scope)
    else:
        check_csv_export(base, deep, min_days, expect_scope)


main()
