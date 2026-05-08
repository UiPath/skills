"""Parse a Claude Code session JSONL → uip calls + presenter output.

Pure parser. No file writes. Emits a single JSON document on stdout.

Output schema:
    {
      "uip_calls": [
        {
          "args": "<everything after the bare 'uip' token>",
          "stdout": "<captured tool_result text>",
          "exit_code": <int|null>,
          "raw_command": "<full Bash input.command, unmodified>"
        },
        ...
      ],
      "presenter_output": "<final assistant text after the last tool_use>",
      "inferred_scenario_name": "<slug>",
      "diagnostics": {
        "uip_calls_total": <int>,
        "uip_calls_unmatched": <int>,
        "transcript_lines": <int>
      }
    }

Usage:
    python extract_session.py <transcript.jsonl> > extracted.json

The script handles two common JSONL line shapes used by Claude Code:
    1. {"type": "assistant"|"user"|"system", "message": {...}}
    2. Bare {"role": ..., "content": [...]} (legacy/raw)

A `uip` call is any Bash tool_use whose `input.command` contains a
bare `uip` token (not `./uip`, not `mocks/uip`, not `uipath` prefix).

`presenter_output` is the last assistant text block in the transcript
after the most recent tool_result — this is the diagnostics skill's
final user-facing answer (the presenter sub-agent's output relayed by
the orchestrator).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Match a bare `uip` invocation. Reject paths like `./uip`, `mocks/uip`,
# and prefix matches like `uipath`. Allow leading whitespace, `cd ... &&`,
# `PATH=... `, and env-var prefixes.
UIP_INVOCATION_RE = re.compile(r"(?:^|[\s;&|])uip(\s+|$)")

# Strip leading shell prelude (cd, env vars) and trailing redirects so the
# `args` field is just the uip subcommand and flags.
LEADING_PRELUDE_RE = re.compile(
    r"""^\s*
        (?:cd\s+[^&;]+(?:&&|;)\s*)?     # optional cd <dir> &&
        (?:[A-Z_][A-Z0-9_]*=\S+\s+)*    # optional ENV=value prefixes
        uip\s+                          # the bare uip token
    """,
    re.VERBOSE,
)
TRAILING_REDIRECT_RE = re.compile(
    r"""(?:\s*
        (?:
            (?:\d?>+\s*\S+)          # > file, 2> file, &> file
          | (?:2>&1|&>)              # combined stderr redirects
          | (?:;.*)                  # ; chained command (rest of string)
          | (?:\|.*)                 # | piped command (rest of string)
        )
    )+\s*$
    """,
    re.VERBOSE | re.DOTALL,
)


def _normalize_message(line_obj: dict) -> tuple[str | None, list]:
    """Return (role, content_list) for a transcript line, or (None, []).

    Accepts both wrapper shape `{"type": ..., "message": {...}}` and bare
    `{"role": ..., "content": [...]}`.
    """
    if "message" in line_obj and isinstance(line_obj["message"], dict):
        msg = line_obj["message"]
    else:
        msg = line_obj
    role = msg.get("role")
    content = msg.get("content", [])
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    return role, content


REDIRECT_TARGET_RE = re.compile(
    r"""\d?>+\s*(?:"([^"]+)"|'([^']+)'|(\S+))""",
    re.VERBOSE,
)


def _extract_uip_args(command: str) -> str:
    """Strip cd/env prelude and trailing redirects from a Bash command."""
    stripped = LEADING_PRELUDE_RE.sub("", command)
    stripped = TRAILING_REDIRECT_RE.sub("", stripped)
    return stripped.strip()


def _extract_redirect_target(command: str) -> str | None:
    """Return the first stdout redirect target in `command`, or None."""
    m = REDIRECT_TARGET_RE.search(command)
    if not m:
        return None
    return m.group(1) or m.group(2) or m.group(3)


def _is_uip_call(command: str) -> bool:
    """True if the command runs the bare `uip` binary (not `./uip`, not `uipath`)."""
    if not isinstance(command, str):
        return False
    return bool(UIP_INVOCATION_RE.search(command))


def _flatten_text(content: list) -> str:
    """Concatenate all text blocks from a content array."""
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "".join(parts)


