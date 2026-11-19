"""Journal of the Slack messages a grader's own debug runs posted.

`_setup/teardown_slack_posts.py` deletes them in post_run. Every attempt of a
debug is read, and the journal is written even when the check fails. Still left
in #coding-agent-testing: posts from an attempt with no readable outputs or a
CLI timeout, and the agent's own test runs.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from _shared.escalation_inputs import SLACK_KEY, SLACK_SEND
from _shared.flow_check import (
    _SLACK_TS_RE,
    _connector_node_ids,
    _get_ci,
    _parse_json,
    get_debug_attempt_raws,
)

JOURNAL = Path(".slack-posts.jsonl")
PROJECT_GLOB = "**/project.uiproj"

Post = tuple[str, str]


def _posts_in_text(text: str) -> list[Post]:
    decoder = json.JSONDecoder()
    found: list[Post] = []
    index = text.find("{")
    while index != -1:
        try:
            value, end = decoder.raw_decode(text, index)
        except (ValueError, RecursionError):
            index = text.find("{", index + 1)
            continue
        found += _posts(value)
        index = text.find("{", end)
    return found


def _posts(value) -> list[Post]:
    """(channel, ts) of each Slack send response in `value`: an object holding a
    channel, a ts and the posted `message`."""
    if isinstance(value, str):
        return _posts_in_text(value)
    if isinstance(value, list):
        return [post for item in value for post in _posts(item)]
    if not isinstance(value, dict):
        return []

    channel, ts = _get_ci(value, "channel"), _get_ci(value, "ts")
    own = []
    if (
        isinstance(channel, str)
        and isinstance(ts, str)
        and _SLACK_TS_RE.match(ts.strip())
        and isinstance(_get_ci(value, "message"), dict)
    ):
        own = [(channel, ts.strip())]
    return own + [post for item in value.values() for post in _posts(item)]


def _send_posts(raw: str) -> list[Post]:
    envelope = _parse_json(raw)
    if envelope is None:
        return _posts_in_text(raw)

    data = _get_ci(envelope, "Data") or {}
    variables = _get_ci(data, "variables", "Variables") or {}
    outputs = _get_ci(variables, "globals", "Globals") or {}
    if not isinstance(outputs, dict):
        return []

    send_ids = _connector_node_ids(SLACK_KEY, PROJECT_GLOB, native_op_hint=SLACK_SEND)
    return [post for node_id in sorted(map(str, send_ids)) for post in _posts(outputs.get(f"{node_id}.output"))]


def read_journal(path: Path = JOURNAL) -> list[Post]:
    if not path.is_file():
        return []

    posts: list[Post] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            channel, ts = json.loads(line)
        except (ValueError, TypeError):
            continue
        posts.append((channel, ts))
    return posts


def journal_last_debug() -> None:
    raws = [raw for raw in get_debug_attempt_raws() if raw]
    if not raws:
        return

    try:
        posts = [post for raw in raws for post in _send_posts(raw)]
        known = set(read_journal())
        with JOURNAL.open("a", encoding="utf-8") as handle:
            for post in dict.fromkeys(posts):
                if post not in known:
                    handle.write(json.dumps(post) + "\n")
    except (Exception, SystemExit):
        return


@contextmanager
def journal_slack_posts() -> Iterator[None]:
    try:
        yield
    finally:
        journal_last_debug()
