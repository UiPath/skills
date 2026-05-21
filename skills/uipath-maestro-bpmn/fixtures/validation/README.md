# Maestro BPMN Validation Fixtures

Public-safe fixture corpus for the `uipath-maestro-bpmn` skill maintenance checks. These files are synthetic and intentionally cover Maestro BPMN XML wrappers, preservation boundaries, and generated package-output families.

## Fixture Set

| Fixture | Coverage |
| --- | --- |
| `linear-process/` | Minimal executable process, root variables, entry point ID, BPMN DI, and generated package metadata. |
| `imported-brownfield-preservation/` | Imported brownfield preservation case with numeric `uipath:migrationVersion`, legacy `uipath:scriptVersion value="v2"`, and matching generated package metadata. |
| `gateway-boundary-error/` | Exclusive gateway conditions/defaults, service task retry/error mapping, boundary error event, terminate end, tags, and package manifest checks. |
| `integration-service-enriched/` | Integration Service trigger and activity extensions, root connection/property bindings, generated `bindings_v2.json` resources, entry point schema, and package metadata. |
| `subprocess-multi-instance/` | Subprocess scoped variables, multi-instance loop metadata, script task metadata, mappings, message event, and diagram/waypoint coverage. |
| `contract-variants/` | Representative public-safe Orchestrator agent, A2A, API workflow, business rule, queue, agentic/case call activity, message send event, case-management draft/preserve shells, `Intsvc.WaitForEvent`, numeric migration, legacy script, and preserve-only extension variants. |
| `registry-coverage-matrix/` | Synthetic static wrapper coverage for current registry rows not otherwise covered by the corpus, including HITL, plain RPA, timer, HTTP, unified HTTP, and remaining Integration Service execution variants. |
| `wrapper-family-contract/` | Maestro BPMN wrapper coverage for `Orchestrator.StartAgentJob` (folder-deployed coded or low-code agent with the required `name`+`folderPath` binding pair), API workflow, business rule, queue wait, case-management call activity, and `Intsvc.WaitForEvent` enrichment paths. `A2A.AgentExecution` (external A2A) coverage stays in `contract-variants/`. |
| `agent-invocation/` | End-to-end runnable example for invoking a folder-deployed coded (Python) or low-code agent: entry-point `uipath:input` projected to a `uipath:inputOutput` via a start-event `BPMN.Variables` mapping, `Orchestrator.StartAgentJob` with the `name`+`folderPath` binding pair, and outputs mapped back to declared variables. Matches the strict shape enforced by `@uipath/maestro-sdk/bpmn-validation` after CLI PR #2137. |

## Contract Coverage Scope

The `contract-variants/` fixture is representative coverage for public-safe XML shells and preservation boundaries; it is not a claim that every row in `references/author/references/supported-elements.md` has a static fixture. Coverage is split as follows:

| Bucket | Static fixture coverage |
| --- | --- |
| Model-owned or model-draft non-Integration-Service shells | Covered by `contract-variants/` for Orchestrator agent/API workflow/queue/business-rule wrappers, agentic and case-management sync/async call activities, and `Maestro.SendMessageEvent`. |
| Preserve-only or dedicated-contract case-management XML | Covered by `contract-variants/` for `uipath:caseManagement`, generic `uipath:Activity`, `Maestro.CasePlanScheduler`, `Maestro.CaseManagerGuardrails`, and `Maestro.CaseRulesEvaluator` preservation/draft shells. |
| CLI-owned `Intsvc.*` enrichment | Covered as synthetic wrapper shells only. `contract-variants/` keeps one representative `Intsvc.WaitForEvent` shell; `integration-service-enriched/` covers enriched trigger/activity sidecars; `registry-coverage-matrix/` covers the remaining current registry wrapper names without claiming connector-specific schemas are model-owned. |
| Standard BPMN structures | Covered across the fixture corpus by targeted structural checks, not by a row-for-row supported-elements matrix. |

The Integration Service fixture is intentionally shape-only. It verifies where enriched XML, bindings, and generated package metadata appear, but it is not evidence that those connector values are valid for a live tenant. Real projects still require current registry-backed enrichment before Operate.

