<!--skill-flavor:host-setup:start-->
## Studio Web

**The builder SDK is built in.** `uip maestro bpmn check`, `compile`, `decompile` and `merge` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: there is no `npm`, no Node process and no Python here.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another. Each project is a folder `/solution/<Project>/` with its `.bpmn`, `project.uiproj` and package files. Create a BPMN project only when the user asks for a new project: run `uip maestro bpmn init <Project>` from `/solution`. A `Data.AutoCreatedSolution` in the response means `init` ran outside the open solution: run it again from `/solution` and report the stray directory.

**Edit the open process.** The context of each turn gives these values:

- `CurrentFile.AbsolutePath` — the open file, for example `/solution/Approval/Approval.bpmn`.
- `CurrentFile.IsCurrentFileEmpty` — `true` when the open `.bpmn` holds no process yet.
- `CurrentProject.AbsolutePath` — the open project, for example `/solution/Approval`.
- `CurrentWorkingDirectory` — the directory of the shell. It can differ from the project, so `cd` to the project first.

The target is the `.bpmn` the user names, else the `.bpmn` at `CurrentFile.AbsolutePath`. Below, `<Project>` is the folder of the target, `<Name>` is the file name of the target without `.bpmn`, and `<Draft>` is `/tmp/bpmn-draft/<Project>/<Name>`.

**The target `.bpmn` is the single source of truth.** The user can change it on the canvas between your turns. So never use a `.bpmn.ts` from an earlier turn: decompile a fresh one every turn.

**Drafts live in two places.** `/solution/<Project>/.flow-sdk/` keeps `<Name>.bpmn.ts`, the undo copy `original/<Name>.bpmn` and the `registry prepare` output. `<Draft>/baseline/` and `<Draft>/edited/` hold throw-away copies: each turn rebuilds them, and a page reload clears `/tmp`.

**Never delete or rename a file under `/solution`.** The project file system refuses both. Overwrite the file instead. `ls -l` shows every file there as 0 bytes: use `wc -c` for a size.

**A read-only page refuses every write.** When the page shows "Locked by you" and an Edit button, a write fails, sometimes as `[object Object]`. Tell the user to click Edit, then try again.

**The builder SDK can be off for this user.** When an SDK verb answers `ConfigError` "this host has no way to run …", the builder SDK is not enabled for this user. Say so, and stop.

Every `uip` call prints `[WARN] [Telemetry] applicationinsights package not available`. This warning is harmless.

### Commands in Studio Web

Some commands in the references do not work in Studio Web. Use this table:

