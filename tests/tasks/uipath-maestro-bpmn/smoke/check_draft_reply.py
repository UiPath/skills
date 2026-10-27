#!/usr/bin/env python3
"""Grade the draft-mode replies the user reads: the 3c gate and the 4g report.

Usage (cwd = sandbox root, as every run_command criterion runs):

    check_draft_reply.py gate  <Name> [--turn N] [--uploaded|--local] [--no-bpmn]
    check_draft_reply.py final <Name> [--turn N] [--uploaded] [--mode draft|auto]
    check_draft_reply.py designer-url --turns 1,2
    check_draft_reply.py after-approval --gate-turn N
    check_draft_reply.py commands --turn N --forbid <REGEX>

Every subcommand accepts ``--transcript <file.jsonl>`` to grade a saved
transcript instead of the live one (fixtures, local re-grading).

Where the reply comes from. coder_eval hands a ``run_command`` criterion no
transcript: no env var, no file in the sandbox. Claude Code itself persists
every session as JSONL under ``$CLAUDE_CONFIG_DIR`` (default ``~/.claude``)
``/projects/<cwd slug>/<session>.jsonl``, each record carrying the ``cwd`` it
ran in. A criterion runs in the agent's own sandbox directory, in the same
host or container (docker mounts a writable copy of ``~/.claude`` at the same
path), so this script selects the records whose ``cwd`` is the current
directory. That keeps the grade deterministic: no judge reads the reply.
The transcript layout is Claude Code's, so these criteria grade Claude Code
runs only; with no transcript found they fail and say so.

A *turn* is one human message (the initial prompt or a simulated-user reply)
and everything the agent did until the next one. Its *reply* is the text the
agent sent after its last tool call in that turn: the message the user reads
when the turn ends. Progress lines sent between tool calls are not the reply.

Standalone on purpose (stdlib only, no ``_shared`` import): the smoke tasks
stage only this directory as ``$REFERENCE_DIR``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
ACTIVITY_TAGS = ("task", "serviceTask", "sendTask", "receiveTask", "scriptTask", "userTask",
                 "businessRuleTask", "manualTask", "callActivity")

QUESTION = "Is this the process you want?"
OPTIONS = ("Build it", "Change it", "Keep it")
# A box line is "one short clause"; this leaves room for a resource name and folder.
MAX_BOX_LINE = 200
# 3c: header, location, one note, the question, three options, plus one line per box.
GATE_FIXED_LINES = 7
GATE_MAX_BOXES_UNKNOWN = 8
FINAL_MAX_CHANGES = 5
FINAL_MAX_LINES = 2 + FINAL_MAX_CHANGES + 2
ARROWS = ("→", "->", "──", "►", "▶", "⟶", "=>")
NOTE_TOPIC = re.compile(
    r"look ?ups?|not checked|fail|unavailable|unreachable|timed? ?out|\b5\d\d\b|login|logged|"
    r"online|edited|your changes|kept",
    re.IGNORECASE,
)
SHAPE_PROSE = re.compile(
    r"^(flow|the flow|shape|the shape|diagram|gateway|gateways|variable|variables|condition|"
    r"conditions|routing|branches|here is|here's|outline)\b",
    re.IGNORECASE,
)


class Fail(Exception):
    pass


# --- transcript --------------------------------------------------------------


def _config_dirs() -> list[Path]:
    dirs = []
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        dirs.append(Path(os.environ["CLAUDE_CONFIG_DIR"]))
    dirs.append(Path.home() / ".claude")
    return dirs


def _slug(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def _same_dir(a: str | None, b: str) -> bool:
    return bool(a) and os.path.realpath(a) == b


def _session_files(cwd: str) -> list[Path]:
    """Every session file whose records ran in ``cwd``.

    The project directory is named after the cwd, so look there first. When
    the slug does not match (a long path Claude Code shortened, a symlinked
    temp dir), scan every project's sessions for one recorded in ``cwd``.
    """
    files: list[Path] = []
    for base in _config_dirs():
        projects = base / "projects"
        for variant in {cwd, os.path.abspath(os.getcwd())}:
            files += sorted((projects / _slug(variant)).glob("*.jsonl"))
        if files:
            return files
    for base in _config_dirs():
        for f in sorted((base / "projects").glob("*/*.jsonl")):
            try:
                with f.open(encoding="utf-8", errors="replace") as fh:
                    for _, line in zip(range(40), fh):
                        if _same_dir(json.loads(line).get("cwd"), cwd):
                            files.append(f)
                            break
            except (OSError, ValueError):
                continue
    return files


def _first_timestamp(path: Path) -> str:
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                stamp = json.loads(line).get("timestamp")
            except ValueError:
                continue
            if stamp:
                return stamp
    return ""


def load_records(transcript: str | None) -> list[dict]:
    """The main-thread records of the session(s) that ran in the current directory.

    Records are kept in file order: a record's ``cwd`` follows the agent's
    shell (it changes after a ``cd`` into the project), and timestamps are
    not monotonic within a file, so neither is used to filter or reorder
    records. A resumed session that landed in a second file is appended in
    the order the files began, with records already seen dropped by ``uuid``.
    """
    cwd = os.path.realpath(os.getcwd())
    files = [Path(transcript)] if transcript else _session_files(cwd)
    if not files:
        raise Fail(f"no Claude Code session transcript recorded for {cwd}; "
                   "these criteria grade Claude Code runs only")
    seen: set[str] = set()
    records = []
    for f in sorted(files, key=_first_timestamp):
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("type") not in ("user", "assistant") or rec.get("isSidechain"):
                continue
            uid = rec.get("uuid")
            if uid:
                if uid in seen:
                    continue
                seen.add(uid)
            records.append(rec)
    return records


def _blocks(rec: dict) -> list[dict]:
    content = (rec.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def _is_human_prompt(rec: dict) -> bool:
    if rec.get("type") != "user" or rec.get("isMeta") or rec.get("isCompactSummary"):
        return False
    blocks = _blocks(rec)
    return bool(blocks) and not any(b.get("type") == "tool_result" for b in blocks)


def _result_text(block: dict) -> str:
    content = block.get("content")
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


class Turn:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.reply_parts: list[str] = []
        self.tools: list[dict] = []  # {"id", "name", "input", "result"}

    @property
    def reply(self) -> str:
        return "\n".join(self.reply_parts).strip()

    def bash_commands(self) -> list[tuple[str, str]]:
        return [(t["input"].get("command", ""), t["result"]) for t in self.tools if t["name"] == "Bash"]


def split_turns(records: list[dict]) -> list[Turn]:
    turns: list[Turn] = []
    by_id: dict[str, dict] = {}
    for rec in records:
        if _is_human_prompt(rec):
            turns.append(Turn("\n".join(b.get("text", "") for b in _blocks(rec))))
            continue
        if not turns:
            continue
        turn = turns[-1]
        for block in _blocks(rec):
            kind = block.get("type")
            if rec["type"] == "assistant" and kind == "text":
                turn.reply_parts.append(block.get("text", ""))
            elif rec["type"] == "assistant" and kind == "tool_use":
                # Text sent before a tool call is progress, not the reply.
                turn.reply_parts = []
                tool = {"id": block.get("id"), "name": block.get("name"),
                        "input": block.get("input") or {}, "result": ""}
                turn.tools.append(tool)
                by_id[tool["id"]] = tool
            elif kind == "tool_result" and block.get("tool_use_id") in by_id:
                by_id[block["tool_use_id"]]["result"] = _result_text(block)
    return turns


def pick_turn(turns: list[Turn], number: int | None) -> tuple[int, Turn]:
    if not turns:
        raise Fail("transcript holds no user turn")
    index = len(turns) if number is None else number
    if not 1 <= index <= len(turns):
        raise Fail(f"turn {index} requested but the transcript holds {len(turns)} turn(s)")
    return index, turns[index - 1]


# --- reply shape -------------------------------------------------------------


def _plain(line: str) -> str:
    """The line with markdown emphasis and code ticks removed."""
    return re.sub(r"[*_`]", "", line).strip()


def _lines(reply: str) -> list[str]:
    return [ln.strip() for ln in reply.splitlines() if ln.strip()]


def _is_location(line: str) -> bool:
    plain = _plain(line).strip("<>[]()")
    return "https://" in line or plain.endswith(".bpmn") or ".bpmn)" in line


def _is_bullet(line: str) -> bool:
    return line.startswith(("- ", "* ", "• "))


def _banned(line: str) -> str | None:
    if re.fullmatch(r"[-*_=]{3,}", line):
        return "a separator line"
    if line.startswith("#"):
        return "a heading"
    if line.startswith("```"):
        return "a code block"
    if any(ch in line for ch in "┌└│├┐┘◇"):
        return "a drawn diagram"
    if SHAPE_PROSE.match(_plain(line)):
        return "a description of the flow, its gateways, or its variables"
    return None


def _header(lines: list[str], pattern: str, what: str, errors: list[str]) -> re.Match | None:
    """Match the template's first line; the message must start with it."""
    if not lines:
        errors.append(f"the turn ended with no visible reply; expected the {what} line")
        return None
    m = re.match(pattern, _plain(lines[0]))
    if not m:
        errors.append(f"first line is not the {what} line: {lines[0][:160]!r}")
    return m


