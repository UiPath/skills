# Maestro BPMN Validation Fixtures

Public-safe fixture corpus for the `uipath-maestro-bpmn` skill maintenance checks. These files are synthetic, but they intentionally cover source-backed canvas serialization, runtime parser, and generated package-output families.

## Fixture Set

| Fixture | Coverage |
| --- | --- |
| `linear-process/` | Minimal executable process, root variables, entry point ID, BPMN DI, and generated package metadata. |
| `gateway-boundary-error/` | Exclusive gateway conditions/defaults, service task retry/error mapping, boundary error event, terminate end, tags, and package manifest checks. |
| `integration-service-enriched/` | Integration Service trigger and activity extensions, root connection/property bindings, generated `bindings_v2.json` resources, entry point schema, and package metadata. |
| `subprocess-multi-instance/` | Subprocess scoped variables, multi-instance loop metadata, script task metadata, mappings, message event, and diagram/waypoint coverage. |
| `contract-variants/` | Public-safe Orchestrator agent, A2A, API workflow, business rule, queue, call activity, `Intsvc.WaitForEvent`, numeric migration, legacy script, and preserve-only extension variants. |

## Pilot Scenarios

The corpus was piloted against these public-safe authoring and debugging requests:

| Request | Fixtures used | Result |
| --- | --- | --- |
| Create a service-desk intake process with a connector trigger, ticket creation, and generated package metadata. | `integration-service-enriched/` | Kept the model/CLI boundary explicit: connector metadata, connection bindings, and generated resources must come from enrichment before Operate. |
| Debug an approval workflow where the run takes the wrong branch and then faults on error handling. | `gateway-boundary-error/` | Tightened checks around gateway conditions/defaults, boundary error references, and package metadata drift. |
| Author a batch item processor with a scoped subprocess, sequential multi-instance loop, script normalization, and a message wait. | `subprocess-multi-instance/` | Added checks for message references and multi-instance collection/item metadata so stuck-loop and stuck-wait issues are caught locally. |
| Review imported XML that mixes public Orchestrator wrappers, Integration Service waits, numeric migrations, legacy script metadata, and unsupported UiPath extension payloads. | `contract-variants/` | Added structural checks that wrappers stay on the documented BPMN element classes and preserve-only payloads are retained without private identifiers. |

## Validation Output

Latest local fixture validation from this pilot:

```text
validation_fixture_projects=5 bpmn_files=5 errors=0
```

## Open Questions for Maestro Owners

- Should `uipath:loopCharacteristics` remain the stable public contract for multi-instance collection and item binding, or should fixture validation prefer registry/CLI-generated loop metadata when available?
- Which `Intsvc.*` context fields are mandatory across all connector families versus connector-specific fields that should stay outside this static checker?
- Should `entry-points.json` validation compare full input schemas against root variables, or only verify entry point IDs and file paths until the CLI generator owns schema normalization?

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