| Command | In Studio Web |
| --- | --- |
| `uip maestro bpmn check`, `compile`, `decompile`, `merge` | Work, inside the page. `merge` takes only `--original`, `--baseline` and `-o`. Check a compiled `.bpmn` with `validate`. |
| `uip maestro bpmn format`, `refresh`, `validate` | Work. `format` lays out the whole diagram again: see the [Validation loop](#validation-loop). |
| `uip maestro bpmn registry search`, `get`, `list`, `pull` | Work: the extension-type catalog. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | Answered by the CLI, with no effect: the library of the session is always loaded. |
| `uip solution resources add`, `list` | Work. |
| `uip solution resources refresh` | Fails: no local `.uipx`. Add connections with `resources add` (the [Validation loop](#validation-loop)). |
| `uip solution publish`, `uip solution deploy run` | Work. Studio Web packages and signs in for `publish`. |
| `uip maestro bpmn debug "<Project>" --inputs '{}'` | Works: a real run of the process open in the designer ([`references/operate.md`](references/operate.md)). |
| `uip maestro bpmn debug-instances variables`, `variables-all`, `incidents` | Work, with the `Trace ID` that `debug` prints. |
| `uip maestro bpmn pack`, `uip solution pack`, `upload` | Not available. Studio Web owns the solution. |
| `uip maestro bpmn eval` | Not available: no evaluators, eval sets, simulations or eval runs ([Evaluating a process](#evaluating-a-process)). |
| `uip login` | Not available. You are already signed in to the tenant of the user. |
| `node -e` | Works for a small script with `fs`. It has no `crypto` and no `uuidgen`. |
| `npm`, `npx`, the `flow-sdk` bin, `python3` | Not available. |

When a reference tells you to run a command that is not available, use the Studio Web route that this guide gives. If there is no route, tell the user.

<!--skill-flavor:host-setup:end-->

<!--skill-flavor:workflow-scaffold:start-->
1. The project already exists: the open project in `/solution`, with its
   `.bpmn`, `project.uiproj` and package files ([Studio Web](#studio-web)).
   Run `uip maestro bpmn init <Project>` from `/solution` only for a new
   project the user asks for.
2. Keep the source at `/solution/<Project>/.flow-sdk/<Name>.bpmn.ts`, and run
   every command from `/solution/<Project>`.
<!--skill-flavor:workflow-scaffold:end-->

<!--skill-flavor:workflow-seed:start-->
4. Seed the source every turn by decompiling the target —
   `uip maestro bpmn decompile <Name>.bpmn -o .flow-sdk/<Name>.bpmn.ts --style nested` — rather than
   hand-writing the skeleton. A new project's `.bpmn` is the template Studio Web or `init` wrote: decompile it too.
   Its source has `.metadata({ entryPointId: false })`: delete that key, or `refresh` fails. The SDK then derives the id.
<!--skill-flavor:workflow-seed:end-->

<!--skill-flavor:workflow-compile:start-->
5. Run `uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --source` after each edit, and fix
   every error it prints (it exits non-zero) before you compile. `compile` writes what
   the source says; `check` is what reports a probable mistake, such as a `vars.<id>`
   read of a variable nothing declares (`EXPR_UNDECLARED_REF`) or a declared variable
   read without `vars.` (`EXPR_BARE_VAR_REF`). For two of these, a read in an
   `errorMapping` condition and a bare `=amount`, `check` is the only offline gate:
   `bpmn validate` accepts both. Studio Web ships its own SDK: an older one refuses the
   read in `compile` itself.
6. Compile the edit into `<Draft>/edited/`, merge it into the target, then
   `refresh` and `validate` — in that order, every time
   ([Validation loop](#validation-loop)). Lay out the diagram only when they
   report a missing shape. `compile` writes no diagram, and `merge` keeps the
   shapes the target already has. Exactly one `<Name>.bpmn`
   exists in the project: the target. Compile straight over it only when it
   is empty.
<!--skill-flavor:workflow-compile:end-->

<!--skill-flavor:workflow-merge:start-->
8. Every change is a targeted edit of the target, so every change goes through
   the merge pipeline of the [Validation loop](#validation-loop).
<!--skill-flavor:workflow-merge:end-->

<!--skill-flavor:api-index-location:start-->
Indexed in the SDK that Studio Web ships, not here. Its package root is
`/plugins/bundled/uipath-studio-web/flow-sdk/`, and a row's path is relative to
it. `dist/api-members.md` is keyed by field or method name (`gateway`), and
`dist/api-index.md` by exported symbol (`BpmnBuilder`). Match one name with
`grep` — do not read either file end to end — then read the span it gives you:
the whole declaration, doc comment included.
<!--skill-flavor:api-index-location:end-->

<!--skill-flavor:validation-loop:start-->
Every change is the same round trip through the target `.bpmn`. Merge keeps
what the SDK does not model (layout, extension rows). Run it from the project
folder:

```bash
cd /solution/<Project>
mkdir -p .flow-sdk/original <Draft>/baseline <Draft>/edited
# 1. Seed, every turn: a copy of the target, a fresh source, the pristine baseline
cp <Name>.bpmn .flow-sdk/original/<Name>.bpmn
uip maestro bpmn decompile <Name>.bpmn -o .flow-sdk/<Name>.bpmn.ts --style nested
uip maestro bpmn compile .flow-sdk/<Name>.bpmn.ts -o <Draft>/baseline/<Name>.bpmn
# 2. Edit .flow-sdk/<Name>.bpmn.ts narrowly, then check until clean
uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --source
uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --graph   # the resolved wiring, implied edges marked ~>
# 3. Compile the edit, then merge the delta into the target
uip maestro bpmn compile .flow-sdk/<Name>.bpmn.ts -o <Draft>/edited/<Name>.bpmn
uip maestro bpmn merge <Draft>/edited/<Name>.bpmn --original <Name>.bpmn --baseline <Draft>/baseline/<Name>.bpmn -o <Name>.bpmn
# 4. The package files, then the product's own check on the file the canvas shows
uip maestro bpmn refresh . --output json
uip maestro bpmn validate <Name>.bpmn --output json
# 5. Only when step 4 reports MISSING_DI_SHAPE or MISSING_DI_EDGE: lay out the diagram, then run step 4 again
uip maestro bpmn format <Name>.bpmn
```

- **Step 1 runs once per turn.** When a later step fails, fix the source and
  start again at step 2. Step 1 again would copy the merged file over the undo
  copy and the baseline.
- **Step 5 lays out the whole canvas again.** `merge` keeps every shape of the
  target, also where the user moved it. A newer SDK also draws the shapes of
  new elements; an older one draws none, and step 4 then reports
  `MISSING_DI_SHAPE` or `MISSING_DI_EDGE`. Only then run step 5, run step 4
  again, and tell the user that the canvas layout was reset.
- **An empty target** gives `decompile` nothing to read. Write
  `.flow-sdk/<Name>.bpmn.ts` from [Minimal shape](#minimal-shape), run step 2,
  compile it straight to `<Name>.bpmn`, then run step 5 and step 4.
- **To undo the merge**, copy `.flow-sdk/original/<Name>.bpmn` back over the
  target, then run step 4.
- **The canvas re-renders the open file after each write.** Always finish with
  the merge into the target; never `uip solution upload`.
- **A process with connectors** needs each connection in the solution. After
  step 4, read each `connection` row in `bindings_v2.json`. For each one that
  `uip solution resources list --source local --output json` does not list,
  run `uip solution resources add --source remote --kind connection --cloud-key <ConnectionId>`.
  Never run `uip solution resources refresh`: it fails here.
  `check` does not read `.flow-sdk/bindings.json`, so `compile` is the step
  that reports a binding name the file does not declare.
<!--skill-flavor:validation-loop:end-->

<!--skill-flavor:operating:start-->
Debug, publish, deploy, run a deployed process, inspect a job, and drive an
instance's lifecycle. You are already signed in to the tenant of the user.
Before every publish or debug, run `uip maestro bpmn refresh .` and make sure
each connection is in the solution ([Validation loop](#validation-loop)).
Run the process with `uip maestro bpmn debug "<Project>" --inputs '{}'`.
Its `Trace ID` is the debug instance id: to report a value, read it with
`uip maestro bpmn debug-instances variables <Trace ID> --output json`, never
from the process logic.
Publish the open solution with `uip solution publish` (the destination is the
user's choice). `bpmn debug` is a REAL run, not a validation step. Every
mutation needs the user's decision for that action. Read
**[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:operating:end-->

<!--skill-flavor:evaluating:start-->
Evaluations are not available in Studio Web.
`uip maestro bpmn eval` (evaluators, eval sets, simulations and eval runs) is not a command here, so do not follow [`references/evaluate.md`](references/evaluate.md).
When the user asks to evaluate a process, tell them that evaluations run from the `uip` CLI on their own machine, outside Studio Web.
<!--skill-flavor:evaluating:end-->

<!--skill-flavor:evaluate-row:start-->
| Evaluate a process: evaluators, eval sets, data points, simulations, eval runs | Not available in Studio Web | [Evaluate](references/evaluate.md) says what to tell the user | — |
<!--skill-flavor:evaluate-row:end-->
