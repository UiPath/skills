import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bpmn_check import NS  # noqa: E402
from check_agent_job import start_agent_jobs  # noqa: E402


def _start_agent_job(type_version: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}"><bpmn:process>'
        '<bpmn:serviceTask id="Task_1"><bpmn:extensionElements>'
        '<uipath:activity version="v1">'
        f'<uipath:type value="Orchestrator.StartAgentJob" version="{type_version}" />'
        "</uipath:activity></bpmn:extensionElements></bpmn:serviceTask>"
        "</bpmn:process></bpmn:definitions>"
    )


def test_start_agent_jobs_accepts_v2() -> None:
    assert start_agent_jobs(_start_agent_job("v2"))


def test_start_agent_jobs_rejects_v1() -> None:
    assert not start_agent_jobs(_start_agent_job("v1"))
