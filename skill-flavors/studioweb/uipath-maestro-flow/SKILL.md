<!--skill-flavor:sdk-project-layout:start-->
**In Studio Web the builder SDK is built in.** `uip maestro flow check`, `compile`, `decompile` and `merge` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: there is no `npm` and no Node process here. `examples/` contains authored examples, and `references/` contains the details routed from this guide.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another. Each project is a folder `/solution/<Project>/`. Create a Flow project only when the user asks for a new project: `uip maestro flow init <Project>` creates it through Studio Web and seeds a trigger-only `.flow`.

**Edit the open flow.** The context of each turn gives these values:

- `CurrentFile.AbsolutePath` — the open file, for example `/solution/Flow/new.flow`.
- `CurrentFile.IsCurrentFileEmpty` — `true` when the open `.flow` holds no flow yet.
- `CurrentProject.AbsolutePath` — the open project, for example `/solution/Flow`.
- `CurrentWorkingDirectory` — the directory of the shell. It can differ from the project, so `cd` to the project first.

Choose the target `.flow` in this order:

1. The user names a file: edit that file.
2. An edit: edit the `.flow` at `CurrentFile.AbsolutePath`.
3. A new flow, and `IsCurrentFileEmpty` is `true`: fill the open `.flow`.
4. A new flow otherwise: write a new `<Name>.flow` in the open project. At the end, tell the user to open `<Name>.flow` in the Explorer. A write refreshes the canvas only for the open file.

Below, `<Project>` is the folder of the target and `<Name>` is the file name of the target without `.flow` (`new` for `new.flow`).

**The target `.flow` is the single source of truth.** The user can change it on the canvas between your turns. So never use a `.flow.ts` from an earlier turn: decompile a fresh one every turn.

