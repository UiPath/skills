"""--forbid-sourcetype-filter flags sourceType used to classify jobs, and nothing else."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_dashboard import sourcetype_misuse  # noqa: E402

MISUSE = [
    """getAll({ filter: "SourceType eq 'Agent'" })""",  # the skill's own Wrong example
    """const f = `sourceType ne 'Manual'`;""",
    """jobs.filter((j) => j.sourceType === 'Agent')""",
    """if (job?.sourceType !== "Manual") n++;""",
    """const isAgent = 'Agent' === job.sourceType;""",
]
ALLOWED = [
    """// never filter on sourceType eq 'Agent'""",
    """/* sourceType is the trigger origin */ const f = "packageType eq 'Agent'";""",
    """const columns = [{key:"sourceType",label:"Trigger"}];""",
    """items.map((j) => ({ sourceType: j.sourceType ?? '—' }))""",
    """jobs.filter((j) => j.sourceType != null)""",
]


def flagged(snippet: str) -> bool:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d, "metric.ts")
        p.write_text(snippet + "\n", encoding="utf-8")
        return bool(sourcetype_misuse([p]))


def test_sourcetype_misuse():
    assert [s for s in MISUSE if not flagged(s)] == []
    assert [s for s in ALLOWED if flagged(s)] == []
