#!/usr/bin/env python3
"""Unit test for find_sourcetype_discriminator() in check_dashboard.py.

Regression guard for a grader false negative: `--forbid-substr "sourceType"`
failed correct builds where sourceType only appeared as a "Trigger" column or
in a comment warning against it. Those builds failed on most Opus nightlies
from late October, and on gpt-6.1-sol. The same grep missed the skill's own
Wrong example, `SourceType eq 'Agent'`, because of the capital S.

The check must flag sourceType used to classify jobs, and nothing else.
"""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_dashboard import find_sourcetype_discriminator, strip_ts_comments  # noqa: E402

MISUSE = [
    """return (await new Jobs(sdk).getAll({ filter: "SourceType eq 'Agent'" })).items""",
    """const f = "sourceType eq 'Agent' and State eq 'Faulted'";""",
    """const f = `Source ne 'Manual' and CreationTime gt ${since}`;""",
    """const agentJobs = jobs.filter((j) => j.sourceType === 'Agent');""",
    """if (job?.sourceType !== "Manual") count++;""",
    """const isAgent = 'Agent' === job.sourceType;""",
    """rows.filter(r => r['sourceType'] == 'Agent')""",
]

ALLOWED = [
    """// sourceType is the trigger origin — never use it.""",
    """/* sourceType eq 'Agent' is the trap: it is the trigger origin */""",
    """/**\n * Agent jobs: ProcessType eq 'Agent'. NOT sourceType (trigger origin).\n */""",
    """const columns = [{key:"packageType",label:"Package type"},{key:"sourceType",label:"Trigger"}];""",
    """return items.map((j) => ({ key: j.key, sourceType: j.sourceType ?? '—' }));""",
    """const known = jobs.filter((j) => j.sourceType != null);""",
    """const opts = { select: 'Key,State,SourceType', filter: "ProcessType eq 'Agent'" };""",
    """const u = 'https://cloud.uipath.com/x'; const f = "packageType eq 'Agent'"; // not sourceType eq 'Agent'""",
    """<InfoTooltip text="Grouped by trigger source, not by agent." />""",
]


def hits_for(snippet: str) -> list:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "metric.ts"
        p.write_text(snippet + "\n", encoding="utf-8")
        return find_sourcetype_discriminator([p])


def test_flags_sourcetype_used_to_classify_jobs():
    missed = [s for s in MISUSE if not hits_for(s)]
    assert not missed, f"misuse not flagged: {missed}"


def test_allows_comments_columns_and_null_checks():
    flagged = [s for s in ALLOWED if hits_for(s)]
    assert not flagged, f"legitimate use flagged: {flagged}"


def test_strip_keeps_strings_and_line_numbers():
    src = "a // x\n/* b\nc */ \"// kept\"\n"
    out = strip_ts_comments(src)
    assert out.count("\n") == src.count("\n")
    assert '"// kept"' in out and "x" not in out.split("\n")[0]


def main() -> int:
    failures = 0
    for t in (test_flags_sourcetype_used_to_classify_jobs,
              test_allows_comments_columns_and_null_checks,
              test_strip_keeps_strings_and_line_numbers):
        try:
            t()
            print(f"PASS: {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}: {e}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
