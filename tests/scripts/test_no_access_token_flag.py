"""Contract guard: no skill tells an agent to ask the CLI for its access token.

`uip login refresh --include-token` prints the live access token. It is hidden
from `--help` on purpose: it exists for programs that spawn `uip` and need the
token (the Flow VSCode extension), not for agents. An agent that runs it puts a
bearer token for the user's whole scope set into its own context, where it is
sent to the model and kept in session transcripts. Skills call REST endpoints
through the CLI instead, so the token never leaves the CLI process.

This test fails if `--include-token` appears anywhere in the repo outside this
file, so a skill, reference, task, script or hook cannot start using it.

Run from repo root:
    pytest tests/scripts/test_no_access_token_flag.py
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THIS_FILE = Path(__file__).resolve()
FORBIDDEN = "--include-token"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist"}


def _files_to_scan():
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == THIS_FILE:
            continue
        if SKIP_DIRS.intersection(path.relative_to(REPO_ROOT).parts):
            continue
        yield path


def _hits(text: str) -> list[int]:
    return [n for n, line in enumerate(text.splitlines(), 1) if FORBIDDEN in line]


def test_detector_matches_the_flag():
    # Guard the guard: a detector that never matches would pass forever.
    assert _hits("uip login refresh --include-token --output json") == [1]
    assert _hits("uip login refresh --output json") == []


def test_no_file_uses_include_token():
    offenders = []
    for path in _files_to_scan():
        data = path.read_bytes()
        if b"\0" in data:
            continue  # binary
        text = data.decode("utf-8", errors="replace")
        offenders += [f"{path.relative_to(REPO_ROOT)}:{n}" for n in _hits(text)]
    assert not offenders, (
        f"`{FORBIDDEN}` prints the CLI's access token into the agent's context. "
        "Call the endpoint through a `uip` command instead. Found at:\n  "
        + "\n  ".join(offenders)
    )
