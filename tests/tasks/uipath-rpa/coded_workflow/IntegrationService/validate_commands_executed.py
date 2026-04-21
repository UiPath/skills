#!/usr/bin/env python3
"""Validate that the agent executed Bash commands matching all given regex patterns.

Reads the agent transcript from $TRANSCRIPT_PATH env var (or first positional
argument when it is an existing file path), then checks that every supplied
regex pattern matches at least one Bash tool call in the transcript.

Usage:
    python validate_commands_executed.py <pattern1> [pattern2 ...]
    python validate_commands_executed.py /path/to/transcript.json <pattern1> [pattern2 ...]

Exits 0 if all patterns matched, 1 otherwise.
"""
import json
import os
import re
import sys


def load_bash_commands(transcript_path: str) -> list[str]:
    with open(transcript_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    commands: list[str] = []
    messages = data if isinstance(data, list) else data.get("messages", [])

    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    if block.get("name") == "Bash":
                        cmd = block.get("input", {}).get("command", "")
                        if cmd:
                            commands.append(cmd)
        for tc in msg.get("tool_calls", []):
            if tc.get("function", {}).get("name") == "Bash":
                try:
                    cmd = json.loads(tc["function"].get("arguments", "{}")).get("command", "")
                    if cmd:
                        commands.append(cmd)
                except (json.JSONDecodeError, KeyError):
                    pass

    return commands


def main() -> None:
    args = sys.argv[1:]
    transcript_path = os.environ.get("TRANSCRIPT_PATH")

    if not transcript_path:
        if args and os.path.isfile(args[0]):
            transcript_path = args[0]
            args = args[1:]
        else:
            print("FAIL: Transcript path not found. Set $TRANSCRIPT_PATH or pass it as the first argument.")
            sys.exit(1)

    if not args:
        print("FAIL: No patterns provided.")
        sys.exit(1)

    try:
        commands = load_bash_commands(transcript_path)
    except FileNotFoundError:
        print(f"FAIL: Transcript file not found: {transcript_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"FAIL: Could not parse transcript JSON: {e}")
        sys.exit(1)

    missing = [p for p in args if not any(re.search(p, cmd) for cmd in commands)]

    if missing:
        print(f"FAIL: {len(missing)} pattern(s) not found in {len(commands)} agent Bash command(s):")
        for p in missing:
            print(f"  - {p!r}")
        sys.exit(1)

    print(f"PASS: All {len(args)} pattern(s) matched across {len(commands)} agent Bash command(s).")


if __name__ == "__main__":
    main()