def _box_names(name: str) -> list[str] | None:
    paths = [p for p in sorted(glob.glob("**/*.bpmn", recursive=True)) if "node_modules" not in p]
    hinted = [p for p in paths if os.path.basename(p).lower() == f"{name.lower()}.bpmn"]
    in_project = [p for p in hinted if (Path(p).parent / "project.uiproj").is_file()]
    chosen = (in_project or hinted)[:1]
    if not chosen:
        raise Fail(f"no {name}.bpmn found to read the boxes from; found {paths}")
    try:
        root = ET.parse(chosen[0]).getroot()
    except ET.ParseError as exc:
        raise Fail(f"{chosen[0]} is not well-formed XML: {exc}") from exc
    names = []
    for tag in ACTIVITY_TAGS:
        names += [el.get("name") or el.get("id") or "" for el in root.iter(f"{{{BPMN_NS}}}{tag}")]
    return names


def _action(box: str) -> str:
    """The action part of a box label: ``Manager review [Action app]`` -> ``manager review``."""
    return re.sub(r"\s+", " ", box.split("[", 1)[0]).strip().casefold()


def check_gate(reply: str, name: str, boxes: list[str] | None, uploaded: bool | None) -> list[str]:
    errors: list[str] = []
    lines = _lines(reply)
    m = _header(lines, rf"^{re.escape(name)}: outline ready(?P<up>, uploaded)? \(draft mode\)\.(?:\s+(?P<rest>.+))?$",
                "`<Name>: outline ready<, uploaded> (draft mode).`", errors)
    if m and uploaded is True and not m.group("up"):
        errors.append("the shape was uploaded but the first line does not say `, uploaded`")
    if m and uploaded is False and m.group("up"):
        errors.append("the first line says `, uploaded` but this run must not upload")

    try:
        q = next(i for i, ln in enumerate(lines) if _plain(ln) == QUESTION)
    except StopIteration:
        errors.append(f"the fixed question {QUESTION!r} is missing")
        return errors
    tail = lines[q + 1:]
    if len(tail) != 3:
        errors.append(f"expected exactly three options after the question, found {len(tail)} line(s): {tail[:5]}")
    for i, (line, option) in enumerate(zip(tail, OPTIONS), start=1):
        if not re.match(rf"^{i}\.\s+{re.escape(option)}\b", _plain(line)):
            errors.append(f"option {i} is not {option!r}: {line[:120]!r}")

    body = lines[1:q]
    if not body or not _is_location(body[0]):
        errors.append("the second line is not the DesignerUrl or the local .bpmn path")
    else:
        body = body[1:]
    bullets = [ln for ln in body if _is_bullet(ln)]
    first_bullet = next((i for i, ln in enumerate(body) if _is_bullet(ln)), len(body))
    notes = []
    for i, line in enumerate(body):
        if _is_bullet(line):
            continue
        reason = _banned(line)
        if reason:
            errors.append(f"reply contains {reason}: {line[:120]!r}")
        elif i < first_bullet and not notes and NOTE_TOPIC.search(line) and len(line) <= 240 \
                and not any(a in line for a in ARROWS):
            notes.append(line)  # the one sentence the template allows (lookup failure, kept online edits)
        else:
            errors.append(f"line outside the template: {line[:120]!r}")

    if not bullets:
        errors.append("no box lines (`- <box>: ...`) before the question")
    for line in bullets:
        if ":" not in line:
            errors.append(f"box line has no `<box>: <resource>` shape: {line[:120]!r}")
        if len(line) > MAX_BOX_LINE:
            errors.append(f"box line longer than {MAX_BOX_LINE} chars (one short clause): {line[:120]!r}...")
    if boxes is not None:
        if len(bullets) != len(boxes):
            errors.append(f"{len(bullets)} box line(s) for {len(boxes)} task box(es) {boxes}; list task boxes only, one line each")
        text = " ".join(_plain(b).casefold() for b in bullets)
        missing = [b for b in boxes if _action(b) and _action(b) not in re.sub(r"\s+", " ", text)]
        if missing:
            errors.append(f"box(es) missing from the box lines: {missing}")
        cap = GATE_FIXED_LINES + len(boxes)
    else:
        if len(bullets) > GATE_MAX_BOXES_UNKNOWN:
            errors.append(f"{len(bullets)} box lines; more than {GATE_MAX_BOXES_UNKNOWN}")
        cap = GATE_FIXED_LINES + GATE_MAX_BOXES_UNKNOWN
    if len(lines) > cap:
        errors.append(f"reply has {len(lines)} non-empty lines; the template allows at most {cap}")
    return errors


