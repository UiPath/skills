"""Assert a conversational coded agent produced two distinct local turns.

Grades the *outcome* of chatting twice, not how many Bash calls the
agent used: `command_executed` with `min_count: 2` counts matching tool
invocations, so an agent that chains both `uip codedagent run` calls in
one shell command is docked for a task it completed correctly.

An echo agent's reply is `"<message> echo"`. Two turns with two
different messages therefore leave two distinct echoed replies on disk.
This helper collects them from the files the agent saved and requires at
least two.

Extraction order:

  1. JSON files — every string value ending in ` echo` (recursive walk).
  2. Plain-text files (`.txt`, `.log`, `.md`, `.out`, `.jsonl`) — line
     scan, for agents that tee replies instead of writing JSON.

Source files (`.py`) are skipped: the workflow itself contains the
f-string that builds the suffix.

A transcript line carries a label (`Reply:   hello there echo`), which
the line scan cannot tell from the reply itself, so each labelled match
also yields an unlabelled variant. Corroboration then decides which of
the two is real.

Each reply is **corroborated**: its message part must occur at least
twice across the project's files — once as the message that was
submitted (an input file, a transcript's user turn, the runtime's
`__uipath` state) and once inside the reply itself. Corroboration scans
bytes, so binary runtime state counts too.

Corroboration is a **filter**, not a veto: uncorroborated candidates are
dropped and the corroborated ones counted, so extraction noise (a label
the scan kept, a reply quoted in prose) cannot fail a run that really
chatted twice. A hand-written reply with no submitted message behind it
is dropped and therefore does not count toward `min_turns`. Replies that
differ only by a leading label collapse to the shortest form, so one turn
saved in several places counts once.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUFFIX = " echo"
MAX_BYTES = 1_000_000
# Corroboration reads runtime state files, which are larger than the
# reply files the extractor looks at.
MAX_CORROBORATION_BYTES = 20_000_000
SKIP_DIRS = {".venv", ".uipath", ".agent", ".claude", "node_modules", "__pycache__", ".git"}
TEXT_SUFFIXES = {".txt", ".log", ".md", ".out", ".jsonl"}
# `{...}` / `$...` markers mean the line is a template or command, not a reply.
TEMPLATE_MARKERS = ("{", "}", "$")
ECHO_LINE = re.compile(r"([^\"'\n\r]{1,200}?)" + re.escape(SUFFIX) + r"(?=[\"'.,\s]|$)")
# A transcript label the line scan would otherwise keep as part of the
# reply: `Reply:   hello there echo`, `assistant: ... echo`, `- Out: ...`.
LABEL_PREFIX = re.compile(r"^[-*\s]*[A-Za-z][\w .\-]{0,30}:\s*")


def _candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix not in {".json"} | TEXT_SUFFIXES:
            continue
        if path.stat().st_size > MAX_BYTES:
            continue
        files.append(path)
    return files


def _echo_strings(node: object) -> list[str]:
    if isinstance(node, str):
        return [node] if node.endswith(SUFFIX) and len(node) > len(SUFFIX) else []
    if isinstance(node, dict):
        return [s for v in node.values() for s in _echo_strings(v)]
    if isinstance(node, list):
        return [s for v in node for s in _echo_strings(v)]
    return []


def _replies_from_json(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return []
    return _echo_strings(doc)


def _replies_from_text(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    replies = []
    for match in ECHO_LINE.finditer(text):
        reply = (match.group(1) + SUFFIX).strip()
        if any(marker in reply for marker in TEMPLATE_MARKERS):
            continue
        # Keep both forms — corroboration picks whichever is the real
        # reply, so a labelled transcript and a bare reply both work.
        for candidate in (reply, LABEL_PREFIX.sub("", reply).strip()):
            if candidate != SUFFIX.strip():
                replies.append(candidate)
    return replies


def collect_echo_replies(root: Path) -> dict[str, list[str]]:
    """Map each distinct echoed reply to the files it was found in."""
    found: dict[str, list[str]] = {}
    for path in _candidate_files(root):
        replies = _replies_from_json(path) if path.suffix == ".json" else []
        if not replies:
            replies = _replies_from_text(path)
        for reply in replies:
            found.setdefault(reply.strip(), []).append(str(path.relative_to(root)))
    return found


def _message_occurrences(root: Path, message: str) -> int:
    """Count byte occurrences of `message` across the project's files."""
    needle = message.encode("utf-8")
    total = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts) or path.suffix == ".py":
            continue
        try:
            if path.stat().st_size > MAX_CORROBORATION_BYTES:
                continue
            total += path.read_bytes().count(needle)
        except OSError:
            continue
    return total


def corroborated_replies(root: Path, replies: dict[str, list[str]]) -> dict[str, int]:
    """Map each reply to how often its message part occurs project-wide."""
    counts = {}
    for reply in replies:
        message = reply[: -len(SUFFIX)]
        counts[reply] = _message_occurrences(root, message) if message else 0
    return counts


def _collapse_labelled(replies: set[str]) -> set[str]:
    """Drop replies that are another reply plus a leading label."""
    return {
        reply
        for reply in replies
        if not any(other != reply and reply.endswith(other) for other in replies)
    }


def assert_two_local_turns(root: Path, min_turns: int = 2) -> None:
    found = collect_echo_replies(root)
    counts = corroborated_replies(root, found)
    turns = _collapse_labelled({reply for reply, n in counts.items() if n >= 2})
    if len(turns) < min_turns:
        dropped = sorted(reply for reply, n in counts.items() if n < 2)
        detail = (
            "; ".join(f"{reply!r} in {sorted(set(files))}" for reply, files in found.items())
            or "none"
        )
        sys.exit(
            f"FAIL: expected at least {min_turns} distinct echoed replies "
            f"(`<message>{SUFFIX}`) saved under {root} with their submitted message "
            f"also on disk, found {len(turns)}. Extracted: {detail}."
            + (
                f" Dropped as uncorroborated (message part occurs only inside the "
                f"reply itself): {', '.join(repr(r) for r in dropped)}."
                if dropped
                else ""
            )
            + " The agent must chat locally twice with two different messages and "
            "save each reply."
        )
    print(
        f"OK: {len(turns)} distinct echoed replies from local chat turns, each with a "
        f"submitted message on disk: {sorted(turns)}"
    )
