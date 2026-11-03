#!/usr/bin/env python3
"""Grades finishing a triage pattern the Flow canvas inserted: every mock replaced
by the real step, every placeholder prompt rewritten, the classifier reading the
item, and each category sent to its own endpoint by the pattern's own routing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import END, fail, load_graph  # noqa: E402

MOCK = "core.logic.mock"
HTTP = "core.action.http"
PLACEHOLDER = "PLACEHOLDER"
TRIGGER = "start"
ROUTER = "routeByCategory"
PERSON = "pickCategory"
HOSTS = ("billing.example.test", "support.example.test", "accounts.example.test")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()

    g = load_graph(str(args.project / f"{args.project.name}.flow"))

    mocks = g.ids(MOCK)
    if mocks:
        fail(f"placeholder steps are still mocks: {sorted(mocks)}")

    for agent in g.agents():
        source = (g.nodes[agent].get("inputs") or {}).get("source")
        sidecar = args.project / str(source) / "agent.json"
        if source and sidecar.is_file() and PLACEHOLDER in sidecar.read_text(encoding="utf-8"):
            fail(f"{agent}'s prompt still carries the canvas {PLACEHOLDER} seed ({sidecar.name})")

    if not any(g.reads(agent, TRIGGER) for agent in g.agents()):
        fail("no agent reads the flow's input email: the classifier has nothing to classify")

    for name in (ROUTER, PERSON):
        if name not in g.nodes:
            fail(f"the pattern's {name} step is gone: finish the pattern, do not rebuild it")

    calls = g.ids(HTTP)
    for host in HOSTS:
        senders = [c for c in calls if host in g.text(c)]
        if not senders:
            fail(f"no HTTP step sends to {host}")
        if not any(g.reaches(ROUTER, s) and g.reaches(PERSON, s) for s in senders):
            fail(f"the {host} step is not reached by both the switch and the person's choice")
        if not any(g.type_of(n) == END for s in senders for n in g.reachable(s)):
            fail(f"the {host} step does not end at an End")

    print(f"PASS: no mocks or placeholder prompts left; {len(HOSTS)} categories sent by {sorted(calls)}")


if __name__ == "__main__":
    main()
