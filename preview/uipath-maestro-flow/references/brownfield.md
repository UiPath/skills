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

`decompile` writes `<Name>.pipeline.mjs` alongside the source. Prefer it for any
narrow edit: it chains all four steps below, and it captures the baseline before
your edit rather than after, which is the ordering mistake that forces a rebuild.

```bash
uip maestro flow decompile Deployed.flow -o Deployed.flow.ts
node Deployed.pipeline.mjs    # compiles the pristine baseline; stops there
# Edit Deployed.flow.ts narrowly; preserve existing step ids.
node Deployed.pipeline.mjs    # compiles the edit, merges into Deployed.merged.flow
```

Re-running it after further edits repeats only the compile and merge — the
baseline is captured once and reused. Pass `--no-pipeline` to `decompile` when
you deliberately want the manual sequence instead. The pipeline writes its
`.flow` artifacts beside the `.flow.ts`; use it only when that source directory
is already outside the canonical Flow project. When source must remain in the
project for relative sidecars, use the safe project loop above.

## The same loop by hand

```bash
uip maestro flow decompile Deployed.flow -o Deployed.flow.ts
uip maestro flow compile Deployed -o Deployed.baseline.flow
# Edit Deployed.flow.ts narrowly; preserve existing step ids.
uip maestro flow compile Deployed -o Deployed.edited.flow
uip maestro flow merge Deployed.flow Deployed.edited.flow \
  -o Deployed.merged.flow --baseline Deployed.baseline.flow
```

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

`mock()` in decompiled source therefore means the flow really contains a
placeholder node (`core.logic.mock`). The one case that still degrades is a node
whose definition is MISSING from the file — nothing can carry it, so it lowers
to `mock() /* TODO: unsupported node type … */`; leave that node untouched and
merge restores the original.

Validate `Deployed.merged.flow`, not the intermediate edited compile. Before
placing it in a solution, copy it over the canonical artifact rather than next
to it, then validate the canonical project path again.

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
