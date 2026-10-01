# Structural BPMN: round-trip and editing

## Do not generate for new authoring (preserve on round-trip only)

These structures are **not** authored for new Maestro BPMN. If they appear in an
imported or brownfield file, preserve them and report that the skill cannot
safely regenerate or normalize them. Planned / preview / TBD statuses count as
unsupported for generation until current tooling confirms them.

- Gateway: `bpmn:complexGateway`.
- Tasks / containers: `bpmn:manualTask`, `bpmn:adHocSubProcess`,
  `bpmn:transaction`.
- Event definitions: `conditionalEventDefinition`, `signalEventDefinition`,
  `escalationEventDefinition`, `compensateEventDefinition`,
  `cancelEventDefinition`, `linkEventDefinition`, multiple, and
  parallel-multiple event definitions.
- Markers: standard-loop and compensation markers (use only documented
  multi-instance parallel/sequential metadata for new loops).
- Terminate is supported **only** on end events — not on start, boundary,
  intermediate-catch, or intermediate-throw events.
- Preserve-only `uipath:*` extension payloads: keep these when imported, and when
  a file legitimately needs one, reproduce the shape (with synthetic, public-safe
  contents) rather than inventing a new one.
  - **Typed activity/event shells always use the lowercase `<uipath:activity>` /
    `<uipath:event>` wrapper with a `<uipath:type value="<Type>" version="v1" />`
    child** — including types not served by the live registry (e.g.
    `Maestro.CasePlanScheduler`, `Maestro.CaseManagerGuardrails`,
    `Maestro.CaseRulesEvaluator`). Do **not** substitute the capital-`A`
    `<uipath:Activity>` element for a typed shell.
  - The capital-`A` `<uipath:Activity>` element is a **separate** generic
    preserve-only payload (its own element, not a wrapper for typed shells). If
    a prompt asks for a generic unsupported `uipath:Activity`, preserve that
    exact capitalized tag, for example:
    `<uipath:Activity version="v1"><uipath:type value="uipath:Activity" version="v1" /></uipath:Activity>`.
    Do not encode it as lowercase `<uipath:activity>` with
    `<uipath:type value="uipath:Activity" />`; that misses the preserve-only
    payload shape.
  - `uipath:caseManagement` is a versioned body-string element —
    `<uipath:caseManagement version="v1">…synthetic payload…</uipath:caseManagement>`.
    If a prompt asks for case-management contract variants, preserve-only
    case-management payloads, or case-plan/case-management wrappers, include an
    actual lowercase `uipath:caseManagement` element with synthetic content. A
    typed `Orchestrator.StartCaseMgmtProcess*` activity shell is not the same
    payload and does not satisfy that preserve-only case-management shape.
  - Preserve existing `uipath:scriptVersion` markers. For a new ScriptTask, use
    the marker supplied by the selected live or compatibility template.

## Editing operations

Safe, surgical edits on an existing `.bpmn` (preserve content you did not author
— see [SKILL.md](../SKILL.md#editing-an-existing-bpmn-preserve-what-you-did-not-author)):

- **Add / delete / reconnect a node**: add the element with a stable id and its
  `<bpmn:incoming>`/`<bpmn:outgoing>` refs, add the sequence-flow elements in the
  owning scope. On delete, remove orphaned flows and recheck entry-point variables,
  output mappings, and binding references. Then regenerate the diagram:
  `uip maestro bpmn format <file.bpmn>`. If CLI unavailable: add/update `BPMNShape`
  and edge waypoints manually.
- **Insert a gateway**: split the existing sequence flow into an incoming and an
  outgoing flow, add conditions to the outgoing flows plus one `default`, add a
  matching join only if branches actually need synchronization. Then regenerate the
  diagram: `uip maestro bpmn format <file.bpmn>`. If CLI unavailable: re-waypoint
  manually (gateway shape + all edges).
- **Move logic into a subprocess**: move only elements that share a valid scope,
  re-scope their variables, and recreate legal subprocess flow boundaries. Then
  regenerate the diagram: `uip maestro bpmn format <file.bpmn>` — it emits one
  shape per nested node in the single root plane. Do not hand-author a second
  plane; the next `format` run replaces it.
- **Add an entry point**: use a root-level start event and generate a stable,
  unique UUID for its serializer-owned `uipath:entryPointId`. Do not copy the
  example UUID; this scaffold field is not a registry-owned node payload. Also
  declare the public variables it needs: each `uipath:input`'s `elementId` must
  match that start event, and each `uipath:output`'s must match a root end
  event. The two mismatches fail differently: an unmatched input is dropped
  silently, leaving an empty `input` schema, while an unmatched output fails
  the project with `Process output "<name>" must target a root end event.`
  Bridge both sides as [Variables](structural-bpmn-variables.md#variables) prescribes.

Do not patch generated JSON to fix source behavior — change the `.bpmn` and
regenerate. For `Intsvc.*` activities/triggers, hand editing to CLI enrichment.

### Edit red-flags

Re-check after any edit:

- A diagram plane references a missing process, collaboration, or subprocess.
- A rendered element lacks a shape or its flow lacks an edge/waypoint.
- An entry-point variable points at the wrong start event.
- A `uipath:context` value references a missing binding.
- A topology edit rewrote unrelated `uipath:*` extension XML.
- An Integration Service element carries hand-authored connection details.
