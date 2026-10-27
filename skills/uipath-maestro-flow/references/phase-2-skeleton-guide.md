# Phase 2 — Skeleton

Author a skeleton of labelled boxes and real control flow, show it to the user,
and stop for their approval. It makes **no registry or library calls**.

**Draft mode only.** Draft mode stops afterwards and asks the user to agree the
shape (phase 3); phase 4 then replaces each box with its real node. Auto mode
skips 2b–2f and phase 3 and authors real nodes directly. Brownfield edits and
discovery-only tasks skip this phase too.

Phases: 0 surface (nothing to do yet; surface detection is future work),
1 preflight, 2 skeleton, 3 iterate until the user approves, 4 wire up.
In plan mode, writes wait for plan approval: put the skeleton outline (boxes,
branches, conditions) in the plan, then run 2a–2f once the plan-mode approval comes.

## What a skeleton is

A skeleton exists so the shape can be read end to end, so a user can say "yes,
that's it" or "drop that step". It is not a working flow and must never be
reported as one.

1. **Every activity is a labelled `mock()` box.** Name it action first, then
   the intended node family in brackets:
   `.step('classifyTicket', mock(), { label: 'Classify ticket [Agent]' })`.
   It compiles to `core.logic.mock`, the box the canvas's own patterns insert.
   Here `mock()` is a draft box, not the capability gap
   [`placeholder.md`](placeholder.md) describes; phase 4 replaces every one.
2. **Make no registry or library calls.** No `uip maestro registry` or
   `uip maestro flow registry` command, no `connector()`, `http()`, agent,
   `script()` or `prepare`. Node types are not being chosen yet. In draft mode
   phase 1 is the solution scan and `init` only: the node choice in
   [SKILL.md — Project layout](../SKILL.md#project-layout) and the search in
   [`author.md`](author.md) rule 12 belong to phase 4.
3. **Control flow is real.** The trigger, `.branch`, `.switch`, `.parallel`,
   `.loop` and the end are what the user approves. A manual, scheduled or form
   start needs no lookup; for a connector event start, use a manual start and
   label the first box `<event> [Trigger]`. Arms that finish the same way fall
   through to one shared end unless the request names separate outcomes.
4. **Label every arm with its outcome**: `.label('approve')` on a branch arm,
   `label: 'High'` on a switch case.
5. **Route on an input or a `.var()`, never on a box.** A condition that reads
   `out(<mock step>)` fails with `MOCK_HAS_NO_OUTPUT`. Declare the value
   as an input or a var and read it; name the producer in the upstream label,
   `Classify ticket [Agent] → category`.
6. **Declare the inputs the request names; leave outputs to phase 4.** A
   declared output must be bound on every path, and a skeleton has nothing to
   bind it to.
7. **Ask nothing about the flow before the sketch.** The phase 1 solution
   choice ([`author.md`](author.md) rule 10) still asks. A structure question (a threshold, an
   unnamed branch) becomes a visible assumption in the shape and waits for
   the 3c question.

## Steps

Phases 0 and 1 run first, and 2a has scaffolded the project
([SKILL.md — Project layout](../SKILL.md#project-layout)). Then:

- **2b Author the skeleton** into the `.flow-sdk/<Name>.flow.ts` that
  `init --sdk-source` seeded, keeping its flow id and name.
- **2c–2e Run the [Lifecycle](../SKILL.md#lifecycle) loop** you picked:
  `check` where the loop allows it, `compile -o`, `validate`, then `format`.
  A skeleton checks, compiles and validates with zero warnings (measured on
  18 CI draft runs), so treat any warning or error as real and fix it without
  adding a real node.
- **2f Show it.** When the request allows an upload and you are logged in, run
  `uip solution resources refresh --solution-folder <SolutionDir> --output json`
  and `uip solution upload <SolutionDir> --output json`; 3c shows the returned
  `Data.DesignerUrl`. Do not ask first: a draft request is the consent rule 9
  in [`author.md`](author.md) asks for, because draft mode exists to show the shape.
  Confirm only when this run did not create the solution. When the request
  forbids upload, skip it.

## Iterating

- **3a Edit the skeleton** from the user's feedback, then re-run 2c–2e.
- **3b Show the change** the same way as 2f. Repeat 3a–3b.
- **3c Ask before building.** Reply in this shape, dropping lines that do not
  apply; the question is fixed and becomes a pick list if the host has one:

  ```text
  <Name>: outline ready<, uploaded>.
  <DesignerUrl as a link on its own line, or the local .flow path>

  - <each box, in order>

  Is this the flow you want?
  1. **Build it**: make every step work.
  2. **Change it**: tell me what to add, remove, or move.
  3. **Keep it**: stop here with this outline.
  ```

  *Build it* goes to phase 4. *Change it* goes back to 3a. *Keep it* ends the
  run with the skeleton reported as an outline. Headless, or when no answer
  comes, this is *Keep it*: no option is recommended, so rule 9 stops here.
  Never pick *Build it* yourself. Say which mode ran
  in the final report.

Only *Build it* authorizes phase 4: node search, connectors, `prepare` and
outputs. Phase 4 replaces each `mock()` box in place, keeping its step name,
drops the `[Type]` suffix from the label, and finishes with
[`author.md` — Completion output](author.md#completion-output). Until then the
skeleton is an outline, and calling it a finished flow misreports it.
