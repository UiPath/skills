"""Synthetic trace controls; no UiPath runtime, source pack or model required."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[4] / "skills/uipath-genome/scripts/check-migration-trace.py"
SPEC = importlib.util.spec_from_file_location("migration_trace", SCRIPT)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def xml(path, tag, **attrs):
    return {"kind": "xml", "path": path, "tag": tag, "attributes": attrs}


@pytest.fixture
def packet(tmp_path):
    source, target, working = (tmp_path / name for name in ("source", "solution", "migration/trace"))
    source.mkdir()
    (target / "Worker").mkdir(parents=True)
    working.mkdir(parents=True)
    # A stage ID reused across containers is legal; bodies and scope differ.
    (source / "release.xml").write_bytes(b'<release><object id="A"><stage id="same">read</stage></object><object id="B"><stage id="same">write</stage></object></release>')
    (target / "Worker/Main.xaml").write_bytes(b'<Sequence><Probe id="probe"/><If id="decision"/><Assign id="size">FileInfo.Length</Assign></Sequence>')
    (target / "Worker/project.json").write_bytes(b'{"name":"Worker"}')
    inventory = {"version": 1, "framework": "synthetic", "scope": "both objects",
                 "artifacts": [{"path": "release.xml", "sha256": sha((source / "release.xml").read_bytes())}],
                 "items": [{"id": name, "identity": [container, "main", "same"], "artifact": "release.xml",
                            "kind": "behavior", "locator": xml([index, 0], "stage", id="same")}
                           for index, (name, container) in enumerate((("s1", "A"), ("s2", "B")))]}
    records = [{"sources": [name], "targets": [{"artifact": "Worker/Main.xaml", "role": role, "locator": locator}],
                "status": "mapped", "relation": "direct", "reason": "Claimed implementation location."}
               for name, role, locator in (("s1", "decision", xml([1], "If", id="decision")),
                                           ("s2", "value-read", xml([2], "Assign", id="size")))]
    trace = {"version": 1, "sourceInventorySha256": "", "targetArtifacts": [], "fragments": ["parts/one.json"]}
    return {"source": source, "target": target, "working": working,
            "inventory": inventory, "trace": trace, "records": records}


def run(packet, capsys, projects=("Worker",), refresh=True, solution_files=()):
    p = packet
    inventory_path = p["working"] / "source-inventory.json"
    trace_path = p["working"] / "trace.json"
    write_json(inventory_path, p["inventory"])
    if refresh:
        p["trace"]["sourceInventorySha256"] = sha(inventory_path.read_bytes())
        p["trace"]["targetArtifacts"] = [{"path": f.relative_to(p["target"]).as_posix(), "sha256": sha(f.read_bytes())}
                                           for f in sorted((p["target"] / "Worker").iterdir()) if f.is_file()]
    write_json(trace_path, p["trace"])
    write_json(p["working"] / "parts/one.json", {"version": 1, "records": p["records"]})
    argv = ["--inventory", str(inventory_path), "--trace", str(trace_path), "--source-root", str(p["source"]),
            "--target-root", str(p["target"]), "--output", "json"]
    for project in projects:
        argv.extend(["--project", project])
    for path in solution_files:
        argv.extend(["--solution-file", path])
    rc = CHECK.main(argv)
    return rc, json.loads(capsys.readouterr().out)


def test_current_links_and_scoped_duplicate_native_ids_pass(packet, capsys):
    rc, result = run(packet, capsys)
    assert rc == 0 and result["counts"]["mapped"] == 2
    assert result["sourceInventoryCompleteness"] == "not-established-by-this-check"
    assert result["behavioralCorrectness"] == "not-assessed"


def test_solution_manifest_and_multiple_projects_are_part_of_snapshot(packet, capsys):
    second = packet["target"] / "Library"
    second.mkdir()
    (second / "project.json").write_text('{}')
    (packet["target"] / "Automation.uipx").write_text('{}')
    assert run(packet, capsys)[0] == 0
    packet["trace"]["targetArtifacts"].extend([
        {"path": "Library/project.json", "sha256": sha(b'{}')},
        {"path": "Automation.uipx", "sha256": sha(b'{}')},
    ])
    rc, result = run(packet, capsys, projects=("Worker", "Library"), refresh=False,
                     solution_files=("Automation.uipx",))
    assert rc == 0 and result["targetProjectCount"] == 2
    (packet["target"] / "Automation.uipx").write_text('{"changed":true}')
    assert run(packet, capsys, projects=("Worker", "Library"), refresh=False,
               solution_files=("Automation.uipx",))[0] == 1


def test_overlapping_even_empty_project_scopes_fail(packet, capsys):
    (packet["target"] / "Worker/Empty").mkdir()
    assert run(packet, capsys, projects=("Worker", "Worker/Empty"))[0] == 1


@pytest.mark.parametrize("relation", ["split", "merge", "group", "rewrite", "moved"])
def test_grouped_links_do_not_require_one_to_one(packet, capsys, relation):
    first, second = packet["records"]
    first["sources"] += second["sources"]
    first["targets"] += second["targets"]
    first["relation"] = relation
    packet["records"] = [first]
    assert run(packet, capsys)[0] == 0


def test_shared_helper_needs_call_site_callee_and_bindings(packet, capsys):
    row = packet["records"][0]
    row["relation"] = "shared"
    assert run(packet, capsys)[0] == 1
    row["targets"][0]["role"] = "call-site"
    row["targets"].append(copy.deepcopy(packet["records"][1]["targets"][0]))
    row["targets"][1]["role"] = "implementation"
    assert run(packet, capsys)[0] == 1
    row["bindings"] = [{"source": "source argument", "target": "helper input", "direction": "in"}]
    assert run(packet, capsys)[0] == 0


@pytest.mark.parametrize("status", ["omitted", "excluded", "unresolved"])
def test_gaps_are_counted_not_credited(packet, capsys, status):
    packet["records"][0].update(status=status, targets=[])
    rc, result = run(packet, capsys)
    assert rc == (1 if status == "unresolved" else 0)
    assert result["counts"][status] == 1 and result["counts"]["mapped"] == 1
    assert result["integrityValid"] is True


def test_changed_requires_decision_not_just_a_target(packet, capsys):
    packet["records"][0]["status"] = "changed"
    assert run(packet, capsys)[0] == 1
    packet["records"][0]["decision"] = "User ruling 3"
    assert run(packet, capsys)[0] == 0


def test_added_and_structural_do_not_hide_behavior(packet, capsys):
    added = copy.deepcopy(packet["records"][0])
    added.update(sources=[], status="added")
    packet["records"].append(added)
    assert run(packet, capsys)[0] == 0
    packet["records"][0].update(status="structural", targets=[])
    assert run(packet, capsys)[0] == 1
    packet["inventory"]["items"][0]["kind"] = "structure"
    assert run(packet, capsys)[0] == 0


@pytest.mark.parametrize("change", ["missing-record", "duplicate-record", "unknown-source", "duplicate-identity", "duplicate-location", "empty-inventory"])
def test_inventory_accounting_errors_fail(packet, capsys, change):
    if change == "missing-record":
        packet["records"].pop()
    elif change == "duplicate-record":
        packet["records"].append(copy.deepcopy(packet["records"][0]))
    elif change == "unknown-source":
        packet["records"][0]["sources"] = ["unlisted"]
    elif change == "duplicate-identity":
        packet["inventory"]["items"][1]["identity"] = packet["inventory"]["items"][0]["identity"]
    elif change == "duplicate-location":
        packet["inventory"]["items"][1]["locator"] = packet["inventory"]["items"][0]["locator"]
    else:
        packet["inventory"]["items"] = []
    assert run(packet, capsys)[0] == 1


def test_different_identity_guards_do_not_make_one_position_two_items(packet, capsys):
    packet["inventory"]["items"][1]["locator"] = xml([0, 0], "stage")
    assert run(packet, capsys)[0] == 1


@pytest.mark.parametrize("side", ["source", "target", "inventory"])
def test_stale_hashes_fail(packet, capsys, side):
    assert run(packet, capsys)[0] == 0
    if side == "source":
        with (packet["source"] / "release.xml").open("ab") as handle:
            handle.write(b" ")
    elif side == "target":
        with (packet["target"] / "Worker/Main.xaml").open("ab") as handle:
            handle.write(b" ")
    else:
        packet["inventory"]["scope"] = "changed selection"
    assert run(packet, capsys, refresh=False)[0] == 1


@pytest.mark.parametrize("side", ["source", "target"])
def test_unlisted_added_files_fail(packet, capsys, side):
    assert run(packet, capsys)[0] == 0
    root = packet[side] if side == "source" else packet[side] / "Worker"
    (root / "forgotten.json").write_text("{}")
    assert run(packet, capsys, refresh=False)[0] == 1


def test_deleted_unreferenced_manifest_invalidates_trace(packet, capsys):
    assert run(packet, capsys)[0] == 0
    (packet["target"] / "Worker/project.json").unlink()
    assert run(packet, capsys, refresh=False)[0] == 1


@pytest.mark.parametrize("change", ["wrong-index", "negative-index", "boolean-index", "wrong-tag", "wrong-native-id"])
def test_final_xml_location_and_identity_guards(packet, capsys, change):
    loc = packet["records"][0]["targets"][0]["locator"]
    if change == "wrong-index":
        loc["path"] = [0]  # Probe is not the claimed If.
    elif change == "negative-index":
        loc["path"] = [-1]
    elif change == "boolean-index":
        loc["path"] = [True]
    elif change == "wrong-tag":
        loc["tag"] = "Assign"
    else:
        loc["attributes"]["id"] = "other"
    assert run(packet, capsys)[0] == 1


def test_raw_json_pointer_and_code_span(packet, capsys):
    code = b"int n = 1;\nreturn n;\n"
    (packet["target"] / "Worker/Main.cs").write_bytes(code)
    packet["records"][0]["targets"] = [{"artifact": "Worker/project.json", "role": "configuration",
                                        "locator": {"kind": "json", "pointer": "/name"}}]
    packet["records"][1]["targets"] = [{"artifact": "Worker/Main.cs", "role": "return",
                                        "locator": {"kind": "text", "start": 11, "end": 20,
                                                    "sha256": sha(code[11:20]), "symbol": "Worker.Run()"}}]
    assert run(packet, capsys)[0] == 0
    packet["records"][1]["targets"][0]["locator"]["end"] = 19
    assert run(packet, capsys)[0] == 1
    packet["records"][1]["targets"][0]["locator"]["end"] = 20
    packet["records"][0]["targets"][0]["locator"]["pointer"] = "/absent"
    assert run(packet, capsys)[0] == 1


@pytest.mark.parametrize("pointer, valid", [("/a~1b/~0/0", True), ("/a~1b/~0/00", False),
                                           ("/a~1b/~0/-1", False), ("/a~1b/~0/1", False),
                                           ("/bad~2", False), ("", True)])
def test_json_pointer_escaping_and_array_bounds(pointer, valid):
    raw = b'{"a/b":{"~":[42]}}'
    if valid:
        CHECK.locate(raw, {"kind": "json", "pointer": pointer}, {})
    else:
        with pytest.raises(CHECK.Invalid):
            CHECK.locate(raw, {"kind": "json", "pointer": pointer}, {})


@pytest.mark.parametrize("field, value", [("status", "preserved"), ("reason", ""),
                                         ("relation", "equivalent"), ("targets", {}),
                                         ("decision", []), ("unexpected", True)])
def test_malformed_records_fail_as_json_error(packet, capsys, field, value):
    packet["records"][0][field] = value
    rc, result = run(packet, capsys)
    assert rc == 1 and result["integrityValid"] is False


def test_binding_directions_and_native_identity_guards(packet, capsys):
    packet["records"][0]["bindings"] = [{"source": "x", "target": "y", "direction": "guessed"}]
    assert run(packet, capsys)[0] == 1
    packet["records"][0].pop("bindings")
    packet["inventory"]["items"][0]["locator"]["attributes"]["id"] = "another-stage"
    assert run(packet, capsys)[0] == 1


@pytest.mark.parametrize("path", ["../outside.json", "/absolute.json", "a/../b", "C:/outside", "a\\b"])
def test_fragment_paths_cannot_escape(packet, capsys, path):
    packet["trace"]["fragments"] = [path]
    assert run(packet, capsys)[0] == 1


def test_symlink_in_project_is_refused(packet, capsys, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("not project data")
    try:
        (packet["target"] / "Worker/link").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    assert run(packet, capsys)[0] == 1


def test_standalone_project_skips_only_generated_target_directories(packet, capsys):
    (packet["target"] / "Worker/.local").mkdir()
    (packet["target"] / "Worker/.local/cache").write_text("transient")
    packet["target"] = packet["target"] / "Worker"
    packet["trace"]["targetArtifacts"] = [{"path": p.name, "sha256": sha(p.read_bytes())}
                                          for p in packet["target"].iterdir() if p.is_file()]
    for row in packet["records"]:
        row["targets"][0]["artifact"] = "Main.xaml"
    inventory_path = packet["working"] / "source-inventory.json"
    write_json(inventory_path, packet["inventory"])
    packet["trace"]["sourceInventorySha256"] = sha(inventory_path.read_bytes())
    assert run(packet, capsys, projects=(".",), refresh=False)[0] == 0


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_BYTES", "MAX_PARSE_BYTES", "MAX_ITEMS"])
def test_exhaustion_is_failure_not_partial_success(packet, capsys, monkeypatch, limit):
    monkeypatch.setattr(CHECK, limit, 1)
    rc, report = run(packet, capsys)
    assert rc == 1 and report["integrityValid"] is False


def test_duplicate_json_keys_and_dtd_are_refused(packet, capsys):
    with pytest.raises(CHECK.Invalid, match="duplicate JSON key"):
        CHECK.json_bytes(b'{"version": 1, "version": 2}')
    (packet["source"] / "release.xml").write_bytes(b'<!DOCTYPE x [<!ENTITY a "expanded">]><x>&a;</x>')
    packet["inventory"]["artifacts"][0]["sha256"] = sha((packet["source"] / "release.xml").read_bytes())
    assert run(packet, capsys)[0] == 1
