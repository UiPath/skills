#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "evals" / "_setup"))
from eval_scoring import run_row  # noqa: E402

INFRA_EXIT = 3
PROVIDER_REFUSAL = re.compile(r"\b429\b|rate.?limit|insufficient_quota|\b50[234]\b|service unavailable",
                              re.IGNORECASE)
MODEL_ENDPOINTS = {
    "uipath-openai-openai": ("/v2/chat/completion", "/chat/completions", "/generatechatcompletion", "/completions",
                             "/generatetextcompletion", "/summarizetext", "/analysetext", "/categorizetext",
                             "/translatetext", "/parsetext", "/draftemail"),
    "uipath-uipath-airdk": ("/v1/llmcall", "/v2/generatechatcompletion", "/summarise", "/rewrite", "/translate",
                            "/categorize", "/generateemail", "/v1/reformat"),
}
POST_READS = {"uipath-salesforce-sfdc": ("/curated_soqlquery", "/parameterizedsearch_post"),
              "uipath-atlassian-jira": ("/search",)}
HTTP_CONNECTOR = "uipath-uipath-http"
ERROR_CODE = re.compile(r'"ErrorCode":\s*"([\w.-]{1,64})"')
SCRIPT_REACH = re.compile(r"\b(fetch|require|import|eval|Function)\s*\(|\b(process|global|self|window|navigator)"
                          r"(?:\.[A-Za-z_$]|\s*\[)|\b(globalThis|XMLHttpRequest|WebSocket|EventSource|Deno|Bun)\b|"
                          r"\.(constructor)\b|\[\s*['\"`](constructor)['\"`]\s*\]|\b(this)\s*\[")
BARE_REACH = frozenset({
    "require", "module", "exports", "process", "global", "globalThis", "self", "window", "navigator", "Function",
    "eval", "import", "Reflect", "Proxy", "fetch", "XMLHttpRequest", "WebSocket", "EventSource", "Deno", "Bun",
    "Worker", "WebAssembly", "importScripts", "postMessage", "onmessage", "addEventListener", "arguments", "this",
    "with", "__dirname", "__filename",
})
MEMBER_REACH = frozenset({
    "constructor", "prototype", "__proto__", "getPrototypeOf", "setPrototypeOf", "getOwnPropertyDescriptor",
    "getOwnPropertyDescriptors", "defineProperty", "defineProperties", "__defineGetter__", "__defineSetter__",
    "__lookupGetter__", "__lookupSetter__",
})
STRING_REACH = MEMBER_REACH | {"require", "process", "globalThis", "global", "module", "eval", "Function", "fetch",
                               "import", "child_process", "worker_threads"}
CODE_KEYS = frozenset({"code", "as", "when", "if"})
JS_NAME = re.compile(r"(?:[^\W\d]|\$)[\w$]*")
JS_NUMBER = re.compile(r"(?:0[xXoObB][0-9a-fA-F_]+|(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?\d[\d_]*)?)n?")
JS_PUNCTUATORS = (">>>=", "...", "===", "!==", "**=", "<<=", ">>=", ">>>", "&&=", "||=", "??=", "=>", "==", "!=", "<=",
                  ">=", "&&", "||", "??", "?.", "++", "--", "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "**", "<<",
                  ">>", *"{}()[];,<>+-*/%&|^!~?:=.@#")
JS_ESCAPE = re.compile(r"\\(?:u\{([0-9a-fA-F]+)\}|u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2})|(.))", re.DOTALL)
LINE_BREAKS = "\n\r\u2028\u2029"
REGEX_AFTER = frozenset({"return", "typeof", "instanceof", "in", "new", "delete", "void", "throw", "case", "do",
                         "else"})
CONTEXTUAL = frozenset({"of", "yield", "await", "let", "async", "get", "set", "static", "as", "from"})
PAREN_KEYWORDS = frozenset({"if", "while", "for", "with"})
DOTS = (("punct", "."), ("punct", "?."))


class InfraError(Exception):
    pass


def uip(*args, timeout=120):
    label = " ".join(args[:4])
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise InfraError(f"uip {label}: {type(exc).__name__}") from exc
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise InfraError(f"uip {label} printed no JSON (exit {proc.returncode})") from exc
    if not isinstance(envelope, dict):
        raise InfraError(f"uip {label} printed a non-object envelope")
    return envelope


def data(*args, timeout=120):
    envelope = uip(*args, timeout=timeout)
    if envelope.get("Result") != "Success":
        detail = {key: envelope[key] for key in ("ErrorCode", "Message") if key in envelope}
        raise InfraError(f"uip {' '.join(args[:4])} failed: {json.dumps(detail)[:300]}")
    return envelope.get("Data")


