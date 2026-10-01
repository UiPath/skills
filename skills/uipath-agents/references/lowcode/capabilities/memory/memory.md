# Agent Memory Spaces

Use this when a low-code agent needs an attached UiPath memory space for dynamic few-shot retrieval, or when runs of a deployed agent should be promoted into that space as memory items.

## Critical Rules

1. **Use `uip agent memory` for memory features.** Do not hand-author `features/{Name}/feature.json` unless recovering from a broken project. The CLI updates the feature file; run `uip agent refresh` afterwards to regenerate derived files.
2. **Inside a solution, `uip agent memory add` declares the memory space for you.** When the agent project sits under a `.uipx`, `add` looks the space up in the solution: a space in `solution_folder` that is not declared yet is minted as a virtual `memorySpace` resource (`Data.SolutionResource.Status: "Created"`), a declared one is reused (`"Linked"`), and the feature's `referenceKey` is set to the resource key. `uip solution deploy run` then creates the space in the tenant. `--folder-path` defaults to `solution_folder` there. Do not run `uip solution resources add --source local --kind MemorySpace` first; `add` does it.
3. **A space in another folder must already exist.** Pass `--folder-path <Folder>`; if the solution does not declare it the result is `"NotDeclared"` and `Data.SolutionResource.Instructions` carries the exact `uip solution resources add --source remote` command to run. Outside a solution `--folder-path` is required, also with `--reference-key`, and the status is `"NotInSolution"`.
4. **Refresh and validate after memory changes.** Memory bindings are generated during `uip agent refresh`; do not edit `bindings_v2.json` directly. `uip solution resources refresh` is still right for inline agents and for spaces in other folders, but a space `add` declared is already in the solution.
5. **Memory items are promoted runs, not seed data.** The runtime store keeps one record per real agent run: episodic items come from feedback left on a run's trace, escalation items from an escalation span. Nothing in the project files seeds a space; `uip agent memory item add` promotes a run that already happened. Do not put secrets or raw PII into feedback comments or escalation answers.

## Workflow

### 1. Decide where the memory space lives

- **Inside a solution, new space:** skip discovery. `uip agent memory add` declares it in `solution_folder` and `solution deploy run` creates it in the tenant.
- **Inside a solution, space already declared:** `add` links it by exact name; nothing else to do.
- **Space in another folder (tenant-level):** discover it, then declare it as a remote resource before attaching:

```bash
uip solution resources list --source remote --kind MemorySpace --search "<MEMORY_SPACE_NAME>" --output json
uip solution resources add --source remote --kind MemorySpace --name "<MEMORY_SPACE_NAME>" --folder-path "<FOLDER_PATH>" --output json
```

Use the row's `Name` as `--memory-space` and `Folder` as `--folder-path`. If the user names a space that discovery cannot find, stop and ask; do not invent one.

### 2. Attach the memory space to the agent

Inside a solution (the usual case; the space is declared or reused and `--folder-path` defaults to `solution_folder`):

```bash
uip agent memory add SupportRecall \
  --memory-space "<MEMORY_SPACE_NAME>" \
  --threshold 0.25 \
  --result-count 5 \
  --search-mode hybrid \
  --field userQuestion=1 \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

Check `Data.SolutionResource.Status` (`Created`, `Linked`, `NotDeclared`, `NotInSolution`, `Provided`) and `Data.ReferenceKey`. For a space in another folder, or outside a solution, add `--folder-path "<FOLDER_PATH>"`.

`SupportRecall` is the feature name inside the agent. Choose a short PascalCase or kebab-free name that describes how the agent will use the memory.

**`--field` names an `inputSchema` key, not a flow variable.** Each `--field` must match a property in the agent's `inputSchema.properties` exactly — retrieval reads the value from the agent's `input` under that key. For inline agents (`--inline-in-flow`), inputs use the flattened key `<triggerNodeId>__output__<var>` (see [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md) § Wiring Flow Inputs Into an Inline Agent), so pass the flattened name:

```bash
# inline agent: flow global userQuestion on trigger node "start"
uip agent memory add SupportRecall \
  --memory-space "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --threshold 0.25 \
  --result-count 5 \
  --search-mode hybrid \
  --field start__output__userQuestion=1 \
  --path "<FLOW_PROJECT_DIR>/<PROJECT_ID>" \
  --output json