def check_final(reply: str, name: str, uploaded: bool, mode: str | None) -> list[str]:
    errors: list[str] = []
    lines = _lines(reply)
    m = _header(lines, rf"^{re.escape(name)}: built, validated(?P<up>, uploaded)?(?P<run>, run)? "
                       r"\((?P<mode>auto|draft) mode\)\.(?:\s+(?P<rest>.+))?$",
                "`<Name>: built, validated<, uploaded><, run> (<auto|draft> mode).`", errors)
    if m and uploaded and not m.group("up"):
        errors.append("the process was uploaded but the first line does not say `, uploaded`")
    if m and mode and m.group("mode") != mode:
        errors.append(f"first line reports {m.group('mode')} mode; this run is {mode} mode")
    body = lines[1:]
    if not body or not _is_location(body[0]):
        errors.append("the second line is not the DesignerUrl or the local .bpmn path")
    else:
        body = body[1:]
    changes = 0
    seen_footer = False
    for line in body:
        plain = _plain(line)
        if _is_bullet(line) and not seen_footer:
            changes += 1
        elif plain.startswith(("Assumed:", "Unverified:")):
            seen_footer = True
        else:
            reason = _banned(line) or ("a numbered list" if re.match(r"^\d+[.)]\s", plain) else None)
            errors.append(f"line outside the template ({reason or 'extra prose'}): {line[:120]!r}")
    if changes > FINAL_MAX_CHANGES:
        errors.append(f"{changes} change lines; the template allows at most {FINAL_MAX_CHANGES}")
    if len(lines) > FINAL_MAX_LINES:
        errors.append(f"reply has {len(lines)} non-empty lines; the template allows at most {FINAL_MAX_LINES}")
    return errors


