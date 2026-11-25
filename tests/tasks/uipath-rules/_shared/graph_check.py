#!/usr/bin/env python3
"""Shared grading for the uipath-rules decision-graph tasks.

A graph is one `.dmn` whose decisions are linked by `informationRequirement`.
`evaluate_graph` runs every decision table in dependency order, so the tasks
grade what each decision returns instead of how the agent named or shaped it.
The diagram checks compare `DMNShape` positions with the fixture the task
started from. `graph_check.py chain` grades a freshly authored LoanRules
project; `graph_check.py names` checks every table's rule annotations;
`graph_check.py engine` asks the rules engine for the LoanRules values.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from rules_check import (
    DMN_NS,
    NS,
    POLICY,
    UNEVALUABLE,
    check_named_rules,
    evaluate,
    fail,
    find_project,
    input_columns,
    load_graph,
    output_names,
    output_properties,
    read_entry_points,
    unary_test,
)

DMNDI_NS = "https://www.omg.org/spec/DMN/20230324/DMNDI/"
DC_NS = "http://www.omg.org/spec/DMN/20180521/DC/"
# The size the designer draws each card, whatever width and height the file holds, from
# PO.Frontend DrdLayout.ts. Graded against the designer rather than against whatever layout
# library the CLI pins, because a user sees the designer: a diagram that is clear at the pinned
# width and collides at the designer's is a collision they would see.
DRAWN_SIZE = {"decision": (288, 96), "inputData": (240, 96),
              "businessKnowledgeModel": (224, 96), "textAnnotation": (224, 64)}

LOAN_PROJECT = "LoanRules"
LOAN_INPUTS = {"creditScore": "number", "income": "number", "loanAmount": "number"}
LOAN_OUTPUTS = {"riskBand": "string", "interestRate": "number"}


def interest_rate(band: str, loan_amount: float) -> float:
    if band == "High":
        return 12.5
    large = loan_amount >= 100000
    return (9 if large else 8) if band == "Medium" else (6 if large else 5.5)


LOAN_CASES = [
    ({**inputs, "loanAmount": amount}, {"riskBand": band, "interestRate": interest_rate(band, amount)})
    for inputs, band in POLICY
    for amount in (20000, 99999, 100000)
]


def decisions(root: ET.Element) -> list[ET.Element]:
    return root.findall("dmn:decision", NS)


def reference_name(decision: ET.Element) -> str:
    """The name a downstream expression reads the decision's result by."""
    variable = decision.find("dmn:variable", NS)
    return (variable.get("name") if variable is not None else None) or decision.get("name") or ""


# Each reference sits inside the requirement element of its own kind, so the holder is not
# always `informationRequirement`: a call to a knowledge model is a `knowledgeRequirement`.
REQUIREMENT_HOLDER = {
    "requiredInput": "informationRequirement",
    "requiredDecision": "informationRequirement",
    "requiredKnowledge": "knowledgeRequirement",
}


def required(element: ET.Element, kind: str) -> list[str]:
    """Ids the element requires; `kind` is `requiredInput`, `requiredDecision` or `requiredKnowledge`."""
    holder = REQUIREMENT_HOLDER[kind]
    return [(e.get("href") or "").lstrip("#")
            for e in element.findall(f"dmn:{holder}/dmn:{kind}", NS)]


def decision_for_output(root: ET.Element, output: str) -> ET.Element:
    """The decision that answers under `output`.

    A decision table answers under its output column names. A decision whose logic is a literal
    expression has no columns and answers under its own name, which is also what a reader of it
    addresses — so it is matched on that. Without this a tableless decision reached
    `output_names(None)` and raised, which failed a correct submission rather than grading it.
    """
    found = []
    for decision in decisions(root):
        table = decision.find("dmn:decisionTable", NS)
        answers = output_names(table) if table is not None else [decision.get("name") or ""]
        if output in answers:
            found.append(decision)
    if len(found) != 1:
        fail(f"{len(found)} decisions return an output named {output}, expected exactly one")
    return found[0]


