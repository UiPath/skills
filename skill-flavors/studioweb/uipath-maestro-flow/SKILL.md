<!--skill-flavor:sdk-project-layout:start-->
**In Studio Web the builder SDK is built in.** `uip maestro flow check`, `compile`, `decompile` and `merge` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: no `npm` or Node.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another, and never copy a project out of it. Each project is a folder `/solution/<Project>/`. Create a Flow project only when the user asks for one, never because the request names the flow ("a Maestro Automate called CronCop"): `uip maestro flow init <Project>` creates it through Studio Web and seeds a trigger-only `new.flow`. Run `uip maestro flow init <Project> --automate` when the request names **Maestro Automate** as the product. A project you fill keeps its type: if the request names Maestro Automate and `/solution/<Project>/.maestro_automate` is missing, keep building, then tell the user to switch Build as to Maestro Automate.

**Edit the open flow.** Each turn's context gives:

- `CurrentFile.AbsolutePath` — the open file, for example `/solution/Flow/new.flow`.
- `CurrentFile.IsCurrentFileEmpty` — `true` when the open `.flow` has no flow yet.
- `CurrentProject.AbsolutePath` — the open project, for example `/solution/Flow`.
- `CurrentWorkingDirectory` — the shell's directory; it can differ from the project, so `cd` there first.

Choose the target `.flow` in order:

