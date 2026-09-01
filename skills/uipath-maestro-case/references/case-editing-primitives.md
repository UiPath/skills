# Case Editing — Primitive Operations

<!-- Split out of case-editing-operations.md so each part can be read whole. Foundations, validation cadence, anti-patterns and the operation->plugin quick reference are in [case-editing-operations.md](case-editing-operations.md); the multi-step recipes are in [case-editing-composites.md](case-editing-composites.md). -->

> **Prerequisite:** the ID-generation algorithm, `id-map.json` contract, expression prefixes and pre-flight checklist in [case-editing-operations.md](case-editing-operations.md) apply to every operation below.

## Primitive Operations

### Tool usage — mandatory

All mutations to `caseplan.json` (and sibling files like `entry-points.json`, `id-map.json`) MUST go through Claude's built-in tools only:

- **Read** to load the file.
- **Edit** for narrowly-scoped, unambiguous in-place replacements — default for all mutations after T01, and required for sections with <10 T-entries.
- **Write** (whole-file) for exactly two things: the T01 scaffold (initial empty-file creation by the `case` plugin) and the Step 7 stage skeleton. Never for a populated `caseplan.json`.
- **Edit — or a single-hunk `apply_patch` on a harness with no `Edit` tool** — for every mutation after the skeleton. See § Skeleton-then-Edit for the tool table.

**Do NOT** shell out to `python`, `node`, `jq`, `sed`, `awk`, or any other process to read, parse, transform, or write the JSON. No helper scripts, no inline one-liners that modify files, no `python3 -c '... json.load ... json.dump ...'`, no `node -e "...fs.writeFileSync...".` The agent holds the parsed object in its own reasoning; the file system is touched only via Read/Write/Edit.

This is a hard constraint — it keeps every mutation reviewable in the tool-call transcript and prevents silent state changes the user cannot audit.

**Anti-patterns that count as file mutation (forbidden — write the file via the Write/Edit tool instead):**

- `node -e "const fs=require('fs'); ... fs.writeFileSync(...)"` — the `node -e` permission is for stdout-only helpers, not file I/O.
- `node -e "..."` / `python -c "..."` / `jq '...' caseplan.json` followed by `> caseplan.json`, `>> caseplan.json`, or `| tee caseplan.json` — shell redirection onto a skill artifact is mutation, regardless of which interpreter ran.
- `cat caseplan.json | jq '...'` even if you only "intend to print" — `jq` is forbidden; use Read.
- `sed -i` / `awk -i inplace` / `python -c "open('caseplan.json','w')..."` — same family, all forbidden.
- `bash -c "...>caseplan.json..."` — wrapping the redirection in another shell does not exempt it.

Pseudocode blocks in this document and in per-plugin `impl-json.md` files (`issues.append(...)`, `existingTriggers = schema.nodes.filter(...)`, etc.) are **specifications of intent**, not commands to execute. Read them, apply the logic in-head, then use Read/Write/Edit to realize the mutation.

