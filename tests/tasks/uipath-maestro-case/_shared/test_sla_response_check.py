"""Unit tests for sla_response_check.assert_interrupting.

An omitted ``isInterrupting`` reads as false: the case-to-BPMN converter
interrupts only on a literal true. The JSON loop writes ``false`` explicitly
and the SDK loop omits the key; both are the same plan and must grade the same.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sla_response_check import assert_interrupting  # noqa: E402


@pytest.mark.parametrize(
    "cond, expected",
    [
        ({}, False),
        ({"isInterrupting": False}, False),
        ({"isInterrupting": True}, True),
    ],
)
def test_accepts(cond, expected):
    assert_interrupting(cond, expected, "lane")


@pytest.mark.parametrize(
    "cond, expected",
    [
        ({"isInterrupting": True}, False),
        ({}, True),
        ({"isInterrupting": False}, True),
        ({"isInterrupting": "false"}, False),
        ({"isInterrupting": 0}, False),
    ],
)
def test_rejects(cond, expected):
    with pytest.raises(SystemExit):
        assert_interrupting(cond, expected, "lane")
