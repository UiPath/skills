#!/usr/bin/env python3
"""Static regression tests for guardrail skill/evaluator contracts."""

from __future__ import annotations

import ast
import importlib.util
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


class ReviewContractTests(unittest.TestCase):
    def test_review_skill_allows_only_explicit_external_report_write(self) -> None:
        skill = (ROOT / "skills/uipath-review/SKILL.md").read_text()
        frontmatter = skill.split("---", 2)[1]
        self.assertIn("TRIGGER:", frontmatter)
        self.assertIn("DO NOT TRIGGER:", frontmatter)
        self.assertRegex(frontmatter, r"allowed-tools:.*\bWrite\b")
        self.assertIn("explicitly requested report path", skill)
        self.assertIn("outside every reviewed project root", skill)

    def test_every_review_guardrail_prompt_is_skill_first_and_nonblocking(self) -> None:
        task_paths = sorted(
            (ROOT / "tests/tasks/uipath-review/agents").glob("*guardrail*/*.yaml")
        )
        self.assertEqual(10, len(task_paths))
        for path in task_paths:
            prompt = load_yaml(path)["initial_prompt"]
            with self.subTest(path=path):
                self.assertIn("Start by invoking the `uipath-review` skill.", prompt)
                self.assertIn("No PDD is available", prompt)


class AgentGuardrailContractTests(unittest.TestCase):
    def test_direct_sdk_tasks_disallow_websearch(self) -> None:
        paths = [
            ROOT / "tests/tasks/uipath-agents/coded/guardrails/recommend_all/recommend_all.yaml",
            ROOT / "tests/tasks/uipath-agents/coded/guardrails/recommend_scoped/recommend_scoped.yaml",
            ROOT / "tests/tasks/uipath-agents/coded/guardrails/validate/validate.yaml",
        ]
        for path in paths:
            agent = load_yaml(path)["agent"]
            with self.subTest(path=path):
                self.assertIn("WebFetch", agent["allowed_tools"])
                self.assertIn("WebSearch", agent["disallowed_tools"])

    def test_conversational_guardrail_task_is_skill_first_without_websearch(self) -> None:
        path = ROOT / (
            "tests/tasks/uipath-agents/lowcode/conversational/guardrails/"
            "guardrail_custom_tool/guardrail_custom_tool.yaml"
        )
        task = load_yaml(path)
        self.assertIn("WebSearch", task["agent"]["disallowed_tools"])
        self.assertIn(
            "Start by invoking the `uipath-agents` skill.", task["initial_prompt"]
        )

    def test_coded_guidance_requires_callable_rules_and_structural_verification(self) -> None:
        guide = (
            ROOT
            / "skills/uipath-agents/references/coded/capabilities/guardrails/guardrails.md"
        ).read_text()
        self.assertIn("CustomValidator(rule=lambda data:", guide)
        self.assertIn("rules=[lambda data:", guide)
        self.assertIn("grep-only verification is not sufficient", guide)
        self.assertIn("ast.Starred", guide)

    def test_validate_guidance_preserves_guardrail_and_rereads_lowcode_json(self) -> None:
        coded = (
            ROOT
            / "skills/uipath-agents/references/coded/capabilities/guardrails/guardrails-recommend.md"
        ).read_text()
        lowcode = (
            ROOT
            / "skills/uipath-agents/references/lowcode/capabilities/guardrails/guardrails-recommend.md"
        ).read_text()
        self.assertIn("move the existing guardrail; do not remove it", coded)
        self.assertIn("Re-read `agent.json` after `refresh` and `validate`", lowcode)

    def test_deterministic_checker_requires_a_callable_predicate(self) -> None:
        path = ROOT / (
            "tests/tasks/uipath-agents/coded/guardrails/deterministic/"
            "check_deterministic.py"
        )
        spec = importlib.util.spec_from_file_location("deterministic_checker", path)
        assert spec and spec.loader
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)

        good = ast.parse(
            """
def lookup_account_info(customer_id):
    pass

agent = create_agent(middleware=[
    *UiPathDeterministicGuardrailMiddleware(
        tools=[lookup_account_info],
        rules=[lambda data: "secret" in data["customer_id"]],
        action=BlockAction(),
    )
])
"""
        )
        bad = ast.parse(
            """
def lookup_account_info(customer_id):
    pass

agent = create_agent(middleware=[
    *UiPathDeterministicGuardrailMiddleware(
        tools=[lookup_account_info],
        rules=["secret"],
        action=BlockAction(),
    )
])
"""
        )
        functions = {"lookup_account_info": good.body[0]}
        self.assertTrue(checker.valid_middleware(good, functions))
        self.assertFalse(checker.valid_middleware(bad, functions))

        wrong_action = ast.parse(
            """
def lookup_account_info(customer_id):
    pass

agent = create_agent(middleware=[
    *UiPathDeterministicGuardrailMiddleware(
        tools=[lookup_account_info],
        rules=[lambda data: "secret" in data["customer_id"]],
        action=LogAction(),
    )
])
BlockAction()
"""
        )
        functions = {"lookup_account_info": wrong_action.body[0]}
        self.assertFalse(checker.valid_middleware(wrong_action, functions))

        unwired = ast.parse(
            """
def lookup_account_info(customer_id):
    pass

unused = [
    *UiPathDeterministicGuardrailMiddleware(
        tools=[lookup_account_info],
        rules=[lambda data: "secret" in data["customer_id"]],
        action=BlockAction(),
    )
]
agent = create_agent(middleware=[])
"""
        )
        functions = {"lookup_account_info": unwired.body[0]}
        self.assertFalse(checker.valid_middleware(unwired, functions))


class MaestroArtifactSafetyTests(unittest.TestCase):
    def test_node_registry_read_is_allowed_but_artifact_write_is_rejected(self) -> None:
        task = load_yaml(
            ROOT / "tests/tasks/uipath-maestro-case/guardrails/artifact_safety_guard.yaml"
        )
        criterion = next(
            item
            for item in task["success_criteria"]
            if item.get("description", "").startswith(
                "Rule 13: no inline interpreter"
            )
        )
        pattern = re.compile(criterion["command_pattern"])
        registry_read = (
            "node -e \"const fs=require('fs'); "
            "fs.readFileSync('/tmp/.uip/case-resources/index.json')\""
        )
        artifact_write = (
            "node -e \"const fs=require('fs'); "
            "fs.writeFileSync('caseplan.json', '{}')\""
        )
        computed_artifact_write = (
            "node -e \"const fs=require('fs'); "
            "fs.writeFileSync('case' + 'plan.json', '{}')\""
        )
        python_computed_write = (
            "python3 -c \"open('case' + 'plan.json', 'w').write('{}')\""
        )
        python_update_write = (
            "python3 -c \"open('case' + 'plan.json', 'r+').write('{}')\""
        )
        self.assertIsNone(pattern.search(registry_read))
        self.assertIsNotNone(pattern.search(artifact_write))
        self.assertIsNotNone(pattern.search(computed_artifact_write))
        self.assertIsNotNone(pattern.search(python_computed_write))
        self.assertIsNotNone(pattern.search(python_update_write))


if __name__ == "__main__":
    unittest.main()
