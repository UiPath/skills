# Handover — uipath-maestro-flow: switch HTTP plugin Step 1 to `uip maestro flow node add`

Status: not started. Branch already exists locally: `feat/uipath-maestro-flow-http-use-cli-add` (off latest `origin/main`).
Owner: next session.
Estimated effort: ~30 min of skill edits + a verification pass.

## TL;DR

The `uipath-maestro-flow` skill's HTTP plugin currently tells the agent to author the managed HTTP node by hand-editing the `.flow` JSON. That instruction routinely produces a flow that **opens-and-crashes Studio Web** on first canvas open. The connector plugin in the same skill already uses the CLI (`uip maestro flow node add`) and is not affected. The fix is to make the HTTP plugin's Step 1 mirror the connector plugin pattern, plus a small general note in the editing-operations doc warning against pasting large registry-get output through `Edit`/`Write`.

A CLI-side guardrail has already landed (validator that fails `uip maestro flow validate` when this field is missing) — see [Reference material](#reference-material). The skill fix is the **authoring-side** half of the same problem.

## The bug (full context)

### Symptom

A flow authored under the current HTTP plugin instructions ships with `inputs.detail.uiPathActivityTypeId` missing on every `core.action.http.v2` node. The flow:

- Passes `uip maestro flow validate` (until the new validator is released — see Reference material).
- Passes `uip maestro flow format`.
- Runs successfully headless via `uip maestro flow debug` and via deployed runs.
- **Crashes Studio Web** when an operator opens it in the canvas — the property-panel renderer dereferences `inputs.detail.uiPathActivityTypeId` to resolve the activity configuration UI, and a missing value takes the editor down.

### Concrete repro

`/Users/jiyang.zhou/Projects/BellevueWeather/BellevueWeather/BellevueWeather.flow`. The `core.action.http.v2` definition embedded in `definitions[]` is missing its entire `form` block. `node configure` was run successfully against it. The resulting `inputs.detail` carries no `uiPathActivityTypeId`. Opening the flow in Studio Web crashes the canvas.

### Root cause

`connector-service.ts:configureManagedHttp` in the CLI populates `inputs.detail.uiPathActivityTypeId` by reading the embedded definition at one of two paths:

1. `form.sections[].fields[].componentProps.connectorDetail.uiPathActivityTypeId` (the registry's only source for managed HTTP).
2. `model.context["metadata"].body.designTimeMetadata.activityConfig.raw.activity.uiPathActivityTypeId` (a fallback path that managed HTTP manifests don't populate).

If neither is present, a conditional spread silently omits the field. No error, no warning.

When the skill instructs the agent to copy the registry-get output into `definitions[]` via `Edit`/`Write`, the agent has to round-trip ~100 lines of nested JSON through its own token stream. Even with explicit "verbatim" instructions, models routinely paraphrase or drop large nested blocks they perceive as canvas UI metadata. The `form.sections[]` block reads exactly like UI rendering data — section IDs, collapsible flags, custom component names, SVG icon URLs, helpUrlTemplate, isExperimental, tags — so it's a natural target for "trim this, it's not runtime data" judgement. With the form block gone, the extractor returns `undefined` and the field is silently lost.

The connector plugin doesn't have this problem because it routes the agent through `uip maestro flow node add`, which copies the manifest into `definitions[]` in code (flow-core's `addNode` function), byte-for-byte, with no model in the loop.

## Reference material

- **CLI validator already landed**: [UiPath/cli PR #2140](https://github.com/UiPath/cli/pull/2140) — `activityTypeIdValidator` in `packages/flow-tool/src/services/node-validators/activity-type-id-validator.ts`. Covers `core.action.http.v2`, `uipath.connector.<name>`, and `uipath.connector.trigger.<name>`. Emits error severity. Read that PR's description for the runtime-failure framing in the validator's user-facing message; reuse the same framing in any skill text you write about the failure mode.
- **Comparator — the connector plugin (already uses CLI, do not change)**: `skills/uipath-maestro-flow/references/author/references/plugins/connector/impl.md` — see lines around `uip maestro flow node add <file> uipath.connector.<connector-key>.<operation>` (Step 2/3 in that file). That's the pattern the HTTP plugin should mirror.
- **The CAPABILITY index that lists both pages**: `skills/uipath-maestro-flow/references/author/CAPABILITY.md`.
- **The general editing-operations doc (potentially needs a sister edit)**: `skills/uipath-maestro-flow/references/author/references/editing-operations-json.md`, around line 31 (the "Definitions and versions — copy verbatim" bullet).

## Goal

Edit `skills/uipath-maestro-flow/references/author/references/plugins/http/impl.md` so that **Step 1 ("Add the node")** routes through `uip maestro flow node add` as the primary path. The CLI handles definition + node instance + variables + layout placeholders in code. The agent should not be touching `definitions[]` for this node type.

Optionally, add a sister note in `editing-operations-json.md` warning against pasting large registry-get definitions through `Edit`/`Write` for any node type — generalizing the lesson.

Everything else in the HTTP plugin page stays the same (Steps 2–5, the `=js:` discussion in Step 3b, branches, wiring, debug table). Only Step 1's authoring mechanic changes.

## Concrete change to make

### 1. `plugins/http/impl.md`, Step 1 — rewrite

Current (Step 1, around line 23-27):

```markdown
### Step 1 — Add the node

Use `Edit` / `Write` to add the `core.action.http.v2` node directly to the `.flow` file. Follow [Edit/Write: Add a node](../../editing-operations-json.md#add-a-node): copy the registry definition into `definitions[]`, add the node instance to `nodes[]`, add `variables.nodes`, and add a placeholder `layout.nodes` entry. Save the node ID for Step 3.

For the node instance shape, follow the [Action Node Structure — Standard JSON skeleton](../../../../shared/action-nodes.md#standard-json-skeleton) with `type: "core.action.http.v2"` and `typeVersion: "2.0"`. Leave `inputs` empty at this stage — Step 3 populates `inputs.detail` via `uip maestro flow node configure`.
```

Replace with something along these lines (tighten / restyle to match the surrounding doc voice; this is intent, not final copy):

```markdown
### Step 1 — Add the node

```bash
uip maestro flow node add <ProjectName>.flow core.action.http.v2 \
  --label "<HTTP node label>" --output json
```

The CLI copies the manifest into `definitions[]`, adds the node instance to `nodes[]`, registers `variables.nodes` entries, and inserts a placeholder in `layout.nodes` — all in code, byte-for-byte from the registry. Save the returned node ID for Step 3.

> **Do not hand-author the definition.** The managed HTTP manifest carries a critical field at `form.sections[].fields[].componentProps.connectorDetail.uiPathActivityTypeId` that the CLI reads at `node configure` time. Copying the registry-get output through `Edit`/`Write` is high-risk: large nested blocks like `form.sections[]` are routinely trimmed when round-tripped through chat, the extractor returns `undefined`, configure silently omits the field, and the resulting flow opens-and-crashes the Studio Web canvas (the property-panel renderer dereferences this field). `uip maestro flow node add` is the only correct path for this node type.

Leave `inputs` empty at this stage — Step 3 populates `inputs.detail` via `uip maestro flow node configure`.
```

Notes for the rewrite:

- Keep the language tight; match the matter-of-fact tone of the connector plugin file.
- The warning text should explain *why* the byte-copy matters — without it, future skill maintainers might re-introduce the Edit/Write path "because it's more flexible".
- Don't expand the section into a tutorial — Steps 2–5 already cover everything else.

### 2. `plugins/http/impl.md`, Debug table — add one row

Search the Debug table near the end of the file for the column header `| Error | Cause | Fix |`. Add a row for the new validator error:

```markdown
| `flow validate` errors with `uiPathActivityTypeId` missing | Node was added by hand-authoring `definitions[]` and the `form` block was paraphrased | Re-add the node: delete it, run `uip maestro flow node add <file> core.action.http.v2 ...`, then re-run `node configure`. The new definition will carry `form` byte-for-byte. |
```

### 3. (Optional but recommended) `editing-operations-json.md`, line ~31

The "Definitions and versions — copy verbatim" bullet currently says "Never hand-write or paraphrase definitions." Add a sentence acknowledging the failure mode and pointing at `node add`:

> Note: for any node type with a `uip maestro flow node add` workflow, prefer the CLI — it copies the manifest in code. Round-tripping a 100+ line registry-get definition through `Edit`/`Write` is the dominant cause of stripped `form` / `connectorDetail` blocks (the failure mode that produces canvas-crashing flows; see the http plugin's Step 1).

## Things to verify before opening the PR

1. **Search for other places the HTTP plugin tells the agent to hand-author the definition.** Grep `plugins/http/` for `Edit`, `Write`, `definitions[]`, `registry get` — make sure Step 1 was the only place. There's also a Step 5 ("Wire edges") that uses `Edit` for edges; **leave that alone** — edges are short, model-authored content where Edit is fine.
2. **Check the connector plugin file** (`plugins/connector/impl.md`) — confirm the pattern you're mirroring still recommends `node add`. If it's drifted, raise it but don't change it in this PR.
3. **Read the CAPABILITY index** (`author/CAPABILITY.md`) for any reference to the HTTP plugin's authoring workflow that might also need updating (e.g., "How to add an HTTP node" → if it links to Step 1 specifically, the link still works; if it paraphrases the instruction, update it).
4. **Activation tests**: this skill has an activation test suite at `tests/tasks/activation/uipath-maestro-flow.jsonl`. Search it for HTTP-related entries; if any fixture references the Edit/Write authoring path, update it.
5. **Don't touch unrelated content.** Steps 2–5, the `=js:` Step 3b warning, the AskUserQuestion connection-creation flow in Step 2, the file's frontmatter — all stay the same.

## Out of scope

- The CLI-side fix (already landed in [PR #2140](https://github.com/UiPath/cli/pull/2140)). Don't touch the CLI repo from this branch.
- Layer 1 (CLI fetches the activity type ID from the live registry as a fallback when the embedded definition is stripped). Decided against earlier — the contract is that the embedded definition is the source of truth; the CLI shouldn't paper over bad authoring.
- Changes to non-HTTP plugins. The connector plugin and others already use `node add`; nothing to do there.

## How to run the skill changes through verification

Skill repos at UiPath don't generally have an automated test for prose changes, but you can sanity-check by:

1. Read the updated `plugins/http/impl.md` end-to-end. Does Step 1 stand on its own? Does the warning explain *why* the CLI path matters? Does Step 3 still flow naturally after the new Step 1?
2. Search for any internal link that pointed at the old "Edit/Write: Add a node" section in `editing-operations-json.md` — if Step 1 was the only caller, the section is still useful for non-HTTP nodes (which is the connector plugin's territory) so leave the section. Just make sure no part of the HTTP page links there anymore.
3. If you have access to a UiPath tenant, run a small smoke test:
   - `uip maestro flow init` a fresh project
   - `uip maestro flow node add <file> core.action.http.v2 --label "Test HTTP"`
   - `uip maestro flow node configure ... --detail '{"authentication": "manual", "method": "GET", "url": "https://example.com"}'`
   - Open the flow in Studio Web — confirm the property panel renders without a crash.
   - This is also a useful regression test for the CLI side.

## PR style

Conventional commits in this repo: `docs(uipath-maestro-flow): switch HTTP plugin Step 1 to node add`. Body should reference [UiPath/cli PR #2140](https://github.com/UiPath/cli/pull/2140) as the matching CLI-side change and link to the BellevueWeather repro path. Keep the description focused on the *what* and *why*; don't re-litigate the whole investigation — the PR description in #2140 already has the full story.

Branch is `feat/uipath-maestro-flow-http-use-cli-add` — `feat/` was chosen because the existing skills repo convention puts skill-content changes on `feat/` or `docs/` branches; `docs/` would also be fine, rename if you prefer.

## When you're done

Delete this handover doc (`git rm HANDOVER-uipath-maestro-flow-http-use-cli-add.md`) as part of the same PR. It's scratch.
