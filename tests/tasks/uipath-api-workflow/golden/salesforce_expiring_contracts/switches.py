#!/usr/bin/env python3
import itertools
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from golden_connectors import DOTS, js_strings, member_base  # noqa: E402

UNKNOWN = object()
UNDEFINED = object()
ANY_STEP = object()
MAX_SWITCHES = 6
INPUT_REFERENCE = re.compile(r"\$workflow(?:\?\.|\.)input(?:(?:\?\.|\.)([A-Za-z_$][\w$]*)"
                             r"|(?:\?\.)?\[\s*(['\"])([A-Za-z_$][\w$]*)\2\s*\])")
LITERALS = {"true": True, "false": False, "null": None, "undefined": UNDEFINED}
NUMBER = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?")
STRING = re.compile(r"'([^'\\]*)'|\"([^\"\\]*)\"")
UNSUPPORTED = re.compile(r"[,;:]|=>|(?<![=!<>])=(?![=>])|(?<!\?)\?(?![?.])")
CLOSING = {")": "(", "]": "[", "}": "{"}
FLOW_WORDS = frozenset({"end", "exit", "continue"})
ROOTS = frozenset({"$workflow", "$input", "$output", "$context"})
ASSIGNMENTS = frozenset({"=", "+=", "-=", "*=", "/=", "%=", "**=", "<<=", ">>=", ">>>=", "&=", "|=", "^=", "&&=", "||=",
                         "??="})
COMPARISONS = frozenset({"===", "!==", "==", "!="})
DECLARATIONS = frozenset({("name", "const"), ("name", "let"), ("name", "var")})


def switch_off(workflow, effects, inputs, booleans):
    if not effects:
        return dict(inputs), []
    if not trusted(workflow):
        return dict(inputs), [description for description, _ in effects]
    read = condition_inputs(workflow)
    candidates = sorted(name for name in booleans if name in read and name not in inputs)[:MAX_SWITCHES]
    best = None
    for count in range(len(candidates) + 1):
        for names in itertools.combinations(candidates, count):
            for values in itertools.product((True, False), repeat=count):
                tried = {**inputs, **dict(zip(names, values))}
                skipped = unreached(workflow, tried)
                left = [description for description, activity in effects if id(activity) not in skipped]
                if not left:
                    return tried, []
                if best is None or len(left) < len(best[1]):
                    best = tried, left
    return best


def condition_inputs(workflow):
    names, stack = set(), [workflow]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            texts = [node["if"]] if isinstance(node.get("if"), str) else []
            cases = node.get("switch")
            for case in cases if isinstance(cases, list) else ():
                for spec in case.values() if isinstance(case, dict) else ():
                    when = spec.get("when") if isinstance(spec, dict) else None
                    if isinstance(when, str):
                        texts.append(when)
            names.update(match.group(1) or match.group(3) for text in texts for match in INPUT_REFERENCE.finditer(text))
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return names


def condition(when, env):
    if not isinstance(when, str):
        return None
    text = when.strip()
    if not (text.startswith("${") and text.endswith("}")):
        return None
    return evaluate(text[2:-1], env)[1]


def evaluate(text, env):
    if "`" in text or "/" in text:
        return UNKNOWN, None
    text = _unwrap(text)
    masked = _mask(text)
    if not text or masked is None or UNSUPPORTED.search(masked):
        return UNKNOWN, None
    if "??" in masked and ("||" in masked or "&&" in masked):
        return UNKNOWN, None
    for operator, combine in (("??", _coalesce), ("||", _or), ("&&", _and)):
        parts = _split(text, masked, operator)
        if len(parts) > 1:
            result = evaluate(parts[0], env)
            for part in parts[1:]:
                result = combine(result, evaluate(part, env))
            return result
    comparisons = list(re.finditer(r"===|!==|==|!=", masked))
    if len(comparisons) > 1:
        return UNKNOWN, None
    if comparisons:
        match = comparisons[0]
        return _compare(match.group(), evaluate(text[:match.start()], env)[0], evaluate(text[match.end():], env)[0])
    if text.startswith("!"):
        truth = evaluate(text[1:], env)[1]
        return (UNKNOWN, None) if truth is None else (not truth, not truth)
    if re.fullmatch(r"Boolean\(\s*\)", masked):
        truth = evaluate(text[len("Boolean("):-1], env)[1]
        return (UNKNOWN, None) if truth is None else (truth, truth)
    if text in LITERALS:
        return _known(LITERALS[text])
    if NUMBER.fullmatch(text):
        return _known(float(text))
    string = STRING.fullmatch(text)
    if string:
        return _known(string.group(1) if string.group(1) is not None else string.group(2))
    reference = INPUT_REFERENCE.fullmatch(text)
    if reference:
        return _known(env.get(reference.group(1) or reference.group(3), UNKNOWN))
    return UNKNOWN, None