1. The user names an existing `.flow`: edit it.
2. An edit: edit the `.flow` at `CurrentFile.AbsolutePath`.
3. A new flow, and `IsCurrentFileEmpty` is `true`, you just created the project, or the project holds only an empty or trigger-only `new.flow`: fill that `new.flow` ([Lifecycle](#lifecycle)).
4. A different new flow, and `new.flow` already has steps: write a new `<Name>.flow` in the open project ([Lifecycle](#lifecycle)). Then tell the user to open it in the Explorer: a write refreshes the canvas only for the open file.

Under rule 3 never write a second `.flow`: the request's flow name names no file. A copy the user asks for is fine.

In every reference, `<Project>` is the target's folder, `<Name>` its file name without `.flow`: `new` for `new.flow`, never the flow's name. `<Draft>` is `/tmp/flow-draft/<Project>/<Name>`.

**The target `.flow` is the single source of truth.** The user can change it on the canvas between turns, so never reuse an earlier turn's `.flow.ts`: decompile a fresh one.

**Drafts live in two places.** `/solution/<Project>/.flow-sdk/` keeps `<Name>.flow.ts`, the undo copy `undo/<Name>.flow` and the `prepare` output. `<Draft>/baseline/` and `<Draft>/edited/` are throw-away: each turn rebuilds them; a page reload clears `/tmp`. Give each `.flow` its own folder: compile writes inline-agent files next to it ([`references/brownfield.md`](references/brownfield.md#why-three-directories-inline-agents)).

**Never delete or rename a file under `/solution`:** the file system refuses both; overwrite it instead.

**A read-only page refuses every write.** When the page shows "Locked by you" and an Edit button, writes fail, sometimes as `[object Object]`. Ask the user to click Edit, then retry.

**The Flow SDK can be off for this user.** When an SDK verb answers `ConfigError` "this host has no way to run …", it is off. Say so, and stop.

Every `uip` call prints a harmless `[WARN] [Telemetry] applicationinsights package not available`.

### Commands in Studio Web

Commands that differ in Studio Web:

| Command | In Studio Web |
| --- | --- |
| `uip maestro flow check`, `compile`, `decompile`, `merge` | Work, inside the page. `decompile` writes no pipeline helper. `merge` takes only `--original`, `--baseline`, `--strict` and `-o`. `check` refuses a compiled `.flow`: use `validate`. |
| `uip maestro flow validate`, `format` | Work. Never `format` a merged file. |
| `uip maestro flow nodes …`, `edges …`, `variables …` | Work: they edit the target `.flow` in place; the canvas reloads the open file. |
| `uip maestro flow registry get`, `search`, `list`, `pull` | Work: the product node registry. |
| `uip maestro flow extraction check` | Works: it answers whether the tenant of the session can run an Extract document node. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | Answered by the CLI, with no effect: it confirms the library of the session, ignores its options, and writes no `./connectors/<key>.ts` modules. |
| `uip maestro registry path` | Not available: there is no local library cache. |
| `uip solution resources add`, `list` | Work. |
| `uip solution resources refresh` | Fails: no local `.uipx`. Add connections with `resources add` ([the connector loop](#the-connector-loop-in-studio-web), step 7). |
| `uip solution publish`, `uip solution deploy run` | Work. Studio Web packages and signs in for `publish`. |
| `uip maestro flow debug "<Project>" --inputs '{}'` | Works: a real run of the flow open in the designer. Without `--inputs` it waits on a dialog. |
| `uip solution pack`, `upload`, `init` | Not available. Studio Web owns the solution. |
| `uip login` | Not available. You are already signed in to the user's tenant. |
| `npm`, `node`, the `flow-sdk` bin, `uv`, `uip codedagent` | Not available. Studio Web cannot create a coded agent. |

For a command that is not available, use the Studio Web route this guide gives. With no route, tell the user.
<!--skill-flavor:sdk-project-layout:end-->

<!--skill-flavor:sdk-connector-discovery:start-->
Integrations with non-UiPath systems use connectors. **Choose the node before writing it.** For an external service or data (weather, Slack, a REST API), run `uip maestro registry search '<brand or service name>'`, unless the request names the transport itself ("over HTTP, not a connector" means `http()`). A hit is a connector. `"total": 0` is a miss and means `http()` (not for an external agent: see the table). For another tenant capability (agent, process), run the `uip maestro flow registry search` of that family ([`references/agent.md`](references/agent.md)). For document extraction, default to a published IXP model ([`references/ixp.md`](references/ixp.md)); the Extract document node only when asked for by name or already in the flow ([`references/extract-document-node.md`](references/extract-document-node.md)). A `script()` that returns fixed values is never a stand-in for that step, and `mock()` only marks a capability that the search proved absent.

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
5. **Check:** `uip maestro flow check .flow-sdk/<Name>.flow.ts --source` (edits add `--baseline`: [Lifecycle](#lifecycle)). It also reports the required fields of the project from the prepared page (for example Jira `components`). Run each `prepare` it names, then check again.
6. **Compile; an edit also merges** ([Lifecycle](#lifecycle)).
7. **Add each connection to the solution.** Then read each `connection` row in `bindings_v2.json` of the project. For each row, run `uip solution resources add --source remote --kind connection --cloud-key <ConnectionId>`. If the file has no such row, use the `resourceKey` of each `ConnectionId` entry in `.flow-sdk/bindings.json`. Without this step, the node shows "The selected resource is not part of the solution". Check the result with `uip solution resources list --source local --output json`.

Connectors require [`.flow-sdk/bindings.json`](references/bindings.md).
`CONNECTOR_NOT_IN_LIBRARY`, `CONNECTOR_OBJECT_REQUIRED` and `CONNECTOR_OBJECT_NOT_GENERIC` are source fixes, not prepares: [connector-params.md](references/connector-params.md#author-first--check-names-every-prepare-you-owe).

Schema-dynamic operations (`loadByDefault`, dependent dropdowns, `customFieldsRequestDetails`) need the prepare `check` names with every required `-f`, and a post-compile cache check: [`references/connector-params.md`](references/connector-params.md#schema-dynamic-operations-the-parent-field-loop).
<!--skill-flavor:sdk-connector-discovery:end-->

<!--skill-flavor:sdk-lifecycle:start-->
**A new flow** (rule 3) fills the project's `new.flow`:

```bash
cd /solution/<Project>
uip maestro flow decompile new.flow -o .flow-sdk/new.flow.ts --no-pipeline
# Add your steps to it:
uip maestro flow check .flow-sdk/new.flow.ts --source
uip maestro flow compile .flow-sdk/new.flow.ts -o new.flow
uip maestro flow format new.flow --output json
uip maestro flow validate new.flow --output json
```

An empty `new.flow` fails `decompile`, and a rule 4 flow has no file yet: write `.flow-sdk/<Name>.flow.ts` from [Hello world](#hello-world-flow) and run the rest on `<Name>.flow`. If `check` or `validate` fails, fix the source and rerun from `check`.

**An edit** round-trips through the target `.flow`. Merge keeps layout and sidecars and moves nodes to make room: never move them back or edit the merged `.flow`.

```bash
cd /solution/<Project>
mkdir -p .flow-sdk/undo <Draft>/baseline <Draft>/edited
# 1. Seed, every turn: target copy, fresh source, pristine baseline
cp <Name>.flow .flow-sdk/undo/<Name>.flow
uip maestro flow decompile <Name>.flow -o .flow-sdk/<Name>.flow.ts --no-pipeline
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Draft>/baseline/<Name>.flow
# 2. Edit .flow-sdk/<Name>.flow.ts narrowly (no .layout() for added steps: merge places them), then check until clean
#    (refused, or step 1 stopped: references/brownfield.md#check-only-what-you-changed-check---baseline)
uip maestro flow check .flow-sdk/<Name>.flow.ts --source --baseline .flow-sdk/undo/<Name>.flow
# 3. Compile the edit (step 2 is the gate), then merge into the target, never a copy
uip maestro flow compile .flow-sdk/<Name>.flow.ts -o <Draft>/edited/<Name>.flow
uip maestro flow merge <Draft>/edited/<Name>.flow --original <Name>.flow --baseline <Draft>/baseline/<Name>.flow -o <Name>.flow
# 4. Validate the file the canvas shows
uip maestro flow validate <Name>.flow --output json
```

**A flow holding an Extract document node skips this round trip** — its baseline compile fails on that node; use the direct commands ([`references/extract-document-node.md`](references/extract-document-node.md)).

Valid is top-level `Result` plus `Data.Status: "Valid"`. Treat `Data.Warnings` as failures, except the reviewed shared-connection advisory and `err()` diagnostics. If an edit fails `validate`, fix the source and rerun steps 2 to 4. To undo the merge, copy `.flow-sdk/undo/<Name>.flow` back over the target.

- **An edit always ends with the merge into the target.** About 400 ms after a write, the canvas reloads the open file. Never run `format` on the merged file: it re-lays out the user's canvas.
- **A baseline compile that refuses a draft node** (a generic operation with no object picked) stops the round trip: [`references/brownfield.md`](references/brownfield.md#flows-with-draft-nodes-let-merge-compile).
- **If the baseline compile refuses a canvas node**, run step 2. A node it marks `(pre-existing)` is a probable SDK defect: stop and tell the user (UiPath/builder-sdk#1402).
- **A flow with connectors** needs each connection in the solution afterwards ([the connector loop](#the-connector-loop-in-studio-web), step 7).

Run the flow only for a stated runtime-behavior claim. `uip maestro flow debug "<Project>" --inputs '{}'` is a real run: ask per references/operate.md. The reply is plain text and waits up to 120 s (`--timeout <s>`, max 150). `TimedOut` means the run is still going, not that it failed: do not re-run it. If it names the dialog, ask the user to click Save & Debug. First add each connection to the solution (connector loop, step 7). Do not run `uip solution resources refresh`: it fails in this host. Or ask the user to run it from the designer.
<!--skill-flavor:sdk-lifecycle:end-->

<!--skill-flavor:sdk-editing:start-->
In brownfield work, preserve the supplied source, step names, and unaffected wiring. Insert a step by moving the old edge through it, not by creating a second path. Edit the decompiled source narrowly and let the merge carry only that delta back ([Lifecycle](#lifecycle)). Validate the merged target `.flow`, never `<Draft>/edited/`. A `.flow-sdk/original/` left by an older turn is stale: never pass it to merge. Studio Web has no pipeline helper: `decompile` here never writes one.

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
with `uip maestro flow debug "<Project>" --inputs '{}'`.
Publish the open solution with `uip solution publish` (the destination is the
user's choice). `flow debug` is a REAL run, not a validation step: ask first, as it says. Read
**[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:sdk-operate:end-->
