# Maestro BPMN Dogfood Report

Task: Dogfood Maestro BPMN skill and CLI end to end.

## Generated Project

- Project: `dogfood-output/customer-onboarding-approval`
- BPMN source: `dogfood-output/customer-onboarding-approval/customer-onboarding-approval.bpmn`
- Package output: `dogfood-output/dist/customer-onboarding-approval.processOrchestration.ProcessOrchestration.0.1.0.nupkg` (ignored by git)

This directory is intentionally committed as the dogfood investigation artifact for PR review, not as a reusable skill fixture.

The BPMN models a customer-onboarding approval workflow with:

- Manual start and complete/rejected end states.
- Sequence flows with exclusive gateways for risk and approval routing.
- `bpmn:scriptTask` risk decision with `uipath:scriptVersion` and `uipath:mapping`.
- `bpmn:userTask` HITL approval using an `Actions.HITL` draft shell.
- `bpmn:serviceTask` RPA-style automation using an `Orchestrator.StartJob` draft shell.
- `bpmn:sendTask` Integration Service notification intent left as draft structure, plus annotation, because connector metadata, connection binding, operation schema, and generated outputs are CLI-owned.

## Commands Run

```bash
uip maestro bpmn --help
uip maestro bpmn init --help
uip maestro bpmn registry --help
uip maestro bpmn validate --help
uip tools list --output json
bun --version
bun run start -- maestro bpmn --help
uip maestro bpmn init customer-onboarding-approval --output json
uip maestro bpmn registry pull --output json
uip maestro bpmn registry search connector --output json
uip maestro bpmn registry get Intsvc.ActivityExecution --output json
uip maestro bpmn registry get Actions.HITL --output json
uip maestro bpmn registry get Orchestrator.StartJob --output json
uip maestro bpmn pack dogfood-output/customer-onboarding-approval dogfood-output/dist --version 0.1.0 --output json
bash skills/uipath-maestro-bpmn/.maintenance/check-all.sh
xmllint --noout dogfood-output/customer-onboarding-approval/customer-onboarding-approval.bpmn
python3 -m zipfile -l dogfood-output/dist/customer-onboarding-approval.processOrchestration.ProcessOrchestration.0.1.0.nupkg
```

## Results

- Global `uip` is installed at `/usr/local/bin/uip`, version `0.9.1`.
- Global `maestro-tool` is `0.9.1` and exposes `init`, `pack`, `debug`, lifecycle commands, and `registry`.
- Global `uip maestro bpmn validate --help` fails with `unknown command 'validate'`.
- Local `<LOCAL_UIPCLI_CHECKOUT>` source includes `registerValidateCommand`, but `bun run start -- maestro bpmn --help` fails before command registration: `Cannot find module '@uipath/flow-migrations' from '<LOCAL_UIPCLI_CHECKOUT>/packages/flow-tool/src/services/flow-migrate-service.ts'`.
- Registry discovery worked from cache: `ExtensionTypeCount=29`, `ConnectorCount=0`, `ProcessCount=26`.
- `Intsvc.ActivityExecution` is discoverable and maps to `bpmn:SendTask`, but no local enrichment command was found and no connector connections were available.
- `Actions.HITL` and `Orchestrator.StartJob` registry specs were discoverable and agreed with the skill wrappers.
- `uip maestro bpmn pack ... --output json` succeeded and emitted the ignored package path above.
- `xmllint --noout` passed for the generated BPMN.
- Skill maintenance passed: `commands_checked=30 unknown=0`, `validation_fixture_projects=4 bpmn_files=4 errors=0`, and `All checks passed.`

## Evaluation

The skill instructions were sufficient for a fresh coding agent to choose BPMN wrappers, keep BPMN XML as source, and avoid hand-authoring Integration Service connection details. Supported elements are discoverable in `supported-elements.md`, and registry checks cross-confirmed the HITL, RPA, and Integration Service wrappers.

The main gap is CLI/setup rather than skill text: the merged local CLI source has the new standalone validation command, but the local checkout cannot run because dependencies are incomplete, while the installed global CLI is older and lacks `validate`. The registry can describe Integration Service node types, but this environment did not expose a command that takes a draft BPMN element and enriches it with selected connector metadata/resources.

Generated package JSON also remained scaffold-derived after editing the BPMN. Pack-time validation accepted the project and produced a package, but there was no discovered command to regenerate `entry-points.json` schemas from the updated root variables or to reconcile connector resources.

## Follow-ups

- owner=CLI; action=schedule_task; Make `<LOCAL_UIPCLI_CHECKOUT>` runnable from main or document the required dependency/bootstrap step that provides `@uipath/flow-migrations`.
- owner=CLI; action=schedule_task; Ensure the installed/local command surface exposes `uip maestro bpmn validate` after PR #1875, or document the supported local invocation while global tools lag.
- owner=CLI; action=schedule_task; Add or document a local BPMN package-metadata regeneration/enrichment command for `entry-points.json`, `bindings_v2.json`, and Integration Service activity payloads.
- owner=skills; action=no_action_needed; No narrow high-confidence skill doc/fixture defect was found in this dogfood pass.