def executable_text(decision: ET.Element) -> str:
    """Only the FEEL a decision runs: its literal expression, and its table's cells.

    Deliberately not `itertext()`. A rule's annotation column, a `<description>` and a
    `<textAnnotation>` are prose the engine never evaluates, so a search over all descendant text
    let a decision that inlined the work it was told to delegate pass by merely naming the model
    in a note beside it.
    """
    parts = [decision.findtext("dmn:literalExpression/dmn:text", default="", namespaces=NS) or ""]
    for cells in ("dmn:decisionTable/dmn:input/dmn:inputExpression/dmn:text",
                  "dmn:decisionTable/dmn:rule/dmn:inputEntry/dmn:text",
                  "dmn:decisionTable/dmn:rule/dmn:outputEntry/dmn:text"):
        parts += [element.text or "" for element in decision.findall(cells, NS)]
    return "\n".join(parts)


def outside_strings(text: str) -> str:
    """`text` with every FEEL string literal blanked, its length unchanged.

    A cell may hold `"discounted(50, tier)"` as data, which the engine never calls, and a string
    may hold an unbalanced parenthesis. Blanking rather than deleting keeps every later offset
    where it was, so a scan over the result still indexes the original text.
    """
    out, quote, escaped = [], "", False
    for char in text:
        if quote:
            out.append(" ")
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
        elif char in ('"', "'"):
            quote, _ = char, out.append(" ")
        else:
            out.append(char)
    return "".join(out)


def model_calls(decision: ET.Element, model: str) -> list[str]:
    """The argument text of each `model(...)` call in what `decision` runs.

    Whitespace between the name and the parenthesis is a call — FEEL allows it — and a name
    ending in the model's is not: `netDiscounted(` is not a call to `discounted`.
    """
    return model_calls_in(executable_text(decision), model)


def model_calls_in(text: str, model: str) -> list[str]:
    """The argument text of each `model(...)` call in `text`."""
    scan = outside_strings(text)
    calls = []
    for match in re.finditer(rf"(?<![A-Za-z0-9_.]){re.escape(model)}\s*\(", scan):
        depth, cursor = 0, match.end() - 1
        for cursor in range(match.end() - 1, len(scan)):
            depth += (scan[cursor] == "(") - (scan[cursor] == ")")
            if depth == 0:
                break
        calls.append(text[match.end():cursor])
    return calls


def executable_cells(decision: ET.Element) -> list[str]:
    """Each FEEL expression the decision runs, one per cell, rather than joined into one blob."""
    cells = [decision.findtext("dmn:literalExpression/dmn:text", default="", namespaces=NS) or ""]
    cells += [element.text or "" for element
              in decision.findall("dmn:decisionTable/dmn:rule/dmn:outputEntry/dmn:text", NS)]
    return [cell.strip() for cell in cells if cell.strip()]


def sole_call_arguments(cell: str, model: str) -> str:
    """The arguments of `model(...)` when that call is the whole of `cell`.

    `discounted(50, tier) + 100` answers a different number from `discounted(50, tier)`, and a
    check that only looked for a call anywhere in the cell accepted both. Requiring the call to
    be the entire expression is what makes its arguments enough to say what the cell returns.
    """
    calls = model_calls_in(cell, model)
    if not calls:
        fail(f"the cell {cell!r} does not call {model}(...)")
    bare = unwrapped(cell)
    if bare not in (f"{model}({calls[0]})", f"{model} ({calls[0]})"):
        fail(f"the cell {cell!r} is not just the result of {model}(...); the prompt asks for that "
             f"result and nothing added to it")
    return calls[0]


def unwrapped(text: str) -> str:
    """`text` without parentheses that wrap the whole of it. `(f(x))` is the expression `f(x)`."""
    bare = text.strip()
    while bare.startswith("(") and bare.endswith(")"):
        depth = 0
        for cursor, char in enumerate(outside_strings(bare)):
            depth += (char == "(") - (char == ")")
            if depth == 0 and cursor < len(bare) - 1:
                return bare  # the opening paren closes early, so it wraps only part of the text
        bare = bare[1:-1].strip()
    return bare


