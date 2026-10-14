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
`scripts/check-task-driver.py` enforces this now — the README alone did not hold, because `_porting/PORTING-BRIEF.md` went on telling authors to add the line.

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

**3. Never name a `references/*.md` file in a prompt.**
`preview/skills/uipath-maestro-bpmn/references/` holds exactly one file, `bpmn-runtime.md`.
`structural-bpmn.md`, `public-safety.md`, `expression-authoring.md` and `registry-workflow.md` exist only under `skills/uipath-maestro-bpmn/`, so "per the skill's structural reference" dangles under the SDK arm.
Read those documents as a task AUTHOR; write what the output must contain, and let each arm's skill decide how.

**4. Grade the artifact where the arm's workflow puts it, and by what it is, not by the v1 mechanism.**
Three shapes of v1-only grading were still in the suite after the 2026-09-25 run (`skill-bpmn-debug-not-validation`, `-event-trigger-start`, `-integration-service-boundary`, `-script-jint-guidance`, and the Data Fabric advisory criteria):
a `file_exists` on `<Name>.bpmn` at the workspace root (the SDK skill scaffolds `<Name>/<Name>.bpmn` and forbids a root copy) — use `_shared/check_bpmn_present.py <Name>`, the same locator every `check_*.py` uses;
"no package files may exist" on a draft (the SDK skill's `init` writes all four) — use `require_no_hand_authored_package_files`, which accepts the CLI-written shape and rejects hand-written metadata or a resolved binding;
a variable matched by `name` alone (the SDK writes `id` = what expressions read, `name` = the display name) — match either;
and `command_executed` on `registry get … --object-name` alone — also accept the SDK arm's `uip is resources describe`.
A fifth shape (2026-09-27, `-script-jint-guidance`): grading the canvas script-task TEMPLATE — a task-scoped `scriptResponse` variable, a task-scoped `Error`, whole-state `args` (`{vars, metadata}`) with its inputSchema, and start/end bridge mappings — where the runtime contract is only the `=result.response` row and the args keys.
The SDK writes per-input args, lands `=result.response` in the public output, and writes no Error unless asked; `check_script_jint_guidance.py` now grades that the values FLOW (each input reaches the script under some name, the result reaches `riskScore`, an Error row when written is the platform envelope) and accepts either spelling.
`patterns/` and `_shared/check_*.py` in the sibling repo UiPath/flow-builder-sdk vendor these graders byte for byte; change them there in the same PR.

**What is still open.** `flow-v2-preview.yaml`'s `extra_mounts` binds the repo root read-only, so the v1 skill tree stays *readable* from inside the preview container even though the working-directory copy is gone.
Invariant 3 is what keeps that from mattering: nothing points an agent at it, so nothing finds it.
Removing that mount is a separate change — plugin discovery depends on it.

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
