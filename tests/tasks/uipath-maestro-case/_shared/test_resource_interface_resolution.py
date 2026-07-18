"""Structural regression tests for the Case resource-interface resolver docs.

The Case skill is documentation-driven, so these tests pin the declarations and
cross-file invariants that make the type-agnostic resolver executable by an
agent. Run this file directly or discover it with unittest/pytest.
"""

import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
CASE = REPO / "skills" / "uipath-maestro-case"


def read(relative: str) -> str:
    return (CASE / relative).read_text(encoding="utf-8")


class ResourceInterfaceResolutionTests(unittest.TestCase):
    def test_all_nine_task_plugins_declare_the_expected_provider(self) -> None:
        expected = {
            "process": "tasks-describe",
            "agent": "local-entry-points",
            "rpa": "tasks-describe",
            "action": "tasks-describe",
            "api-workflow": "local-entry-points",
            "case-management": "tasks-describe",
            "connector-activity": "case-spec-activity",
            "connector-trigger": "case-spec-trigger",
            "wait-for-timer": "none",
        }

        for plugin, provider in expected.items():
            with self.subTest(plugin=plugin):
                planning = read(f"references/plugins/tasks/{plugin}/planning.md")
                self.assertIn("## Resource Interface Declaration", planning)
                self.assertIn("interface-provider:", planning)
                self.assertIn(provider, planning)
                self.assertIn("placeholder-profile:", planning)
                self.assertIn("recovery-capabilities:", planning)

                if plugin in {
                    "process",
                    "agent",
                    "rpa",
                    "action",
                    "api-workflow",
                    "case-management",
                }:
                    self.assertIn("inputs: Data.Inputs[]", planning)
                    self.assertIn("outputs: Data.Outputs[]", planning)

    def test_event_and_all_connector_rule_scopes_share_trigger_provider(self) -> None:
        event = read("references/plugins/triggers/event/planning.md")
        self.assertIn("interface-provider: case-spec-trigger", event)
        self.assertIn("placeholder-profile: event-trigger", event)

        scopes = {
            "case-exit-conditions": "scope: case-exit",
            "stage-entry-conditions": "scope: stage-entry",
            "stage-exit-conditions": "scope: stage-exit",
            "task-entry-conditions": "scope: task-entry",
        }
        for plugin, owner_scope in scopes.items():
            with self.subTest(plugin=plugin):
                planning = read(f"references/plugins/conditions/{plugin}/planning.md")
                implementation = read(f"references/plugins/conditions/{plugin}/impl-json.md")
                self.assertIn("interface-provider: case-spec-trigger", planning)
                self.assertIn("placeholder-profile: connector-rule", planning)
                self.assertIn(owner_scope, planning)
                self.assertIn("tasks/interface-resolved.json", implementation)
                self.assertIn("validated connector-rule stub", implementation)

    def test_canonical_contract_comparison_and_sidecar_are_complete(self) -> None:
        resolver = read("references/resource-interface-resolution.md").lower()
        required_tokens = (
            "acquire(context)",
            "requestedcontract",
            "effectivecontract",
            "actualcontract",
            '"kind": "task|event-trigger|condition-rule"',
            '"status": "compatible|adapted|deferred|unavailable|not-applicable"',
            "names are exact and case-sensitive",
            "case value type -> resource input type",
            "resource output type -> case variable type",
            "integer -> float -> double",
            "date -> datetime",
            "jobattachment",
            "retry acquisition once",
            "legacy run with no sidecar",
            "consumer interface integrity",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, resolver)

    def test_blocking_results_route_to_each_standard_placeholder(self) -> None:
        resolver = read("references/resource-interface-resolution.md")
        self.assertIn("write `data: {}`", resolver)
        self.assertIn('serviceType: "Intsvc.EventTrigger"', resolver)
        self.assertIn("validated stub `uipath`", resolver)
        self.assertIn(
            "Incompatible best-effort continuation is forbidden",
            read("references/implementation.md"),
        )

    def test_fresh_and_adopted_local_are_gated_before_registration(self) -> None:
        discovery = read("references/registry-discovery.md")
        fresh_gate = discovery.index("### 3 — Fresh interface gate, then register")
        fresh_register = discovery.index("uip solution project add", fresh_gate)
        self.assertLess(fresh_gate, fresh_register)

        adopted = discovery.index('### 3b — "Already exists" = adopt')
        adopted_gate = discovery.index(
            "Run the interface gate as an existing-local origin before registration", adopted
        )
        adopted_register = discovery.index(
            "Register only a compatible/adapted residual", adopted
        )
        self.assertLess(adopted_gate, adopted_register)

        correction = read("references/plugins/tasks/create-inline-common.md")
        self.assertIn("origin` is `fresh", correction)
        self.assertIn("Maximum two correction attempts", correction)
        self.assertIn("Do not call `init`", correction)

    def test_inline_rpa_is_a_future_plugin_not_a_dependency(self) -> None:
        rpa = read("references/plugins/tasks/rpa/planning.md")
        resolver = read("references/resource-interface-resolution.md")
        declaration = rpa.split("```yaml", 1)[1].split("```", 1)[0]

        self.assertIn("interface-provider: tasks-describe", declaration)
        self.assertNotIn("local-entry-points", declaration)
        self.assertIn("Inline/local RPA creation is intentionally not part of this branch", rpa)
        self.assertIn("A future inline RPA plugin may declare its own paths", resolver)

    def test_skill_contract_lists_artifact_and_integrity_check(self) -> None:
        skill = read("SKILL.md")
        self.assertIn("tasks/interface-resolved.json", skill)
        self.assertIn("Consumer Interface Integrity", skill)
        self.assertIn(
            "all nine task types", read("references/resource-interface-resolution.md")
        )

    def test_brownfield_resource_edits_cannot_bypass_the_resolver(self) -> None:
        brownfield = read("references/brownfield.md")
        self.assertIn("Resource-bearing edits use the same interface resolver", brownfield)
        self.assertIn("tasks/interface-resolved.json", brownfield)
        self.assertIn("Run Consumer Interface Integrity", brownfield)
        self.assertIn("standard placeholder", brownfield)


if __name__ == "__main__":
    unittest.main()
