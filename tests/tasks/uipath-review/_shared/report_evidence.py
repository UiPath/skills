"""Shared helpers for report-evidence checkers.

Both the review-CLI and guardrail-catalog checkers ask the same two questions of
a saved review report, so the regexes live here rather than drifting apart in
two copies. Imported by sibling `check_*.py` scripts, which coder_eval invokes
as `python3 $SKILLS_REPO_PATH/tests/tasks/uipath-review/_shared/check_*.py` --
so this directory is already `sys.path[0]` and a plain import works.
"""

import re
import shutil
import subprocess

# SKILL.md Critical Rule 11 / rule-catalog-workflow.md 2.5a: when a required
# input genuinely cannot be obtained, the report must say so HERE and not just
# anywhere in prose ("the CLI was unavailable, so I guessed" must not count).
SKIPPED_HEADING = re.compile(r"^#+\s*Rules Skipped\s*$", re.MULTILINE)

# Phrasing varies a lot between agents; observed forms include "unavailable",
# "does not provide the `review` command", and "unknown command". Keep this
# alternation generous -- a missed phrasing turns an honest skip declaration
# into a confusing failure, while a spurious match only relaxes a branch that
# already fails on its own.
_UNAVAILABLE = (
    r"(unavailable|not\s+available|not\s+installed|could\s+not\s+be\s+(run|fetched|retrieved)|failed"
    r"|does\s+not\s+(provide|support|have)|unknown\s+command|missing|unsupported)"
)


def declares_unavailable(text: str, subject: str) -> bool:
    """True if the report's 'Rules Skipped' section calls `subject` unavailable.

    `subject` is an alternation of names for the thing (e.g. the review CLI, the
    guardrail catalog). Matching is confined to the section body so prose
    elsewhere cannot satisfy the contract.
    """
    heading = SKIPPED_HEADING.search(text)
    if not heading:
        return False
    body = text[heading.end():]
    return bool(re.search(rf"({subject})[^.\n]*{_UNAVAILABLE}", body, re.IGNORECASE))


def cli_identity(uip: str) -> str:
    """`which` + `--version` of the CLI this checker resolved.

    Printed on every run because agent and checker resolve `uip` through
    different shells: the agent's is a login shell (and, under
    `sandbox.mock_path_dirs`, a per-task HOME whose dotfiles never run), so a
    host with several `uip` installs can hand them different binaries. When that
    happens the report and the ground truth disagree for environmental reasons,
    and the criterion detail needs to say which binary it spoke to.
    """
    path = shutil.which(uip) or uip
    try:
        proc = subprocess.run([uip, "--version"], capture_output=True, text=True, timeout=60)
        version = (proc.stdout or proc.stderr).strip().splitlines()[-1] if proc.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError, IndexError):
        version = "unknown"
    return f"{path} (v{version})"
