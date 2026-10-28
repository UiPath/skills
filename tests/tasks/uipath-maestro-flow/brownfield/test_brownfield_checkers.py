"""The brownfield graders pass the right edits and fail the round-trip losses they exist for."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture" / "BillingDisputeResolution" / "BillingDisputeResolution"
FLOW = f"{FIXTURE.name}.flow"
ANALYST = "07b8b6ea-ce49-4d28-9370-7b8bee866def"
WRITER = "e6360c37-75b3-4315-b63e-afe9815dd65c"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preserved = _load("check_brownfield_preserved", HERE.parent / "_shared" / "check_brownfield_preserved.py")
edit = _load("check_brownfield_edit", HERE / "check_brownfield_edit.py")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    target = tmp_path / FIXTURE.name
    shutil.copytree(FIXTURE, target)
    return target


def mutate(project: Path, change) -> None:
    path = project / FLOW
    flow = json.loads(path.read_text())
    change(flow)
    path.write_text(json.dumps(flow, indent=2))


def node(flow: dict, node_id: str) -> dict:
    return next(n for n in flow["nodes"] if n["id"] == node_id)


def graph(project: Path, *extra: str) -> int:
    return preserved.main(["--original", str(FIXTURE), "--project", str(project), *extra])


def layout(project: Path) -> int:
    return preserved.main(["--aspect", "layout", "--original", str(FIXTURE), "--project", str(project)])


def merged(project: Path) -> int:
    return preserved.main(["--aspect", "merged", "--original", str(FIXTURE), "--project", str(project)])


def intent(project: Path, which: str) -> int:
    return edit.main([which, "--original", str(FIXTURE), "--project", str(project)])


def insert_cap(flow: dict) -> None:
    cap = copy.deepcopy(node(flow, "logCreditAmount"))
    cap["id"] = "capCreditAmount"
    cap["inputs"]["script"] = "return { creditAmount: Math.min($vars.disputeAnalyst.output.creditAmount, 500) };"
    flow["nodes"].append(cap)
    flow["edges"] = [
        e for e in flow["edges"]
        if not (e["sourceNodeId"] == "logCreditAmount" and e["targetNodeId"] == "financialPosting")
    ]
    flow["edges"] += [
        {"id": "a", "sourceNodeId": "logCreditAmount", "sourcePort": "success", "targetNodeId": "capCreditAmount", "targetPort": "input"},
        {"id": "b", "sourceNodeId": "capCreditAmount", "sourcePort": "success", "targetNodeId": "financialPosting", "targetPort": "input"},
    ]
    flow["layout"]["nodes"]["capCreditAmount"] = {"position": {"x": 1632, "y": 96}, "size": {"width": 96, "height": 96}}


CAP_EDGE = "logCreditAmount:success>financialPosting:input"


def test_unedited_fixture_is_preserved(project: Path) -> None:
    assert graph(project) == 0
    assert layout(project) == 0
    assert merged(project) == 1
    for which in ("credit-cap", "switch-route", "writer-prompt"):
        assert intent(project, which) == 1


def test_credit_cap_edit_passes_only_with_its_allowance(project: Path) -> None:
    mutate(project, insert_cap)
    assert intent(project, "credit-cap") == 0
    assert graph(project, "--removed-edge", CAP_EDGE) == 0
    assert graph(project) == 1
    assert layout(project) == 0


@pytest.mark.parametrize(
    "script",
    [
        pytest.param("return { creditAmount: Math.max($vars.disputeAnalyst.output.creditAmount, 500) };", id="max-not-min"),
        pytest.param("return { creditAmount: 500 };", id="constant"),
        pytest.param("return { creditAmount: Math.min($vars.disputeAnalyst.output.creditAmount, 5000) };", id="wrong-cap"),
        pytest.param("return Math.min($vars.disputeAnalyst.output.creditAmount, 500);", id="bare-number"),
    ],
)
def test_credit_cap_rejects_a_script_that_does_not_cap(project: Path, script: str) -> None:
    def wrong(flow: dict) -> None:
        insert_cap(flow)
        node(flow, "capCreditAmount")["inputs"]["script"] = script

    mutate(project, wrong)
    assert intent(project, "credit-cap") == 1


def test_credit_cap_accepts_the_logged_amount(project: Path) -> None:
    def from_log(flow: dict) -> None:
        insert_cap(flow)
        node(flow, "capCreditAmount")["inputs"]["script"] = (
            "const amount = $vars.logCreditAmount.output.creditAmount;\nreturn { creditAmount: amount > 500 ? 500 : amount };"
        )

    mutate(project, from_log)
    assert intent(project, "credit-cap") == 0


def add_route(flow: dict, expression: str = "$vars.disputeAnalyst.output.recommendedAction === 'request_more_info'") -> dict:
    node(flow, "routeByAction")["inputs"]["cases"].append({"id": "info", "label": "request_more_info", "expression": expression})
    end = copy.deepcopy(node(flow, "returnRejection"))
    end["id"] = "returnInfoRequest"
    end["outputs"]["resolutionEmailBody"] = {"source": "=js:'More information was requested.'"}
    flow["nodes"].append(end)
    flow["edges"].append(
        {"id": "c", "sourceNodeId": "routeByAction", "sourcePort": "case-info", "targetNodeId": "returnInfoRequest", "targetPort": "input"}
    )
    flow["layout"]["nodes"]["returnInfoRequest"] = {"position": {"x": 1536, "y": 320}, "size": {"width": 96, "height": 96}}
    return end


def test_switch_route_edit(project: Path) -> None:
    mutate(project, add_route)
    assert intent(project, "switch-route") == 0
    assert graph(project, "--changed-node", "routeByAction") == 0
    assert layout(project) == 0


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda f: add_route(f, "$vars.disputeAnalyst.output.recommendedAction !== 'request_more_info'"), id="negated-condition"),
        pytest.param(lambda f: add_route(f, "$vars.disputeAnalyst.output.recommendedAction.includes('re')"), id="matches-other-actions"),
        pytest.param(lambda f: add_route(f)["outputs"].update(creditAmount={"source": "=js:0"}), id="pass-through-output-differs"),
        pytest.param(lambda f: add_route(f)["outputs"].update(resolutionEmailBody={"source": "=js:$vars.resolutionWriter.output.body"}), id="body-reads-writer"),
    ],
)
def test_switch_route_rejects_wrong_routes(project: Path, change) -> None:
    mutate(project, change)
    assert intent(project, "switch-route") == 1


def envelope(output: dict) -> None:
    source = output["source"]
    if source.startswith("=js:"):
        output["source"] = {"type": "jsExpression", "expression": source[4:], "fieldType": "string"}
    else:
        output["source"] = {"type": "literal", "expression": source, "fieldType": "string"}


def compiled_route(flow: dict, body: str = "=js:'More information was requested.'") -> None:
    end = add_route(flow)
    end["outputs"]["resolutionEmailBody"]["source"] = body
    for output in end["outputs"].values():
        envelope(output)


@pytest.mark.parametrize("body", ["=js:'More information was requested.'", "More information was requested."], ids=["js", "literal"])
def test_switch_route_accepts_compiled_envelopes(project: Path, body: str) -> None:
    mutate(project, lambda f: compiled_route(f, body))
    assert intent(project, "switch-route") == 0


@pytest.mark.parametrize(
    "source",
    [
        pytest.param({"type": "jsExpression", "expression": "'invalid'", "fieldType": "string"}, id="differing-expression"),
        pytest.param({"type": "literal", "expression": "=js:$vars.disputeAnalyst.output.determination", "fieldType": "string"}, id="literal-js-text"),
    ],
)
def test_switch_route_rejects_a_differing_envelope(project: Path, source: dict) -> None:
    def differ(flow: dict) -> None:
        compiled_route(flow)
        node(flow, "returnInfoRequest")["outputs"]["determination"]["source"] = source

    mutate(project, differ)
    assert intent(project, "switch-route") == 1


def test_switch_route_rejects_a_renamed_original_case(project: Path) -> None:
    def rename(flow: dict) -> None:
        cases = node(flow, "routeByAction")["inputs"]["cases"]
        cases[0]["id"] = "case_1"
        cases.append({"id": "info", "expression": "x === 'request_more_info'"})

    mutate(project, rename)
    assert intent(project, "switch-route") == 1


def requote_cases(flow: dict) -> None:
    for case in node(flow, "routeByAction")["inputs"]["cases"]:
        case["expression"] = case["expression"].replace("'", '"')


def test_switch_route_accepts_requoted_original_cases(project: Path) -> None:
    mutate(project, lambda f: (add_route(f), requote_cases(f)))
    assert intent(project, "switch-route") == 0


def test_switch_route_rejects_a_renamed_switch(project: Path) -> None:
    mutate(project, lambda f: (add_route(f), node(f, "routeByAction")["display"].update(label="routeByAction")))
    assert intent(project, "switch-route") == 1


def renumber_edges(flow: dict) -> None:
    for i, edge in enumerate(flow["edges"]):
        edge["id"] = f"edge_{i}"


@pytest.mark.parametrize("edit", [insert_cap, add_route], ids=["credit-cap", "switch-route"])
def test_hand_edit_fails_the_merge_check(project: Path, edit) -> None:
    mutate(project, edit)
    assert merged(project) == 1


@pytest.mark.parametrize("edit", [insert_cap, add_route], ids=["credit-cap", "switch-route"])
def test_merged_edit_passes_the_merge_check(project: Path, edit) -> None:
    mutate(project, lambda f: (edit(f), renumber_edges(f)))
    assert merged(project) == 0


NEW_LINE = "- Say the credit appears on the next statement within 5 business days."


def edit_writer(project: Path, change) -> None:
    path = project / WRITER / "agent.json"
    agent = json.loads(path.read_text())
    change(agent, next(m for m in agent["messages"] if m["role"] == "system"))
    path.write_text(json.dumps(agent))


def add_line(_agent: dict, system: dict) -> None:
    system["content"] = system["content"].replace("\n\nYou have no tools.", f"\n{NEW_LINE}\n\nYou have no tools.")
    system["contentTokens"][0]["rawString"] = system["content"]


def test_writer_prompt_edit(project: Path) -> None:
    edit_writer(project, add_line)
    assert intent(project, "writer-prompt") == 0
    assert graph(project, "--changed-agent", WRITER) == 0
    assert graph(project) == 1
    assert layout(project) == 0


def _content_only(_agent: dict, system: dict) -> None:
    system["content"] = system["content"].replace("\n\nYou have no tools.", f"\n{NEW_LINE}\n\nYou have no tools.")


def _drop_bullet(agent: dict, system: dict) -> None:
    add_line(agent, system)
    system["content"] = system["content"].replace('- Sign off as "Billing Operations Team".\n', "")
    system["contentTokens"][0]["rawString"] = system["content"]


def _schema_changed(agent: dict, system: dict) -> None:
    add_line(agent, system)
    agent["outputSchema"] = {}


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(_content_only, id="content-tokens-stale"),
        pytest.param(_drop_bullet, id="existing-line-dropped"),
        pytest.param(_schema_changed, id="output-schema-changed"),
    ],
)
def test_writer_prompt_rejects_collateral_changes(project: Path, change) -> None:
    edit_writer(project, change)
    assert intent(project, "writer-prompt") == 1


def test_writer_task_keeps_the_flow_node(project: Path) -> None:
    edit_writer(project, add_line)
    mutate(project, lambda f: node(f, "resolutionWriter")["inputs"]["agentInputVariables"].pop())
    assert graph(project, "--changed-agent", WRITER) == 1


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda f: node(f, "sopIndex").update(type="uipath.agent.resource.context.index.x."), id="context-index-id-lost"),
        pytest.param(lambda f: f["bindings"].append({**f["bindings"][0], "id": "dup"}), id="binding-duplicated"),
        pytest.param(lambda f: f["edges"].pop(next(i for i, e in enumerate(f["edges"]) if e["sourcePort"] == "default")), id="edge-dropped"),
        pytest.param(lambda f: f["variables"]["globals"].pop(), id="flow-output-dropped"),
        pytest.param(lambda f: f["definitions"].pop(), id="definition-dropped"),
        pytest.param(lambda f: f["definitions"][-1].update(description="rewritten"), id="definition-body-changed"),
        pytest.param(lambda f: node(f, "approvalDecision")["inputs"].update(expression="true"), id="untouched-node-rewritten"),
    ],
)
def test_round_trip_losses_fail_the_graph_check(project: Path, change) -> None:
    mutate(project, change)
    assert graph(project) == 1


def test_analyst_sidecar_change_fails(project: Path) -> None:
    resource = next((project / ANALYST / "resources").glob("*/resource.json"))
    data = json.loads(resource.read_text())
    data["indexName"] = ""
    resource.write_text(json.dumps(data))
    assert graph(project) == 1


def test_relayout_fails_the_layout_check(project: Path) -> None:
    mutate(project, lambda f: f["layout"]["nodes"]["financialPosting"]["position"].update(x=1920))
    assert graph(project) == 0
    assert layout(project) == 1


def test_new_node_on_top_of_another_fails_the_layout_check(project: Path) -> None:
    def stacked(flow: dict) -> None:
        insert_cap(flow)
        flow["layout"]["nodes"]["capCreditAmount"]["position"] = {"x": 1728, "y": -40}

    mutate(project, stacked)
    assert layout(project) == 1


DOWNSTREAM_OF_CAP = ("financialPosting", "resolutionWriter", "returnResolution")


def shift(flow: dict, node_ids, dx: int = 0, dy: int = 0) -> None:
    for node_id in node_ids:
        position = flow["layout"]["nodes"][node_id]["position"]
        position.update(x=position["x"] + dx, y=position["y"] + dy)


def make_room(flow: dict) -> None:
    insert_cap(flow)
    flow["layout"]["nodes"]["capCreditAmount"]["position"] = {"x": 1728, "y": -32}
    shift(flow, DOWNSTREAM_OF_CAP, dx=192)


def test_merge_making_room_passes_the_layout_check(project: Path) -> None:
    mutate(project, make_room)
    assert layout(project) == 0


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda f: shift(f, ["logCreditAmount"], dx=192), id="upstream-moved"),
        pytest.param(lambda f: shift(f, ["returnRejection"], dx=192), id="unrelated-moved"),
        pytest.param(lambda f: shift(f, ["returnResolution"], dx=-400), id="moved-left"),
        pytest.param(lambda f: shift(f, ["returnResolution"], dy=-200), id="moved-up"),
        pytest.param(lambda f: shift(f, ["financialPosting"], dx=96), id="gap-closed"),
        pytest.param(lambda f: shift(f, ["returnResolution"], dx=-150), id="lands-on-another"),
        pytest.param(lambda f: f["layout"]["nodes"]["financialPosting"].update(collapsed=True), id="entry-rewritten"),
    ],
)
def test_layout_check_rejects_moves_merge_does_not_make(project: Path, change) -> None:
    def moved(flow: dict) -> None:
        make_room(flow)
        change(flow)

    mutate(project, moved)
    assert layout(project) == 1


def container_flow(children: dict[str, dict], loop_size: dict, after_x: int = 800) -> dict:
    layout_nodes = {
        "start": {"position": {"x": 0, "y": 0}, "size": {"width": 96, "height": 96}},
        "loop": {"position": {"x": 192, "y": -112}, "size": loop_size},
        "after": {"position": {"x": after_x, "y": 0}, "size": {"width": 96, "height": 96}},
        "below": {"position": {"x": 256, "y": 300}, "size": {"width": 96, "height": 96}},
    }
    nodes = [{"id": i} for i in layout_nodes] + [{"id": i, "parentId": "loop"} for i in children]
    chain = ["loop", *children]
    edges = [{"sourceNodeId": "start", "targetNodeId": "loop"}, {"sourceNodeId": "loop", "targetNodeId": "after"}]
    edges += [{"sourceNodeId": a, "targetNodeId": b} for a, b in zip(chain, chain[1:])]
    return {"nodes": nodes, "edges": edges, "layout": {"nodes": {**layout_nodes, **children}}}


def at(x: int, y: int = 112) -> dict:
    return {"position": {"x": x, "y": y}, "size": {"width": 96, "height": 96}}


ORIGINAL_BODY = {"classify": at(144), "record": at(336)}
GROWN_BODY = {"classify": at(144), "dedupe": at(336), "record": at(528)}


def layout_of(tmp_path: Path, original: dict, final: dict, *extra: str) -> int:
    for name, flow in (("Original", original), ("Final", final)):
        (tmp_path / name).mkdir()
        (tmp_path / name / f"{name}.flow").write_text(json.dumps(flow))
    return preserved.main(["--aspect", "layout", "--original", str(tmp_path / "Original"), "--project", str(tmp_path / "Final"), *extra])


def test_container_growing_for_an_added_child_passes(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow(GROWN_BODY, {"width": 768, "height": 320}, after_x=1008)
    final["layout"]["nodes"]["below"]["position"]["y"] = 300
    assert layout_of(tmp_path, original, final) == 0


def test_sibling_under_a_grown_container_may_move_down(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow({**GROWN_BODY, "dedupe": at(336, 304)}, {"width": 560, "height": 496})
    final["layout"]["nodes"]["below"]["position"]["y"] = 476
    assert layout_of(tmp_path, original, final) == 0


def test_container_resizing_without_a_changed_child_fails(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow(ORIGINAL_BODY, {"width": 768, "height": 320})
    assert layout_of(tmp_path, original, final) == 1


def test_container_shrinking_fails(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow({**ORIGINAL_BODY, "dedupe": at(144, 224)}, {"width": 480, "height": 320})
    assert layout_of(tmp_path, original, final) == 1


def test_grown_container_downstream_of_an_added_node_may_move(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow(GROWN_BODY, {"width": 768, "height": 320}, after_x=1200)
    final["nodes"].append({"id": "enrich"})
    final["edges"] = [e for e in final["edges"] if e["sourceNodeId"] != "start"]
    final["edges"] += [{"sourceNodeId": "start", "targetNodeId": "enrich"}, {"sourceNodeId": "enrich", "targetNodeId": "loop"}]
    final["layout"]["nodes"]["enrich"] = at(192, 0)
    final["layout"]["nodes"]["loop"]["position"]["x"] = 384
    assert layout_of(tmp_path, original, final) == 0


def test_added_child_outside_its_container_fails(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    final = container_flow({**ORIGINAL_BODY, "dedupe": at(528)}, {"width": 560, "height": 320})
    assert layout_of(tmp_path, original, final) == 1


def test_added_node_left_of_its_successor_fails(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 768, "height": 320})
    final = container_flow({"classify": at(144), "dedupe": at(528), "record": at(336)}, {"width": 768, "height": 320})
    assert layout_of(tmp_path, original, final) == 1


def test_moved_node_landing_on_another_fails(tmp_path: Path) -> None:
    original = container_flow({**ORIGINAL_BODY, "aside": at(528, 224)}, {"width": 768, "height": 320})
    final = container_flow({**GROWN_BODY, "record": at(528, 200), "aside": at(528, 224)}, {"width": 768, "height": 320})
    for flow in (original, final):
        flow["edges"] = [e for e in flow["edges"] if "aside" not in (e["sourceNodeId"], e["targetNodeId"])]
    assert layout_of(tmp_path, original, final) == 1


def retry_flow(fetch_x: int = 192, done_x: int = 384, retry: bool = False) -> dict:
    layout_nodes = {"start": at(0, 0), "fetch": at(fetch_x, 0), "done": at(done_x, 0)}
    edges = [{"sourceNodeId": "start", "targetNodeId": "fetch"}]
    if retry:
        layout_nodes["retry"] = at(384, 0)
        edges += [
            {"sourceNodeId": "fetch", "targetNodeId": "retry"},
            {"sourceNodeId": "retry", "targetNodeId": "fetch"},
            {"sourceNodeId": "retry", "targetNodeId": "done"},
        ]
    else:
        edges.append({"sourceNodeId": "fetch", "targetNodeId": "done"})
    return {"nodes": [{"id": i} for i in layout_nodes], "edges": edges, "layout": {"nodes": layout_nodes}}


def test_added_retry_edge_back_to_an_earlier_node_passes(tmp_path: Path) -> None:
    assert layout_of(tmp_path, retry_flow(), retry_flow(done_x=576, retry=True)) == 0


def test_retry_edge_does_not_let_its_target_move(tmp_path: Path) -> None:
    assert layout_of(tmp_path, retry_flow(), retry_flow(fetch_x=240, done_x=576, retry=True)) == 1


def test_malformed_edge_fails_instead_of_crashing(tmp_path: Path) -> None:
    final = retry_flow()
    final["edges"].append({"id": "broken", "sourceNodeId": "fetch"})
    assert layout_of(tmp_path, retry_flow(), final) == 1


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda f: f["layout"]["nodes"]["returnResolution"]["position"].update(x=5000), id="shift-beyond-room"),
        pytest.param(lambda f: shift(f, ["resolutionWriter", "returnResolution"], dy=3000), id="drop-with-no-growth"),
        pytest.param(lambda f: f["layout"]["nodes"]["capCreditAmount"].update(position={"x": -500, "y": 600}), id="added-left-of-predecessor"),
    ],
)
def test_layout_check_caps_room_to_what_merge_needs(project: Path, change) -> None:
    def moved(flow: dict) -> None:
        make_room(flow)
        change(flow)

    mutate(project, moved)
    assert layout(project) == 1


def test_invented_edge_gives_no_room(project: Path) -> None:
    def invented(flow: dict) -> None:
        make_room(flow)
        flow["edges"].append({"id": "x", "sourceNodeId": "capCreditAmount", "sourcePort": "success", "targetNodeId": "returnManagerRejection", "targetPort": "input"})
        shift(flow, ["returnManagerRejection"], dx=192)

    mutate(project, invented)
    assert layout(project) == 1


def row_flow(positions: dict[str, tuple[int, int]], edges: list[tuple[str, str]], sticky: tuple[str, ...] = ()) -> dict:
    nodes = [{"id": i, **({"type": "stickyNote"} if i in sticky else {})} for i in positions]
    layout_nodes = {i: at(x, y) for i, (x, y) in positions.items()}
    return {"nodes": nodes, "edges": [{"sourceNodeId": u, "targetNodeId": v} for u, v in edges], "layout": {"nodes": layout_nodes}}


def test_insert_on_an_existing_retry_edge_makes_room_past_it(tmp_path: Path) -> None:
    cycle = [("a", "b"), ("b", "c"), ("c", "d")]
    original = row_flow({"a": (0, 0), "b": (192, 0), "c": (384, 0), "d": (576, 0)}, [*cycle, ("c", "a")])
    final = row_flow({"a": (0, 0), "b": (192, 0), "c": (384, 0), "n": (576, 0), "d": (768, 0)}, [*cycle, ("c", "n"), ("n", "a")])
    assert layout_of(tmp_path, original, final) == 0


def test_sticky_notes_are_left_out_of_order_and_overlap(project: Path) -> None:
    sticky = {"id": "note", "type": "stickyNote"}

    def with_note(flow: dict) -> None:
        flow["nodes"].append(dict(sticky))
        flow["layout"]["nodes"]["note"] = {"position": {"x": 1740, "y": -20}, "size": {"width": 96, "height": 96}}

    mutate(project, lambda f: (with_note(f), make_room(f)))
    original = project.parent / "original" / FIXTURE.name
    shutil.copytree(FIXTURE, original)
    mutate(original, with_note)
    assert preserved.main(["--aspect", "layout", "--original", str(original), "--project", str(project)]) == 0


def test_sibling_within_merge_padding_of_a_grown_container_may_move(tmp_path: Path) -> None:
    original = container_flow(ORIGINAL_BODY, {"width": 560, "height": 320})
    original["layout"]["nodes"]["below"]["position"]["y"] = 400
    final = container_flow({**GROWN_BODY, "dedupe": at(336, 304)}, {"width": 560, "height": 496})
    final["layout"]["nodes"]["below"]["position"]["y"] = 576
    assert layout_of(tmp_path, original, final) == 0


def test_two_inserted_steps_make_room_for_both(tmp_path: Path) -> None:
    original = row_flow({"a": (0, 0), "b": (192, 0)}, [("a", "b")])
    final = row_flow({"a": (0, 0), "n1": (192, 0), "n2": (384, 0), "b": (576, 0)}, [("a", "n1"), ("n1", "n2"), ("n2", "b")])
    assert layout_of(tmp_path, original, final) == 0


FORK = {"a": (0, 0), "b": (192, 0), "d": (384, 0), "c": (192, 160), "e": (192, 400), "f": (420, 110)}
FORK_EDGES = [("a", "b"), ("b", "d"), ("a", "c")]


def fork_insert(**moves: tuple[int, int]) -> dict:
    positions = {**FORK, "n": (192, 0), "b": (384, 0), "d": (576, 0), "c": (384, 160), "f": (612, 110), **moves}
    return row_flow(positions, [("a", "b"), ("b", "d"), ("a", "n"), ("n", "c")])


def test_fork_insert_pushes_the_node_it_lands_on_and_its_downstream(tmp_path: Path) -> None:
    assert layout_of(tmp_path, row_flow(FORK, FORK_EDGES), fork_insert()) == 0


@pytest.mark.parametrize(
    "moves",
    [
        pytest.param({"e": (384, 400)}, id="node-nothing-landed-on"),
        pytest.param({"a": (48, 0)}, id="node-left-of-the-insertion"),
    ],
)
def test_fork_insert_moves_nothing_it_did_not_push(tmp_path: Path, moves) -> None:
    assert layout_of(tmp_path, row_flow(FORK, FORK_EDGES), fork_insert(**moves)) == 1


def test_replacing_a_removable_node_makes_room_past_it(tmp_path: Path) -> None:
    original = row_flow({"a": (0, 0), "h": (192, 0), "b": (520, 0)}, [("a", "h"), ("h", "b")])
    final = row_flow({"a": (0, 0), "n": (192, 0), "m": (384, 0), "b": (576, 0)}, [("a", "n"), ("n", "m"), ("m", "b")])
    assert layout_of(tmp_path, original, final, "--removable-node", "h") == 0


@pytest.mark.parametrize(
    "z, expected",
    [pytest.param((952, 200), 0, id="pushed"), pytest.param((1060, 330), 1, id="unplaced-node-pushes-nothing")],
)
def test_growth_pushes_an_author_node_and_what_it_lands_on(tmp_path: Path, z: tuple[int, int], expected: int) -> None:
    original = row_flow({"start": (0, 0), "after": (800, 0), "w": (1000, 220)}, [("start", "loop"), ("loop", "after")])
    original["nodes"] += [{"id": "loop"}, {"id": "classify", "parentId": "loop"}, {"id": "record", "parentId": "loop"}]
    original["layout"]["nodes"].update(loop={"position": {"x": 192, "y": -112}, "size": {"width": 560, "height": 320}}, classify=at(144), record=at(336))
    original["edges"] += [{"sourceNodeId": "loop", "targetNodeId": "classify"}, {"sourceNodeId": "classify", "targetNodeId": "record"}]
    final = copy.deepcopy(original)
    final["nodes"] += [{"id": "z"}, {"id": "dedupe", "parentId": "loop"}]
    final["edges"] = [e for e in final["edges"] if e["sourceNodeId"] != "classify"]
    final["edges"] += [{"sourceNodeId": "classify", "targetNodeId": "dedupe"}, {"sourceNodeId": "dedupe", "targetNodeId": "record"}]
    final["layout"]["nodes"].update(
        loop={"position": {"x": 192, "y": -112}, "size": {"width": 752, "height": 320}},
        record=at(528), dedupe=at(336), after=at(992, 0), w=at(1192, 220), z=at(*z),
    )
    assert layout_of(tmp_path, original, final) == expected
