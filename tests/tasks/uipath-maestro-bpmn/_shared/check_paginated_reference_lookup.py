#!/usr/bin/env python3
"""SlackPaginationTest (BPMN): connector node wired with a paginated-lookup id.

Ported from Flow `connector_features/paginated_reference_lookup.yaml`'s
``flow_contains.py`` criteria: same scenario (a Slack "Send Message to
Channel" node targets a channel whose id can only be resolved by paging past
page 1 of the Slack channel resources, or by the SDK's lookup resolver),
translated from a JSON node/edge substring search to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3). The two
``command_executed`` criteria that grade the CLI discovery/pagination
transcript (paged resource-list loop, `flow validate`→`bpmn validate`) stay in
the task YAML unchanged/verb-swapped; they are not this script's concern.

Two subcommands (subcommand-dispatched, matching the sibling connector
graders in this suite):

  check_exists   Flow's ``flow_contains.py --flow-name SlackPaginationTest``
                  (no extra assertions) -- the .bpmn exists and parses.
  check_wired    Flow's ``flow_contains.py --flow-name SlackPaginationTest
                  'uipath.connector.uipath-salesforce-slack.send-message-to-channel'
                  '"C083AN4E61E"'`` -- a Slack send-message-to-channel node
                  carries the resolved channel id C083AN4E61E.

Assertion map (Flow → BPMN):
  F criterion 4  flow_contains --flow-name SlackPaginationTest (existence only)
                  → check_exists(): parse_bpmn("SlackPaginationTest")
  F criterion 5  flow_contains --flow-name SlackPaginationTest
                  'uipath.connector.uipath-salesforce-slack.send-message-to-channel'
                  '"C083AN4E61E"'
                  → check_wired(): any Intsvc.ActivityExecution bpmn:sendTask
                    with connectorKey uipath-salesforce-slack whose objectName
                    names the Send Message to Channel operation, and whose
                    serialised XML contains the channel id C083AN4E61E
                    (path/query/body input, any depth, either the curated
                    separate-inputs form or the single JSON `target="body"`
                    form -- registry-workflow.md §3 "Body shape")
  I              locate/parse .bpmn (file exists, well-formed XML)
                  → parse_bpmn()
  T              curated objectName spelling tolerance (send_message_to_channel
                  / send_message_to_channel_v2, any separator/case)
                  → SEND_MESSAGE_RE
  T              channel id present anywhere in the node's inputs, at any
                  depth, in either body form → has_type() substring match over
                  the node's full serialised XML (both a raw JSON CDATA string
                  and a typed separate-input value contain "C083AN4E61E" as a
                  literal substring)
  DROPPED        require_no_private_connector_values / require_sequence_integrity
                  / require_di_for_visible_elements / connection-binding checks
                  (not in Flow; the `bpmn validate` criterion covers structure)
"""

from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    context_value,
    elements,
    fail,
    has_type,
    parse_bpmn,
)

NAME_HINT = "SlackPaginationTest"
CONNECTOR_KEY = "uipath-salesforce-slack"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
CHANNEL_ID = "C083AN4E61E"

# Loose match: the agent's objectName was `send_message_to_channel_v2` (CI run
# 35791969905); match on the concept (any separator,
# optional "_v2"/"v2" suffix, either "message" spelling) rather than pin one
# exact objectName spelling.
SEND_MESSAGE_RE = re.compile(r"send[\s_-]*messages?[\s_-]*to[\s_-]*channel", re.IGNORECASE)


def find_slack_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_type(task, ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
        and SEND_MESSAGE_RE.search(context_value(task, "objectName"))
    ]


def check_exists() -> None:
    path, _root = parse_bpmn(NAME_HINT)
    print(f"OK: {path} exists and is well-formed XML")


def check_wired() -> None:
    _path, root = parse_bpmn(NAME_HINT)

    nodes = find_slack_nodes(root)
    if not nodes:
        fail(
            f"no bpmn:sendTask carries {ACTIVITY_TYPE} with connectorKey "
            f"{CONNECTOR_KEY!r} and an objectName naming Send Message to Channel"
        )
    print(f"OK: {len(nodes)} {CONNECTOR_KEY} Send Message to Channel node(s) present")

    wired = [node for node in nodes if has_type(node, CHANNEL_ID)]
    if not wired:
        ids = [node.attrib.get("id", "?") for node in nodes]
        fail(
            f"none of the Slack send-message nodes {ids} carries the resolved "
            f"channel id {CHANNEL_ID!r}"
        )
    print(f"OK: Slack send-message node {wired[0].attrib.get('id', '?')!r} "
          f"(objectName={context_value(wired[0], 'objectName')!r}) carries "
          f"channel id {CHANNEL_ID!r}")


DISPATCH = {
    "check_exists": check_exists,
    "check_wired": check_wired,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(DISPATCH)}}}")
    DISPATCH[sys.argv[1]]()


if __name__ == "__main__":
    main()