**Bash is still used for**: UUID v4 generation only (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId`; subprocess MUST NOT `require('fs')`, `require('child_process')`, or use any redirection operator), `uip solution init` / `uip solution projects add` / `uip solution upload`, `uip maestro case validate`, `uip maestro case debug`, `uip maestro case registry` discovery, and read-only metadata fetches (`uip maestro case tasks describe`, `is resources describe`, `is triggers describe`). Never for file mutation.

**Prefixed IDs (`Stage_`, `t`, `Rule_`, `Condition_`, `trigger_`, `c`, `r`, `b`, `sla_`, `esc_`, `StickyNote_`) are picked inline by the agent — no subprocess.** See § ID Generation algorithm above.

### Per-section batch write contract — canonical

`caseplan.json` mutations follow a **per-section batched Edit** contract. The unit is one `tasks.md` section (e.g., §4.4 stages, §4.6 task-shapes, §4.7 conditions, §4.8 SLA), not one T-entry.

Procedure per section:

1. **One Read** of `caseplan.json` at section entry — authoritative state.
2. **N Edits in sequence, one per T-entry** — regardless of how many T-entries the section holds. Edit targets the smallest unambiguous slice of JSON the T-entry mutates (one node, one array field, one task's `data.inputs`). There is no large-section branch: a section with 40 T-entries is 40 Edits, not one big write. See § Skeleton-then-Edit for why.
3. **Skip the re-Read between sibling Edits** — Edit's tool result confirms applied state in context; explicit re-Read is redundant for in-memory correctness.
4. **One `validate`** at section boundary (Pre-flight Item 12 above).
5. **Repair preservation.** Repair a validation error with a targeted Edit on the node or binding the error names — never by rewriting the file. If the error location is unclear, re-Read `caseplan.json` first and locate it, then Edit. A repair may not remove or replace unrelated topology, bindings, or a resolved task merely to make `validate` pass.

**Same-file sequential Edits — anchoring.** N Edits against `caseplan.json` in one section serialize in order; each later Edit runs against the text the earlier ones already changed. `caseplan.json` has keys that recur across nodes (`"tasks"`, `"data"`, `"entryConditions"`, `"exitConditions"`, `"inputs"`) — a bare recurring key is NOT a safe anchor.

- **Anchor each Edit on a unique value** — the target stage/task's `"id": "<Stage_… | t…>"` — then extend `old_string` to the slice you mutate. Never anchor on a bare `"tasks": [` or `"entryConditions": [`.
- **Extend until the match is unique within the whole file**, not just within the intended node.
- An `old_string` that overlaps text a prior Edit in the same turn removed or shifted fails with "string not found" — order Edits so each targets an untouched slice, or re-Read if a later Edit depends on an earlier one's output.

### Skeleton-then-Edit — the only cadence for `caseplan.json`

`caseplan.json` is written by **exactly two Writes, then Edits for everything else**:

1. **Write 1 — T01 scaffold.** The empty case shell created by the `case` plugin.
2. **Write 2 — stage skeleton (Step 7).** All stage nodes with their `id`, `data.label`, and empty containers: `data.tasks: []`, empty condition arrays, `layout: {}`, `schema.edges: []`. No tasks, no conditions, no SLA, no bindings. For a large case this is a few KB.
3. **Every mutation after that is an Edit.** Tasks append into their stage's `data.tasks`, anchored on that stage's unique `"id": "Stage_…"`. Conditions, SLA, connector `caseShape`, and I/O values are all Edits against the node they belong to.

**Which tool — "Edit" means a targeted patch, not a tool name.** Harnesses differ, and this contract is about the *size of the change you emit*, never about which tool emits it. Use whichever your harness actually has:

| Your harness has | Emit the change as |
|---|---|
| An `Edit` tool | One `old_string` / `new_string` pair covering the smallest unambiguous slice. |
| Only a patch tool (`apply_patch`, `Write` taking a patch) and **no `Edit`** | A **single-hunk patch touching only the target node's lines**. This is the compliant way to do it from a patch-based harness — it is not a workaround. |
| Only whole-file write, no patch form at all | Say so in the completion report and keep sections as small as possible. This is the rare case; check for a patch tool first. |

**A patch whose hunk spans the whole file is a whole-file Write wearing a patch costume** — it costs the same output tokens and carries the same field-drop risk, so it is forbidden on the same terms. What matters is that the emitted bytes are proportional to the change.

**Never emit a whole-file Write of a populated `caseplan.json`.** Not to add a section, not to "get it all consistent", not to repair a validate error, and not because the file is now large. Once the skeleton exists, the file only grows by Edit.

**Why.** A whole-file Write costs output tokens proportional to the *entire file*, while an Edit costs tokens proportional to the *change*. A populated case plan reaches 90–120KB — one whole-file Write is 23–30K output tokens, which on a lower-output-budget harness is most or all of what the agent can emit for the whole run. Agents that hit that wall do not fail loudly; they offload composition to a `python`/`node` heredoc and paste the result through Write, which violates Rule 13 while looking compliant in the transcript. The skeleton-then-Edit cadence removes the incentive: no single write ever has to carry the whole file, so the generator shortcut has nothing to solve.

The correctness argument points the same way. Write rebuilds the file from agent reasoning and silently drops fields the agent forgot; Edit preserves untouched fields structurally. The 12-item Pre-flight Checklist exists because field drops have happened.

**Repairs are Edits too.** When `validate` reports an error, Edit the specific node or binding it names. Re-Read first if the error location is unclear. Never rewrite the file to fix one field.

**Status text bundling.** Any progress text the agent emits before a section's first Edit/Write MUST share the same assistant turn as the tool_use (text block + tool_use block in one content array). Standalone text-only turns between Edits are forbidden — they each cost ~5s inference latency + full prompt cache replay for no work. Cap inline status to ≤1 sentence / ~20 tokens. Per-T-entry audit lives in TaskUpdate, NOT in narration.

**Planning monologues forbidden.** Pre-Write/pre-Edit text turns that announce intent ("Caveman push:", "Approach:", "Strategy:", "Big single Write:", "Writing full caseplan.json structurally", "Now I'll batch all stages") are forbidden, whether bundled or standalone. The tool call itself IS the announcement — TaskUpdate carries the T-by-T narrative, the Edit/Write tool input is self-describing. If the status text the agent wants to emit exceeds one short sentence, the correct action is to cut it, not to bundle it. Multi-paragraph status text is always a violation.

**Hard token cap on any single text block.** Outside the allow-list below, no text block may exceed **200 tokens**. Inside the allow-list, no text block may exceed **500 tokens**, ever. A text block >200 tokens outside the allow-list, or >500 inside it, is by definition a planning monologue regardless of content or framing. Allow-list (and only this list): the once-per-run kickoff flow overview, hard-stop AskUserQuestion preambles, Phase 5/6 completion reports, `Publish for review` DesignerUrl print, post-validate result summaries.

**Forbidden announcement verbs.** Text blocks (bundled or standalone) starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Next step:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call are FORBIDDEN regardless of length. Restating the upcoming tool_use in prose is pure cost. Allowed exceptions remain: the once-per-run kickoff flow overview, AskUserQuestion preambles, completion reports (Phase 5/6 exit), `Publish for review` DesignerUrl print, and post-validate result summaries (`N errors, M warnings — fixing X` is fine; `Composing fix for ...` is not).

**Audit trail via TaskUpdate.** Reviewers see T-by-T progress in the todo log, not in the file diff. Each plugin seeds TaskCreate items keyed by T-number; mark each `in_progress` before composing the entry's mutation in reasoning, `completed` after the Edit/Write returns success. The transcript shows one or N writes per section — what changes is the dropped re-Read between siblings and the dropped standalone narration turns.

**CLI-gated sections — gather-then-write.** Where each T-entry needs its own CLI call before its JSON shape is known (Phase 2 §4.6 non-connector `tasks describe`; Phase 3 §9.7 connector `case spec`): run all CLI calls first, collect results in reasoning, then enter the Read → N-Edits → validate batch.

**Recovery.** On any mid-batch interruption (Edit failure, context compact, abort): re-Read `caseplan.json` + `tasks.md`, scan for next un-applied T-entry, resume from there. No sidecar checkpoint file. For CLI-gated sections, re-run the CLI calls for un-applied entries — typically cheap.

**Scope.** This contract applies to **`caseplan.json`**. `tasks.md` (Phase 1) and `registry-resolved.json` follow the mirror section-batched contract in [planning.md §4.0a](planning.md) — same one-Read-per-section + N-Edit-appends shape, with markdown Edit-append as the primitive (no whole-section Write needed; markdown appends are cheap regardless of count).

**Whole-file Write outside T01.** Permitted only for the Step 7 stage skeleton. Forbidden everywhere else, at every size — see § Skeleton-then-Edit.

**No size threshold changes the cadence.** Because every post-skeleton mutation is an Edit, output cost scales with the change rather than the file, and there is no case size at which a bigger write becomes necessary or a helper script becomes justified. Phase 2 Edits in root, nodes, variables, task shapes, SLA/escalations, and conditions (connector-backed rules use the canonical stub); Phase 3 Edits connector context/input/output and other task values, then upgrades resolved connector-rule stubs.

**Forbidden: build-assembler helper scripts.** Writing `/tmp/build-caseplan.js`, `/tmp/gen-tasks.py`, or any script that assembles a skill artifact and pipes/writes it to disk is a Rule 13 violation — regardless of `/tmp` placement, "mechanical copy" framing, or "avoid Read+Write churn" rationale. The script-write + script-run + script-output-to-file pattern bypasses the tool-call audit trail Rule 13 protects. If the artifact is too large for a single Write turn, apply the ~15K-token Write cap and Phase 2 → Phase 3 split above. There is no helper-script escape hatch.

### Generate a fresh ID

**Inline — no subprocess.** Per § ID Generation § Algorithm above. Pick chars in-head following the constraints (mixed case + digits, no sequential, no dictionary words), scan existing IDs in the just-Read `caseplan.json` for collisions, embed via Write/Edit.

Examples — agent picks these directly when writing JSON:

```
Stage_  + "kQ7mNt"  → "Stage_kQ7mNt"
t       + "8GQTYo8O" → "t8GQTYo8O"
Rule_   + "jdBFrJ"  → "Rule_jdBFrJ"
```

> **UUID v4 only** (`operate.json.projectId`, `entry-points.json` `uniqueId`) uses `node -e "console.log(crypto.randomUUID())"` — see § Tool usage. Prefixed-IDs above never call Bash.

### Add a node (Trigger / Stage)

1. Read `caseplan.json`.
2. Determine `data` fields per plugin's JSON Recipe. Do not emit `position`, `style`, `measured`, `width`, `height`, `zIndex` at the node level (Rule 18).
3. Generate a fresh node ID.
4. Append the node to `schema.nodes` (stages use `.unshift()` in the CLI — prepend — but either position works for the frontend; prepend to match CLI output exactly).
5. Edit `caseplan.json` — narrow slice targeting `schema.nodes`. Never whole-file Write.

### Add an edge — RETIRED

Not authored (Rule 20). To make a stage reachable, add a `stage-entry-conditions` rule on the target stage (Step 10), not an edge.

### Add a task to a stage

1. Read `caseplan.json`.
2. Locate the stage node by ID.
3. Ensure `stageNode.data.tasks` exists. Use the task's activation mode and entry rule before honoring lane placement: strict sequential / `runs-sequentially`, adhoc, event-driven, fan-in, conditional-gate, and standalone tasks append as new single-task inner arrays. Reuse an existing `stageNode.data.tasks[laneIndex]` only for tasks explicitly planned as `parallel` or `parallel-after-predecessor` siblings with same-lane intent and rationale.
4. Generate a task ID.
5. Compute `elementId = ${stageId}-${taskId}`.
6. Build the task object per the plugin's JSON Recipe. Do NOT add `entryConditions` here — the task-entry-conditions plugin (Step 10) writes them from the SDD's authored rows, for every task type alike.
7. Push onto `stageNode.data.tasks[laneIndex]` only for explicitly parallel or parallel-after-predecessor siblings; otherwise write `[task]` as its own inner task set. If `laneIndex` conflicts with activation mode, activation mode wins and note the lane correction in the completion report.
8. Edit — narrow slice targeting that stage node's `data.tasks[laneIndex]`. Never whole-file Write.

### Bind an input

Variable bindings live on the task's `data.inputs[<index>]` entries — each input has either a literal/expression `value` or a cross-task source reference (`sourceStage`, `sourceTask`, `sourceOutput`). Modify the input entry in place via Edit — narrow slice targeting that input entry. Never whole-file Write.

Details per plugin — see [bindings-and-expressions.md](bindings-and-expressions.md).

### Delete a node

1. Read `caseplan.json`.
2. Remove the node from `schema.nodes` by ID.
3. **If the deleted node is a stage with successors, repoint them — do NOT skip.** Edges are retired, so a successor reaches only via an entry-condition rule naming the deleted stage in `selectedStageId`. Find every stage whose `data.entryConditions[].rules[][]` has a `selected-stage-completed` / `selected-stage-exited` rule with `selectedStageId == <removedStageId>`, and repoint each to a surviving predecessor (the deleted stage's own predecessor, or `case-entered` if the deleted stage was first). Leaving them unrepointed orphans every successor — the case can validate structurally yet the successors never execute. Inverse of § Insert a stage between two existing stages.
4. `schema.edges` is `[]` (Rule 20) — nothing to remove. Defensive: drop any stray edge referencing the removed node's ID.
5. **If the deleted node is a Trigger, prune its `entry-points.json` entry.** Triggers live in `schema.nodes`, so trigger removal routes here — but every trigger plugin mandates a matching `entry-points.json` entry ([manual/impl-json.md § Recipe — entry-points.json](plugins/triggers/manual/impl-json.md#recipe--entry-pointsjson-append-to-entrypoints), timer, event). Remove the entry whose `filePath` ends in `#<removedTriggerId>` from `entry-points.json.entryPoints`. Leaving it orphans a `#<triggerId>` fragment pointing at a node that no longer exists.
6. **If the deleted node is a Trigger with In-args / trigger outputs, run the variable cascade.** An In-arg emits three entries keyed by the trigger ([global-vars/impl-json.md § In argument](plugins/variables/global-vars/impl-json.md)): the formal slot in `root.inputs[]` (`elementId == <triggerId>`), the companion in `root.inputOutputs[]` (`elementId == "root"`), and the bridge on `triggerNode.data.inputs.outputs[]`. The bridge dies with the node, but the formal slot and companion survive — leaving every `=vars.<name>` consumer reading undefined (`validate` does not catch dangling `=vars.*`). For the deleted trigger:
   - Prune `root.inputs[]` entries with `elementId == <removedTriggerId>`.
   - For each, read its companion's name, then sweep consumers of `=vars.<name>` and prune the `root.inputOutputs[]` companion (`id == <name>`, `elementId == "root"`) when no other producer remains — per § Rename or delete a global variable or argument (Delete path).
   - Step 7's companion-prune below is scoped to connector *rule* outputs (`elementId == "root"`); this trigger branch covers the In-arg companions specifically.
7. If the node was a stage containing a connector task **or a connector condition rule** (in `entryConditions[]` / `exitConditions[]` / task `entryConditions[]`), prune entries from the top-level `bindings` referenced only by that task/rule. A connector rule contributes the same Connection/Folder binding pair as a task — `rule.uipath.context[name="connection"|"folderKey"]` references `=bindings.<bindingId>`. Walk every remaining task/trigger/rule; an entry whose `resourceKey` is no longer referenced anywhere is the one to prune. Case-exit rules are NOT in scope here — they live on root, not inside a node; use § Delete a condition rule for those.
8. If the removed node held connector rule outputs that were bound to case variables (B/C feature), prune their `root.inputOutputs[]` companions. The companion's `elementId` is `"root"` — `<removedStageId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each removed rule output at `elementId = <removedStageId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` that no longer has a producer.
9. Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
10. Edit — separate slices for `schema.nodes`, `entry-points.json` (trigger only), `root.inputs[]` / `inputOutputs[]`, and the bindings array. Never whole-file Write.

### Delete a task

Remove a task from a stage. Tasks live in `stageNode.data.tasks[laneIndex][]` — **never** in `schema.nodes` — so § Delete a node cannot reach them. Deleting a task also dangles every reference to its `TaskId`; sweep them all, then re-pack lanes.

1. Read `caseplan.json`. Locate the task in its owning `stageNode.data.tasks[laneIndex]` and note its `id` (the `TaskId`) and `elementId`.
2. **Remove the task** from `data.tasks[laneIndex]`.
3. **Re-pack task sets.** Removing the only task in an inner `data.tasks` array leaves an empty task set. Drop the empty task set and preserve the remaining task-set order; never infer execution semantics from lane placement.
4. **Prune conditions that reference the dead `TaskId`:**
   - Any task's `entryConditions[].rules[][]` `selected-tasks-completed` rule whose `selectedTasksIds` names the deleted task — remove the id from the array; if it empties, remove the rule (and the parent condition object when it empties), per § Delete a condition rule's DNF removal mechanic.
   - Any `conditionExpression` (`=js:...`) referencing the deleted task's outputs — repoint or remove.
5. **Repoint cross-task bindings that consumed this task's outputs.** Any other task input with `sourceTask == <deletedTaskId>` (and `sourceStage == <ownerStageId>`) now dangles — repoint to a surviving producer or clear the binding. A consumer left bound to a deleted producer reads undefined at runtime; `validate` does not catch it.
6. **Binding cascade — every task type, not just connectors.** Prune the deleted task's top-level `bindings[]` pair once no other task/trigger/rule references it: Connection/Folder for a connector-activity / wait-for-connector task, `name`/`folderPath` for a process / agent / rpa / action / api-workflow / case-management task. Connector tasks additionally prune any `root.inputOutputs[]` companions tied to their rule outputs — same cascade as § Delete a node steps 5–7. Then regenerate `bindings_v2.json` and prune the solution resource the removal orphaned ([bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal)).
7. Update the task's `id-map.json` entry (remove it) if the sidecar is present.
8. Edit — narrow slices for the source `data.tasks` (removal + lane re-pack), each swept condition, each repointed consumer binding, and (connector only) the bindings array / `inputOutputs[]`. Never whole-file Write. Validate at the section boundary.

> **Reverse of § Add a task to a stage.** § Move a task always re-pushes to a destination; § Delete a task is the terminal removal — there is no destination, so the cascade prunes references instead of repointing them to a new stage.

### Delete a condition rule

Remove a single rule from a condition (without deleting the parent stage / task / case-exit). Applies to **any** rule scope — stage entry/exit, task entry, case exit — and to both plain and connector-bound rules. The generic DNF removal (steps 1–3) is all a **plain** rule needs; the binding cascade (steps 4–6) is **connector-only** and a no-op for plain rules.

1. Read `caseplan.json`.
2. Locate the rule by `id`. **FE composes one rule per condition** (OR-style across multiple condition objects), so the target is almost always a condition object that contains exactly this one rule. The underlying shape is DNF (`rules[][]`), so honor it: if other rules share the inner AND-array, remove just the rule; if the rule is the sole entry, remove the entire condition object.
3. Remove the rule (or the parent condition object when it becomes empty). **Plain (non-connector) rules stop here** — skip steps 4–6. **For case-exit completion rules, first run the ≥1-completion-rule guard** in § Delete a case-exit completion rule below.
4. **(Connector rules only)** Walk all remaining tasks/triggers/rules; prune root `bindings[]` entries whose `resourceKey` is no longer referenced.
5. **(Connector rules only)** Prune `root.inputOutputs[]` companions tied to this rule's outputs. The companion's `elementId` is `"root"`; `<ownerNodeId>-<ruleId>` is the rule output entry's `elementId`, not the companion's. For each of this rule's outputs at `elementId = <ownerNodeId>-<ruleId>`, read its `var`, then prune the companion whose `id == <var>` and `elementId == "root"` when its case variable has no other producer.
6. **(Connector rules only)** Regenerate `bindings_v2.json` per [bindings-v2-sync.md § Cleanup on task or rule removal](bindings-v2-sync.md#cleanup-on-task-or-rule-removal).
7. Edit — separate slices for the conditions array, and (connector only) the bindings array and `inputOutputs[]`. Never whole-file Write.

#### Modify a condition rule in place

Change a rule's behavior without removing it — keep the rule `id` so any reference stays valid.

1. Read `caseplan.json`; locate the rule by `id` in its `rules[][]` DNF array.
2. Edit the rule fields in place:
   - **Operator / expression:** rewrite `conditionExpression` (`=js:<expr>`) — use strict `===` / `!==`, parenthesize each sub-clause of a combined boolean ([bindings-and-expressions.md § Canonical form per sink](bindings-and-expressions.md#canonical-form-per-sink)). Re-validate any `=vars.<id>` referenced still type-checks.
   - **`rule` type:** swap the `rule` value (e.g., `selected-stage-completed` ↔ `selected-stage-exited`) and add/drop the side field the new type requires (`selectedStageId`, `selectedTasksIds`). For case-exit, honor the rule-type × `marksCaseComplete` matrix ([case-exit-conditions/impl-json.md](plugins/conditions/case-exit-conditions/impl-json.md#rule-type--markscasecomplete-matrix)).
   - **`marksCaseComplete` (case-exit only):** flipping `true`→`false` may remove the last completion rule — run the ≥1-completion-rule guard in § Delete a case-exit completion rule first.
3. Connector-bound rules: if the connector configuration (`rule.uipath`) changed, re-fetch via `uip maestro case spec` (never hand-author) and re-run the bindings cascade (steps 4–6 above).
4. Edit — narrow slice targeting that rule. Never whole-file Write. Validate at the section boundary.

### Delete a case-exit completion rule

Remove a plain completion / exit rule from `metadata.caseExitRules[]`. **Guard: a case must keep ≥1 rule with `marksCaseComplete: true`** — `validate` rejects an all-`marksCaseComplete:false` case ("Case has no completion rules").

1. Read `caseplan.json`; locate the rule in `metadata.caseExitRules[]`.
2. **Before removing, check the invariant.** If the rule being removed is the only entry with `marksCaseComplete: true`, removing it leaves the case with no completion path. Do NOT silently remove — AskUserQuestion: `Replace it with a different completion rule` / `Keep it` / `Remove anyway (case will fail validation)`. Removing the last completer is almost always a mistake; surfacing it here avoids the After-edits retry thrash (validate would reject it on the next loop).
3. Remove the condition object from `metadata.caseExitRules[]` (DNF removal per § Delete a condition rule steps 2–3). Connector-bound case-exit rules also run the connector cascade (steps 4–6).
4. Edit — narrow slice targeting `metadata.caseExitRules`. Never whole-file Write. Validate at the section boundary.

### Delete an edge — defensive only

The skill never creates edges, so `schema.edges` should already be `[]`. If a stray edge is found (e.g., in an imported file): Read, filter `schema.edges` by the edge ID, Edit the narrow slice. Never whole-file Write.

---

---

**Multi-step recipes:** [case-editing-composites.md](case-editing-composites.md). **Foundations:** [case-editing-operations.md](case-editing-operations.md).

<!-- END: case-editing-primitives.md -->