# --- dialog checks -----------------------------------------------------------


DESIGNER_URL = re.compile(r'"DesignerUrl"\s*:\s*"(https://[^"]+)"')


def upload_urls(turn: Turn) -> list[str]:
    urls = []
    for command, result in turn.bash_commands():
        if not re.search(r"\bsolution\s+upload\b", command):
            continue
        found = DESIGNER_URL.findall(result) or re.findall(r"https://\S+", result)
        urls += [u.rstrip("\",)'") for u in found]
    return urls


def check_designer_url(turns: list[Turn], numbers: list[int]) -> list[str]:
    errors = []
    for n in numbers:
        _, turn = pick_turn(turns, n)
        urls = upload_urls(turn)
        if not urls:
            errors.append(f"turn {n}: no `uip solution upload` returned a DesignerUrl")
        elif urls[-1] not in turn.reply:
            errors.append(f"turn {n}: the DesignerUrl {urls[-1]} is not in the turn-ending reply")
    return errors


FINAL_HEADER = re.compile(r"^\S.*: built, validated\b")


def check_after_approval(turns: list[Turn], gate: int) -> list[str]:
    """The turn answering *Build it* must itself end with the 4g report.

    A question in that turn (a structure or resource question, a pick list)
    hands the turn back to the user, so the report arrives a turn later or
    never. Turns after a correct report are the simulated user's doing, not
    the agent's, and are not held against it.
    """
    if len(turns) < gate + 1:
        return [f"the dialog ended after turn {len(turns)}; the user never answered the gate"]
    errors = []
    answer = turns[gate].prompt
    if not re.search(r"\b1\b|build it", answer, re.IGNORECASE):
        errors.append(f"the simulated user did not pick Build it at the gate: {answer[:120]!r}")
    reply = turns[gate].reply
    lines = _lines(reply)
    if not lines or not FINAL_HEADER.match(_plain(lines[0])):
        later = next((i for i, t in enumerate(turns[gate + 1:], start=gate + 2)
                      if _lines(t.reply) and FINAL_HEADER.match(_plain(_lines(t.reply)[0]))), None)
        where = f"it came in turn {later}" if later else "it never came"
        errors.append(f"turn {gate + 1} (after Build it) did not end with the 4g report ({where}); "
                      f"it ended with: {reply[-300:]!r}")
    asks = [ln for ln in lines if ln.rstrip("*_ ").endswith("?")]
    if asks:
        errors.append(f"the reply after Build it asks the user something: {asks[:3]}")
    return errors