def answering_cell(decision: ET.Element, inputs: dict) -> str:
    """The FEEL text the decision's logic actually answers with for `inputs`.

    A literal expression has one. A table has one per row, and only the row that fires counts:
    grading the first cell that happened to hold a call let the other rows say anything at all.
    """
    literal = decision.find("dmn:literalExpression", NS)
    table = decision.find("dmn:decisionTable", NS)
    if literal is not None and table is not None:
        fail(f"decision {decision.get('name')!r} carries both a table and a literal expression; DMN "
             f"gives a decision one expression, and the engine would not know which answers")
    if literal is not None:
        return (literal.findtext("dmn:text", default="", namespaces=NS) or "").strip()
    if table is None:
        fail(f"decision {decision.get('name')!r} carries neither a table nor a literal expression")
    policy = table.get("hitPolicy", "UNIQUE")
    # COLLECT and RULE ORDER answer with every matching row, so the first one is not the answer.
    # `rules_check.evaluate` refuses them too; this path has to agree or a COLLECT table would be
    # graded on a row that is only part of what it returns.
    if policy not in ("FIRST", "UNIQUE", "ANY"):
        fail(f"decision {decision.get('name')!r} has hit policy {policy}, which answers with more "
             f"than one row; this check grades a decision that answers with one value")
    columns = input_columns(table)
    # Without a column the caller supplies, `all(...)` is vacuously true and the first row always
    # "fires" — so a table keyed on something else entirely would be graded on row one.
    if not any(column in inputs for column in columns):
        fail(f"decision {decision.get('name')!r} reads {columns}, none of which this check supplies "
             f"({sorted(inputs)}), so which row answers cannot be told")
    for rule in table.findall("dmn:rule", NS):
        cells = [(e.findtext("dmn:text", default="", namespaces=NS) or "") for e in rule.findall("dmn:inputEntry", NS)]
        if all(unary_test(cell, inputs[column]) for cell, column in zip(cells, columns) if column in inputs):
            answers = [(e.findtext("dmn:text", default="", namespaces=NS) or "").strip()
                       for e in rule.findall("dmn:outputEntry", NS)]
            if len(answers) != 1:
                fail(f"decision {decision.get('name')!r} answers with {len(answers)} outputs; this check "
                     f"grades a decision that answers with one")
            return answers[0]
    fail(f"decision {decision.get('name')!r} matches no rule for {inputs}, so it answers nothing")
    raise AssertionError  # unreachable; `fail` exits


def check_model_called(root: ET.Element, decision: ET.Element, model: str) -> list[str]:
    """`decision` both requires the named knowledge model and calls it in the FEEL it runs."""
    models = {m.get("name"): m.get("id") for m in knowledge_models(root)}
    if model not in models:
        fail(f"the rule declares no knowledge model named {model!r}; it holds {sorted(models) or 'none'}")
    if models[model] not in required(decision, "requiredKnowledge"):
        fail(f"decision {decision.get('name')!r} does not require the knowledge model {model!r}")
    calls = model_calls(decision, model)
    if not calls:
        fail(f"decision {decision.get('name')!r} requires {model!r} but never calls {model}(...) in its logic; "
             f"a mention in an annotation is not a call")
    return calls


def resolve(context: dict, path: str) -> tuple[bool, object]:
    """`path` in `context`, where `a.b` reads member `b` of a multi-output decision `a`."""
    value: object = context
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return False, None
        value = value[part]
    return True, value


# A decision the offline evaluator cannot run — a literal expression, or a table whose cells call
# a knowledge model. Distinct from `None`, which is a table that matched no rule and so really
# does answer nothing.
UNEVALUATED = object()


