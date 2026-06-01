"""Contract guard: maestro flow/case checkers must read the debug RUNTIME
payload case-insensitively.

Background — uipath-cli PR #2266 made ``OutputFormatter`` recursively PascalCase
every key of a ``--output json`` ``Data`` payload. Checkers written against the
documented camelCase shape then read ``None`` and fail with misleading messages
(``finalStatus=None``; ``Statuses: []`` for terminate; ``{None}`` ID sets for
outlook). PR #1153 hardened ``_shared/flow_check.py`` but not the task-local
checkers, so the break kept resurfacing one layer deeper (skill-flow-terminate,
run 2026-06-01). The durable fix is: route every runtime-payload read through a
case-insensitive accessor (``_get_ci``).

This test fails if any checker reads a RUNTIME-ONLY key — ``finalStatus`` or
``elementExecutions``, which exist only in debug output, never in ``.flow`` /
``caseplan.json`` source — by a hard-coded lowercase ``.get("…")`` / ``["…"]``
instead of through ``_get_ci``. It deliberately targets only those two
unambiguous keys (``variables``/``outputs``/``value`` also appear in source
files and would false-positive).

Run from repo root:
    pytest tests/scripts/test_runtime_payload_key_casing.py
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS = REPO_ROOT / "tests" / "tasks"

# Runtime-only debug-payload keys. They never appear in .flow / caseplan source,
# so a literal-lowercase read of them is always an unguarded runtime read.
RUNTIME_ONLY_KEYS = ("finalStatus", "elementExecutions")

_RAW_READ = re.compile(
    r"""\.get\(\s*['"](?:%s)['"]\s*[,)]|\[\s*['"](?:%s)['"]\s*\]"""
    % ("|".join(RUNTIME_ONLY_KEYS), "|".join(RUNTIME_ONLY_KEYS))
)


def _files_to_scan():
    # The checker contract surface: success-criteria checkers and their shared
    # helpers. Diagnostics (e.g. canary.py) and unit tests are out of scope.
    for path in TASKS.rglob("check_*.py"):
        yield path
    for shared in TASKS.rglob("_shared/*.py"):
        if shared.name.startswith("test_"):
            continue
        yield shared


def test_no_raw_lowercase_runtime_key_reads():
    offenders = []
    for path in sorted(_files_to_scan()):
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if _RAW_READ.search(line):
                rel = path.relative_to(REPO_ROOT)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")

    assert not offenders, (
        "Runtime debug-payload keys must be read via _get_ci (case-insensitive) so a "
        "PascalCasing CLI (PR #2266) cannot silently break the checker. Offenders:\n  "
        + "\n  ".join(offenders)
    )