def check_commands(turn: Turn, forbid: str) -> list[str]:
    pattern = re.compile(forbid)
    return [f"forbidden command in this turn: {c[:200]!r}" for c, _ in turn.bash_commands() if pattern.search(c)]


# --- entry point -------------------------------------------------------------


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("check", choices=("gate", "final", "designer-url", "after-approval", "commands"))
    ap.add_argument("name", nargs="?")
    ap.add_argument("--turn", type=int)
    ap.add_argument("--turns", default="")
    ap.add_argument("--gate-turn", type=int, default=1)
    ap.add_argument("--uploaded", action="store_true")
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--no-bpmn", action="store_true")
    ap.add_argument("--mode", choices=("draft", "auto"))
    ap.add_argument("--forbid")
    ap.add_argument("--transcript")
    args = ap.parse_args(argv)

    try:
        turns = split_turns(load_records(args.transcript))
        if args.check in ("gate", "final") and not args.name:
            raise Fail(f"{args.check} needs the process name")
        if args.check == "gate":
            n, turn = pick_turn(turns, args.turn)
            boxes = None if args.no_bpmn else _box_names(args.name)
            uploaded = True if args.uploaded else (False if args.local else None)
            errors = check_gate(turn.reply, args.name, boxes, uploaded)
        elif args.check == "final":
            n, turn = pick_turn(turns, args.turn)
            errors = check_final(turn.reply, args.name, args.uploaded, args.mode)
        elif args.check == "designer-url":
            numbers = [int(x) for x in args.turns.split(",") if x.strip()] or [len(turns)]
            errors = check_designer_url(turns, numbers)
        elif args.check == "after-approval":
            errors = check_after_approval(turns, args.gate_turn)
        else:
            if not args.forbid:
                raise Fail("commands needs --forbid")
            n, turn = pick_turn(turns, args.turn)
            errors = check_commands(turn, args.forbid)
    except Fail as exc:
        print(f"FAIL: {exc}")
        return 1

    if errors:
        print("FAIL:\n" + "\n".join(f"  - {e}" for e in errors))
        if args.check in ("gate", "final"):
            print("--- reply ---\n" + turn.reply[:3000])
        return 1
    print(f"OK: {args.check} ({len(turns)} turn(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
