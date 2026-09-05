"""Discovery under the Studio Web export layout.

The studioweb-stdio bridge mirrors the in-product ``/solution/<project>/`` tree
into the sandbox: ``<Project>/project.uiproj`` + ``<Project>/new.flow`` (Studio
Web's canonical entry-point name), with no ``<Solution>/`` wrapper. Graders that
pass a name-prefixed ``flow_glob`` (``SummarizeDemo*.flow``) or
``flow_contains.py --flow-name`` therefore name the project, not the file.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flow_check import find_flow_file, find_flow_files  # noqa: E402
from flow_contains import main as flow_contains_main  # noqa: E402

FLOW_BODY = json.dumps({"nodes": [{"id": "n1", "type": "core.trigger.manual"}], "expr": "$vars.x"})


def _studio_web_project(root, project, *, flow_body=FLOW_BODY):
    proj = root / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (proj / "new.flow").write_text(flow_body)
    (proj / "entry-points.json").write_text("{}")
    return proj


def _cli_project(root, solution, project, *, flow_body=FLOW_BODY):
    proj = root / solution / project
    proj.mkdir(parents=True)
    (proj / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (proj / f"{project}.flow").write_text(flow_body)
    return proj


def _abs(paths):
    return [os.path.abspath(p) for p in ([paths] if isinstance(paths, str) else paths)]


def test_name_prefixed_glob_matches_the_studio_web_project_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _studio_web_project(tmp_path, "SummarizeDemo")

    assert _abs(find_flow_file(flow_glob="SummarizeDemo*.flow")) == [str(proj / "new.flow")]
    assert _abs(find_flow_files(flow_glob="SummarizeDemo*.flow")) == [str(proj / "new.flow")]


def test_cli_layout_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj = _cli_project(tmp_path, "SummarizeDemoSolution", "SummarizeDemo")

    assert _abs(find_flow_file(flow_glob="SummarizeDemo*.flow")) == [str(proj / "SummarizeDemo.flow")]


def test_glob_naming_a_different_project_still_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _studio_web_project(tmp_path, "SummarizeDemo")

    with pytest.raises(SystemExit) as exc:
        find_flow_file(flow_glob="DelayDemo*.flow")
    assert "No .flow file matching 'DelayDemo*.flow'" in str(exc.value)


def test_flow_contains_flow_name_accepts_the_project_directory(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _studio_web_project(tmp_path, "VendorPOReview")

    assert flow_contains_main(["--flow-name", "VendorPOReview", '"core.trigger.manual"']) == 0
    assert flow_contains_main(["--flow-name", "SomethingElse"]) == 1
    assert "lives in a project directory named SomethingElse" in capsys.readouterr().err


def test_flow_contains_flow_name_still_matches_the_cli_basename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _cli_project(tmp_path, "VendorPOReviewSolution", "VendorPOReview")

    assert flow_contains_main(["--flow-name", "VendorPOReview"]) == 0