def _known(value):
    return value, _truthy(value)


def _truthy(value):
    if value is UNKNOWN:
        return None
    if value is UNDEFINED or value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == value and value != 0
    if isinstance(value, str):
        return value != ""
    return True


def _js_type(value):
    if value is UNDEFINED:
        return "undefined"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    return "string" if isinstance(value, str) else "object"


def _compare(operator, left, right):
    if left is UNKNOWN or right is UNKNOWN:
        return UNKNOWN, None
    kinds = {_js_type(left), _js_type(right)}
    if len(kinds) == 1:
        equal = left == right
    elif operator in ("===", "!=="):
        equal = False
    elif kinds == {"null", "undefined"}:
        equal = True
    else:
        return UNKNOWN, None
    result = equal if operator in ("===", "==") else not equal
    return result, result


def _coalesce(left, right):
    value, truth = left
    if value is None or value is UNDEFINED:
        return right
    return left if value is not UNKNOWN or truth is True else (UNKNOWN, None)


def _or(left, right):
    if left[1] is True:
        return left
    if left[1] is False:
        return right
    return UNKNOWN, True if right[1] is True else None


def _and(left, right):
    if left[1] is False:
        return left
    if left[1] is True:
        return right
    return UNKNOWN, False if right[1] is False else None


def _mask(text):
    masked, open_brackets, quote, escaped = [], [], None, False
    for char in text:
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
                masked.append(" " if open_brackets else char)
                continue
            masked.append(" ")
            continue
        if char in CLOSING and (not open_brackets or open_brackets.pop() != CLOSING[char]):
            return None
        masked.append(" " if open_brackets else char)
        if char in "'\"":
            quote = char
        elif char in "([{":
            open_brackets.append(char)
    return None if open_brackets or quote else "".join(masked)


def _unwrap(text):
    text = text.strip()
    while text.startswith("(") and text.endswith(")"):
        masked = _mask(text)
        if masked is None or masked[1:-1].strip():
            break
        text = text[1:-1].strip()
    return text


def _split(text, masked, operator):
    parts, start = [], 0
    for match in re.finditer(re.escape(operator), masked):
        parts.append(text[start:match.start()])
        start = match.end()
    return parts + [text[start:]]


def unreached(workflow, env):
    skipped = set()
    _run_list(workflow.get("do") if isinstance(workflow, dict) else None, env, skipped)
    return skipped


def _run_list(tasks, env, skipped):
    if not isinstance(tasks, list):
        return True
    entries = [next(iter(item.items())) if isinstance(item, dict) and len(item) == 1 else (None, item)
               for item in tasks]
    positions = {}
    for index, (name, _) in enumerate(entries):
        positions.setdefault(name, []).append(index)
    reached, finishes, todo = set(), False, [0]
    while todo:
        index = todo.pop()
        if index >= len(entries):
            finishes = True
            continue
        if index in reached:
            continue
        reached.add(index)
        for step in _steps(entries[index][1], env, skipped):
            if step == "continue":
                todo.append(index + 1)
            elif step == "exit":
                finishes = True
            elif step == "end":
                continue
            elif isinstance(step, str) and step in positions:
                todo.extend(positions[step])
            else:
                todo.extend(range(len(entries) + 1))
    for index, (_, spec) in enumerate(entries):
        if index not in reached:
            skipped.update(_ids(spec))
    return finishes


def _steps(spec, env, skipped):
    if not isinstance(spec, dict):
        return {"continue"}
    guard = condition(spec["if"], env) if "if" in spec else True
    if guard is False:
        skipped.update(_ids(spec))
        return {"continue"}
    cases = spec.get("switch")
    if isinstance(cases, list):
        steps = _switch(cases, env)
    elif not _finishes(spec, env, skipped):
        steps = set()
    else:
        then = spec.get("then", "continue")
        steps = {then} if isinstance(then, str) else {ANY_STEP}
    return steps | {"continue"} if guard is None else steps


