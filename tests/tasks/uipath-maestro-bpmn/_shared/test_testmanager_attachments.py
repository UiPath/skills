"""check_testmanager_attachments.py --all-ops: download method accept-set."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_testmanager_attachments.py")

NODE = """
    <bpmn:sendTask id="Task_{object_name}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-testmanager" />
            <uipath:input name="objectName" type="string" value="{object_name}" />
            <uipath:input name="method" type="string" value="{method}" />
          </uipath:context>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""


def _run(tmp_path: Path, download_method: str) -> subprocess.CompletedProcess:
    nodes = [
        ("UploadAttachment", "POST"),
        ("GetAttachments", "GET"),
        ("DownloadAttachment", download_method),
        ("DeleteAttachment", "DELETE"),
    ]
    body = "".join(NODE.format(object_name=o, method=m) for o, m in nodes)
    (tmp_path / "Process.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f'<bpmn:process id="Process_1">{body}</bpmn:process></bpmn:definitions>'
    )
    return subprocess.run(
        [sys.executable, str(CHECKER), "--all-ops"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("method", ["GETBYID", "GET", "get"])
def test_download_accepts_get_spellings(tmp_path: Path, method: str) -> None:
    result = _run(tmp_path, method)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("method", ["DELETE", "POST"])
def test_download_rejects_other_methods(tmp_path: Path, method: str) -> None:
    result = _run(tmp_path, method)
    assert result.returncode != 0
    assert "download an attachment" in result.stderr
