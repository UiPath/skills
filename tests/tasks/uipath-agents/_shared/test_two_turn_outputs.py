"""Unit tests for the two-local-turns helper.

The regression these lock in: a transcript line carries a label
(`Reply:   hello there echo`) that the line scan cannot distinguish from
the reply, so corroboration must drop the labelled variant rather than
fail the whole run. A real llamaindex trajectory that saved both turn
inputs, both outputs *and* a labelled transcript failed the smoke test
because of it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.two_turn_outputs import assert_two_local_turns  # noqa: E402

TRANSCRIPT = (
    "chat-agent — local chat transcript\n"
    "===================================\n\n"
    "Turn 1\n  Message: hello there\n  Reply:   hello there echo\n\n"
    "Turn 2\n  Message: what time is it\n  Reply:   what time is it echo\n"
)


def turn_input(message: str) -> str:
    return json.dumps(
        {
            "messages": [
                {
                    "role": "user",
                    "contentParts": [
                        {"mimeType": "text/plain", "data": {"inline": message}}
                    ],
                }
            ]
        }
    )


def project(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        (tmp_path / name).write_text(body)
    return tmp_path


def test_accepts_turn_files_plus_labelled_transcript(tmp_path: Path) -> None:
    """The exact shape that failed CI: outputs *and* a labelled transcript."""
    root = project(
        tmp_path,
        {
            "turn1.json": turn_input("hello there"),
            "turn2.json": turn_input("what time is it"),
            "turn1-output.json": json.dumps({"response": "hello there echo"}),
            "turn2-output.json": json.dumps({"response": "what time is it echo"}),
            "chat-replies.txt": TRANSCRIPT,
        },
    )
    assert_two_local_turns(root)


def test_accepts_labelled_transcript_alone(tmp_path: Path) -> None:
    """No JSON outputs — the transcript carries both messages and replies."""
    assert_two_local_turns(project(tmp_path, {"chat-replies.txt": TRANSCRIPT}))


def test_accepts_json_turn_files_alone(tmp_path: Path) -> None:
    root = project(
        tmp_path,
        {
            "t1.json": turn_input("hello there"),
            "t1-out.json": json.dumps({"response": "hello there echo"}),
            "t2.json": turn_input("what time is it"),
            "t2-out.json": json.dumps({"response": "what time is it echo"}),
        },
    )
    assert_two_local_turns(root)


def test_accepts_message_containing_a_colon(tmp_path: Path) -> None:
    """Label stripping must not eat a colon that belongs to the message."""
    root = project(
        tmp_path,
        {
            "t1.json": turn_input("time: now"),
            "t1-out.json": json.dumps({"response": "time: now echo"}),
            "t2.json": turn_input("hello there"),
            "t2-out.json": json.dumps({"response": "hello there echo"}),
        },
    )
    assert_two_local_turns(root)


def test_rejects_fabricated_replies(tmp_path: Path) -> None:
    """Replies with no submitted message behind them do not count."""
    root = project(tmp_path, {"out.txt": "hello there echo\nwhat time is it echo\n"})
    with pytest.raises(SystemExit) as exc:
        assert_two_local_turns(root)
    assert "uncorroborated" in str(exc.value)


def test_rejects_single_turn(tmp_path: Path) -> None:
    root = project(
        tmp_path,
        {
            "turn1.json": turn_input("hello there"),
            "turn1-output.json": json.dumps({"response": "hello there echo"}),
        },
    )
    with pytest.raises(SystemExit) as exc:
        assert_two_local_turns(root)
    assert "found 1" in str(exc.value)


def test_one_turn_saved_in_many_places_counts_once(tmp_path: Path) -> None:
    """Copies of a single turn must not inflate the turn count."""
    root = project(
        tmp_path,
        {
            "turn1.json": turn_input("hello there"),
            "turn1-output.json": json.dumps({"response": "hello there echo"}),
            "copy.txt": "Reply: hello there echo\n",
            "copy2.log": "Reply: hello there echo\n",
        },
    )
    with pytest.raises(SystemExit) as exc:
        assert_two_local_turns(root)
    assert "found 1" in str(exc.value)