```

Passing the un-flattened global name (`--field userQuestion=1`) on an inline agent names a field the agent never receives; `validate` does not catch this.

Options:

| Option | Meaning |
|---|---|
| `--memory-space` | Memory space name to attach |
| `--folder-path` | Folder path containing the memory space; defaults to `solution_folder` inside a solution, required outside one |
| `--reference-key` | Solution resource key to store as given; skips the solution lookup. Still needs `--folder-path` outside a solution |
| `--description` | Human-readable feature description |
| `--threshold` | Retrieval score threshold; default `0` |
| `--result-count` | Number of memory results; default `3` |
| `--search-mode` | `hybrid` or `semantic`; default `hybrid` |
| `--field name=weight` | Input field weighting; `name` = agent `inputSchema` key (inline: `<trigger>__output__<var>`); repeat for multiple fields |
| `--disable-dynamic-few-shot` | Attach the memory space without runtime retrieval |
| `--path` | Agent project directory; default `.` |

### 3. Promote runs into memory items (deployed agent)

`uip agent memory item add` and `item list` talk to the runtime memory store, so they need `uip login` and a space that exists in the tenant, i.e. after `uip solution deploy run` (or after Studio Web attached it). A memory item is a record about one real run; there is no way to seed a space from files.

**Episodic item: promote feedback left on a run's trace.**

```bash
# run the deployed agent, then find its trace and leave feedback
uip or jobs start <process-key> --folder-path "<DEPLOY_FOLDER>" --input-arguments '{"question":"..."}' --wait-for-completion --output json
uip traces spans get --job-key <job-key> --folder-path "<DEPLOY_FOLDER>" --output json
uip traces feedback create --trace-id <trace-id> --positive --comment "Keep as example" --folder-key <deploy-folder-key> --output json

# promote it into the space the SupportRecall feature points at
uip agent memory item add SupportRecall \
  --memory-type episodic \
  --feedback-id <feedback-id> \
  --folder-path "<DEPLOY_FOLDER>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

**Escalation item: store the span of an escalation the agent raised, with the answer.**

```bash
uip agent memory item add SupportRecall \
  --memory-type escalation \
  --trace-id <trace-id> --span-id <span-id> \
  --answer "Refund within 14 days" \
  --folder-path "<DEPLOY_FOLDER>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

Rules the store enforces, surfaced verbatim by the CLI:

| Value | Numeric | Needs |
|---|---:|---|
| `episodic` | `0` | `--feedback-id` of feedback on the run's trace |
| `escalation` | `1` | `--trace-id` and `--span-id` of an escalation span; `--answer` optional |

- The feature gives the memory space name. `--folder-path` **or** `--folder-key` (never both) gives the Orchestrator folder the space lives in at runtime; it defaults to the feature's folder and is **required when that is `solution_folder`**, because that placeholder is replaced at deploy time with the deployment folder (`uip solution deploy list` shows it).
- `--span-id` takes the span id as a zero-padded GUID, the form `feedback create` prints it in: span `acc0be396bfd0d4b` is `00000000-0000-0000-acc0-be396bfd0d4b`.
- A run whose agent input is empty is refused ("payload has no non-empty fields under 'input'"): the agent needs an `inputSchema` property with a value. A span that is not an escalation is refused for escalation items.
- There is no `item remove` yet; remove items in the Agents portal.

### 4. Verify

```bash
uip agent memory list --path "<AGENT_PROJECT_DIR>" --output json
uip agent refresh "<AGENT_PROJECT_DIR>" --output json
uip agent validate "<AGENT_PROJECT_DIR>" --output json
# after deploy, what the runtime space holds (filter with --memory-type episodic|escalation)
uip agent memory item list SupportRecall --folder-path "<DEPLOY_FOLDER>" --path "<AGENT_PROJECT_DIR>" --output json
```

After refresh, inspect `<AGENT_PROJECT_DIR>/bindings_v2.json` only to verify that a `memorySpace` binding exists. Do not edit it. A space that `add` declared (`Created`/`Linked`) is already in the solution; run `uip solution resources refresh --output json` from the solution root for inline agents and for spaces in other folders. Do not skip `uip agent refresh` because the memory space name/folder were provided or because `bindings_v2.json` looks correct.

## Remove

Remove a feature by feature name or ID:

```bash
uip agent memory remove SupportRecall --path "<AGENT_PROJECT_DIR>" --output json
```

Remove by memory space name only when you also pass the folder path:

```bash
uip agent memory remove "<MEMORY_SPACE_NAME>" \
  --folder-path "<FOLDER_PATH>" \
  --path "<AGENT_PROJECT_DIR>" \
  --output json
