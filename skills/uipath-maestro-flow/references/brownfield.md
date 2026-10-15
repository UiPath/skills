# True-brownfield decompile, edit, and merge

Use this procedure when a task supplies a deployed `.flow` and no `.flow.ts`.
Do not hand-transcribe the graph: decompile it to builder source, edit that
source, and merge only the delta back into the original.

## The safe project loop

Keep authored source beside the canonical Flow so relative sidecars still
resolve, but put every compiled working artifact outside the Flow project. The
project must contain exactly one `.flow` file when product validation discovers
it recursively.

```bash
PROJECT=Solution/Deployed
CANONICAL="$PROJECT/Deployed.flow"
WORK=.flow-work/Deployed
mkdir -p "$WORK"

uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/baseline.flow"
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/edited.flow"
uip maestro flow merge "$CANONICAL" "$WORK/edited.flow" \
  -o "$WORK/candidate.flow" --baseline "$WORK/baseline.flow"

uip maestro flow validate "$WORK/candidate.flow" --output json
cp "$WORK/candidate.flow" "$CANONICAL"
uip maestro flow validate "$CANONICAL" --output json
```

Replace the canonical artifact only after the candidate validates. Do not copy
`baseline.flow`, `edited.flow`, or `candidate.flow` into the project, and do not
leave an earlier `*.merged.flow` there: the project validator treats every
`.flow` below the project directory as a deliverable.

## The generated pipeline

`decompile` writes `<Name>.pipeline.mjs` into the `.flow-sdk/` work directory
beside the source. Prefer it for any narrow edit: it chains all four steps below,
and it captures the baseline before your edit rather than after, which is the
ordering mistake that forces a rebuild.

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts
node .flow-sdk/Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
node .flow-sdk/Deployed.pipeline.mjs    # compiles the edit, merges into .flow-sdk/Deployed.merged.flow
```

Re-running it after further edits repeats only the compile and merge — the
baseline is captured once and reused. Pass `--no-pipeline` to `decompile` when
you deliberately want the manual sequence instead. The pipeline writes its
`.flow` artifacts into that `.flow-sdk/` directory; use it only when the
directory is outside the canonical Flow project, because product validation
treats every `.flow` below the project, hidden folders included, as a
deliverable. When source must remain in the
project for relative sidecars, use the safe project loop above.

## The same loop by hand

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts --no-pipeline
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/Deployed.baseline.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/Deployed.edited.flow
uip maestro flow merge Deployed.flow .flow-sdk/Deployed.edited.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/Deployed.baseline.flow
```

Like the pipeline, this keeps every candidate in `.flow-sdk/`; validate
`.flow-sdk/Deployed.merged.flow`, then replace the original with it.

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
way. When the canvas or the CLI named the node or its resource directory
differently from what compile derives, the decompiled entry carries `nodeId`
and `source` (and a context index its canvas `label`):

```ts
context: [{ name: "Example SOP Index", id: "11111111-2222-4333-8444-555555555555",
  folderPath: "Shared/Example", label: "SOP lookup",
  nodeId: "ctx_7f2a1b", source: "d84e2c17-6a3f-4c59-b0e2-7f1a9c5b3d28" }]
```

Leave these as they are. Removing them makes compile name the node
`<agent>Context` with a new directory, so merge drops the original node and adds
a different one. Do not add them to a resource you create.

A node type the SDK has no factory for still round-trips: it comes back as
`rawNode({ nodeType, version, manifest, inputs })`, carrying the definition the
file supplied, so the node keeps its type, its version and its inputs. Leave it
alone unless the task asks you to change it — and if you do, edit its `inputs`,
not the hoisted `…Definition` const, which is the platform's own manifest.

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
- Pass `--strict` to make merge refuse (exit 1, no file written) instead of
  warning. The benign End line never refuses. `--strict` needs `--baseline`,
  so use it in [the hand loop](#the-same-loop-by-hand); the generated
  pipeline does not pass it. If `uip maestro flow merge` rejects `--strict`,
  your CLI does not forward it yet; run the same merge through the globally
  installed SDK's `flow-sdk` bin instead:

  ```bash
  flow-sdk flow merge .flow-sdk/Deployed.edited.flow --original Deployed.flow \
    -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/Deployed.baseline.flow --strict
  ```

## The file's schema version comes back out

`decompile` emits `.schemaVersion("<the file's version>")` as the first line of
the chain, so the recompile declares the version the file had — not the SDK's
own floor. Most deployed flows are `1.8`; the writable band is `1.6`–`1.10`.
Leave that call alone unless you mean to retarget the document, and note that
`check` warns either way off the `1.9` floor (`SCHEMA_VERSION_ABOVE_FLOOR`: a
reader pinned lower refuses the file; `SCHEMA_VERSION_BELOW_FLOOR`: every reader
migrates it forward on open). Changing versions is `uip maestro flow migrate`'s
job, not an edit to this call.

These findings the source cannot carry are printed on stderr as
`flow-decompile: warning: …`, and `--strict` turns each into an error:

- A node **no trigger reaches** — no edge leads to it, as when a designer or
  `node add` left it unconnected. The builder has no detached-node construct,
  so the source omits it and marks the spot with `// TODO: node "<id>" … is not
  reachable`; recompiling drops that node. If it is your edit target, connect
  it in the `.flow` first or edit that node's JSON directly.
- A `(type, typeVersion)` **this SDK does not bundle**, for a type it bundles
  at other versions — for example `uipath.human-in-the-loop.quick-form@1.6`
  (written by `node add`) when the SDK ships `1.0` and `1.1`. Versions resolve
  exactly, so the source **omits** that `{ version }` and the node compiles at
  the SDK's default. `merge --baseline` keeps the node at the file's version,
  with the file's definition, as long as you leave it untouched; a node you
  edit moves to the SDK's version. If it is your edit target, edit that
  node's JSON in the `.flow` directly, or tell the user the edit moves it from
  the file's version (here `1.6`) to the SDK's default. A type the SDK bundles
  at no version (a connector, a published process or agent) keeps its pin.
  A pin like that written back by hand is still refused by `compile`, which
  names the bundled versions; for a registered family `check` reports it first
  as `NODE_VERSION_UNREGISTERED`.
- A **file-format version outside the writable band** (below `1.6`) — the source
  omits the `.schemaVersion()` call, marks the spot with a `// TODO:` line, and
  recompiling writes `1.9`. Migrate the file first, or keep the original and
  merge into it: `merge` preserves the original's declared version.
- An **edge the builder cannot spell** — for example a second edge leaving a
  decision's `true` port, which no builder construct produces. The
  warning names it as `<source>@<port> -> <target>@<port>`, and the source marks
  the spot with a `/* TODO: edge(s) … are NOT in this source */` comment (or a
  `// TODO: edge …` line near the top when no step leads to it). Recompiling
  drops that edge, and `merge` writes the loss into the original. If your edit
  touches that part of the flow, change the `.flow` JSON there directly instead
  of round-tripping it through the source.
- A **switch whose cases carry their own conditions** — for example `High:
  amount > 100` and `Low: amount <= 100`. `.switch(name, on, cases)` models
  only `on === value`, so the decompiled `on` and `value`s are placeholders
  (with a `/* TODO: this switch's case expressions are not a uniform … */`
  comment). Recompiling fails or picks a different case, even when your edit is
  somewhere else in the flow, so make the change in the `.flow` JSON directly.

Validate `Deployed.merged.flow`, not the intermediate edited compile. Before
placing it in a solution, copy it over the canonical artifact rather than next
to it, then validate the canonical project path again.

Do not run `uip maestro flow format` on the merged file; it discards the author's layout.

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