def evaluate_graph(root: ET.Element, inputs: dict) -> dict:
    """Every decision's outputs by output name, each table reading only what its decision requires."""
    by_id = {d.get("id"): d for d in decisions(root)}
    input_names = {e.get("id"): e.get("name") for e in root.findall("dmn:inputData", NS)}
    hits: dict[str, dict | None] = {}

    def run(decision_id: str, path: tuple[str, ...]) -> None:
        if decision_id in hits:
            return
        if decision_id in path:
            fail(f"the decisions require each other in a cycle: {' -> '.join(path + (decision_id,))}")
        decision = by_id.get(decision_id)
        if decision is None:
            fail(f"a requirement names decision {decision_id}, which the file does not hold")
        context: dict = {}
        for input_id in required(decision, "requiredInput"):
            if input_id not in input_names:
                fail(f"decision {decision.get('name')!r} requires input {input_id}, which the file does not hold")
            context[input_names[input_id]] = inputs.get(input_names[input_id])
        unevaluated = False
        for upstream_id in required(decision, "requiredDecision"):
            run(upstream_id, path + (decision_id,))
            hit = hits[upstream_id]
            if hit is UNEVALUATED:
                # Passing the missing value on as a FEEL null would let this table fall through to
                # its `-` row and answer plausibly, so a case could be graded against a value that
                # was never computed. The decision is unevaluated too, and says so below.
                unevaluated = True
                continue
            single = hit is not None and len(hit) == 1
            context[reference_name(by_id[upstream_id])] = next(iter(hit.values())) if single else hit
        table = decision.find("dmn:decisionTable", NS)
        if table is None or unevaluated:
            hits[decision_id] = UNEVALUATED
            return
        values = {}
        for column in input_columns(table):
            found, value = resolve(context, column)
            if not found:
                fail(f"decision {decision.get('name')!r} reads {column!r}, which is not an input or decision it requires")
            if value is UNEVALUABLE:
                hits[decision_id] = UNEVALUATED
                return
            values[column] = value
        # Unsupported values are kept per output, not raised to the whole decision: a matched row
        # can answer a literal band beside a model-computed fee, and marking both unknown failed a
        # case that asked only for the band. They reach a consumer through `values` above, which
        # is what makes a decision that reads one unevaluable in turn.
        hits[decision_id] = evaluate(table, values, context)

    for decision_id in by_id:
        run(decision_id, ())
    # Flat, keyed by column name, so two decisions sharing one would overwrite each other and the
    # last in file order would win — a correct graph could fail or a wrong one pass depending on
    # declaration order. `decision_for_output` refuses a duplicate; this path has to as well.
    outputs: dict = {}
    owner: dict[str, str] = {}
    for decision_id, decision in by_id.items():
        table = decision.find("dmn:decisionTable", NS)
        # An unevaluated decision publishes no output, so a case that names one fails on the
        # "no decision table returns an output named ..." branch rather than on a value the
        # evaluator never worked out.
        if table is None:
            continue
        hit = hits[decision_id]
        for name in output_names(table):
            if name in owner:
                fail(f"decisions {owner[name]!r} and {decision.get('name')!r} both answer with an output "
                     f"named {name!r}; a reader cannot tell them apart")
            owner[name] = decision.get("name") or decision_id
            value = None if hit in (None, UNEVALUATED) else hit.get(name)
            # An output only the engine can work out publishes nothing, so a case naming it fails
            # on the "no decision table returns ..." branch instead of on a value never computed.
            if hit is UNEVALUATED or value is UNEVALUABLE:
                continue
            outputs[name] = value
    return outputs


def same_value(actual: object, expected: object) -> bool:
    """FEEL equality, not Python's.

    Python holds `True == 1` and `False == 0`, so a decision declaring a number where the task
    asked for a boolean passed every case. FEEL keeps the two apart, and keeps `5` and `5.0`
    together: it has one number type, and the engine answers with whichever JSON carries.
    """
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    if not isinstance(actual, bool) and isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return float(actual) == float(expected)
    return actual == expected