```

Runtime memory items cannot be removed from the CLI yet; use the Agents portal.

## Generated Shape

The CLI writes a feature file at:

```text
<AGENT_PROJECT_DIR>/features/SupportRecall/feature.json
```

Expected shape, for review only (standalone agent; an inline agent's `fieldSettings[].name` is the flattened key, e.g. `start__output__userQuestion`):

```json
{
  "$featureType": "memorySpace",
  "id": "<uuid>",
  "referenceKey": "<solution resource key, or null outside a solution>",
  "folderPath": "solution_folder",
  "name": "SupportRecall",
  "memorySpaceName": "support-memory",
  "description": null,
  "isEnabled": true,
  "dynamicFewShotSettings": {
    "isEnabled": true,
    "threshold": 0.25,
    "resultCount": 5,
    "searchMode": "hybrid",
    "fieldSettings": [
      {
        "id": "<uuid>",
        "name": "userQuestion",
        "weight": 1
      }
    ]
  }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `--folder-path is required when the agent project is not inside a solution` | Standalone project, no folder given (also with `--reference-key`) | Pass `--folder-path <Folder>`, or scaffold inside a solution |
| `Data.SolutionResource.Status: "NotDeclared"` | Space is in another folder and the solution does not declare it | Run the command in `Data.SolutionResource.Instructions` (`uip solution resources add --source remote ...`), then `add` again |
| `the resource builder renamed it to "<name>_2"` | Another memorySpace resource conflicts with that name | Pick a different `--memory-space` name, or declare it with `uip solution resources add --source local --kind MemorySpace --name <name>` |
| `An episodic item is promoted from feedback: pass --feedback-id` | Episodic `item add` without `--feedback-id` | Create feedback with `uip traces feedback create`, pass its `Id` |
| `An escalation item is stored from the escalation span: pass both --trace-id and --span-id` | Escalation `item add` missing one of the two | Take both from `uip traces spans get --job-key <key>`; pad the span id into a GUID |
| `Invalid memory-type value` | Unsupported type | Use `episodic`, `escalation`, `0`, or `1` |
| `Feature "<name>" points at solution_folder, the placeholder the deploy replaces` | Item command on a solution-scoped feature without a runtime folder | Pass `--folder-path <deployment folder>` or `--folder-key <key>` (`uip solution deploy list`) |
| `Pass either --folder-path or --folder-key, not both` | Both folder flags given | Keep one |
| `Memory space "<name>" was not found in that folder` | Space not deployed in that folder, or wrong folder | Check `uip solution deploy list`; a space is created when the declaring solution is deployed |
| `payload has no non-empty fields under 'input'` | The run's agent input was empty | Give the agent an `inputSchema` property and run it with a value; the user prompt does not count |
| `Unable to Ingest Memory for ... SpanId[...]` | Escalation `item add` pointed at a span that is not an escalation | Use the span of an escalation the agent raised |
| `Memory space "<name>" is attached N times` | More than one feature references the same memory space name | Select by feature name or feature ID |
| No `memorySpace` binding after refresh | Refresh was not run after the memory edit | Run `uip agent refresh "<AGENT_PROJECT_DIR>" --output json` |
| Inline agent memory exists but `uip solution resources refresh` misses it | Binding was not propagated to the parent flow project | Re-run inline refresh with `--bindings-target "<FLOW_PROJECT_DIR>/bindings_v2.json"` — see [../inline-in-flow/inline-in-flow.md](../inline-in-flow/inline-in-flow.md) |
| Items added from the CLI do not show in the Agents portal | Looking at a same-named space in another folder | Two solutions declaring `cli-recall` give two runtime spaces; match `Data.MemorySpaceId` from `item list` with the portal URL |
