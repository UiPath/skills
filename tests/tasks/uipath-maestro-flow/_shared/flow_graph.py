"""Graph view of an emitted .flow for the pattern graders.

Patterns are graded by topology, so every check walks edges rather than
matching node ids: the canvas and the builder name steps differently, and the
builder fans out from the preceding step where the canvas draws a merge.

An inline subflow is spliced into its call site: its nodes take the caller's
parent, the call node leads into the child's trigger, and the child's Ends lead
wherever the call node does. A pattern moved into a subflow grades the same.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .flow_check import find_flow_file

AGENT_TYPES = ("uipath.agent.autonomous", "uipath.core.agent.")
HITL_PREFIX = "uipath.human-in-the-loop"
DECISION = "core.logic.decision"
SWITCH = "core.logic.switch"
MERGE = "core.logic.merge"
LOOP = "core.logic.loop"
DO_WHILE = "core.logic.dowhile"
SUBFLOW = "core.subflow"
END = "core.control.end"
TERMINATE = "core.logic.terminate"
CONTROL = (DECISION, SWITCH, MERGE)
CONTINUE_PORT = "continue"
ERROR_PORT = "error"
CASE_PREFIX = "case-"

SUBFLOW_ENTRY = "subflow.entry"
SUBFLOW_EXIT = "subflow.exit"
_TRIGGER = "core.trigger."
_OPERATOR = re.compile(r"(?<![=!<>])(<=|<|>=|>)(?!=?>)")
_CLAUSE = re.compile(r"&&|\|\||(?<!\?)\?(?![?.])|:")
_NEGATION = re.compile(r"!\s*\(")
_CONFIDENCE = re.compile(r"confid", re.I)
_LOW_WHEN_TRUE = {"<": True, "<=": True, ">": False, ">=": False}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def _splice(flow: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [dict(n) for n in flow.get("nodes", [])]
    edges = [dict(e) for e in flow.get("edges", [])]
    subflows = flow.get("subflows") or {}
    local = lambda node_id: node_id.rsplit("/", 1)[-1]

    # Subflows are flat, keyed by the call's own id, and a child may call another.
    pending = [n for n in nodes if n.get("type") == SUBFLOW and local(n["id"]) in subflows]
    while pending:
        call = pending.pop()
        child = subflows[local(call["id"])]
        prefix = f"{call['id']}/"
        exits = [e for e in edges if e["sourceNodeId"] == call["id"]]
        errors = [e for e in exits if e["sourcePort"] == ERROR_PORT]
        child_errors = {e["sourceNodeId"] for e in child.get("edges", []) if e["sourcePort"] == ERROR_PORT}
        for node in child.get("nodes", []):
            spliced = {**node, "id": prefix + node["id"]}
            if node.get("parentId"):
                spliced["parentId"] = prefix + node["parentId"]
            elif call.get("parentId"):
                spliced["parentId"] = call["parentId"]
            else:
                spliced.pop("parentId", None)
            kind = str(node.get("type", ""))
            if kind.startswith(_TRIGGER):
                spliced["type"] = SUBFLOW_ENTRY
                edges.append({"sourceNodeId": call["id"], "sourcePort": "input",
                              "targetNodeId": spliced["id"], "targetPort": "input"})
            elif kind == END:
                spliced["type"] = SUBFLOW_EXIT
                edges.extend({**e, "sourceNodeId": spliced["id"]} for e in exits if e not in errors)
            elif node["id"] not in child_errors and not kind.startswith(CONTROL):
                # One .onError on the call catches a failure of any step inside it.
                edges.extend({**e, "sourceNodeId": spliced["id"]} for e in errors)
            if kind == SUBFLOW and node["id"] in subflows:
                pending.append(spliced)
            nodes.append(spliced)
        for edge in child.get("edges", []):
            edges.append({**edge, "sourceNodeId": prefix + edge["sourceNodeId"],
                          "targetNodeId": prefix + edge["targetNodeId"]})
        edges = [e for e in edges if e not in exits]
    return nodes, edges


class FlowGraph:
    def __init__(self, flow: dict[str, Any]):
        self.flow = flow
        nodes, self.edges = _splice(flow)
        self.nodes: dict[str, dict[str, Any]] = {n["id"]: n for n in nodes}
        self.out: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in self.edges:
            self.out[edge["sourceNodeId"]].append(edge)

    def type_of(self, node_id: str) -> str:
        return str(self.nodes.get(node_id, {}).get("type", ""))

    def ids(self, *prefixes: str) -> list[str]:
        return [i for i in self.nodes if self.type_of(i).startswith(prefixes)]

    def agents(self) -> list[str]:
        return self.ids(*AGENT_TYPES)

    def hitl(self) -> list[str]:
        return self.ids(HITL_PREFIX)

    def parent(self, node_id: str) -> str | None:
        return self.nodes.get(node_id, {}).get("parentId")

    def inside(self, node_id: str, container: str) -> bool:
        """``node_id`` sits in ``container``'s body, at any depth."""
        current = self.parent(node_id)
        while current is not None:
            if current == container:
                return True
            current = self.parent(current)
        return False

    def text(self, node_id: str) -> str:
        return json.dumps(self.nodes.get(node_id, {}).get("inputs", {}))

    def reads(self, reader: str, step: str) -> bool:
        """``reader``'s inputs reference ``step``'s value (``$vars.<step>`` or ``vars.<step>``)."""
        local = step.rsplit("/", 1)[-1]
        if re.search(rf"\bvars\.{re.escape(local)}\b", self.text(reader)):
            return True
        if any(re.search(rf"\bvars\.{re.escape(var)}\b", self.text(reader)) for var in self.writes(step)):
            return True
        # Inside a spliced subflow the value arrives through the call's inputs.
        call = reader.rsplit("/", 1)[0] if "/" in reader else None
        return call is not None and call in self.nodes and self.reads(call, step)

    def feeds(self, reader: str, step: str, hops: int = 3) -> bool:
        """``reader`` gets ``step``'s value directly or through up to ``hops``
        intermediate steps that each read the one before (a script that reshapes a
        loop's results for the agent after it)."""
        if self.reads(reader, step):
            return True
        return hops > 0 and any(
            n not in (reader, step) and self.reads(reader, n) and self.feeds(n, step, hops - 1)
            for n in self.nodes
        )

    def writes(self, step: str) -> set[str]:
        """Flow variables ``step`` sets with ``{ updates }``."""
        updates = (self.flow.get("variables") or {}).get("variableUpdates") or {}
        return {u["variableId"] for u in updates.get(step, []) if "variableId" in u}

    def subject_pattern(self, step: str, at: str) -> re.Pattern[str]:
        """Matches a read, from node ``at``, of ``step``'s value: its output, a
        variable it writes, or, inside a spliced subflow whose call passes that
        value in, the child's trigger output."""
        names = [step.rsplit("/", 1)[-1], *sorted(self.writes(step))]
        call = at.rsplit("/", 1)[0] if "/" in at else None
        while call is not None:
            if call in self.nodes and self.reads(call, step):
                names += [n.rsplit("/", 1)[-1] for n in self.ids(SUBFLOW_ENTRY) if n.startswith(f"{call}/")]
            call = call.rsplit("/", 1)[0] if "/" in call else None
        return re.compile(r"\bvars\.(?:" + "|".join(map(re.escape, names)) + r")\b")

    def low_ports(self, gate: str, subject: str | None = None) -> set[str]:
        """Ports of ``gate`` taken when ``subject``'s value is BELOW its bound.

        A decision's ``true``/``false``; a switch's ``case-<id>`` for a case that
        tests below the bound, plus ``default`` when some case tests above it.
        The bound is whatever the value is compared with: a number, a variable,
        an input.
        """
        reads = self.subject_pattern(subject, gate) if subject else re.compile(r"\bvars\.")

        def below(expression: str) -> bool | None:
            """Direction of the comparison on the subject. Prefer an operand that
            names a confidence, then the last comparison (a ternary or a guard
            comes first). A ``!( ... )`` around it flips it."""
            found = []
            for clause in _CLAUSE.split(expression):
                match = _OPERATOR.search(clause)
                if match is None:
                    continue
                left, right = clause[:match.start()], clause[match.end():]
                if reads.search(left):
                    low, operand = _LOW_WHEN_TRUE[match.group(1)], left
                elif reads.search(right):
                    low, operand = not _LOW_WHEN_TRUE[match.group(1)], right
                else:
                    continue
                for negation in _NEGATION.finditer(left):
                    inner = left[negation.end():]
                    if inner.count("(") >= inner.count(")"):
                        low = not low
                found.append((bool(_CONFIDENCE.search(operand)), low))
            if not found:
                return None
            named = [low for is_named, low in found if is_named]
            return (named or [low for _, low in found])[-1]

        inputs = self.nodes.get(gate, {}).get("inputs") or {}
        if self.type_of(gate) == DECISION:
            low = below(str(inputs.get("expression", "")))
            return set() if low is None else {"true" if low else "false"}
        ports: set[str] = set()
        for case in inputs.get("cases") or []:
            low = below(str(case.get("expression", "")))
            if low is True:
                ports.add(f"{CASE_PREFIX}{case.get('id')}")
            elif low is False:
                ports.add("default")
        return ports

    def routes_low(self, gate: str, targets: Iterable[str], subject: str | None = None) -> bool:
        """``gate`` sends only its below-the-bound side to ``targets``: every port
        that reaches one of them without passing another gate is a low port."""
        targets = set(targets)
        others = [n for n in self.ids(DECISION, SWITCH) if n != gate]
        toward = {
            e["sourcePort"] for e in self.edges_from(gate)
            if e["targetNodeId"] in targets
            or (e["targetNodeId"] not in others and self.reachable(e["targetNodeId"], others) & targets)
        }
        return bool(toward) and toward <= self.low_ports(gate, subject)

    def thresholds(self, gate: str, step: str) -> bool:
        """``gate`` compares a value from ``step`` against a bound (``<``, ``>=``...),
        as a confidence floor does and a category switch (``===``) does not."""
        return self.reads(gate, step) and re.search(r"(?<!=)[<>]", self.text(gate)) is not None

    def edges_from(self, node_id: str, port: str | None = None) -> list[dict[str, Any]]:
        return [e for e in self.out[node_id] if port is None or e["sourcePort"] == port]

    def fan_out(self, node_id: str) -> list[dict[str, Any]]:
        """Edges that start ``node_id``'s branches: its own, or, when it leads only
        into a merge with one edge in, that merge's (the canvas parallel split)."""
        out = self.edges_from(node_id)
        if len(out) != 1:
            return out

        fork = out[0]["targetNodeId"]
        if self.type_of(fork) != MERGE:
            return out

        if sum(e["targetNodeId"] == fork for e in self.edges) != 1:
            return out

        arms = self.edges_from(fork)
        return arms if len(arms) >= 2 else out

    def reachable(self, start: str | Iterable[str], blocked: Iterable[str] = ()) -> set[str]:
        """Nodes reachable from ``start`` (exclusive), never entering ``blocked``.

        An edge into a loop's ``continue`` handle closes the iteration rather than
        re-entering the body, so it is not followed.
        """
        frontier = [start] if isinstance(start, str) else list(start)
        stop = set(blocked)
        seen: set[str] = set()
        while frontier:
            current = frontier.pop()
            for edge in self.out[current]:
                target = edge["targetNodeId"]
                if edge.get("targetPort") == CONTINUE_PORT or target in stop or target in seen:
                    continue
                seen.add(target)
                frontier.append(target)
        return seen

    def reaches(self, source: str, target: str, blocked: Iterable[str] = ()) -> bool:
        return target in self.reachable(source, blocked)

    def on_cycle(self, node_id: str) -> bool:
        return self.reaches(node_id, node_id)

    def continues(self, start: str, loop: str) -> bool:
        """Every path from ``start`` stays in ``loop``'s body and moves on to the
        next item: something reachable closes the iteration, and nothing reachable
        ends or terminates the run, or leaves the body."""
        region = self.reachable(start) | {start}
        closes = any(
            e["targetNodeId"] == loop and e.get("targetPort") == CONTINUE_PORT
            for n in region for e in self.out[n]
        )
        escapes = any(
            n != loop and (self.type_of(n) in (END, TERMINATE) or not self.inside(n, loop))
            for n in region - {start}
        )
        return closes and not escapes


def load_graph(path: str | None = None) -> FlowGraph:
    flow_path = Path(path or find_flow_file())
    try:
        return FlowGraph(json.loads(flow_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read {flow_path}: {error}")
        raise