def check_graph_cases(root: ET.Element, cases: list) -> None:
    for inputs, expected in cases:
        actual = evaluate_graph(root, inputs)
        for name, value in expected.items():
            if name not in actual:
                fail(f"no decision table returns an output named {name} that this check can evaluate; "
                     f"a literal expression, a call or a formula is graded by the engine "
                     f"(graph_check.py engine), not here")
            if not same_value(actual[name], value):
                fail(f"{inputs} returned {name}={actual[name]!r}, expected {value!r}")


def requires(root: ET.Element, decision: ET.Element, upstream: ET.Element) -> bool:
    """Whether `decision` requires `upstream`, directly or through other decisions."""
    by_id = {d.get("id"): d for d in decisions(root)}
    seen, pending = set(), required(decision, "requiredDecision")
    while pending:
        current = pending.pop()
        if current == upstream.get("id"):
            return True
        if current in seen or current not in by_id:
            continue
        seen.add(current)
        pending += required(by_id[current], "requiredDecision")
    return False


def check_chain(root: ET.Element, downstream_output: str, upstream_output: str) -> None:
    downstream, upstream = decision_for_output(root, downstream_output), decision_for_output(root, upstream_output)
    if downstream is upstream:
        fail(f"{downstream_output} and {upstream_output} come from one decision, expected two")
    if not requires(root, downstream, upstream):
        fail(f"the decision returning {downstream_output} does not require the one returning {upstream_output}")


def check_whole_file_contract(project: Path, dmn_file: Path, inputs: dict, outputs: dict) -> None:
    """The whole-file entry point `uip rules refresh` writes for a graph, carrying every input and output."""
    entry = next((e for e in read_entry_points(project) if e.get("filePath") == f"/{dmn_file.name}"), None)
    if entry is None:
        fail(f"no entry point addresses /{dmn_file.name}; run `uip rules refresh`")
    declared_inputs = (entry.get("input") or {}).get("properties") or {}
    declared_outputs = output_properties(entry.get("output") or {})
    for kind, declared, wanted in (("input", declared_inputs, inputs), ("output", declared_outputs, outputs)):
        for name, json_type in wanted.items():
            if (declared.get(name) or {}).get("type") != json_type:
                fail(f"entry-points.json has no {json_type} {kind} {name}; run `uip rules refresh`")


