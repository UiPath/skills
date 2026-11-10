<!--skill-flavor:flow-sdk-hitl-stop:start-->
**Flow surface (a `.flow.ts`, a `.flow`, or a new flow) — the default: stop here.** Hand the HITL request to the `uipath-maestro-flow` skill: it authors `hitl(...)` in `<Name>.flow.ts` — decompiling an existing `.flow` first — and compiles ([hitl.md](../uipath-maestro-flow/references/hitl.md)). Never read or hand-edit the compiled `.flow`; the next `compile` overwrites it. Steps 2–6 below cover the Case, Low-Code Agent and Maestro surfaces.

<!--skill-flavor:flow-sdk-hitl-stop:end-->
<!--skill-flavor:case-sdk-surface-row:start-->
| `caseplan.case` (any `*.json` or `*.case` whose `nodes[]` carry `data.parentElement.type: "case-management:root"` — the marker is per-node; there is no `root` node on disk) | **Case** | Write `action` task into stage — see [hitl-casetask-action.md](references/hitl-casetask-action.md) |
<!--skill-flavor:case-sdk-surface-row:end-->
<!--skill-flavor:case-sdk-hitl-stop:start-->
<!--skill-flavor:case-sdk-hitl-stop:end-->
<!--skill-flavor:flow-project-creation:start-->
**If no `.flow` file exists and the surface is Flow**, create the Flow project with the `CreateProjects` tool.
<!--skill-flavor:flow-project-creation:end-->
<!--skill-flavor:case-json-task-type:start-->
Infer the right option from the description below — do not pull the registry first, and do not wait for the user to pick before proceeding.

| # | Option | Fingerprint | Description |
|---|---|---|---|
| 1 | **QuickForm (file-based schema)** | separate `<TaskLabel>.hitl.json` file + `hitlType: "quick"` context entry in the action task | Structured form fields in a `.hitl.json` file alongside `caseplan.case`. Action Center renders fields at runtime. No deployed app needed. |
| 2 | **App-based action task** | `data.name` and `data.folderPath` as `=bindings.<id>` references + `data.actionCatalogName` | Uses a deployed Action Center app with custom input/output fields. Requires the app to exist in Orchestrator. |

> **Default: QuickForm.** Pick QuickForm unless the request explicitly names a deployed Action Center app. State the choice, do not ask: "I'll use QuickForm — it's the quickest to set up, supports structured form fields, and doesn't need a deployed app. You can upgrade to an app-based task later if you need a custom UI layout."

> **Build vs design time.** QuickForm in case management must round-trip both ways: the JSON written here is what Studio Web's case designer reads (design time), and what `uip maestro case validate` + Action Center render at runtime (build time). Always validate after writing.

| Option chosen | Next step |
|---|---|
| QuickForm (file-based schema) | Read [references/hitl-casetask-action.md — Path 1](references/hitl-casetask-action.md#path-1--quickform-file-based-schema-no-deployed-app), then continue with Step 4 |
| App-based action task — the request must already name the app | Read [references/hitl-casetask-action.md — Path 2](references/hitl-casetask-action.md#path-2--app-based-action-task-deployed-action-center-app), then continue with Step 4 |

**Fallback rules — never block on these, fall back and state what you did:**

| Path | Blocker | Response |
|---|---|---|
| App-based | App not found in registry or `action-apps-index.json`, or no app name was given | Fall back to QuickForm and proceed. State: "I couldn't find (or wasn't given) that app, so I used QuickForm instead. Point me at a real app name and I'll swap it in." |
| QuickForm | Schema design rejected on validate (e.g. duplicate field IDs, missing primary outcome) | Fix the schema yourself from the validator's error and re-validate. Apply Step 4b checks. Note the fix in the final report — do not pause to re-show the schema first. |
| Any | Auth expired (401 on API call) | Fall back to QuickForm and proceed. State: "The session looked expired, so I used QuickForm rather than stall on re-authenticating. Run `uip login` and ask me to swap in the app when you're ready." |
<!--skill-flavor:case-json-task-type:end-->
<!--skill-flavor:case-json-write:start-->
Read the plan file the detection above found to identify the target stage: `caseplan.case`, or `caseplan.json` in a project an older CLI scaffolded. Edit and validate that file; never create a second plan beside it. Write an `action` task directly into `stage.data.tasks[lane][]`. **Direct JSON write is the only supported method** — the `uipath-maestro-case` skill ships no `hitl` CLI subcommand (unlike Flow's `uip maestro flow hitl add`).

Full reference: **[references/hitl-casetask-action.md](references/hitl-casetask-action.md)** — three task JSON shapes (QuickForm, generic, app-based), field reference, assignee handling, post-write verification, and downstream output access.

| Path chosen in Step 3 | What gets written |
|---|---|
| QuickForm | A `<TaskLabel>.hitl.json` schema file (unified `fields[]` with `direction`, `outcomes[]`) + action task in `caseplan.case` with `data.context[hitlType].value: "quick"`, `_schemaFileId` (placeholder UUID), and `hitlSchemaId` (matches `schemaId` in `.hitl.json`). `data.inputs[]` and `data.outputs[]` are empty arrays. No `root.data.uipath.bindings[]` entries. Apply Step 4b schema-design checks before writing. |
| App-based | Action task with `data.actionCatalogName`, `data.name` and `data.folderPath` as `=bindings.<id>` references. Add 2 root-level bindings. |

After writing, validate (build-time check — must pass before reporting success):

```bash
uip maestro case validate <caseplan.case> --output json
```

> `uip maestro case validate` is the only `uip maestro case` CLI used by this skill on the Case surface. All authoring is direct JSON.
<!--skill-flavor:case-json-write:end-->