def field(record, name):
    if not isinstance(record, dict):
        return None
    for key, value in record.items():
        if key.lower() == name.lower():
            return value
    return None


def dicts_in(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from dicts_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from dicts_in(item)


def connection_id(connector_key):
    for scope, where in (((), "in the personal workspace"), (("--all-folders",), "across all folders")):
        try:
            rows = data("is", "connections", "list", connector_key, *scope, "--refresh")
        except InfraError:
            if scope:
                raise
            continue
        rows = [row for row in rows or [] if str(field(row, "ConnectorKey") or "").lower() == connector_key]
        enabled = [row for row in rows if str(field(row, "State") or "").lower() == "enabled"]
        if len(enabled) == 1:
            return field(enabled[0], "Id")
        if enabled:
            break
    raise InfraError(f"expected one Enabled {connector_key} connection {where}, found {len(enabled)} of {len(rows)}")


def workflow_paths(root="."):
    root = Path(root).resolve()
    return sorted((p for p in root.rglob("Workflow.json") if p.parent != root and "node_modules" not in p.parts),
                  key=str)


def read_workflow(path):
    try:
        workflow = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return workflow if isinstance(workflow, dict) else None


def choose_workflow(fits, answers, root="."):
    paths = workflow_paths(root)
    fitting, answering = [], []
    for path in paths:
        workflow = read_workflow(path)
        if workflow is not None and fits(workflow):
            fitting.append(path)
            if answers(workflow):
                answering.append(path)
    chosen = answering or fitting or paths
    return chosen[0] if chosen else None


def declared_inputs(workflow):
    return _schema_properties(field(workflow, "input"))


def declared_outputs(workflow):
    return _schema_properties(field(workflow, "output"))


def _schema_properties(side):
    properties = field(field(field(side, "schema"), "document"), "properties")
    if not isinstance(properties, dict):
        return {}
    return {name: spec if isinstance(spec, dict) else {} for name, spec in list(properties.items())[:20]}


def needed_inputs(workflow):
    required = field(field(field(field(workflow, "input"), "schema"), "document"), "required")
    if not isinstance(required, list):
        return []
    declared = declared_inputs(workflow)
    return [name for name in required if isinstance(name, str) and "default" not in declared.get(name, {})]


def connection_map():
    rows = data("is", "connections", "list", "--all-folders", "--refresh")
    return {str(field(row, "Id")).lower(): str(field(row, "ConnectorKey") or "").lower()
            for row in rows or [] if field(row, "Id")}


def side_effect_tasks(workflow, reads_from, connections=None, open_urls=()):
    connections = {str(key).lower(): value for key, value in (connections or {}).items()}
    found = []
    stack = [(None, workflow, None, False)]
    while stack:
        name, node, task, listed = stack.pop()
        if isinstance(node, dict):
            effect = _side_effect(node, name, reads_from, connections, open_urls)
            if effect:
                found.append((f"{task or name} ({effect})", node))
            stack.extend((key, value, key if listed and len(node) == 1 else task, False) for key, value in node.items())
        elif isinstance(node, list):
            stack.extend((name, item, task, name in ("do", "try")) for item in node)
    return sorted(found, key=lambda pair: pair[0])


def side_effects(workflow, reads_from, connections=None, open_urls=()):
    return [description for description, _ in side_effect_tasks(workflow, reads_from, connections, open_urls)]


def _side_effect(node, parent, reads_from, connections, open_urls):
    reach = set()
    for key, value in _code(node, parent):
        reach.update(name for match in SCRIPT_REACH.finditer(value) for name in match.groups() if name)
        tokens = script_tokens(parent, key, value)
        if tokens is None:
            return "JavaScript the grader cannot read"
        reach |= _reach(tokens)
    if reach:
        return "JavaScript using " + ", ".join(sorted(reach))
    run = node.get("run")
    if "emit" in node:
        return "emit"
    if isinstance(run, dict) and set(run) - {"script"}:
        return "run " + ", ".join(sorted(set(run) - {"script"}))
    if "call" not in node:
        return None
    call = node["call"]
    spec = node.get("with") if isinstance(node.get("with"), dict) else {}
    if call in ("UiPath.IntSvc", "UiPath.IntSvcEvent"):
        label = str(spec.get("connector") or "").lower()
        connector = connections.get(str(spec.get("connectionId") or "").lower())
        method = "trigger" if call == "UiPath.IntSvcEvent" else str(spec.get("method") or "").upper()
        endpoint = str(spec.get("endpoint") or "")
        if connector is None or connector != label:
            where = "an unlisted connection" if connector is None else f"a {connector} connection"
            return _describe(label or call, method, endpoint, "through", where)
        if call == "UiPath.IntSvcEvent":
            return None if connector == reads_from else _describe(connector, method)
        return None if _reads(connector, method, endpoint.lower(), reads_from) else _describe(connector, method, endpoint)
    if call == "UiPath.Http":
        request = spec.get("bodyParameters") if isinstance(spec.get("bodyParameters"), dict) else {}
        method, url = str(request.get("method") or "").upper(), str(request.get("url") or "")
        manual = (str(spec.get("connector") or "").lower() == HTTP_CONNECTOR
                  and spec.get("connectionId") == "ImplicitConnection" and spec.get("method") == "POST"
                  and spec.get("endpoint") == "/http-request" and not request.get("targetConnector")
                  and str(request.get("authentication") or "manual").lower() == "manual")
        if manual and _open(url, open_urls):
            return None
        return _describe("HTTP", method, url, "" if manual else "through a connector")
    if call == "http":
        endpoint = spec.get("endpoint")
        url = str((endpoint.get("uri") if isinstance(endpoint, dict) else endpoint) or "")
        method = str(spec.get("method") or "").upper()
        return None if _open(url, open_urls) else _describe("HTTP", method, url)
    return f"call {call}"


def _reads(connector, method, endpoint, reads_from):
    if method == "POST" and endpoint in MODEL_ENDPOINTS.get(connector, ()):
        return True
    return connector == reads_from and (method == "GET" or (method == "POST" and endpoint in POST_READS.get(connector, ())))


def _open(url, prefixes):
    return any(prefix.startswith("https://") and prefix.endswith("/") and url.startswith(prefix) for prefix in prefixes)


def _code(node, parent=None):
    stack = list(node.items())
    while stack:
        key, value = stack.pop()
        if isinstance(value, list):
            stack.extend((key, item) for item in value)
        elif isinstance(value, str) and (key in CODE_KEYS or "${" in value or
                                         (key == "from" and parent in ("input", "output"))):
            yield key, value


def script_tokens(parent, key, value):
    tokens = _script_tokens(parent, key, value)
    if tokens is None and (parent, key) == ("script", "arguments"):
        return _script_tokens(parent, key, value.replace('\\"', '"'))
    return tokens


def _script_tokens(parent, key, value):
    text = value.strip()
    if text.startswith("${") and text.endswith("}"):
        tokens = js_tokens(text[2:-1])
        return tokens if tokens is not None else js_tokens(value, interpolated=True)
    if key in CODE_KEYS or (key == "from" and parent in ("input", "output")):
        return js_tokens(value)
    if "${" in value:
        return js_tokens(value, interpolated=True)
    return []


def js_strings(workflow):
    stack = [(None, None, workflow)]
    while stack:
        parent, key, value = stack.pop()
        if isinstance(value, dict):
            stack.extend((key, child, item) for child, item in value.items())
        elif isinstance(value, list):
            stack.extend((parent, key, item) for item in value)
        elif isinstance(value, str):
            tokens = script_tokens(parent, key, value)
            if tokens:
                yield parent, key, value, tokens


def _reach(tokens):
    found = set()
    for index, (kind, value) in enumerate(tokens):
        dotted = index > 0 and tokens[index - 1] in DOTS
        if kind == "name" and (value in MEMBER_REACH or (value in BARE_REACH and not dotted)):
            found.add(value)
        elif kind == "str" and _unescape(value).strip() in STRING_REACH:
            found.add(_unescape(value).strip())
        elif (kind, value) == ("punct", "[") and index > 0 and member_base(tokens[index - 1]):
            close = closing(tokens, index)
            inner = tokens[index + 1:close]
            if len(inner) > 1 and any(part[0] in ("str", "text") for part in inner):
                found.add("a computed property name")
    return found


def member_base(token):
    kind, value = token
    if kind == "name":
        return value not in REGEX_AFTER and value not in CONTEXTUAL
    return kind in ("str", "text", "regex", "num") or value in (")", "]", "?.")


def _unescape(text):
    def replace(match):
        code = match.group(1) or match.group(2) or match.group(3)
        if code is None:
            return match.group(4)
        value = int(code, 16)
        return chr(value) if value <= 0x10FFFF else ""
    return JS_ESCAPE.sub(replace, text)


def closing(tokens, index):
    depth = 0
    for position in range(index, len(tokens)):
        if tokens[position] == ("punct", "["):
            depth += 1
        elif tokens[position] == ("punct", "]"):
            depth -= 1
            if depth == 0:
                return position
    return len(tokens)


def js_tokens(text, interpolated=False):
    tokens, stack, keyword_paren, i = [], [], False, 0
    if interpolated:
        stack.append("text")
        i = _template(text, 0, tokens, stack)
    while i is not None and i < len(text):
        char = text[i]
        if char.isspace() or char == "﻿":
            i += 1
        elif text.startswith("//", i):
            i = min((index for index in (text.find(mark, i) for mark in LINE_BREAKS) if index >= 0), default=len(text))
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = None if end < 0 else end + 2
        elif char in "'\"":
            i = _string(text, i, tokens)
        elif char == "`":
            stack.append("`")
            i = _template(text, i + 1, tokens, stack)
        elif char == "/":
            regex = _starts_regex(tokens, keyword_paren)
            if regex is None:
                return None
            if regex:
                i = _regex(text, i, tokens)
            else:
                operator = "/=" if text.startswith("/=", i) else "/"
                tokens.append(("punct", operator))
                i += len(operator)
        elif JS_NAME.match(text, i):
            name = JS_NAME.match(text, i).group()
            tokens.append(("name", name))
            i += len(name)
        elif char.isdigit() or (char == "." and text[i + 1:i + 2].isdigit()):
            number = JS_NUMBER.match(text, i).group()
            tokens.append(("num", number))
            i += len(number)
        else:
            operator = next((op for op in JS_PUNCTUATORS if text.startswith(op, i)), None)
            if operator is None:
                return None
            if operator == "?." and text[i + 2:i + 3].isdigit():
                operator = "?"
            if operator in "([{":
                previous = tokens[-1] if tokens else None
                keyword = (operator == "(" and previous is not None and previous[0] == "name"
                           and previous[1] in PAREN_KEYWORDS and not (len(tokens) > 1 and tokens[-2] in DOTS))
                stack.append("(k" if keyword else operator)
            elif operator in ")]}":
                opener = stack.pop() if stack else None
                if operator == "}" and opener == "${":
                    tokens.append(("punct", "}"))
                    i = _template(text, i + 1, tokens, stack)
                    continue
                if opener is None or opener[0] != {")": "(", "]": "[", "}": "{"}[operator]:
                    return None
                keyword_paren = opener == "(k"
            tokens.append(("punct", operator))
            i += len(operator)
    if i is None or stack not in ([], ["text"]):
        return None
    return tokens


def _starts_regex(tokens, keyword_paren):
    if not tokens:
        return True
    kind, value = tokens[-1]
    if kind in ("num", "str", "regex", "text"):
        return False
    if kind == "name":
        if len(tokens) > 1 and tokens[-2] in DOTS:
            return False
        if value in REGEX_AFTER:
            return True
        return None if value in CONTEXTUAL else False
    if value == ")":
        return keyword_paren
    if value == "]":
        return False
    return None if value in ("}", "++", "--") else True


def _string(text, i, tokens):
    quote, j = text[i], i + 1
    while j < len(text):
        if text[j] == "\\":
            j += 2
        elif text[j] == quote:
            tokens.append(("str", text[i + 1:j]))
            return j + 1
        elif text[j] in "\n\r":
            return None
        else:
            j += 1
    return None


def _template(text, i, tokens, stack):
    raw, start = stack[-1] == "text", i
    while i < len(text):
        if text.startswith("${", i):
            tokens += [("text", text[start:i]), ("punct", "${")]
            stack.append("${")
            return i + 2
        if not raw and text[i] == "\\":
            i += 2
        elif not raw and text[i] == "`":
            tokens.append(("text", text[start:i]))
            stack.pop()
            return i + 1
        else:
            i += 1
    if raw:
        tokens.append(("text", text[start:]))
        return len(text)
    return None


def _regex(text, i, tokens):
    j, in_class = i + 1, False
    while j < len(text):
        char = text[j]
        if char in LINE_BREAKS:
            return None
        if char == "\\":
            j += 2
            continue
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and not in_class:
            flags = re.match(r"[\w$]*", text[j + 1:]).group()
            tokens.append(("regex", text[i:j + 1 + len(flags)]))
            return j + 1 + len(flags)
        j += 1
    return None


def _describe(*parts):
    return " ".join(part for part in parts if part)


def run_workflow(workflow_path, inputs, timeout):
    try:
        return run_row(workflow_path, inputs, timeout=timeout, no_auth=False)
    except OSError as exc:
        raise InfraError(f"cannot run uip: {exc}") from exc


def brief(error):
    if error in ("run timed out", "grading time budget used up", "no Response evaluation found in debug log"):
        return error
    code = ERROR_CODE.search(error or "")
    return f"run failed ({code.group(1)})" if code else "run failed"


def strings_in(value):
    found = []
    if isinstance(value, str):
        found.append(value)
        decoded = decode_json_string(value)
        if decoded is not None:
            found += strings_in(decoded)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found += strings_in(item)
    elif isinstance(value, list):
        for item in value:
            found += strings_in(item)
    return found


def decode_json_string(value):
    text = value.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        decoded = json.loads(text)
    except ValueError:
        return None
    return decoded if isinstance(decoded, (dict, list)) else None
