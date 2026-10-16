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
mkdir -p "$WORK/baseline" "$WORK/edited" "$WORK/candidate"

uip maestro flow decompile "$CANONICAL" -o "$PROJECT/Deployed.flow.ts" --no-pipeline
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/baseline/Deployed.flow"
# Edit $PROJECT/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile "$PROJECT/Deployed.flow.ts" -o "$WORK/edited/Deployed.flow"
uip maestro flow merge "$CANONICAL" "$WORK/edited/Deployed.flow" \
  -o "$WORK/candidate/Deployed.flow" --baseline "$WORK/baseline/Deployed.flow"

uip maestro flow validate "$WORK/candidate/Deployed.flow" --output json
cp -r "$WORK/candidate/." "$PROJECT/"
uip maestro flow validate "$CANONICAL" --output json
```

Replace the canonical artifact only after the candidate validates. Do not copy
the `baseline/` or `edited/` directories into the project, and do not leave an
earlier `*.merged.flow` there: the project validator treats every `.flow` below
the project directory as a deliverable.

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

`cp -r "$WORK/candidate/."` installs the `.flow` and every agent file merge
carried. Fields the round trip does not reproduce (such as `maxIterations`, or a
`description` on an agent input) keep the project's values.

Merge warns, does not carry, and refuses under `--strict` when:

- the baseline and the edited flow are in ONE directory. The second compile
  overwrote the baseline's `agent.json`, so merge cannot tell your edit from the
  round trip's own changes (`the edited <source>/agent.json differs from the
  original's ... The change is NOT carried`). Use separate directories.
- the edit adds or removes an agent's resource (a context index or a tool).
  Make that change on the canvas.
- the agent node carries its prompts on the node itself (older canvas saves).
  The edited `agent.json` would not be what runs. Make that change on the canvas.

Never copy `$WORK/edited/<source>/` into the project by hand: it carries the
round trip's changes along with yours.

## The generated pipeline

`decompile` writes `<Name>.pipeline.mjs` into the `.flow-sdk/` work directory
beside the source. Prefer it for any narrow edit: it chains all four steps below,
and it captures the baseline before your edit rather than after, which is the
ordering mistake that forces a rebuild.

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts
node .flow-sdk/Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
node .flow-sdk/Deployed.pipeline.mjs --strict   # compiles the edit, merges into .flow-sdk/Deployed.merged.flow
```

`--strict` goes to the merge step: merge refuses (exit 1, no file written)
instead of warning when the no-edit round trip changed something you did not
author (see [Merge warnings](#merge-warnings-what-the-round-trip-changed)).
The Node stack trace after `flow-merge: refused (--strict)` is expected; read
the refusal above it. Leave `--strict` off to get the warnings and a merged
file. A pipeline written by an SDK older than this option ignores `--strict`
silently: if `grep -q STRICT .flow-sdk/Deployed.pipeline.mjs` fails, use the
hand loop below with `merge --strict`.

Re-running it after further edits repeats only the compile and merge — the
baseline is captured once and reused. Pass `--no-pipeline` to `decompile` when
you deliberately want the manual sequence instead. The pipeline writes its
`.flow` artifacts into that `.flow-sdk/` directory (the baseline and the edited
compile each in a directory of their own, for the agent reason above), and the
agent files merge carries next to `Deployed.merged.flow`; use it only when the
directory is outside the canonical Flow project, because product validation
treats every `.flow` below the project, hidden folders included, as a
deliverable. When source must remain in the
project for relative sidecars, use the safe project loop above.

## The same loop by hand

```bash
uip maestro flow decompile Deployed.flow -o .flow-sdk/Deployed.flow.ts --no-pipeline
mkdir -p .flow-sdk/baseline .flow-sdk/edited
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/baseline/Deployed.flow
# Edit .flow-sdk/Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile .flow-sdk/Deployed.flow.ts -o .flow-sdk/edited/Deployed.flow
uip maestro flow merge Deployed.flow .flow-sdk/edited/Deployed.flow \
  -o .flow-sdk/Deployed.merged.flow --baseline .flow-sdk/baseline/Deployed.flow
```

Like the pipeline, this keeps every candidate in `.flow-sdk/`; validate
`.flow-sdk/Deployed.merged.flow`, then replace the original with it and copy
every `<source>/` file merge reports writing.

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

Validate `Deployed.merged.flow`, not the intermediate edited compile. Before
placing it in a solution, copy it over the canonical artifact rather than next
to it, together with every `<source>/` file merge reports writing, then
validate the canonical project path again.

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
