# Phase 2 — Skeleton

Author a skeleton of blank boxes, arrows and labels, upload it, and reach a link
the user can open in about two minutes — it makes **no registry calls**.

**Both draft and auto mode run this phase.** Draft mode stops afterwards and
asks the user to agree the shape (phase 3); auto mode continues straight into
phase 4 and pastes real payloads into these same boxes. Building the structure
first means a template error is never tangled up with a structural one. Skip
this phase only for a brownfield edit (the shape already exists) or a
discovery-only task (nothing is authored).

## What a skeleton is

A skeleton exists so the shape can be read end to end — so a user can say "yes,
that's it" or "drop that step", and so phase 4 has a validated structure to fill
in. It is not a working process and must never be reported as one.

1. **Every activity is a bare `<bpmn:task>`** carrying only an `id` and a
   `name`. No `uipath:activity`, no `uipath:event`, no payloads, no resource
   identities, no connections.
2. **Do not use `serviceTask` or `sendTask`.** They render with their own icons
   (a gear, an envelope), which makes a box look like a decided product choice
   and pulls review toward "is this the right element?" instead of "should this
   step exist?". Uniform blank boxes are the point.
3. **Make no registry calls.** No `registry pull`, `list`, `search`, or `get`.
   Element types are not being chosen yet.
4. **Control flow is real.** Genuine `bpmn:startEvent`, `bpmn:exclusiveGateway`,
   `bpmn:sequenceFlow`s, and a single `bpmn:endEvent` that every branch
   converges on. Branch structure *is* the shape being approved, so it is not
   simplified.
5. **Label each box with the action first and the intended element family last,
   in brackets** — `Classify ticket [Agent]`, `Notify approvals team [Slack]`,
   `Prepare ticket summary [Script]`. The label carries all the meaning a blank
   box cannot, so it is load-bearing rather than decorative.
6. **Name each branch flow** with the outcome it carries (`approve`, `reject`,
   `escalate`) via the flow's `name` attribute, so the routing reads off the
   picture.
7. **Declare variables and gateway conditions for real.** The basis a gateway
   routes on is part of what the user is approving — three branches out of a
   diamond with no stated basis could mean anything. See
   [Gateways cost more than boxes](#gateways-cost-more-than-boxes).

Element families come from the bundled catalog, not the registry: the
login-free table in
[registry-workflow.md](registry-workflow.md#ootb-extension-types-29-login-free)
and the `label` field of each entry in `validator/bpmn-spec.json`. Those labels
distinguish the families a user's wording leaves ambiguous — "Start and wait for
RPA workflow" versus "Start and wait for agent" versus "Start and wait for
agentic process" versus "Start and wait for external agent". Family is enough
for a label; the specific type, its template and its resource are resolved later.

## Gateways cost more than boxes

Boxes are free. A gateway is not, and the three costs always arrive together:

1. An exclusive gateway needs `default="<flow id>"` on the gateway and a
   `conditionExpression` on **every other** outgoing flow, or validation fails
   `MISSING_CONDITION_EXPRESSION`.
2. A condition referencing a variable needs that variable declared in the
   process's `<uipath:variables>` block, or validation fails
   `VARIABLE_DOES_NOT_EXIST`:
   `<uipath:inputOutput id="Classification" name="Classification" type="string" elementId="Process_1" />`
3. A `conditionExpression` uses `xsi:type="bpmn:tFormalExpression"`, and older
   `init` scaffolds do not declare that namespace. Add
   `xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"` to
   `bpmn:definitions` before writing any `xsi:type`, or the file is not
   well-formed XML and fails at parse with
   `XML_NOT_WELL_FORMED: Unbound namespace prefix: "xsi"`.

A skeleton can express **reads but not writes**. The gateway reads the variable
through its conditions, which is plain structural BPMN. What *assigns* the
variable is a `uipath:output` mapping inside a node's registry payload, which a
skeleton deliberately does not have. So the producer is implied by position — the
box upstream of the gateway is understood to be what will assign it. Naming it
in the label helps: `Classify ticket [Agent] → Classification`.

## Expected findings — do not chase them

A skeleton validates as **Valid** with warnings, and those warnings are correct
for a skeleton. Fix nothing that appears here:

- `Variable "vars.<id>" is read but never assigned; it will be empty at run
  time` — one, at process level.
- `VARIABLE_NOT_SET: Variable '<name>' is not set at this point in the flow` —
  one per conditioned branch flow. These read like errors and are not.

Treat a skeleton as validating cleanly when there are **zero errors**. Act only on
error-severity findings, and only when they block import.

## Steps

Phase 1 (preflight) runs first — see [SKILL.md](../SKILL.md#workflow). Then:

1. **Author the skeleton** into the `.bpmn` that `init` generated, editing in
   place. Preserve the generated start event's `id`, its
   `<uipath:entryPointId>`, and the four generated JSON files. **Do not rename
   the start event**: its name feeds the entry-point schema, so renaming it
   makes `refresh` rewrite `entry-points.json` for no benefit.
2. **`uip maestro bpmn format <file>.bpmn`** — generates the diagram. Without
   it no box renders on the canvas (Rule 5). Re-run it after each batch of edits
   while the user is watching.
3. **`uip maestro bpmn validate <file>.bpmn --output json`** — must reach
   `Status: Valid`. This is an import-readiness check, not a design review:
   act on errors, ignore the expected warnings above.
4. **`uip maestro bpmn refresh <project-path> --output json`** — run it from the
   solution directory. `refresh` validates internally and refuses to write
   anything while validation fails, so step 3 must pass first. On a skeleton that
   preserved the start event it reports `WrittenFiles: []`, which is the
   drift check passing rather than a no-op to skip.
5. **Make the shape visible.** Every surface except a bare terminal edits a
   local workspace behind a live canvas, so `format` in step 2 already put the
   change on screen and there is nothing to do here. In a bare terminal, run
   `uip solution upload <SolutionDir> --output json` and report the returned
   `Data.DesignerUrl`. Do not ask first: a request to build the process
   authorizes the upload that shows it, and a consent gate per iteration would
   defeat the mode. The one case that still needs confirmation is adopting a
   solution the agent did not create, because `upload` overwrites the cloud
   solution matching the local `.uipx` SolutionId. Confirm that when phase 1
   picks an existing solution, not here.

## Iterating

Adjust the skeleton, re-`format`, show the change, repeat. On a live canvas the
refresh is automatic. In a bare terminal, each upload after the first reports
`Data.Action: "Overwritten"` and reuses the same `SolutionId` and
`DesignerUrl`, because `upload` writes the cloud solution id back into the local
`.uipx`. `"Imported"` on a later upload means that id was lost and a second
cloud solution was just created — stop and fix that before continuing.

Removing a box is the common edit: delete the task, delete its two sequence
flows, add one replacement flow, then `format`. Since entry points are
untouched, `refresh` stays a no-op.

In draft mode the loop ends at an explicit approval gate, and that approval is
what authorizes phase 4 — registry pull, element disambiguation, live
connections, and payloads pasted into the existing boxes. Until then the
skeleton is an unapproved draft, and saying otherwise misreports it. In auto
mode there is no gate and no iteration: phase 2 hands straight to phase 4.
