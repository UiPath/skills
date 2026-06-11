#!/usr/bin/env python3
"""OutlookWaitForEmail: structural check (no execution).

The flow must be:
  manual start trigger
    -> mid-flow Wait-for-event node (Outlook email-received, Inbox)
       filtered to SUBJECT CONTAINS "TestWaitFor"
    -> End

`flow debug` is intentionally NOT run — the task only requires the flow to
build and validate. So every assertion here is static, read from the `.flow`
source:

  1. The start trigger is preserved (manual/scheduled) — the event node was
     added mid-flow, NOT used to replace the trigger.
  2. A Wait-for-event node of the Outlook email-received connector event exists
     (`uipath.connector.event.uipath-microsoft-outlook365.email-received`).
  3. That node carries a structured `filter` tree with a `subject` / `Contains`
     leaf whose literal value is "TestWaitFor". `node configure` persists this
     tree inside the `inputs.detail.configuration` blob (a `=jsonString:`
     envelope, under `essentialConfiguration.filter`) and compiles the JMESPath
     into `inputs.detail.filterExpression`. We match the structured tree — a
     bare `filterExpression` string (which the CLI rejects as an INPUT field,
     MST-8802) cannot satisfy the check on its own.
"""

import glob
import json
import sys

EVENT_MARKERS = (
    "uipath.connector.event",
    "uipath-microsoft-outlook365",
    "email-received",
)
FILTER_VALUE = "TestWaitFor"
_JSONSTRING_PREFIX = "=jsonString:"


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _parse_jsonstring(value: object) -> dict:
    """Decode a `=jsonString:{...}` envelope (or a plain dict) to a dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.startswith(_JSONSTRING_PREFIX):
        try:
            parsed = json.loads(value[len(_JSONSTRING_PREFIX):])
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _filter_trees(detail: dict):
    """Yield every structured filter tree on a configured connector-event node.

    `node configure` stores the tree in `inputs.detail.configuration`
    (`=jsonString:` → `essentialConfiguration.filter`). Older shapes may expose
    `inputs.detail.filter` directly. Yield whatever is present."""
    direct = detail.get("filter")
    if isinstance(direct, dict):
        yield direct
    config = _parse_jsonstring(detail.get("configuration"))
    essential = config.get("essentialConfiguration") or {}
    tree = essential.get("filter") if isinstance(essential, dict) else None
    if isinstance(tree, dict):
        yield tree


def _read_flow() -> dict:
    flows = glob.glob("**/OutlookWaitForEmail*.flow", recursive=True)
    if not flows:
        _fail("no OutlookWaitForEmail*.flow found under cwd")
    with open(flows[0]) as f:
        return json.load(f)


def _iter_filter_leaves(node_filter: dict):
    """Yield every leaf condition in a (possibly nested) filter tree."""
    if not isinstance(node_filter, dict):
        return
    for leaf in node_filter.get("filters") or []:
        if isinstance(leaf, dict):
            yield leaf
    for group in node_filter.get("groups") or []:
        yield from _iter_filter_leaves(group)


def _leaf_value(leaf: dict) -> str:
    """Extract the literal value from a WorkflowValue-wrapped leaf, tolerating
    both the wrapped shape and a bare string."""
    v = leaf.get("value")
    if isinstance(v, dict):
        return str(v.get("value", ""))
    return str(v) if v is not None else ""


def main() -> None:
    flow = _read_flow()
    nodes = flow.get("nodes") or []
    types_seen = sorted({str(n.get("type", "")) for n in nodes})

    # 1. Start trigger preserved.
    if not any(str(n.get("type", "")).startswith("core.trigger.") for n in nodes):
        _fail(
            "no start trigger (core.trigger.*) — the Wait-for-event node must be "
            f"added mid-flow, not replace the start trigger. Types: {types_seen}"
        )

    # 2. Outlook email-received Wait-for-event node present.
    event_nodes = [
        n
        for n in nodes
        if all(m in str(n.get("type", "")).lower() for m in EVENT_MARKERS)
    ]
    if not event_nodes:
        _fail(
            "no Outlook email-received Wait-for-event node "
            f"(type containing {' + '.join(EVENT_MARKERS)}). Types: {types_seen}"
        )

    # 3. A subject / Contains / "TestWaitFor" leaf in the structured filter tree.
    for node in event_nodes:
        detail = (node.get("inputs") or {}).get("detail") or {}
        if not isinstance(detail, dict):
            continue
        for tree in _filter_trees(detail):
            for leaf in _iter_filter_leaves(tree):
                field = str(leaf.get("id", "")).lower()
                operator = str(leaf.get("operator", "")).lower()
                value = _leaf_value(leaf)
                if "subject" in field and "contains" in operator and value == FILTER_VALUE:
                    print(
                        "OK: start trigger preserved; mid-flow Outlook email-received "
                        f"node filters subject Contains {FILTER_VALUE!r} via the filter tree"
                    )
                    return

    _fail(
        "Outlook email-received node found, but no structured filter leaf matches "
        f"subject / Contains / {FILTER_VALUE!r}. The subject filter must be a "
        "`filter` tree leaf (id=subject, operator=Contains, value=TestWaitFor), "
        "not a bare filterExpression string."
    )


if __name__ == "__main__":
    main()
