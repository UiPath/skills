"""Unit tests for check_managed_http_fallback's per-node evidence blob."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

QUERY_PARAMS = "query_params"


def _load():
    path = Path(__file__).parent / "check_managed_http_fallback.py"
    spec = importlib.util.spec_from_file_location("_check_managed_http_fallback", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _node(body: dict) -> ET.Element:
    return ET.fromstring(
        '<bpmn:sendTask xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        '<bpmn:extensionElements><uipath:activity version="v1">'
        '<uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        '<uipath:context><uipath:input name="connectorKey" type="string" value="uipath-uipath-http" /></uipath:context>'
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{json.dumps(body)}]]></uipath:input>'
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _missing(grader, body: dict) -> list[str]:
    required = list(grader.FALLBACK_CHECKS[QUERY_PARAMS]["required"])
    return grader.require_all(grader.node_blob(_node(body)), required)


def test_query_params_accepts_split_url_and_path() -> None:
    grader = _load()
    body = {
        "method": "GET",
        "url": "https://tasks.googleapis.com/",
        "path": "/tasks/v1/lists/@default/tasks",
        "query": {"showHidden": True},
    }
    assert _missing(grader, body) == []


def test_query_params_accepts_single_url() -> None:
    grader = _load()
    body = {
        "method": "GET",
        "url": "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks",
        "query": {"showHidden": True},
    }
    assert _missing(grader, body) == []


def test_query_params_rejects_wrong_host() -> None:
    grader = _load()
    body = {
        "method": "GET",
        "url": "https://example.com",
        "path": "/tasks/v1/lists/@default/tasks",
        "query": {"showHidden": True},
    }
    assert _missing(grader, body) == ["tasks.googleapis.com/tasks/v1/lists"]
