# True-brownfield decompile, edit, and merge

Use this procedure to edit a `.flow` that already exists, unless the task
supplied its `.flow.ts`. A `.flow.ts` an earlier turn left is not supplied: the
canvas may have changed the `.flow` since.

<!--skill-flavor:fresh-decompile-cleanup:start-->
Decompile fresh, after removing an earlier turn's pipeline artifacts
([The generated pipeline](#the-generated-pipeline)).

<!--skill-flavor:fresh-decompile-cleanup:end-->
Do not hand-transcribe the graph: decompile it to builder source, edit that
source, and merge only the delta back into the original.

An edit that adds one of the [patterns](author.md#patterns) (a review gate,
triage, a batch loop, a chat or voice front door, a panel of agents) reads that
pattern's guide first and inserts only the part the flow lacks, as its "Adapting
it" says. Inserting a pattern is still a narrow edit through this loop.

A pattern the canvas inserted arrives unfinished: `core.logic.mock` steps
labelled "(replace with …)", agent prompts that start `PLACEHOLDER -`, and a
sticky note listing the setup. Finishing it means replacing each mock with the
real node (rule 1 in [author.md](author.md)), rewriting each placeholder prompt
for the request, and doing what the note lists. A note item the builder cannot
do (such as attaching a tool to a voice agent) goes under Open questions. Keep
every other step, port and name the pattern inserted.

## The safe project loop

<!--skill-flavor:safe-project-loop:start-->
Keep authored source beside the canonical Flow so relative sidecars still
resolve, but put every compiled working artifact outside the Flow project. The
project must contain exactly one `.flow` file when product validation discovers
it recursively.

```bash
PROJECT=Solution/Deployed
CANONICAL="$PROJECT/Deployed.flow"
WORK=.flow-work/Deployed
rm -rf "${WORK:?}" && mkdir -p "$WORK/baseline" "$WORK/edited" "$WORK/candidate"

uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/baseline/Deployed.flow"
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
# Leave added steps out of .layout(...): merge places them (builder-sdk#1320).
# Check against the original until no (edited) error is left:
uip maestro flow check "$PROJECT/Deployed.flow.ts" --source --baseline "$CANONICAL"
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/edited/Deployed.flow"
uip maestro flow merge "$WORK/edited/Deployed.flow" --original "$CANONICAL" \
  -o "$WORK/candidate/Deployed.flow" --baseline "$WORK/baseline/Deployed.flow"

BACKUP=$(mktemp -d) && echo "backup: $BACKUP" && cp -r "$PROJECT/." "$BACKUP/"
cp -r "$WORK/candidate/." "$PROJECT/"
# Then delete each directory merge listed as `flow-merge: remove <dir> ...`.
uip maestro flow validate "$CANONICAL" --output json && rm -rf "${BACKUP:?}"
```

Install the candidate whole with `cp`. Never write or patch the `.flow`
yourself, and never copy only your change into the original. Merge renumbers
every edge (`edge_0`, `edge_1`, ...), may reorder nodes, and adds default
fields: that is its normal output, not drift to undo. The changes to act on
are the [merge warnings](#merge-warnings-what-the-round-trip-changed).

Validate in the project, not `candidate/` alone: it holds only the agent files
merge changed, so an unchanged inline agent's `agent.json` is missing there
([builder-sdk#1318](https://github.com/UiPath/builder-sdk/issues/1318)).
If validate fails, restore the project before merging again:
`test -d "${BACKUP:?}" && rm -rf "${PROJECT:?}" && mkdir "$PROJECT" && cp -r "$BACKUP/." "$PROJECT/" && rm -rf "$BACKUP"`.
Keep the backup in `mktemp -d`, never under the working directory: a copy of
the project there is a second Flow project.
<!--skill-flavor:safe-project-loop:end-->

Compile the baseline before the edit, never after: merge diffs edited against
it, so a baseline of the edited source drops your change.

With an edited `.flow.ts` and `--baseline-from`, `merge` runs `check` on the edited source and refuses the write on an error in a node or subflow the edit changed (`N error(s) in nodes merge takes from the edited flow`), and on one it cannot place that the edit introduced.
An error on a node, or in a subflow, the edit did not touch prints as `DRAFT_NODE_KEPT` and the original is kept; an untouched node the SDK cannot compile at all is kept as saved too and prints as `LOWERING_NODE_KEPT` (a probable SDK defect: tell the user; 6.62.0 or later); a finding `merge` cannot place on a node prints as `CHECK_FINDING_UNPLACED` when the original's own round trip reports it too.
Fix a finding when you edit its node.
Needs `@uipath/maestro-builder-sdk` 6.44.4 or later; an older SDK refuses the write for any error it cannot place on an untouched root node,
<!--skill-flavor:merge-check-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:merge-check-sdk-upgrade:end-->

Do not copy the `baseline/` or `edited/` directories into the project, and do
not leave an earlier `*.merged.flow` there: the project validator treats every
`.flow` below the project directory as a deliverable.

### Check only what you changed: `check --baseline`

`compile` does not run `check`: it writes any flow it can serialize. So run
`check` before every `compile`, and treat its errors as the gate. In a
brownfield edit, pass the original `.flow` (not a compiled baseline) as
`--baseline`, and each finding says whether your edit caused it:

```
$ uip maestro flow check "$PROJECT/Deployed.flow.ts" --source --baseline "$CANONICAL"
✗ [UNKNOWN_REF] Reference to undeclared variable/step "lookup" in "report". (edited)
⚠ [HTTP_READ_WITHOUT_RETURNS] ... (pre-existing, not counted)
⚠ [CONNECTOR_INPUT] Connector step "notify": ... unknown input "designerOnly". ... (pre-existing)
  This node is unchanged from the baseline, so this is probably an SDK defect: ...

1 error(s) in edited nodes, 1 pre-existing SDK defect(s), 1 pre-existing warning(s)
```

- **`(edited)`** (JSON `origin: "edited"`): fix it. It includes a node you did
  not touch that your edit broke, like `report` above, which reads the
  `lookup` step the edit deleted. The exit code is 1 only while one is left.
- **`(pre-existing, not counted)`**: the canvas already had it. Leave it unless
  the user asked you to fix it. For example, a deployed HTTP node with no body
  schema gives `HTTP_READ_WITHOUT_RETURNS`
  ([builder-sdk#1319](https://github.com/UiPath/builder-sdk/issues/1319)).
<!--skill-flavor:check-baseline-lowering:start-->
- **`(pre-existing)` worded as a probable SDK defect** (JSON
  `class: "lowering"`): `compile` refuses that node, so both compiles of the
  loop above stop on it. When the baseline compile stops on a canvas node, run
  this check before you edit to tell this case apart. Do not edit the node to
  get around it. Write the edit back with [`merge --baseline-from`](#flows-with-draft-nodes-let-merge-compile),
  which keeps the node as saved (`LOWERING_NODE_KEPT`), and tell the user it is
  a probable SDK defect to report at
  <https://github.com/UiPath/builder-sdk/issues>.
<!--skill-flavor:check-baseline-lowering:end-->
- **`CHECK_INCOMPLETE`**: check stopped at a refusal that covers the whole flow
  (for instance two Ends whose names give one node id), so the rest was not
  judged. Fix that refusal first, even if the canvas had it, then check again.

Needs `@uipath/maestro-builder-sdk` 6.62.0 or later (it compiles without
linting and reads `--baseline`); with an older SDK, `uip` refuses `--baseline`
as below its minimum version,
<!--skill-flavor:check-baseline-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:check-baseline-sdk-upgrade:end-->

### Why three directories: inline agents

An inline agent is two files: the node in the `.flow`, and its prompts, model
and run settings in `<source>/agent.json` beside it. An edit to a prompt
changes only that file. Each compile writes `<source>/agent.json` next to its
own output, and merge compares the baseline's copy with the edited copy, applies
only your change to the project's `agent.json`, and writes the result next to
the candidate:

```
flow-merge: wrote Deployed.flow (12 nodes, 13 edges)
flow-merge: wrote <source-uuid>/agent.json (carries messages[0].content)
```

<!--skill-flavor:install-agent-files:start-->
`cp -r "$WORK/candidate/."` installs the `.flow` and every agent file merge
carried. Fields the round trip does not reproduce (such as `maxIterations`, or a
`description` on an agent input) keep the project's values.
<!--skill-flavor:install-agent-files:end-->

Merge warns, does not carry, and refuses under `--strict` when:

- the baseline and the edited flow are in ONE directory. The second compile
  overwrote the baseline's `agent.json`, so merge cannot tell your edit from the
  round trip's own changes (`the edited <source>/agent.json differs from the
  original's ... The change is NOT carried`). Use separate directories.
- the edit changes or removes an agent resource that merge cannot pair with
  one of the project's: the canvas gave the resource node an id compile does
  not reproduce, and its `resource.json` has fields compile does not write.
  Make that change on the canvas.
- the agent node carries its prompts on the node itself (older canvas saves).
  The edited `agent.json` would not be what runs. Make that change on the canvas.

Never copy `$WORK/edited/<source>/` into the project by hand: it carries the
round trip's changes along with yours.

### Agent resources: added, changed, removed

An agent's context index or tool lives in
`<source>/resources/<dir>/resource.json`.

```
flow-merge: wrote <source-uuid>/resources/<new-dir>/resource.json (carries added resource)
flow-merge: wrote <source-uuid>/resources/<dir>/resource.json (carries settings.resultCount)
flow-merge: remove <project>/<source-uuid>/resources/<dir> from the project: the edit removed this agent resource, and copying the candidate cannot delete it
flow-merge: wrote bindings_v2.json (the changed agents' resource rows, re-derived as compile does)
```

<!--skill-flavor:resource-install:start-->
- An added or changed resource is installed by `cp -r`. A changed one keeps its
  original directory.
- A removed one is not: delete every directory merge lists under `remove`
  (`Data.Removed` in `--output json`). Otherwise the agent keeps that resource.
<!--skill-flavor:resource-install:end-->
- A resource another `.flow` in the project still uses is kept
  (`flow-merge: kept <source>/resources/<dir>: <Other>.flow still references it`).
  No action needed: do not delete it.
- In a Flow project, merge also writes `bindings_v2.json` with the changed
  agent's rows re-derived, so a removed index is no longer declared.

## Flows with draft nodes: let merge compile

<!--skill-flavor:draft-nodes:start-->
A canvas-saved flow often holds **draft** nodes: a connector with no connection
yet, a required input left empty, or a generic operation with no object picked
(connector action steps only; a draft trigger, `waitForEvent` or connector tool
still refuses and must be finished first). Decompile carries the definition
of each draft the canvas saved, so `compile` writes it with a warning
(`⚠ [CONNECTOR_INPUT_MISSING] ... Written as a draft`) and the loops on this
page get past it. Three cases still stop `compile`, and with it the pipeline
and the by-hand loop below: a generic operation with no object
(`CONNECTOR_OBJECT_REQUIRED`), a draft you wrote yourself (no carried
definition), and an untouched node the SDK cannot compile (`check --baseline`
prints it as a probable SDK defect). For those, hand the edited **source** to
`merge` instead, and let it build the baseline from the original itself:

```bash
rm -rf "${WORK:?}" && mkdir -p "$WORK/candidate"
uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
flow-sdk flow merge "$PROJECT/Deployed.flow.ts" --original "$CANONICAL" \
  --baseline-from "$CANONICAL" -o "$WORK/candidate/Deployed.flow"
```

Set `PROJECT`, `CANONICAL` and `WORK`, then validate and replace, as in the
loop above.

- `--baseline-from <original.flow>` builds the baseline in memory; skip the
  baseline compile. A `.flow.ts` edited input is compiled by merge too. Both
  compiles tolerate draft nodes. Needs `@uipath/maestro-builder-sdk` 6.28.0 or
  later; an older `flow-sdk` answers `unknown option '--baseline-from'`, so
  upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
- A draft node you did **not** touch is restored exactly as saved, with
  `[DRAFT_NODE_KEPT]` on stderr. So is a draft inside a subflow the edit did
  not change: merge keeps that subflow from the original (6.44.4 or later; an
  older SDK takes every subflow from the edited source and refuses the draft).
- A draft node you **changed** gets the refusal a normal compile gives
  (`[BINDING_MISSING]`, `[CONNECTOR_INPUT_MISSING]` or
  `[CONNECTOR_OBJECT_REQUIRED]`) and nothing is written. Finish that node or
  revert the edit.
- An untouched node the SDK cannot compile is kept exactly as saved, with
  `⚠ [LOWERING_NODE_KEPT] "<node>" is untouched, so the original node is kept
  as is, but the SDK cannot compile it (<CODE>)` on stderr. Tell the user it is
  a probable SDK defect and that it should be filed at
  <https://github.com/UiPath/builder-sdk/issues>. The same refusal on a node the
  edit changed is `✗ [<CODE>] "<node>" is changed or new` and nothing is
  written: revert the edit to that node, or fix it. An untouched node that
  fails only because of an edit elsewhere (it reads a step the edit deleted)
  also stops the write. Needs `@uipath/maestro-builder-sdk` 6.62.0 or later.
- Pass `--library` / `--bindings` as you would to `compile`; `--strict` works
  here too. Use the SDK's `flow-sdk` bin: `uip maestro flow merge` does not
  forward `--baseline-from` yet (UiPath/cli#5214).
<!--skill-flavor:draft-nodes:end-->

## The generated pipeline

<!--skill-flavor:generated-pipeline:start-->
`decompile` writes `<Name>.pipeline.mjs` into the `.flow-sdk/` work directory
beside the source. Prefer it for any narrow edit: it chains all four steps below,
and it captures the baseline before your edit rather than after, which is the
ordering mistake that forces a rebuild.

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts
node .flow-sdk/Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
node .flow-sdk/Deployed.pipeline.mjs --strict   # compiles the edit, merges into .flow-sdk/Deployed.merged.flow
```

The pipeline's compiles do not run `check`, so run
[`check --baseline`](#check-only-what-you-changed-check---baseline) yourself
before the second run, until no `(edited)` error is left.
`--strict` goes to the merge step: merge refuses (exit 1, no file written)
instead of warning when the no-edit round trip changed something you did not
author (see [Merge warnings](#merge-warnings-what-the-round-trip-changed)).
The Node stack trace after `flow-merge: refused (--strict)` is expected; read
the refusal above it. Leave `--strict` off to get the warnings and a merged
file. A pipeline written by an SDK older than this option ignores `--strict`
silently: if `grep -q STRICT .flow-sdk/Deployed.pipeline.mjs` fails, use the
hand loop below with `merge --strict`.

Re-running it after further edits repeats only the compile and merge — the
baseline is captured once and reused. A later turn is not a further edit: before
its fresh decompile, remove the earlier turn's artifacts and agent sidecars:
`[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name 'Deployed.baseline' -o -name 'Deployed.edited' -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +`.
Pass `--no-pipeline` to `decompile` when
you deliberately want the manual sequence instead. The pipeline writes its
`.flow` artifacts into that `.flow-sdk/` directory (the baseline and the edited
compile each in a directory of their own, for the agent reason above), and the
agent files merge carries next to `Deployed.merged.flow`; use it only when the
directory is outside the canonical Flow project, because product validation
treats every `.flow` below the project, hidden folders included, as a
deliverable. When source must remain in the
project for relative sidecars, use the safe project loop above.
<!--skill-flavor:generated-pipeline:end-->

## A supplied source

<!--skill-flavor:supplied-source:start-->
When the task supplied `.flow-sdk/Deployed.flow.ts`, do not decompile: it
overwrites that source. Compile its baseline before the edit, then merge:

```bash
[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +
mkdir -p .flow-sdk/baseline .flow-sdk/edited
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/baseline/Deployed.flow --no-check
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/edited/Deployed.flow
uip maestro flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow
```

Install `.flow-sdk/Deployed.merged.flow` as [the same loop by hand](#the-same-loop-by-hand) says.
<!--skill-flavor:supplied-source:end-->

## The same loop by hand

<!--skill-flavor:hand-loop:start-->
```bash
[ ! -d .flow-sdk ] || find .flow-sdk -maxdepth 1 \( -name baseline -o -name edited -o -name 'Deployed.merged.flow' -o -name '????????-????-????-????-????????????' \) -exec rm -rf {} +
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts --no-pipeline
mkdir -p .flow-sdk/baseline .flow-sdk/edited
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/baseline/Deployed.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow check .flow-sdk/Deployed.flow.ts --source --baseline Deployed.flow
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/edited/Deployed.flow
uip maestro flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow
```

Like the pipeline, this keeps every candidate in `.flow-sdk/`. Back up the
project, replace the original with `.flow-sdk/Deployed.merged.flow`, copy every
`<source>/` file merge reports writing, then validate the original, as in
[the safe project loop](#the-safe-project-loop).
<!--skill-flavor:hand-loop:end-->

The baseline must be compiled from the pristine decompiled source, before any
edit. It lets merge distinguish authored changes from reconstructed content;
without it, merge falls back to taking the compiled graph wholesale, including
layout.

Decompile reconstructs branch, switch, loop, parallel, error/ref, and
subflow structure. It preserves original node ids so merge can reattach them.
Every family the SDK can AUTHOR is reconstructed through its own factory —
including human tasks, agents and their attached resources, the published
resource families, queue items, the AI patterns, document steps, conversational
and voice steps, and connector event subscriptions. A recovered agent keeps its
`source` uuid, so its `agent.json` sidecar still resolves.

An agent's context index, tool or escalation node keeps its identity the same
way. A decompiled resource entry may carry `nodeId` (the resource node's id),
`source` (its `resources/<source>/` directory) or `label` (a context index's
canvas label):

```ts
context: [{ name: "Example SOP Index", id: "11111111-2222-4333-8444-555555555555",
  folderPath: "Shared/Example", label: "SOP lookup",
  nodeId: "ctx_7f2a1b", source: "d84e2c17-6a3f-4c59-b0e2-7f1a9c5b3d28" }]
```

Leave these as they are. Removing them makes compile name the node
`<agent>Context` / `Tool` / `Escalation` (with `2`, `3`, ... for more than one)
with a new directory, so merge drops the original node and adds a different
one. Do not add them to a resource you create, including one copied from a
decompiled entry. `check` reports `INLINE_AGENT_RESOURCE_NODE_ID` for a blank
`nodeId` or one another node has (or that compile derives for another
resource), `INLINE_AGENT_RESOURCE_SOURCE_NOT_GUID` for a `source` that is not a
uuid, and `INLINE_AGENT_RESOURCE_SOURCE_DUP` for two resources on one agent
with the same `source`: both would write one `resource.json`. Delete both
`nodeId` and `source` from a copied entry.
Needs `@uipath/maestro-builder-sdk`
6.33.0 or later; an older SDK's decompile omits these fields and compile renames
the node with a new directory,
<!--skill-flavor:resource-ids-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:resource-ids-sdk-upgrade:end-->

A step's node id is its name with every character other than a letter, digit
or `_` turned into `_` (`a b` gets id `a_b`), and compile never renames a step
to make it unique. A new step whose name a step in the same flow already has
is refused by `check` and by `compile`: `DUP_STEP` for the same name,
`STEP_ID_COLLISION` for a name that gives the same id (`a b` vs `a_b`) or that
equals the trigger's id. Give the new step a name of its own. (A child flow's
steps are not checked against the caller's: a copy whose ids are taken is
prefixed `<caller>_<step>`.) To send a
second path to an existing step, end that path with `.stepToRef('<name>')`
instead of adding the step again.
Needs `@uipath/maestro-builder-sdk` 6.32.4 or
later; an older SDK silently renames the second step `<name>2`,
<!--skill-flavor:dup-step-sdk-upgrade:start-->
so upgrade with
`npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:dup-step-sdk-upgrade:end-->

A node type the SDK has no factory for still round-trips: it comes back as
`rawNode({ nodeType, version, manifest, inputs })`, carrying the definition the
file supplied, so the node keeps its type, its version and its inputs. Leave it
alone unless the task asks you to change it — and if you do, edit its `inputs`,
not the hoisted `…Definition` const, which is the platform's own manifest.
When that definition declares several exits and every one is wired (for
example `core.logic.agentic-switch`: one `case-<id>` exit per choice in
`inputs.criteria`, plus `default`), the node comes back as
`.stepSwitch('<id>', rawNode(…), [{ value: 'case-returns', body: … }, …])`:
one arm per exit, each arm's `value` being its port. Adding or removing a
choice in `inputs.criteria` adds or removes its `case-<id>` exit: change the
arms to match. When only some exits are wired, it comes back as
`.step('<id>', rawNode(…))` whose main path continues on the definition's main
port (`default` for an agentic switch), with each other wired exit as
`.stepToList('case-<id>', …)`; an unwired exit stays unwired.

`mock()` in decompiled source therefore means the flow really contains a
placeholder node (`core.logic.mock`). The one case that still degrades is a node
whose definition is MISSING from the file — nothing can carry it, so it lowers
to `mock() /* TODO: unsupported node type … */`; leave that node untouched and
merge restores the original.

## Merge warnings: what the round trip changed

Merge prints `flow-merge: warning: …` for each change the merged file gets
although you did not make it. With `--baseline` it also compares the baseline
(the round trip with no edit) with the original. For example:

```
flow-merge: warning: the round trip rewires logFailure1@success from forEachItem1@continue to callApi1ErrorEnd@input; merge will write the new target.
flow-merge: warning: the merged edge route1@case-case_1 -> review1@input leaves handle "case-case_1", which node "route1" (core.logic.switch) does not declare …
```

- Each warning names a change you did not author: a node or edge added,
  dropped or rewired, a node's type changed, a switch case id or human-task
  outcome id renamed, or a binding row added, dropped or duplicated. If the
  spot is one you did not mean to change, do not copy the candidate over the
  canonical file; fix the `.flow.ts` there and merge again. A warning about a
  merged edge's handle means `validate` will refuse the candidate.
- `the round trip appends End "<id>" after …` is the one benign line: compile
  adds an End where the original path just stops. It does not change behaviour.
  A flow decompiled with `.openTails()` gets this line only after a human
  task that ends a path; see
  [A path without an End stays open](#a-path-without-an-end-stays-open).
- `agent "<id>" carries its prompts, model and settings on the node (embedded) …`
  means that agent keeps its configuration in the `.flow`, not in
  `<source>/agent.json` (some canvas and `node add` saves do this). Merge keeps
  that configuration and applies only your change to the node: an input, an
  output, the label. A prompt, model or settings edit in the `.flow.ts` does
  not reach an embedded agent; make it on the canvas. `--strict` accepts an
  input or output edit, and refuses a merged node that drops or changes that
  configuration, or whose kept prompt still uses `{{input.X}}` after your edit
  removed input `X`.
<!--skill-flavor:strict-merge:start-->
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. `--strict` needs `--baseline`:
  run `node .flow-sdk/<Name>.pipeline.mjs --strict`, which always has one, or
  add it to the merge in [the hand loop](#the-same-loop-by-hand). If
  `uip maestro flow merge` rejects `--strict`, or the pipeline exits 2 with
  `--strict was asked for, but …`,
  your CLI does not forward it yet; run the same merge through the globally
  installed SDK's `flow-sdk` bin instead:

  ```bash
  flow-sdk flow merge .flow-sdk/edited/Deployed.flow --original Deployed.flow \
    -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow --strict
  ```
<!--skill-flavor:strict-merge:end-->

## Scripts come back as functions

`decompile` prints each script step as a TypeScript function, declared after the flow and passed by name:

```ts
  .step("normalize", script(script_normalize, { returns: { amount: "number" } }), { version: "1.0.0" })
  // …
function script_normalize($vars: FlowVars) {
  const amount = Number($vars.start.output.amount);
  return { amount };
}
```

Edit the script in the function's body; the text between its braces is exactly the node's script, so an untouched script compiles back byte for byte.
The rules in [script.md](script.md#writing-the-script-as-a-function) apply to the edit: the function may read only what the script runtime has.

A script that cannot be printed as a function stays `script({ code: "…" })`, and decompile warns once for each: `flow-decompile: warning: step "<id>": script kept as a string: <why>`.
The reasons are a body that does not parse (a half-written designer script), TypeScript-only syntax, a name that is not on the SDK's list of runtime names, a trailing line comment, or an error that would stop the module from loading.
The warning is informational: the string form loses nothing, and `--strict` does not turn it into an error.
Edit such a script as a string, as before.
To print every script that way, pass `--scripts string`: `uip maestro flow decompile <file> -o <file>.flow.ts --scripts string`. With an SDK older than 6.57.0, `uip` refuses the option and names the version to install.

Needs `@uipath/maestro-builder-sdk` 6.57.0 or later (its `dist/api-index.md` lists `ScriptValue`); an older SDK's decompile prints every script as `script({ code })`.

## The file's schema version comes back out

`decompile` emits `.schemaVersion("<the file's version>")` as the first line of
the chain, so the recompile declares the version the file had — not the SDK's
own floor. Most deployed flows are `1.8`; the writable band is `1.6`–`1.10`.
Leave that call alone unless you mean to retarget the document, and note that
`check` warns either way off the `1.9` floor (`SCHEMA_VERSION_ABOVE_FLOOR`: a
reader pinned lower refuses the file; `SCHEMA_VERSION_BELOW_FLOOR`: every reader
migrates it forward on open). Changing versions is `uip maestro flow migrate`'s
job, not an edit to this call.

## Designer shapes decompile keeps

Leave each as decompile writes it.
Needs `@uipath/maestro-builder-sdk` 6.44.0 or later: an older SDK's decompile writes `js\`[object Object]\`` for the envelope, drops the fork's arms and the `variable` rows with a `has no spelling` / `cannot write back` warning, and compile then refuses the source
<!--skill-flavor:envelope-sdk-upgrade:start-->
— upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:envelope-sdk-upgrade:end-->

- a decision or switch condition stored as a `jsExpression` envelope or as `=js: …`
- a quick form's asked-field `variable` ([hitl.md](hitl.md))
- `{ fork }`, arms that end in `.stepToRef`, and a pass-through merge as `rawNode` ([parallel-merge.md](parallel-merge.md))
- a `core.logic.loop@1.0` on its `output` / `loopBack` handles, through the definition the file carries
- a subflow's reads of its own Start node as `input('<name>')`, and the `.onError()` on the subflow step

These findings the source cannot carry are printed on stderr as
`flow-decompile: warning: …`, and `--strict` turns each into an error. Edit the
`.flow` JSON directly only when decompile printed one of these warnings and
its case below says to; every other edit goes through merge.

- A node **no trigger reaches** — no edge leads to it, as when a designer or
  `node add` left it unconnected. The builder has no detached-node construct,
  so the source omits it and marks the spot with `// TODO: node "<id>" … is not
  reachable`; recompiling drops that node. If it is your edit target, connect
  it in the `.flow` first or edit that node's JSON directly.
- A `(type, typeVersion)` **this SDK does not bundle**, for a type it bundles
  at other versions, **and the file holds no definition for it**. Versions
  resolve exactly, so the source **omits** that `{ version }` and the node
  compiles at the SDK's default. `merge --baseline` keeps an untouched node at
  the file's version; a node you edit moves to the SDK's version, and merge
  warns `node "<id>" moved <type>@<old> -> <new>`. If it is your edit target,
  edit that node's JSON in the `.flow` directly, or tell the user the edit
  moves it to the SDK's default. A type the SDK bundles at no version (a
  connector, a published process or agent) keeps its pin.

  When the file *does* hold the definition (the normal case: every `.flow`
  carries one per node type and version it uses), the node does not move.
  Decompile copies that definition into a `const`, passes it to
  `.definitions([...])`, and keeps the pin; compile resolves the pin against
  it. For example `uipath.human-in-the-loop.quick-form@1.6`, written by
  `node add`, when the SDK ships `1.0` and `1.1`:

  ```ts
  const quickFormV1_6Definition = { nodeType: "uipath.human-in-the-loop.quick-form", version: "1.6", ... };
  export default flow("review")
    .definitions([quickFormV1_6Definition])
    .step("review1", hitl({ ... }), { version: "1.6" })
  ```

  The node keeps `1.6` even when you edit it. Leave the `const` and the
  `.definitions([...])` call as decompile wrote them: without them, `compile`
  refuses the pin and names the versions it can resolve (for a registered
  family, `check` reports it first as `NODE_VERSION_UNREGISTERED`). The SDK
  still writes an edited node's inputs from its own factory (`hitl()` here).
  When the carried definition's inputs differ from that factory's version,
  decompile warns `node "<id>" keeps <type>@<version> from the file's
  definitions[]; its inputs differ from <sdk-version> (<fields>)`. If that
  node is your edit target, edit its inputs in the merged `.flow` JSON
  directly. `rawNode` is not a substitute here: it cannot yet route a human
  task's outcome exits.
- A **file-format version outside the writable band** (below `1.6`) — the source
  omits the `.schemaVersion()` call, marks the spot with a `// TODO:` line, and
  recompiling writes `1.9`. Migrate the file first, or keep the original and
  merge into it: `merge` preserves the original's declared version.
- An **edge the builder cannot spell** — for example two edges out of one
  port where one path stops on a step with no successor and no End. Other
  fan-outs do come back as a `.parallel`, see
  [parallel-merge.md](parallel-merge.md):
  - paths that meet again at a plain step: each arm ends in
    `.stepToRef(<step>)` (SDK 6.44.0 or later);
  - paths that each end at an End or a Terminate: the arms all end, and the
    fork is named `<node>Fork` after the node it leaves (SDK 6.46.6 or later).

  Two shapes of the second kind still get the TODO below: an arm that runs a
  step before its Terminate (`check` allows a Terminate only at an arm's head,
  `TERMINATE_NOT_ARM_HEAD`), and a fan-out inside a loop body whose arms leave
  by `.break()` or `.continue()`. A fan-out decompile cannot spell keeps its
  first arm behind a `/* TODO: unstructured fan-out … */` marker.

  The warning names each dropped edge as `<source>@<port> -> <target>@<port>`,
  and the source marks the spot with a
  `/* TODO: edge(s) … are NOT in this source */` comment (or a
  `// TODO: edge …` line near the top when no step leads to it). Recompiling
  drops that edge, and `merge` writes the loss into the original. If your edit
  touches that part of the flow, change the `.flow` JSON there directly instead
  of round-tripping it through the source.
- A **context-index setting `context: [...]` cannot express**. Decompile reads
  an index's retrieval settings (mode, query, threshold, result count, file
  extension) from `<agent source>/resources/<source>/resource.json`, so keep the
  agent's folder beside the `.flow`. A few settings have no field, for example
  a static plain-text query, a query bound to an agent argument, deeprag
  citations turned off, or a folder-path prefix. The warning names the setting,
  and recompiling writes the SDK's value into the compiled
  `resources/<source>/resource.json` beside the `-o` output. Merge does not
  touch the project's copy: do not copy the compiled file over it. If that
  already happened, tell the user to set the setting again in Studio Web.
- A **fire-and-forget process start's output schema**. The designer keeps the
  process's output fields on the definition whether or not the step waits, and
  `agenticProcess()` refuses `returns` beside `completion: 'fire-and-forget'`
  (nothing could read it), so the source omits it and the warning names the
  fields.
  Needs `@uipath/maestro-builder-sdk` 6.44.0 or later; an older SDK's
  decompile writes `returns` and compile refuses it
<!--skill-flavor:fire-and-forget-sdk-upgrade:start-->
  — upgrade with
  `npm install -g @uipath/maestro-builder-sdk@latest`.
<!--skill-flavor:fire-and-forget-sdk-upgrade:end-->
  Recompiling writes the definition without the schema; `merge` keeps
  the original's definition row, so a no-edit round trip loses nothing. To read
  the result, set `completion: 'wait'` and declare `returns`.

Pin a step you add with a `{ version }` the source gives other nodes of its
type, one that decompile did not warn about. If it warned about all of them,
leave it unpinned. If no node keeps the file's version, merge drops its
definition with no warning. An End also needs a fresh name: see
[A path without an End stays open](#a-path-without-an-end-stays-open).

Validate the merged file after installing it as in
[the safe project loop](#the-safe-project-loop), never the intermediate edited
compile.

Do not run `uip maestro flow format` on the merged file; it discards the author's layout.

Decompiled source carries that layout as a `.layout({ nodes })` block, one long-hand entry per node.
Keep it.
Only an added step's entry lands: a step the edit adds has none, so compile places it on its placeholder row and `merge` moves it next to its neighbours; to choose the spot yourself, add `<step>: at(x, y)` beside the neighbouring entries (`import { at } from '@uipath/maestro-builder-sdk'`), avoiding any x where (x − 256) is a multiple of 288 on y = 144 or 304, which `merge` reads as a compile placeholder and moves; a container the edit grows can still push that spot aside, so keep where it lands.
At the root, an existing node's position and size come from the original whatever the source says, except that `merge` shifts later nodes and grows a container to fit added steps; moving or resizing one in the source does nothing, so for any other change set `layout.nodes.<id>.position` or `.size` in the merged `.flow` instead, and only when the file has no `layout.nodes` map, the node's `ui`.
Inside a subflow the source's entries land only when the edit changed that subflow: `merge` then takes the subflow from the edited compile whole, and otherwise keeps the original subflow as it was (6.44.4 or later; an older SDK takes every subflow from the edited compile,
<!--skill-flavor:subflow-layout-sdk-upgrade:start-->
so upgrade with `npm install -g @uipath/maestro-builder-sdk@latest`).
<!--skill-flavor:subflow-layout-sdk-upgrade:end-->
A step the edit removes must lose its entry, or compile fails on the unknown key.
Grid and rules: [`operate.md`](operate.md#lay-out-from-source-instead-layout-at-dim).

## A path without an End stays open

A flow built in the designer or with `uip maestro flow node add` often ends on
a step with no End node after it. `decompile` emits `.openTails()` near the
top of every chain it writes: the root `flow(...)` chain and each subflow
child's chain. With it, a path that runs out of steps compiles with no End
node, as in the original. Leave the call alone. Removing it makes compile add
an End to every open path in that flow; a subflow child has its own call.

When you add a step after an open tail, the new step becomes the tail and is
left open too. To make that path return the flow's outputs, end it with
`.return({ ... })`. An open path maps no outputs. A human task's exit is
always capped with an End, because a task with nothing after it never
finishes.

Give an End you add a name no node uses and, when the source has Ends, their
`{ version }`: `.return({ ... }, { name: 'endSummary', version: '<END_VERSION>' })`.
An added `name: 'end'` takes the id of an existing End decompile wrote without
a name, which becomes `end2` with no warning.

## Split (`$ref`) artifacts

A deployed `.flow` may be SPLIT across sibling files with JSON Reference —
`"definitions": { "$ref": "./definitions.json" }`, or the same for layout or an
extracted subflow. Decompile resolves those into one model as it reads the file:
point it at the main file and nothing else is needed. Do NOT inline the sidecar
by hand first, and do not edit either file to "prepare" it — the recovered source
is identical either way.

Only relative paths resolve. An absolute path, a Windows drive letter, a
protocol URI (`https://…`, `file:///…`) or a traversal above the referencing
file's root is refused by design: a `.flow` is untrusted input, and the
alternative is a way to read arbitrary files. A same-document pointer
(`{"$ref": "#/definitions/…"}`) is left alone — those are legitimate internal
JSON-Schema pointers, not file references. A missing or unreadable target is an
error naming the file, not a silent gap.

Compile always writes ONE file. Write-through splitting is deliberately not
supported: nothing in the designer or the skills splits files today, so there is
no producer to round-trip against. Expect the recompiled artifact to carry the
sidecar's content inline, and no `$ref` — that is correct, not drift.