**Drafts live in the `.flow-sdk/` folder of the project.** Keep the source and every intermediate `.flow` in `/solution/<Project>/.flow-sdk/`: `<Name>.flow.ts`, `original/<Name>.flow`, `baseline/<Name>.flow` and `edited/<Name>.flow`. `prepare` writes `connectors-local/` and `bindings.json` there too. Each compile writes inline-agent files next to its output, so keep each intermediate `.flow` in its own folder ([`references/brownfield.md`](references/brownfield.md#why-three-directories-inline-agents)).

**Never delete or rename a file under `/solution`.** The project file system refuses both. Overwrite the file instead.

**A read-only page refuses every write.** When the page shows "Locked by you" and an Edit button, a write fails, sometimes as `[object Object]`. Tell the user to click Edit, then try again.

**The Flow SDK can be off for this user.** When an SDK verb answers `ConfigError` "this host has no way to run …", the Flow SDK is not enabled for this user. Say so, and stop.

Every `uip` call prints `[WARN] [Telemetry] applicationinsights package not available`. This warning is harmless.

### Commands in Studio Web

Some commands in the references do not work in Studio Web. Use this table:

| Command | In Studio Web |
| --- | --- |
| `uip maestro flow check`, `compile`, `decompile`, `merge` | Work, inside the page. `decompile` writes no pipeline helper. `merge` takes only `--original`, `--baseline`, `--strict` and `-o`. `check` refuses a compiled `.flow`: use `validate`. |
| `uip maestro flow validate`, `format` | Work. Never `format` a merged file. |
| `uip maestro flow registry get`, `search`, `list`, `pull` | Work: the product node registry. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | Answered by the CLI, with no effect: it confirms the library of the session, ignores its options, and writes no `./connectors/<key>.ts` modules. |
| `uip maestro registry path` | Not available: there is no local library cache. |
| `uip solution resources add`, `list` | Work. |
| `uip solution resources refresh` | Fails: no local `.uipx`. Add connections with `resources add` ([the connector loop](#the-connector-loop-in-studio-web), step 7). |
| `uip solution publish`, `uip solution deploy run` | Work. Studio Web packages and signs in for `publish`. |
| `uip maestro flow debug "<Project>"` | Works: a real run of the saved project. `<Project>` is a project name, not a path. |
| `uip solution pack`, `upload`, `init` | Not available. Studio Web owns the solution. |
| `uip login` | Not available. You are already signed in to the tenant of the user. |
| `npm`, `node`, the `flow-sdk` bin, `uv`, `uip codedagent` | Not available. Studio Web cannot create a coded agent. |

When a reference tells you to run a command that is not available, use the Studio Web route that this guide gives. If there is no route, tell the user.
<!--skill-flavor:sdk-project-layout:end-->

<!--skill-flavor:sdk-connector-discovery:start-->
Integrations with non-UiPath systems use connectors. **Choose the node before writing it.** For an external service or data (weather, Slack, a REST API), run `uip maestro registry search '<brand or service name>'`, unless the request names the transport itself ("over HTTP, not a connector" means `http()`). A hit is a connector. `"total": 0` is a miss and means `http()` (not for an external agent: see the table). For document extraction or another tenant capability (agent, process), run the `uip maestro flow registry search` of that family ([`references/ixp.md`](references/ixp.md), [`references/agent.md`](references/agent.md)). A `script()` that returns fixed values is never a stand-in for that step, and `mock()` only marks a capability that the search proved absent.

### The connector loop in Studio Web

Run each command from the project folder `/solution/<Project>`. `prepare` writes `.flow-sdk/connectors-local/<key>.ts` and `.flow-sdk/bindings.json` there.

1. **Describe the operation:** `uip maestro registry describe <node-type> --output plain`. The page gives the inputs, outputs, lookup fields and the code to write.
2. **Choose the connection:** `uip is connections list <connector-key> --all-folders --output json`. When more than one connection is `Enabled`, ask the user which one to use. Then pass `--connection-id <id>` to `prepare`, and report it ([completion output](references/author.md#completion-output) item 5). `prepare` refuses a connection in state `Failed`.
3. **Prepare the action:** `uip maestro registry prepare <connector-key> --action <action>`. For each lookup field, add `--resolve <field>:<key|name>=<value>`. Then run it again with `-f <field>=<value>` for all of those fields. The hints of `prepare` give the exact next command: run it.
4. **Author with the prepared descriptor**, as the `next:` lines of `prepare` show. The import path is relative to the draft in `.flow-sdk/`:

   ```ts
   import { CreateIssue } from './connectors-local/uipath-atlassian-jira.ts';
   // …
   .step('issue', connector(CreateIssue, { /* fields */ }, { connection: 'jira', folder: 'shared' }))
   ```

   With no prepared descriptor, write `connector('<key>', '<action>', inputs, { connection, folder })`. Never import from `./connectors/`: Studio Web writes no modules there.
5. **Check:** `uip maestro flow check .flow-sdk/<Name>.flow.ts --source`. It also reports the required fields of the project from the prepared page (for example Jira `components`). Run each `prepare` it names, then check again.
6. **Compile and merge** ([Lifecycle](#lifecycle)).
7. **Add each connection to the solution.** After the merge, read each `connection` row in `bindings_v2.json` of the project. For each row, run `uip solution resources add --source remote --kind connection --cloud-key <ConnectionId>`. If the file has no such row, use the `resourceKey` of each `ConnectionId` entry in `.flow-sdk/bindings.json`. Without this step, the node shows "The selected resource is not part of the solution". Check the result with `uip solution resources list --source local --output json`.

Connectors require [`.flow-sdk/bindings.json`](references/bindings.md).
`CONNECTOR_NOT_IN_LIBRARY`, `CONNECTOR_OBJECT_REQUIRED` and `CONNECTOR_OBJECT_NOT_GENERIC` are source fixes, not prepares: [connector-params.md](references/connector-params.md#author-first--check-names-every-prepare-you-owe).

Schema-dynamic operations (`loadByDefault`, dependent dropdowns, `customFieldsRequestDetails`) need the prepare `check` names with every required `-f`, and a post-compile cache check: [`references/connector-params.md`](references/connector-params.md#schema-dynamic-operations-the-parent-field-loop).
<!--skill-flavor:sdk-connector-discovery:end-->

<!--skill-flavor:sdk-lifecycle:start-->
Every change — a new flow or an edit — is the same round trip through the target `.flow` ([Project layout](#project-layout)). The merge keeps what the SDK does not model (canvas layout, positions, sidecars) as the user left it. Run it from the project folder:

```bash
cd /solution/<Project>
mkdir -p .flow-sdk/original .flow-sdk/baseline .flow-sdk/edited
# 1. Seed, every turn: a copy of the target, a fresh source, the pristine baseline
cp <Name>.flow .flow-sdk/original/<Name>.flow
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts --no-pipeline
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o .flow-sdk/baseline/<Name>.flow --no-check
# 2. Edit .flow-sdk/<Name>.flow.ts narrowly (no .layout() for added steps: merge places them), then check until clean
uip maestro flow check .flow-sdk/<Name>.flow.ts --source
# 3. Compile the edit, then merge only the delta into the target
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o .flow-sdk/edited/<Name>.flow
uip maestro flow merge .flow-sdk/edited/<Name>.flow --original <Name>.flow --baseline .flow-sdk/baseline/<Name>.flow -o <Name>.flow
# 4. The product's own static check on the file the canvas shows
uip maestro flow validate <Name>.flow --output json
```

Valid is top-level `Result` plus `Data.Status: "Valid"`. Treat `Data.Warnings` as failures, except the reviewed shared-connection advisory and `err()` diagnostics. If `validate` fails, fix the source and run steps 2 to 4 again. To undo the merge, copy `.flow-sdk/original/<Name>.flow` back over the target.

- **Always finish with the merge into the target.** About 400 ms after a write, the canvas reloads the open file. Never run `format` on the merged file: it lays out the canvas of the user again.
- **An open `.flow` with no content** gives `decompile` nothing to read. Treat it as a new file (next item), and compile straight to it.
- **A new `.flow` in a new file** has no original. Write `.flow-sdk/<Name>.flow.ts` from [Hello world](#hello-world-flow), run step 2, and compile it straight to `<Name>.flow`. Then run `uip maestro flow format <Name>.flow --output json` once, and validate it.
- **A baseline compile that refuses a draft node** (a connector with no connection, an empty required input) stops the round trip: see [`references/brownfield.md`](references/brownfield.md#flows-with-draft-nodes-let-merge-compile).
- **If the baseline compile refuses a decompiled connector input**, stop and tell the user (UiPath/builder-sdk#1402).
- **A flow with connectors** needs each connection in the solution after the merge ([the connector loop](#the-connector-loop-in-studio-web), step 7).

Run the flow only for a stated runtime-behavior claim. `uip maestro flow debug "<Project>"` is a real run: ask first unless the user asked for it. The reply is plain text and waits up to 120 s (`--timeout <s>`, max 150). `TimedOut` means the run is still going, not that it failed: do not re-run it. First make sure each connection is in the solution ([the connector loop](#the-connector-loop-in-studio-web), step 7). Do not run `uip solution resources refresh`: it fails in this host. You can also ask the user to run it from the designer.
<!--skill-flavor:sdk-lifecycle:end-->

<!--skill-flavor:sdk-editing:start-->
In brownfield work, preserve the supplied source, step names, and unaffected wiring. Insert a step by moving the old edge through it, not by creating a second path. Edit the decompiled source narrowly and let the merge carry only that delta back ([Lifecycle](#lifecycle)). Validate the merged target `.flow`, never `.flow-sdk/edited/`. Studio Web has no pipeline helper: `decompile` here never writes one.

**True-brownfield procedure:**
**[`references/brownfield.md`](references/brownfield.md)** — read its judgments. Its shell sequences assume a terminal, so use the round trip above instead.
<!--skill-flavor:sdk-editing:end-->

<!--skill-flavor:sdk-api-index:start-->
**Every signature, option shape and field is indexed in the SDK that Studio Web ships**, not in this guide. Its package root is `/plugins/bundled/uipath-studio-web/flow-sdk/`, and a row's path is relative to it:

| you have | look in | a row gives you |
| --- | --- | --- |
| a field or method — `outcomePorts`, `stepToList` (the usual case) | `dist/api-members.md` | the shape that declares it, and the lines that do |
| an exported symbol — `HitlInputs`, `hitl`, `FlowBuilder` | `dist/api-index.md` | its kind, area, and the lines that declare it |

**Match one name; do not read either file end to end** — `grep` it. Then read the span (e.g. `dist/core/actions.d.ts:583-597`): the whole declaration with its doc comment, so one read answers the question. A name in neither index is probably a RUNTIME output key, which the node references carry.
<!--skill-flavor:sdk-api-index:end-->

<!--skill-flavor:sdk-operate:start-->
Debug, publish, deploy, trigger, inspect a job, and drive an instance's
lifecycle. You are already signed in to the tenant of the user. Before every
publish or debug, make sure each connection is in the solution; never run
`uip solution resources refresh` here. Run the flow
with `uip maestro flow debug "<Project>"`.
Publish the open solution with `uip solution publish` (the destination is the
user's choice). `flow debug` is a REAL run, not a validation step: ask first, as it says. Read
**[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:sdk-operate:end-->