def _switch(cases, env):
    targets, has_default = set(), False
    for case in cases:
        if not (isinstance(case, dict) and len(case) == 1):
            return {ANY_STEP}
        (key, spec), = case.items()
        then = spec.get("then", "continue") if isinstance(spec, dict) else None
        if not isinstance(then, str):
            return {ANY_STEP}
        if key == "default" or "when" not in spec:
            has_default = True
            targets.add(then)
            if "when" not in spec:
                continue
        holds = condition(spec["when"], env)
        if holds is not False:
            targets.add(then)
        if holds is True:
            return targets
    return targets if has_default else targets | {"continue"}


def _finishes(spec, env, skipped):
    if isinstance(spec.get("try"), list):
        catch = spec.get("catch")
        tried = _run_list(spec["try"], env, skipped)
        caught = _run_list(catch.get("do"), env, skipped) if isinstance(catch, dict) else True
        return tried or caught
    if isinstance(spec.get("do"), list):
        finished = _run_list(spec["do"], env, skipped)
        return finished or "for" in spec or "doWhile" in spec
    return True


def _ids(node):
    found, stack = set(), [node]
    while stack:
        item = stack.pop()
        if isinstance(item, (dict, list)):
            found.add(id(item))
            stack.extend(item.values() if isinstance(item, dict) else item)
    return found


def trusted(workflow):
    stack = [workflow]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("then") == "continue" or ("switch" in node and set(node) - {"switch", "metadata"}):
                return False
            for key in ("do", "try"):
                items = node.get(key)
                if isinstance(items, list) and not all(
                        isinstance(item, dict) and len(item) == 1 and next(iter(item)) not in FLOW_WORDS
                        for item in items):
                    return False
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return not any(_writes(tokens) or _aliases(parent, key, tokens) for parent, key, _, tokens in js_strings(workflow))


def _writes(tokens):
    for index, (kind, value) in enumerate(tokens):
        if kind == "punct" and value in ASSIGNMENTS and _bad_target(tokens, index - 1):
            return True
        if kind == "punct" and value in ("++", "--") and (
                _bad_target(tokens, index - 1, True) or _bad_operand(tokens, index + 1, True)):
            return True
        if (kind, value) == ("name", "delete") and _bad_operand(tokens, index + 1):
            return True
        if kind == "name" and value in ("of", "in") and _for_head(tokens, index) and _bad_target(tokens, index - 1):
            return True
    return False


def _bad_target(tokens, end, optional=False):
    if end < 0:
        return not optional
    kind, value = tokens[end]
    if kind == "name":
        if end > 0 and tokens[end - 1] in DOTS:
            return _bad_root(tokens, end - 2)
        return value in ROOTS
    if (kind, value) == ("punct", "]"):
        opener = _opening(tokens, end)
        if opener is None:
            return True
        if opener > 0 and member_base(tokens[opener - 1]):
            return _bad_root(tokens, opener - 1)
        return opener == 0 or tokens[opener - 1] not in DECLARATIONS
    if (kind, value) == ("punct", "}"):
        opener = _opening(tokens, end)
        return opener is None or opener == 0 or tokens[opener - 1] not in DECLARATIONS
    if (kind, value) == ("punct", ")"):
        opener = _opening(tokens, end)
        if opener is not None and opener > 0 and member_base(tokens[opener - 1]):
            return not optional
        return _bad_target(tokens, end - 1)
    return not optional


def _bad_root(tokens, end):
    while end >= 0:
        kind, value = tokens[end]
        if kind == "name":
            if end > 0 and tokens[end - 1] in DOTS:
                end -= 2
                continue
            return value in ROOTS
        if (kind, value) != ("punct", "]"):
            return True
        opener = _opening(tokens, end)
        if opener is None or opener == 0 or not member_base(tokens[opener - 1]):
            return True
        end = opener - 1
    return True


def _bad_operand(tokens, start, optional=False):
    if start >= len(tokens):
        return not optional
    kind, value = tokens[start]
    if kind == "name":
        return value in ROOTS
    if (kind, value) == ("punct", "("):
        return _bad_operand(tokens, start + 1)
    return not optional


