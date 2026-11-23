#!/usr/bin/env python3
"""Assert the sweep payload reached `update <record>` as a JSON object, by any route.

feedback.md teaches three routes: inline `--metadata '<json>'`, `--metadata-file <path>`,
and `--metadata-file -` (stdin). The record_cli log holds argv only, so a stdin payload
cannot be read back; that route passes on the flag alone.
"""
import json
import sys
from pathlib import Path

RECORD = "9b41c7e0-5d38-4a62-b1f7-2c8e5a0d94f3"
FOLDER_KEY = "2f6c8a41-93bd-4d17-8e55-6a0b7c19d3e2"
LOG = Path("cli_mocks/calls.jsonl")


def flag_values(argv: list[str], name: str) -> list[str]:
    """Values of --name in both `--name v` and `--name=v` forms."""
    out = []
    for i, tok in enumerate(argv):
        if tok == f"--{name}" and i + 1 < len(argv):
            out.append(argv[i + 1])
        elif tok.startswith(f"--{name}="):
            out.append(tok.split("=", 1)[1])
    return out


def payload(argv: list[str]) -> tuple[str | None, str]:
    """Return (text, source), or (None, reason) when no payload text is readable."""
    inline = flag_values(argv, "metadata")
    if inline:
        return inline[-1], "--metadata"
    files = flag_values(argv, "metadata-file")
    if not files:
        return None, "no --metadata or --metadata-file"
    path = files[-1]
    if path == "-":
        return None, "stdin"
    if not Path(path).is_file():
        return None, f"--metadata-file {path}: file not found"
    return Path(path).read_text(), f"--metadata-file {path}"


def leaves(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from leaves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from leaves(v)
    else:
        yield obj


def missing_facts(data: dict) -> list[str]:
    """The three facts the prompt states in prose: reviewer, round, sample source."""
    vals = list(leaves(data))
    facts = {
        "reviewer qa-sweep": any(v == "qa-sweep" for v in vals),
        "round 3": any(v in (3, "3") and not isinstance(v, bool) for v in vals),
        "monthly export": any(isinstance(v, str) and "monthly" in v.lower() for v in vals),
    }
    return [name for name, ok in facts.items() if not ok]


def main() -> None:
    if not LOG.is_file():
        sys.exit(f"FAIL: {LOG} not found")
    calls = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    updates = [
        c["argv"] for c in calls
        if c.get("tool") == "uip"
        and c.get("argv", [])[:3] == ["traces", "feedback", "update"]
        and RECORD in c["argv"]
    ]
    if not updates:
        sys.exit(f"FAIL: no `traces feedback update {RECORD}` call recorded")

    reasons = []
    for argv in updates:
        if FOLDER_KEY not in flag_values(argv, "folder-key"):
            reasons.append(f"missing --folder-key {FOLDER_KEY}")
            continue
        text, source = payload(argv)
        if text is None:
            if source == "stdin":
                print("OK: payload sent on stdin (--metadata-file -); the argv log cannot show it")
                return
            reasons.append(source)
            continue
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            reasons.append(f"{source}: not valid JSON ({e.msg})")
            continue
        if not isinstance(data, dict):
            reasons.append(f"{source}: JSON {type(data).__name__}, not an object")
            continue
        missing = missing_facts(data)
        if missing:
            reasons.append(f"{source}: object lacks {', '.join(missing)}")
            continue
        print(f"OK: {source} carries the sweep payload as a JSON object")
        return
    sys.exit("FAIL: " + "; ".join(reasons))


if __name__ == "__main__":
    main()
