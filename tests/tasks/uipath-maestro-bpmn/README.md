# Maestro BPMN Skill Eval Tasks

These tasks exercise the `uipath-maestro-bpmn` skill — a registry-driven,
authoring-only skill for producing valid, importable Maestro `.bpmn` XML.

- `smoke/` covers the core registry-driven authoring loop.
  `registry_discovery.yaml` checks that the agent discovers extension types via
  `uip maestro bpmn registry pull/list/search/get` (saving raw CLI output as
  evidence) before authoring. `author_validate.yaml` checks that the agent
  authors a structurally sound BPMN (start -> exclusive gateway with two
  conditioned branches -> end, with a full `bpmndi:BPMNDiagram`) and validates
  it with a well-formed-XML parse plus the structural checklist. Both are
  authoring-only — no upload, publish, deploy, debug, run, or pack.
- `author/` covers BPMN skeleton structure, gateways, sequence flows, and
  diagrams.
- `authoring/` covers implementation rows that are not fixture-only: business
  rules, API workflow execution, and the script/Jint lifecycle path.
- `nodes/` covers task-wrapper and script-task authoring behavior, including
  public-safe Maestro BPMN XML contract variants.
- `connector/` covers Integration Service boundary behavior and registry
  discovery for connector wrapper types without cloud-side mutations.
- `hitl/` covers human-in-the-loop (`Actions.HITL` user task) authoring —
  completion wiring, multi-outcome gateway routing, task data-mapping design,
  downstream consumption of the reviewer's decision, boolean-typed decisions,
  and surgical insertion of an approval gate into an existing `.bpmn`. Ported
  from the flow suite's `hitl/` intent.
- `edit/` covers surgical brownfield edits on a pre-built, valid `.bpmn`
  fixture (add / remove / update / reorder a node, add an output mapping,
  extract a group into a subprocess). Each task ships its own fixture and
  grades the requested edit plus preservation of untouched ids, `uipath:*`
  payloads, and `uipath:migrationVersion` via an ElementTree diff against the
  pristine original.
- `e2e/` covers a multi-node authoring scenario end to end.
- `operate-diagnose/` covers diagnostic inspection and operate-action guidance
  using mocked CLI responses, matching the operate and diagnose capabilities the
  skill retains.
- `_shared/` contains small Python helpers for durable XML shape assertions, plus every per-task `check_*.py` grader (reached only via `$REFERENCE_DIR`, never staged into the agent's sandbox).

These tasks validate with `uip maestro bpmn validate <file>`, which runs the
full PO.Frontend canvas rule set offline (added in UiPath/cli#3135). If the CLI
is unavailable, they fall back to parsing the BPMN for well-formedness and
walking the structural checklist in the skill's `references/structural-bpmn.md`.

## Arm neutrality — two invariants these tasks must keep

Every task here is shared by both comparison arms: the shipped `skills/uipath-maestro-bpmn`
(registry + raw XML) and `preview/skills/uipath-maestro-bpmn` (the TypeScript builder SDK),
selected by `agent.plugins` in the experiment, not by the task.
Two things therefore have to stay out of the task YAMLs, or a run measures the fixture instead of the skill.

**1. Never stage a skill directory via `sandbox.template_sources`.**
Until 2026-09-23 all 87 of these tasks copied `skills/uipath-maestro-bpmn` (368 KB: `SKILL.md`, `references/`, `validator/bpmn-spec.json`) into the agent's working directory at `mount_point: .`.
No other skill family does this, nothing reads it — the skill arrives through the plugin catalog — and under the preview arm it put the *other* generation's guidance in the agent's cwd, which agents then read and followed instead of the SDK skill.
That defeats the stated purpose of `flow-v2-preview.yaml` ("measures the Flow v2 authoring path rather than a mix of both generations").
`template_sources` is for pre_run/post_run tooling and fixtures only; see tests/README.md.

**2. Prompts state the outcome, never the mechanism.**
These two both prescribe the v1 path, and the second asks by hand for work the builder SDK's serializer and `bpmn format` do on their own:

```
- Discover X via the registry and author it from the registry template.
- Include a bpmndi:BPMNDiagram with a BPMNShape for every node and a BPMNEdge
  for every sequence flow.
```

Write what the emitted file must contain and let each arm's skill decide how:

```
- Resolve X's type and payload the way your skill prescribes.
- The emitted `.bpmn` must carry a complete bpmndi:BPMNDiagram — a shape for
  every node and an edge for every sequence flow.
```

The exception is a task that grades registry usage itself (`smoke/registry_discovery.yaml`,
`connector/registry_discovery.yaml`, `single_node/timer_start/timer_start.yaml`, and the
`connector_features/` tasks whose criteria assert `registry pull`/`get`).
There the registry IS the subject under test, so naming it is correct.

## Contributor Commands

Run the Maestro BPMN smoke eval:

```bash
cd tests
make tags TAGS="uipath-maestro-bpmn smoke" EXPERIMENT=experiments/smoke.yaml
```

Run all tests for this skill:

```bash
cd tests
make test-uipath-maestro-bpmn
```
