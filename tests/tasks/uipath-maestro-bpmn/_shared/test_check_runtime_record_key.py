#!/usr/bin/env python3
"""Regression tests for check_runtime_record_key.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CHECK = Path(__file__).with_name("check_runtime_record_key.py")
JIRA = "uipath-atlassian-jira"


def _bpmn(method: str, path: dict, query: dict, mapping: str = "") -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="P">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:input id="issueKey" name="issueKey" type="string" elementId="Event_start" />
        <uipath:inputOutput id="fixedKey" name="fixedKey" type="string" elementId="P" />
        <uipath:inputOutput id="issKey" name="issKey" type="string" elementId="P" />
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="Event_start">
      <bpmn:extensionElements>
        <uipath:output name="fixed" type="string" source="=&quot;CE-1&quot;" var="fixedKey" />
        {mapping}
      </bpmn:extensionElements>
    </bpmn:startEvent>
    <bpmn:serviceTask id="getIssue">
      <bpmn:extensionElements>
        <uipath:activity>
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="{JIRA}" />
            <uipath:input name="method" type="string" value="{method}" />
          </uipath:context>
          <uipath:input name="pathParameters" type="json" target="pathParameters"><![CDATA[{json.dumps(path)}]]></uipath:input>
          <uipath:input name="queryParameters" type="json" target="queryParameters"><![CDATA[{json.dumps(query)}]]></uipath:input>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
  </bpmn:process>
</bpmn:definitions>
"""


class RuntimeRecordKeyTests(unittest.TestCase):
    def _run(self, method: str = "GET", path: dict | None = None, query: dict | None = None, mapping: str = "") -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "IssueDigest.bpmn").write_text(_bpmn(method, path or {}, query or {}, mapping), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CHECK), "IssueDigest", JIRA, "project,issuetype"],
                cwd=tmp, capture_output=True, text=True,
            )

    def assertPasses(self, **kw) -> None:
        result = self._run(**kw)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assertFails(self, **kw) -> None:
        result = self._run(**kw)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_retrieve_by_input_key_passes(self) -> None:
        self.assertPasses(path={"issueId": "=vars.issueKey"})

    def test_jql_by_input_key_passes(self) -> None:
        self.assertPasses(query={"jql": '=js:"key = " + vars.issueKey'})

    def test_jql_with_project_from_an_expression_passes(self) -> None:
        self.assertPasses(query={"jql": '=js:"project = " + vars.projKey + " AND key = " + vars.issueKey'})

    def test_key_mapped_from_an_input_passes(self) -> None:
        self.assertPasses(
            path={"issueId": "=vars.issKey"},
            mapping='<uipath:output name="k" type="string" source="=vars.issueKey" var="issKey" />',
        )

    def test_lookup_sent_fails(self) -> None:
        self.assertFails(path={"issueIdOrKey": "=vars.issueKey"}, query={"project": "=vars.issueKey.split('-')[0]"})

    def test_literal_key_in_an_expression_fails(self) -> None:
        self.assertFails(path={"issueId": '="CE-1"'})

    def test_key_from_a_non_input_variable_fails(self) -> None:
        self.assertFails(path={"issueId": "=vars.fixedKey"})

    def test_jql_pinning_a_literal_project_fails(self) -> None:
        self.assertFails(query={"jql": '=js:"project = CE AND key = " + vars.issueKey'})
        self.assertFails(query={"jql": "=js:\"project = 'CE' AND key = \" + vars.issueKey"})
        self.assertFails(query={"jql": '=js:"project in (CE, OPS) AND key = " + vars.issueKey'})

    def test_non_read_operation_fails(self) -> None:
        self.assertFails(method="DELETE", path={"issueId": "=vars.issueKey"})


if __name__ == "__main__":
    unittest.main()