def _for_head(tokens, index):
    depth = 0
    for position in range(index - 1, -1, -1):
        kind, value = tokens[position]
        if kind != "punct":
            continue
        if value in (")", "]", "}"):
            depth += 1
        elif value in ("(", "[", "{", "${"):
            if depth:
                depth -= 1
                continue
            if value != "(" or position == 0:
                return False
            before = tokens[position - 1]
            return before == ("name", "for") or (
                before == ("name", "await") and position > 1 and tokens[position - 2] == ("name", "for"))
        elif value == ";" and not depth:
            return False
    return False


def _opening(tokens, end):
    depth = 0
    for position in range(end, -1, -1):
        kind, value = tokens[position]
        if kind != "punct":
            continue
        if value in (")", "]", "}"):
            depth += 1
        elif value in ("(", "[", "{", "${"):
            depth -= 1
            if depth == 0:
                return position
    return None


def _aliases(parent, key, tokens):
    export = (parent, key) == ("export", "as")
    if (parent, key) == ("output", "as") and tokens in ([("name", "$input")], [("name", "$output")]):
        return False
    for index, (kind, root) in enumerate(tokens):
        if kind != "name" or root not in ROOTS or (index > 0 and tokens[index - 1] in DOTS):
            continue
        members, end = _chain(tokens, index)
        if not _holds_inputs(root, members):
            continue
        before = tokens[index - 1] if index > 0 else None
        after = tokens[end] if end < len(tokens) else None
        if before == ("punct", "..."):
            if root != "$context" or len(members) == 2:
                continue
            if export and (_enclosing_object(tokens, index) == 0 if not members else _in_outputs(tokens, index)):
                continue
            return True
        if before in (("name", "typeof"), ("punct", "!")) or any(
                token is not None and token[0] == "punct" and token[1] in COMPARISONS for token in (before, after)):
            continue
        if export and root == "$output" and before == ("punct", ":") and after in (("punct", "}"), ("punct", ",")) \
                and _in_outputs(tokens, index):
            continue
        if root != "$context" and (root == "$workflow") == bool(members) and _destructured(tokens, index):
            continue
        if (parent, key) == ("script", "arguments") and not members and before == ("punct", ":") \
                and tokens[index - 2] == ("str", root) and after in (("punct", "}"), ("punct", ",")) \
                and _enclosing_object(tokens, index) == 0:
            continue
        return True
    return False


def _destructured(tokens, index):
    if index < 3 or tokens[index - 1] != ("punct", "=") or tokens[index - 2] != ("punct", "}"):
        return False
    opener = _opening(tokens, index - 2)
    return opener is not None and opener > 0 and tokens[opener - 1] in DECLARATIONS


def _chain(tokens, index):
    members, position = [], index + 1
    while position < len(tokens):
        if tokens[position] in DOTS and position + 1 < len(tokens) and tokens[position + 1][0] == "name":
            members.append(tokens[position + 1][1])
            position += 2
        elif tokens[position] == ("punct", "?.") and position + 1 < len(tokens) and tokens[position + 1] == ("punct", "["):
            position += 1
        elif tokens[position] == ("punct", "["):
            close = _closing_bracket(tokens, position)
            inner = tokens[position + 1:close]
            members.append(inner[0][1] if len(inner) == 1 and inner[0][0] == "str" else None)
            position = close + 1
        else:
            break
    return members, position


def _closing_bracket(tokens, index):
    depth = 0
    for position in range(index, len(tokens)):
        kind, value = tokens[position]
        if kind != "punct":
            continue
        if value in ("(", "[", "{", "${"):
            depth += 1
        elif value in (")", "]", "}"):
            depth -= 1
            if depth == 0:
                return position
    return len(tokens)


def _holds_inputs(root, members):
    if root == "$workflow":
        return not members or (len(members) == 1 and members[0] in (None, "input"))
    if root == "$context":
        return not members or (len(members) <= 2 and members[0] in (None, "outputs"))
    return not members


def _enclosing_object(tokens, index):
    depth = 0
    for position in range(index - 1, -1, -1):
        kind, value = tokens[position]
        if kind != "punct":
            continue
        if value in (")", "]", "}"):
            depth += 1
        elif value in ("(", "[", "{", "${"):
            if depth:
                depth -= 1
            else:
                return position if value == "{" else None
    return None


def _in_outputs(tokens, index):
    opener = _enclosing_object(tokens, index)
    if opener is None or opener < 3 or tokens[opener - 1] != ("punct", ":"):
        return False
    return tokens[opener - 2] in (("name", "outputs"), ("str", "outputs")) and _enclosing_object(tokens, opener - 2) == 0