def check_entry_points_kept(project: Path, fixture: Path) -> None:
    """Every entry point the fixture published keeps its filePath and uniqueId, so bound consumers still resolve."""
    before = json.loads((fixture / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]
    after = {e.get("filePath"): e.get("uniqueId") for e in read_entry_points(project)}
    for entry in before:
        if after.get(entry["filePath"]) != entry["uniqueId"]:
            fail(f"entry point {entry['filePath']} is gone or has a new uniqueId; consumers bound to it would break")


def shapes(root: ET.Element) -> dict[str, tuple[float, float]]:
    """Where the diagram places each element, by element id."""
    placed = {}
    for shape in root.iter(f"{{{DMNDI_NS}}}DMNShape"):
        bounds = shape.find(f"{{{DC_NS}}}Bounds")
        reference = (shape.get("dmnElementRef") or "").lstrip("#").split(":")[-1]
        if bounds is not None and reference:
            placed[reference] = (float(bounds.get("x", 0)), float(bounds.get("y", 0)))
    return placed


def check_shapes_kept(before: ET.Element, after: ET.Element, *, elements_may_go: bool = False) -> None:
    """Every element the fixture placed is still placed, and where the user left it.

    Deliberately not narrowed to the ids the edit kept. An edit can give an element a new id,
    repoint its references and move the card; the old id then leaves the file, and narrowing reads
    that as nothing to check. A task that tells the agent to leave the diagram alone is asking for
    the shape to survive, so a missing id fails like a moved one.

    `elements_may_go` for a task whose edit may legitimately delete an element — a repair of a
    file someone broke by hand. There the shapes that remain still have to be where they were.
    """
    kept = {e.get("id") for e in after} if elements_may_go else None
    now = shapes(after)
    moved = [f"{element} {position} -> {now.get(element)}"
             for element, position in shapes(before).items()
             if (kept is None or element in kept) and now.get(element) != position]
    if moved:
        fail(f"the edit moved or dropped shapes the user had placed: {moved}")


def check_no_overlap(root: ET.Element) -> None:
    """Every drawable element is placed, or none is, and no two cards overlap at the drawn size."""
    kinds = {e.get("id"): e.tag.replace(f"{{{DMN_NS}}}", "") for e in root}
    placed = shapes(root)
    drawable = {element for element, kind in kinds.items() if element and kind in DRAWN_SIZE}
    # No diagram at all is fine: the editor lays one out when it opens a file with no shapes. A
    # partial diagram is not, because it leaves the unplaced elements off the canvas — which is
    # what `uip rules format` prevents. Without this, an element with no shape never enters
    # `boxes` below, so an edit that adds a decision and skips `format` grades as clean.
    missing = sorted(drawable - set(placed))
    if placed and missing:
        fail(f"the diagram places some elements but not {missing}; run 'uip rules format'")
    boxes = [(element, x, y, *DRAWN_SIZE[kinds[element]]) for element, (x, y) in placed.items()
             if kinds.get(element) in DRAWN_SIZE]
    for index, (first, ax, ay, aw, ah) in enumerate(boxes):
        for second, bx, by, bw, bh in boxes[index + 1:]:
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                fail(f"the shapes of {first} and {second} overlap on the canvas")


def knowledge_models(root: ET.Element) -> list[ET.Element]:
    return root.findall("dmn:businessKnowledgeModel", NS)


def check_knowledge_models(root: ET.Element) -> None:
    """Every knowledge model is callable, wired to a caller, and part of no cycle."""
    models = {m.get("id"): m for m in knowledge_models(root)}
    if not models:
        fail("the rule declares no businessKnowledgeModel")
    for model_id, model in models.items():
        name = model.get("name")
        variable = model.find("dmn:variable", NS)
        # The engine rejects a model with no variable and `validate` does not catch it, so the
        # rule would pass every offline check and fail at run time.
        if variable is None or not variable.get("name"):
            fail(f"knowledge model {name or model_id!r} declares no named <variable>; the engine rejects it")
        if variable.get("name") != name:
            fail(f"knowledge model {name!r} has a variable named {variable.get('name')!r}; they must match")
        if model.find("dmn:encapsulatedLogic", NS) is None:
            fail(f"knowledge model {name!r} has no <encapsulatedLogic>, so nothing to call")

    callers = {e.get("id"): required(e, "requiredKnowledge") for e in root
               if e.tag in (f"{{{DMN_NS}}}decision", f"{{{DMN_NS}}}businessKnowledgeModel")}
    for caller_id, needed in callers.items():
        for model_id in needed:
            if model_id not in models:
                fail(f"{caller_id} requires knowledge {model_id}, which the file does not hold")
    wired = {model_id for needed in callers.values() for model_id in needed}
    orphans = sorted(set(models) - wired)
    if orphans:
        fail(f"no decision or knowledge model calls {orphans}; a model nothing requires is dead")

    def walk(model_id: str, path: tuple[str, ...]) -> None:
        if model_id in path:
            fail(f"the knowledge models call each other in a cycle: {' -> '.join(path + (model_id,))}")
        for nxt in callers.get(model_id, []):
            walk(nxt, path + (model_id,))
    for model_id in models:
        walk(model_id, ())


def check_annotations_attached(root: ET.Element) -> None:
    """Every text annotation says something and is tied to an element that is there."""
    notes = {n.get("id"): n for n in root.findall("dmn:textAnnotation", NS)}
    if not notes:
        fail("the rule declares no textAnnotation")
    ids = {e.get("id") for e in root if e.get("id")}
    for note_id, note in notes.items():
        if not (note.findtext("dmn:text", default="", namespaces=NS) or "").strip():
            fail(f"text annotation {note_id} is empty")
    tied = set()
    for association in root.findall("dmn:association", NS):
        # tDMNElementReference: each end is a child element carrying `href`, not an attribute on
        # `<association>`. The attribute spelling parses and validates but the designer reads no
        # ends and drops the connector (PO.Frontend DrdProjection.ts), so it is not accepted here.
        ends = []
        for end in ("sourceRef", "targetRef"):
            child = association.find(f"dmn:{end}", NS)
            if child is None:
                fail(f"association {association.get('id')} has no <{end} href=\"#...\" /> child element"
                     f"; {end} is never an attribute")
            ends.append((child.get("href") or "").lstrip("#"))
        for end in ends:
            if end not in ids:
                fail(f"association {association.get('id')} points at {end}, which the file does not hold")
        tied |= {end for end in ends if end in notes}
    loose = sorted(set(notes) - tied)
    if loose:
        fail(f"text annotations {loose} are tied to nothing; add an <association>")


def check_all_named(root: ET.Element) -> None:
    for decision in decisions(root):
        check_named_rules(decision.find("dmn:decisionTable", NS))


# One case per rate row. Each `rules debug` uploads the solution, so the engine grade keeps to these.
ENGINE_CASES = [case for case in LOAN_CASES if case[0]["loanAmount"] != 99999
                and (case[0]["creditScore"], case[0]["income"]) in ((550, 90000), (580, 50000), (700, 0))]


def engine_outputs(project: Path, inputs: dict) -> dict:
    """What `uip rules debug` returns for `inputs`, by output name.

    A decision table answers with a context keyed by its output columns; a literal expression
    answers with the one value, keyed by the decision's name. Two decisions answering under one
    name are refused rather than merged: `dict.update` let whichever came last in the response
    overwrite the first, so a wrong value from the decision a case names passed whenever another
    decision happened to answer under that name. `evaluate_graph` refuses the same way offline.
    """
    completed = subprocess.run(
        ["uip", "rules", "debug", str(project), "--inputs", json.dumps(inputs), "--output", "json"],
        capture_output=True, text=True, timeout=180,
    )
    if completed.returncode != 0:
        fail(f"rules debug exited {completed.returncode} for {inputs}: {(completed.stdout or completed.stderr)[-1500:]}")
    result = (json.loads(completed.stdout).get("Data") or {}).get("result") or {}
    outputs: dict = {}
    owner: dict[str, str] = {}
    for decision in result.get("decisions") or []:
        name = decision.get("decisionName")
        value = decision.get("outputs")
        for key, item in (value if isinstance(value, dict) else {name: value}).items():
            if key in owner:
                fail(f"the engine returned an output named {key!r} for both {owner[key]!r} and {name!r}; "
                     f"a case naming it cannot say which decision it grades")
            owner[key] = name
            outputs[key] = item
    return outputs


def grade_engine() -> None:
    project = find_project(LOAN_PROJECT)
    for inputs, expected in ENGINE_CASES:
        actual = engine_outputs(project, inputs)
        for name, value in expected.items():
            if not same_value(actual.get(name), value):
                fail(f"the engine returned {name}={actual.get(name)!r} for {inputs}, expected {value!r}; it returned {actual}")
    print(f"OK: the engine returns the expected risk band and interest rate for all {len(ENGINE_CASES)} cases")


def grade_chain() -> None:
    project = find_project(LOAN_PROJECT)
    dmn_file, root = load_graph(project)
    check_chain(root, "interestRate", "riskBand")
    check_graph_cases(root, LOAN_CASES)
    check_whole_file_contract(project, dmn_file, LOAN_INPUTS, LOAN_OUTPUTS)
    check_no_overlap(root)
    print(f"OK: two chained decisions, the contract is current, no cards overlap, and all {len(LOAN_CASES)} cases match")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    name = sys.argv[2] if len(sys.argv) > 2 else LOAN_PROJECT
    if mode == "chain":
        grade_chain()
    elif mode == "engine":
        grade_engine()
    elif mode == "names":
        check_all_named(load_graph(find_project(name))[1])
        print("OK: every rule of every decision carries an annotation")
    else:
        fail("mode: chain | engine | names [project]")
