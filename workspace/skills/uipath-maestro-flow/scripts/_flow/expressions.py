"""Audit `=js:` usage in a `.flow` file against the per-node-type field matrix.

Flags: $vars/$metadata/$self references in value fields without the =js: prefix, the invented
nodes.X.output.Y syntax, =js: wrongly applied to condition fields or a script body, brace
interpolation in connector/HTTP inputs, and a quoted =js: prefix.
"""
import re

from . import lib as fl

REF = re.compile(r"\$(vars|metadata|self)\.")
INVENTED = re.compile(r"(?<![.$\w])nodes\.[A-Za-z_]\w*\.(output|error)\b")
BRACES = re.compile(r"\{\s*\$?vars\.|\{\{")
CONNECTOR_HTTP = ("uipath.connector.", "core.action.http")


def _walk(value, path, out):
    if isinstance(value, dict):
        for k in sorted(value):
            _walk(value[k], "%s.%s" % (path, k), out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, "%s[%d]" % (path, i), out)
    elif isinstance(value, str):
        out.append((path, value))


def _strings(node):
    out = []
    _walk(node.get("inputs", {}), "inputs", out)
    _walk(node.get("outputs", {}), "outputs", out)
    return out


def _needs_js(ntype, path):
    if ntype.startswith("uipath.connector.") or ntype.startswith("core.action.http.v2"):
        return path.startswith("inputs.detail.")
    if ntype == "core.action.http":
        return any(path.startswith("inputs." + k) for k in ("url", "headers", "body", "queryParams"))
    if fl.is_terminal(ntype):
        return path.startswith("outputs.") and path.endswith(".source")
    if ntype == "core.logic.loop":
        return path == "inputs.collection"
    if ntype == "core.subflow":
        return path.startswith("inputs.") and path.endswith(".source")
    return False


def _forbids_js(ntype, path):
    if ntype == "core.logic.decision" and path == "inputs.expression":
        return True
    if ntype == "core.logic.switch" and re.fullmatch(r"inputs\.cases\[\d+\]\.expression", path):
        return True
    if ntype.startswith("core.action.http") and re.fullmatch(r"inputs\.branches\[\d+\]\.conditionExpression", path):
        return True
    if ntype == "core.action.script" and path == "inputs.script":
        return True
    return False


def collect(flow):
    out = []
    for node in flow["nodes"]:
        nid = node.get("id")
        ntype = node.get("type", "")
        for path, value in _strings(node):
            if value.startswith('"=js:'):
                out.append(fl.finding("error", "QUOTED_JS_PREFIX",
                                      "value is a string containing the =js: prefix, not an expression",
                                      node=nid, path=path))
            if INVENTED.search(value):
                out.append(fl.finding("error", "INVENTED_NODES_SYNTAX",
                                      "there is no nodes.X.output.Y syntax; use =js:$vars.X.output.Y",
                                      node=nid, path=path))
            if _forbids_js(ntype, path):
                if value.startswith("=js:"):
                    out.append(fl.finding("error", "JS_ON_CONDITION",
                                          "condition/script fields are evaluated as JS; remove the =js: prefix",
                                          node=nid, path=path))
                continue
            if ntype.startswith("core.action.transform") and path == "inputs.collection":
                if value.startswith("=js:"):
                    out.append(fl.finding("warning", "TRANSFORM_COLLECTION_PREFIXED",
                                          "Transform inputs.collection is a path string such as "
                                          "$vars.orders.output.items, without =js:", node=nid, path=path))
                continue
            if ntype.startswith(CONNECTOR_HTTP) and BRACES.search(value):
                out.append(fl.finding("error", "BRACE_INTERPOLATION",
                                      "{ } interpolation is skipped in connector/HTTP inputs; use =js: and a JS template literal",
                                      node=nid, path=path))
            if REF.search(value) and not value.startswith("=js:"):
                if _needs_js(ntype, path):
                    out.append(fl.finding("error", "MISSING_JS_PREFIX",
                                          "value references %s without =js:; it ships as a literal string"
                                          % REF.search(value).group(0).rstrip("."), node=nid, path=path))
                else:
                    out.append(fl.finding("warning", "UNPREFIXED_REF",
                                          "value references %s without =js:; confirm the plugin documents this "
                                          "field as a path, otherwise prefix it"
                                          % REF.search(value).group(0).rstrip("."), node=nid, path=path))

    updates = (flow.get("variables") or {}).get("variableUpdates") or {}
    if isinstance(updates, dict):
        for nid in sorted(updates):
            entries = updates[nid] if isinstance(updates[nid], list) else []
            for i, entry in enumerate(entries):
                expr = (entry or {}).get("expression") if isinstance(entry, dict) else None
                if isinstance(expr, str) and REF.search(expr) and not expr.startswith("=js:"):
                    out.append(fl.finding("error", "MISSING_JS_PREFIX",
                                          "variableUpdates expression references $vars without =js:",
                                          node=nid, path="variables.variableUpdates.%s[%d].expression" % (nid, i)))
    return out

