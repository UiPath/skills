import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_investigate_criteria import FLAGS, _criteria, _hits

TASK = "reporting-discipline/smoke.yaml"

RETRY = "Agent did not retry by looping or chaining uip insights calls"

READ = 'uip insights jobs summary --time-range 1440 --process-name "Nonexistent_Process_ZZZ" --output json'

RETRIES = [
    f"for i in 1 2 3; do {READ}; done",
    f"for i in 1 2 3\ndo\n  {READ}\ndone",
    f"for i in 1 2 \\\n  3; do {READ}; done",
    f"while true; do {READ} && break; sleep 5; done",
    f"sleep 1; while true; do {READ}; done",
    f"x=$(for i in 1 2; do {READ}; done)",
    f"until {READ}; do sleep 5; done",
    f"while ! {READ}; do sleep 5; done",
    f"for f in $(uip insights filter-folders list --output json); do {READ}; done",
    f"{READ} || {READ}",
    f"bash -lc 'for i in 1 2; do {READ}; done'",
]

NOT_RETRIES = [
    READ,
    f"{READ} > jobs.json",
    f"{READ} && uip insights alert-history list --output json",
    f"{READ}\nuip insights users list --output json",
    f"echo 'retry is not safe for this'\n{READ}",
    f"for x in a b; do echo $x; done\n{READ}",
    f"{READ}\nfor x in a b; do echo $x; done",
    f"# Wait for the result; do not retry\n{READ}",
    f"echo 'wait for it; do nothing'\n{READ}",
    f"cat notes.md # look for it; do not loop\n{READ}",
    "uip insights alert-deliveries list --output json | jq '.Data[] | select(.Status == \"Sent\")'",
]


def _retry_regex():
    matches = [crit for crit in _criteria(TASK) if crit["description"] == RETRY]
    assert len(matches) == 1, f"expected one {RETRY!r} criterion, found {len(matches)}"
    return re.compile(matches[0]["command_pattern"], FLAGS)


@pytest.mark.parametrize("command", RETRIES)
def test_a_retry_is_caught(command):
    assert _hits(_retry_regex(), command), f"misses the retry {command!r}"


@pytest.mark.parametrize("command", NOT_RETRIES)
def test_a_single_read_is_not_a_retry(command):
    assert not _hits(_retry_regex(), command), f"flags the compliant call {command!r}"
