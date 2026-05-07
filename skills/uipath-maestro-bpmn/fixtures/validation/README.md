# Maestro BPMN Validation Fixtures

Public-safe fixture corpus for the `uipath-maestro-bpmn` skill maintenance checks. These files are synthetic, but they intentionally cover the same structural families summarized from PO.Frontend mocks, private exported BPMN reviews, and generated BPMN package outputs.

## Fixture Set

| Fixture | Coverage |
| --- | --- |
| `linear-process/` | Minimal executable process, root variables, entry point ID, BPMN DI, and generated package metadata. |
| `gateway-boundary-error/` | Exclusive gateway conditions/defaults, service task retry/error mapping, boundary error event, terminate end, tags, and package manifest checks. |
| `integration-service-enriched/` | Integration Service trigger and activity extensions, root connection/property bindings, generated `bindings_v2.json` resources, entry point schema, and package metadata. |
| `subprocess-multi-instance/` | Subprocess scoped variables, multi-instance loop metadata, script task metadata, mappings, message event, and diagram/waypoint coverage. |

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