def _flatten_tool_result(content) -> str:
    """tool_result content can be str or [{type:'text', text:...}, ...]."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return _flatten_text(content)
    return ""


def parse_transcript(path: Path) -> dict:
    """Accepts a single .jsonl OR a directory containing transcripts.

    Directory mode walks `*.jsonl` recursively. Files under a `subagents/`
    segment are treated as sub-agent transcripts; their `uip` calls
    contribute to `uip_calls`, but their final assistant text is ignored.
    The `presenter_output` is taken from the largest main (non-subagent)
    transcript.
    """
    if path.is_dir():
        all_jsonl = sorted(path.rglob("*.jsonl"))
        main_files = [p for p in all_jsonl if "subagents" not in p.parts]
        sub_files = [p for p in all_jsonl if "subagents" in p.parts]
    else:
        all_jsonl = [path]
        main_files = [path]
        sub_files = []

    main_files.sort(key=lambda p: p.stat().st_size, reverse=True)
    primary_main = main_files[0] if main_files else None

    aggregated_calls: list[dict] = []
    presenter_output = ""
    inferred_release_name: str | None = None
    transcript_lines = 0
    unmatched = 0
    user_initial_prompt: str | None = None

    for f in main_files + sub_files:
        result = _parse_one(f)
        aggregated_calls.extend(result["uip_calls"])
        transcript_lines += result["transcript_lines"]
        unmatched += result["unmatched"]
        if inferred_release_name is None and result["release_name"]:
            inferred_release_name = result["release_name"]
        if f == primary_main:
            presenter_output = result["last_assistant_text"]
            user_initial_prompt = result["first_user_text"]

    inferred = (
        _slugify(inferred_release_name) if inferred_release_name else "diagnostic-scenario"
    )

    return {
        "uip_calls": aggregated_calls,
        "presenter_output": presenter_output.strip(),
        "user_initial_prompt": (user_initial_prompt or "").strip(),
        "inferred_scenario_name": inferred,
        "diagnostics": {
            "uip_calls_total": len(aggregated_calls),
            "uip_calls_unmatched": unmatched,
            "transcript_lines": transcript_lines,
            "main_files": [str(p) for p in main_files],
            "sub_files": [str(p) for p in sub_files],
        },
    }


PRESENTER_MARKERS = (
    "Root Cause:",
    "Root cause:",
    "**Root Cause",
    "**Root cause",
    "Final Resolution",
    "## Resolution",
    "What went wrong:",
)


def _looks_like_presenter(text: str) -> bool:
    return any(m in text for m in PRESENTER_MARKERS)


def _parse_one(path: Path) -> dict:
    """Parse a single transcript file. Returns intermediate state."""
    transcript_lines = 0
    pending_tool_uses: dict[str, dict] = {}
    uip_calls: list[dict] = []
    last_assistant_text_after_tools = ""
    last_presenter_like = ""
    first_user_text: str | None = None
    last_was_tool_result = False
    project_release_name: str | None = None

    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            transcript_lines += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            role, content = _normalize_message(obj)
            if role is None:
                continue

            if role == "assistant":
                # Capture text and tool_use blocks.
                text_block = _flatten_text(content)
                if text_block and not pending_tool_uses and last_was_tool_result:
                    # First post-tool-result assistant text — keep updating
                    # so we end up with the final one.
                    last_assistant_text_after_tools = text_block
                if text_block and _looks_like_presenter(text_block):
                    last_presenter_like = text_block
                # Track tool_use blocks for later result matching.
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use" and block.get("name") == "Bash":
                        cmd = (block.get("input") or {}).get("command", "")
                        if _is_uip_call(cmd):
                            pending_tool_uses[block["id"]] = {
                                "raw_command": cmd,
                                "args": _extract_uip_args(cmd),
                                "redirect_target": _extract_redirect_target(cmd),
                            }
                last_was_tool_result = False

            elif role == "user":
                # Capture the first plain-text user message as the initial prompt.
                if first_user_text is None:
                    if isinstance(content, list):
                        text_block = _flatten_text(content)
                    elif isinstance(content, str):
                        text_block = content
                    else:
                        text_block = ""
                    if text_block.strip():
                        first_user_text = text_block.strip()
                # Look for tool_result blocks pairing back to our uip uses.
                saw_tool_result = False
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_result":
                        continue
                    saw_tool_result = True
                    tool_use_id = block.get("tool_use_id")
                    if tool_use_id not in pending_tool_uses:
                        continue
                    pending = pending_tool_uses.pop(tool_use_id)
                    stdout = _flatten_tool_result(block.get("content", ""))
                    exit_code = None
                    # Try to recover an exit code if the user echoed one.
                    m = re.search(r"(?:Exit|exit):\s*(\d+)", stdout)
                    if m:
                        exit_code = int(m.group(1))
                    elif block.get("is_error"):
                        exit_code = 1
                    if project_release_name is None:
                        for field in ("ReleaseName", "processKey", "ProcessKey", "processName", "ProcessName"):
                            rel = re.search(rf'"{field}"\s*:\s*"([^"]+)"', stdout)
                            if rel:
                                project_release_name = rel.group(1)
                                break
                    uip_calls.append(
                        {
                            "args": pending["args"],
                            "stdout": stdout,
                            "exit_code": exit_code,
                            "raw_command": pending["raw_command"],
                            "redirect_target": pending.get("redirect_target"),
                        }
                    )
                if saw_tool_result:
                    last_was_tool_result = True

    # Prefer a presenter-like text block; fall back to last-after-tools.
    chosen = last_presenter_like or last_assistant_text_after_tools
    return {
        "uip_calls": uip_calls,
        "last_assistant_text": chosen.strip(),
        "first_user_text": first_user_text or "",
        "release_name": project_release_name,
        "transcript_lines": transcript_lines,
        "unmatched": len(pending_tool_uses),
    }


def _slugify(name: str) -> str:
    out = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return out or "diagnostic-scenario"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: extract_session.py <transcript.jsonl-or-dir>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"transcript not found: {path}", file=sys.stderr)
        return 2
    result = parse_transcript(path)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
