"""Lint script bodies and =js: expressions for constructs the Jint runtime does not support.

Checks the documented unsupported set (no network, timers, DOM/console, modules, dynamic code,
async/Promise, bare Date), the script-node rules (top-level return of an object, no function main
wrapper, no `aggregate` variable), and reports each hit with node id and field path.
"""
import re

from . import lib as fl

BANNED = [
    ("fetch", r"\bfetch\s*\("),
    ("XMLHttpRequest", r"\bXMLHttpRequest\b"),
    ("setTimeout", r"\bsetTimeout\s*\("),
    ("setInterval", r"\bsetInterval\s*\("),
    ("document", r"\bdocument\s*\."),
    ("window", r"\bwindow\s*\."),
    ("console", r"\bconsole\s*\."),
    ("require", r"\brequire\s*\("),
    ("import", r"(^|\n)\s*import\s|[^.\w]import\s*\("),
    ("eval", r"\beval\s*\("),
    ("Function constructor", r"\bnew\s+Function\s*\("),
    ("async", r"\basync\b"),
    ("await", r"\bawait\b"),
    ("Promise", r"\bPromise\b"),
    ("Date constructor", r"\bnew\s+Date\s*\("),
]
RETURN_OBJ = re.compile(r"return\s*(\{|[A-Za-z_$][\w$]*\s*;?\s*$)", re.M)
RETURN_ANY = re.compile(r"\breturn\b")
MAIN_WRAPPER = re.compile(r"function\s+main\s*\(")
AGGREGATE = re.compile(r"\b(var|let|const)\s+aggregate\b")


def _expr_strings(node):
    out = []
    fl_paths = []
    _walk(node.get("inputs", {}), "inputs", fl_paths)
    for path, value in fl_paths:
        if value.startswith("=js:"):
            out.append((path, value[4:]))
    return out


def _walk(value, path, out):
    if isinstance(value, dict):
        for k in sorted(value):
            _walk(value[k], "%s.%s" % (path, k), out)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, "%s[%d]" % (path, i), out)
    elif isinstance(value, str):
        out.append((path, value))


def _scan(text, nid, path, out, severity="error"):
    for label, pattern in BANNED:
        if re.search(pattern, text):
            out.append(fl.finding(severity, "JINT_UNSUPPORTED",
                                  "%s is not available in the Jint runtime" % label, node=nid, path=path))


def collect(flow):
    out = []
    for node in flow["nodes"]:
        nid = node.get("id")
        ntype = node.get("type", "")
        if ntype == "core.action.script":
            body = (node.get("inputs") or {}).get("script")
            if not isinstance(body, str):
                out.append(fl.finding("error", "SCRIPT_MISSING_BODY", "script node has no inputs.script string", node=nid))
            else:
                _scan(body, nid, "inputs.script", out)
                if MAIN_WRAPPER.search(body):
                    out.append(fl.finding("error", "SCRIPT_MAIN_WRAPPER",
                                          "the node runs the script text directly; a function main() wrapper is never called",
                                          node=nid, path="inputs.script"))
                if not RETURN_ANY.search(body):
                    out.append(fl.finding("error", "SCRIPT_NO_RETURN",
                                          "script must end with a top-level return of an object",
                                          node=nid, path="inputs.script"))
                elif not RETURN_OBJ.search(body):
                    out.append(fl.finding("warning", "SCRIPT_RETURN_SHAPE",
                                          "return an object (return { key: value }), not a bare scalar",
                                          node=nid, path="inputs.script"))
                if AGGREGATE.search(body):
                    out.append(fl.finding("error", "SCRIPT_RESERVED_AGGREGATE",
                                          "`aggregate` is a reserved host global; rename the variable",
                                          node=nid, path="inputs.script"))
        for path, expr in _expr_strings(node):
            _scan(expr, nid, path, out)
    return out