## Pilot Scenarios

The corpus was piloted against these public-safe authoring and debugging requests:

| Request | Fixtures used | Result |
| --- | --- | --- |
| Create a service-desk intake process with a connector trigger, ticket creation, and generated package metadata. | `integration-service-enriched/` | Kept the model/CLI boundary explicit: connector metadata, connection bindings, and generated resources must come from enrichment before Operate. |
| Validate that imported XML survives local checks without normalizing legacy script metadata. | `imported-brownfield-preservation/` | Covers the XML analyst baseline by preserving numeric `uipath:migrationVersion` values and imported `uipath:scriptVersion value="v2"` alongside package metadata. |
| Debug an approval workflow where the run takes the wrong branch and then faults on error handling. | `gateway-boundary-error/` | Tightened checks around gateway conditions/defaults, boundary error references, and package metadata drift. |
| Author a batch item processor with a scoped subprocess, sequential multi-instance loop, script normalization, and a message wait. | `subprocess-multi-instance/` | Added checks for message references and multi-instance collection/item metadata so stuck-loop and stuck-wait issues are caught locally. |
| Review imported XML that mixes public Orchestrator wrappers, Integration Service waits, message events, case-management draft/preserve shells, numeric migrations, legacy script metadata, and unsupported UiPath extension payloads. | `contract-variants/` | Added structural checks that wrappers stay on the documented BPMN element classes and preserve-only payloads are retained without private identifiers. |
| Compare the static fixture corpus against the registry surface exposed by `uip maestro bpmn registry list`. | `registry-coverage-matrix/` plus existing fixtures | Filled the missing wrapper rows with synthetic placeholders while keeping cloud resource resolution as a later authenticated test. |
| Verify that Maestro BPMN XML keeps the documented wrapper family for agent execution, API workflow, business rules, queue wait, case management, and connector wait nodes. | `wrapper-family-contract/` | Added contract checks for wrapper-to-service-type alignment so coverage fails if supported behavior drifts to the wrong BPMN element family. |
| Invoke a folder-deployed coded Python agent end-to-end from BPMN with the post-#2137 binding-pair shape (`name`+`folderPath`, `resource="process"`, `resourceSubType="Agent"`) and the required entry-point input projection. | `agent-invocation/` | Demonstrates the single shape that survives both `uip maestro bpmn pack` and `uip solution pack` validation under the shared `@uipath/maestro-sdk/bpmn-validation` validator. |

## Validation Output

Latest local fixture validation from this pilot:

```text
validation_fixture_projects=9 bpmn_files=9 errors=0
```

The local checker also runs a narrow negative regression for a misnamed
single-file BPMN project, seeded from the `gateway-boundary-error/` fixture. The
regression passes only when basename validation rejects copied project metadata
whose single BPMN file no longer matches the project directory name.

## Open Questions for Maestro Owners

- Should `uipath:loopCharacteristics` remain the stable public contract for multi-instance collection and item binding, or should fixture validation prefer registry/CLI-generated loop metadata when available?
- Which `Intsvc.*` context fields are mandatory across all connector families versus connector-specific fields that should stay outside this static checker?

## Maintenance Commands

Contributor check from the repository root:

```bash
bash skills/uipath-maestro-bpmn/.maintenance/check-validation-fixtures.sh
```

Full skill maintenance suite from the repository root:

```bash
bash skills/uipath-maestro-bpmn/.maintenance/check-all.sh
```

CI should run the same two commands before skill evals. The smoke eval task for this corpus is:

```bash
cd tests
make tags TAGS="uipath-maestro-bpmn smoke" EXPERIMENT=experiments/default.yaml
```

## Public-Safety Rules

- Do not copy raw exported BPMN, screenshots, tenant metadata, connection IDs, folder keys, URLs, user names, private process names, or temporary mission notes into these fixtures.
- Keep IDs readable and synthetic, for example `Task_CreateTicket` and `Binding_ServiceDeskConnection`.
- Keep package metadata deterministic and local to the fixture folder.
