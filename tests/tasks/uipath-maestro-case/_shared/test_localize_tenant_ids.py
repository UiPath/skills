"""`localize_tenant_ids.py` rewrites cloud-pinned fixture IDs to the running tenant's IDs.

Each test owns one resolution rule, so blanking that rule turns its test red. The
`uip` calls are stubbed: what is under test is which live record the script picks
and what it writes, not the CLI.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

CASE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE_ROOT))

from _shared.case_check import localize_ids  # noqa: E402

OUTLOOK = "dd657127-91f5-4568-a3a3-c024bc03fb0f"
HELPDESK = "4d5c6aa7-a1a6-4dd9-aa4d-6304a22014e8"
PROJECT_EULER = "486edc26-0658-4ac1-92c9-1ef953927151"
AGENT = "ccf5793f-54ab-4262-bf44-fcd09a52ed4e"
PURCHASE_APP = "b20c471c-adef-4b37-a884-897f56ca53bc"
LIVE_OUTLOOK = "11111111-1111-1111-1111-111111111111"
LIVE_HELPDESK = "22222222-2222-2222-2222-222222222222"
LIVE_EULER = "33333333-3333-3333-3333-333333333333"
LIVE_APP = "44444444-4444-4444-4444-444444444444"


@pytest.fixture
def module():
    spec = importlib.util.spec_from_file_location(
        "localize_tenant_ids", CASE_ROOT / "_setup" / "localize_tenant_ids.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sandbox(tmp_path, module, monkeypatch):
    """A sandbox root with the real manifest and an empty registry cache."""
    (tmp_path / "_setup").mkdir()
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / "cache"
    cache.mkdir()
    monkeypatch.setattr(module, "RESOURCE_DIR", cache)
    monkeypatch.setattr(module, "MAP_FILE", Path("_setup") / ".tenant-ids.map.json")
    return tmp_path


def _stub_uip(module, monkeypatch, connections):
    calls = []

    def fake(args, timeout):
        calls.append(args)
        if args[:3] == ["is", "connections", "list"]:
            return {"Result": "Success", "Data": connections.get(args[3], [])}
        return {"Result": "Success", "Data": {}}

    monkeypatch.setattr(module, "_uip", fake)
    return calls


def _index(sandbox, name, entries):
    (sandbox / "cache" / f"{name}-index.json").write_text(json.dumps(entries))


def _process(key, name, folder):
    return {"entityKey": key, "name": name, "folders": [{"fullyQualifiedName": folder}]}


def test_a_connection_maps_to_the_enabled_one_in_its_folder(module, sandbox, monkeypatch):
    (sandbox / "sdd.md").write_text(f"**Connection ID:** `{OUTLOOK}`\n")
    _stub_uip(module, monkeypatch, {"uipath-microsoft-outlook365": [
        {"Id": "99999999-9999-9999-9999-999999999999", "Folder": "Shared", "State": "Enabled", "IsDefault": True},
        {"Id": LIVE_OUTLOOK, "Folder": "uipath-maestro-flow", "State": "Enabled"},
    ]})

    assert module.main() == 0

    assert (sandbox / "sdd.md").read_text() == f"**Connection ID:** `{LIVE_OUTLOOK}`\n"
    assert json.loads((sandbox / "_setup" / ".tenant-ids.map.json").read_text()) == {OUTLOOK: LIVE_OUTLOOK}


def test_an_id_the_tenant_already_has_is_left_alone(module, sandbox, monkeypatch):
    (sandbox / "sdd.md").write_text(f"{OUTLOOK}\n")
    _stub_uip(module, monkeypatch, {"uipath-microsoft-outlook365": [
        {"Id": LIVE_OUTLOOK, "Folder": "uipath-maestro-flow", "State": "Enabled"},
        {"Id": OUTLOOK, "Folder": "Shared", "State": "Enabled"},
    ]})

    assert module.main() == 0

    assert (sandbox / "sdd.md").read_text() == f"{OUTLOOK}\n"
    assert json.loads((sandbox / "_setup" / ".tenant-ids.map.json").read_text()) == {OUTLOOK: OUTLOOK}


def test_a_process_maps_by_name_and_folder(module, sandbox, monkeypatch):
    (sandbox / "sdd.md").write_text(f"entityKey {HELPDESK}\n")
    calls = _stub_uip(module, monkeypatch, {})
    _index(sandbox, "process", [
        _process("55555555-5555-5555-5555-555555555555", "HelpDeskLookup", "Shared"),
        _process(LIVE_HELPDESK, "HelpDeskLookup", "Shared/uipath-maestro-flow/HelpDeskLookup RPA"),
    ])

    assert module.main() == 0

    assert LIVE_HELPDESK in (sandbox / "sdd.md").read_text()
    assert ["maestro", "case", "registry", "pull", "--force"] in calls


def test_a_folder_holding_one_process_matches_under_another_name(module, sandbox, monkeypatch):
    # The ETE deploys ProjectEuler RPA's process as "RPA Workflow".
    (sandbox / "sdd.md").write_text(f"{PROJECT_EULER}\n")
    _stub_uip(module, monkeypatch, {})
    _index(sandbox, "process", [_process(LIVE_EULER, "RPA Workflow", "Shared/uipath-maestro-flow/ProjectEuler RPA")])

    assert module.main() == 0

    assert (sandbox / "sdd.md").read_text() == f"{LIVE_EULER}\n"


def test_an_unresolvable_id_stays_and_is_reported(module, sandbox, monkeypatch, capsys):
    (sandbox / "sdd.md").write_text(f"{AGENT}\n")
    _stub_uip(module, monkeypatch, {})

    assert module.main() == 0

    assert (sandbox / "sdd.md").read_text() == f"{AGENT}\n"
    assert AGENT in capsys.readouterr().err
    assert json.loads((sandbox / "_setup" / ".tenant-ids.map.json").read_text()) == {}


def test_an_action_app_maps_by_name(module, sandbox, monkeypatch):
    (sandbox / "registry-resolved.json").write_text(json.dumps({"id": PURCHASE_APP}))
    _stub_uip(module, monkeypatch, {})
    _index(sandbox, "action-apps", [{"id": LIVE_APP, "deploymentTitle": "purchaseorderapp-1782974854"}])

    assert module.main() == 0

    assert json.loads((sandbox / "registry-resolved.json").read_text()) == {"id": LIVE_APP}


def test_a_task_without_pinned_ids_calls_nothing(module, sandbox, monkeypatch):
    (sandbox / "sdd.md").write_text("no ids here\n")
    calls = _stub_uip(module, monkeypatch, {})

    assert module.main() == 0

    assert calls == []
    assert not (sandbox / "_setup" / ".tenant-ids.map.json").exists()


def test_a_checker_applies_the_same_map_to_the_reference_fixture(tmp_path):
    map_path = tmp_path / "map.json"
    map_path.write_text(json.dumps({OUTLOOK: LIVE_OUTLOOK, HELPDESK: HELPDESK}))

    assert localize_ids(f"{OUTLOOK.upper()} and {HELPDESK}", str(map_path)) == f"{LIVE_OUTLOOK} and {HELPDESK}"
    assert localize_ids(OUTLOOK, str(tmp_path / "absent.json")) == OUTLOOK


def test_the_manifest_covers_every_pinned_id_the_catalog_reports():
    """A new pinned ID in a fixture must get a manifest entry, or the ETE run keeps the cloud ID."""
    sys.path.insert(0, str(CASE_ROOT.parents[1] / "scripts"))
    import tenant_catalog

    catalog = tenant_catalog.to_json(tenant_catalog.build_catalog("uipath-maestro-case"))
    pinned = {pid.lower() for dep in catalog["dependencies"] for pid in dep.get("pinned_ids", [])}
    manifest = json.loads((CASE_ROOT / "_setup" / "tenant_ids.json").read_text())
    known = {pid for kind in manifest.values() for pid in kind}
    assert pinned <= known, sorted(pinned - known)


def test_the_registry_cache_is_left_as_the_task_staged_it(module, sandbox, monkeypatch):
    """Tasks grade the agent's own pull or a stale cache, so the lookup pull leaves no trace."""
    (sandbox / "sdd.md").write_text(f"{HELPDESK}\n")
    cache = sandbox / "cache"
    (cache / "process-index.json").write_text("[]")
    (cache / "agent-index.json").write_text('["stale"]')

    def fake(args, timeout):
        if args[:4] == ["maestro", "case", "registry", "pull"]:
            (cache / "process-index.json").write_text(json.dumps([
                _process(LIVE_HELPDESK, "HelpDeskLookup", "Shared/uipath-maestro-flow/HelpDeskLookup RPA"),
            ]))
            (cache / "agent-index.json").write_text("[]")
            (cache / "api-index.json").write_text("[]")
        return {"Result": "Success", "Data": {}}

    monkeypatch.setattr(module, "_uip", fake)

    assert module.main() == 0

    assert LIVE_HELPDESK in (sandbox / "sdd.md").read_text()
    assert sorted(p.name for p in cache.iterdir()) == ["agent-index.json", "process-index.json"]
    assert (cache / "process-index.json").read_text() == "[]"
    assert (cache / "agent-index.json").read_text() == '["stale"]'


def test_a_failed_registry_pull_leaves_ids_unresolved_instead_of_failing_the_task(module, sandbox, monkeypatch, capsys):
    (sandbox / "sdd.md").write_text(f"{HELPDESK}\n")

    def fake(args, timeout):
        raise RuntimeError("`uip maestro case registry pull --force` failed: boom")

    monkeypatch.setattr(module, "_uip", fake)

    assert module.main() == 0

    assert (sandbox / "sdd.md").read_text() == f"{HELPDESK}\n"
    assert "registry pull failed" in capsys.readouterr().err
