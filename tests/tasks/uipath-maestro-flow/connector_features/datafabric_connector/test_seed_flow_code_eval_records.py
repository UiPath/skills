"""`seed_flow_code_eval_records.py` sends a folder key only for a folder entity (G21)."""

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SEED = HERE / "_setup" / "seed_flow_code_eval_records.py"
BPMN_SEED = (
    HERE.parents[2] / "uipath-maestro-bpmn" / "connector_features" / "datafabric_connector" / "_setup" / SEED.name
)
ENTITY = {"Id": "entity-1", "Name": "FlowCodeEvalEntity", "FolderId": "folder-1"}


@pytest.fixture
def seed():
    spec = importlib.util.spec_from_file_location("seed_flow_code_eval_records", SEED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stub(seed, monkeypatch, tenant_entities, folder_entities, records=()):
    calls = []

    def run(*args):
        calls.append(list(args))
        if args[:2] == ("df", "entities"):
            return {"Data": folder_entities if "--include-folders" in args else tenant_entities}
        if args[:3] == ("df", "records", "list"):
            return {"Data": {"Items": list(records)}}
        return {"Data": {}}

    monkeypatch.setattr(seed, "run", run)
    return calls


def test_a_tenant_entity_is_read_and_seeded_with_no_folder_key(seed, monkeypatch):
    calls = _stub(seed, monkeypatch, [ENTITY], [ENTITY])

    assert seed.main() == 0

    assert [c[:3] for c in calls] == [["df", "entities", "list"], ["df", "records", "list"], ["df", "records", "insert"]]
    assert not any("--folder-key" in c for c in calls)


def test_a_folder_entity_is_read_and_seeded_in_its_folder(seed, monkeypatch):
    calls = _stub(seed, monkeypatch, [], [ENTITY])

    assert seed.main() == 0

    records = [c for c in calls if c[:2] == ["df", "records"]]
    assert [c[2] for c in records] == ["list", "insert"]
    assert all(c[-2:] == ["--folder-key", "folder-1"] for c in records)


def test_a_seeded_entity_gets_no_second_copy(seed, monkeypatch):
    calls = _stub(seed, monkeypatch, [ENTITY], [], records=[{"title": seed.SENTINEL}])

    assert seed.main() == 0

    assert not any(c[:3] == ["df", "records", "insert"] for c in calls)


def test_a_missing_entity_fails_the_setup(seed, monkeypatch):
    _stub(seed, monkeypatch, [], [])
    assert seed.main() == 1


def test_the_bpmn_copy_matches_this_one():
    assert BPMN_SEED.read_bytes() == SEED.read_bytes()

