<!--skill-flavor:host-setup:start-->
## Studio Web

**The builder SDK is built in.** `uip maestro case check`, `compile` and `decompile` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: there is no `npm` and no Python here.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another. Each project is a folder `/solution/<Project>/` with its plan file, `project.uiproj` and package files. Create a Case project only when the user asks for a new project: run `uip maestro case init <Project>` from `/solution`. A `Data.AutoCreatedSolution` in the response means `init` ran outside the open solution: run it again from `/solution` and report the stray directory.

**Edit the open plan.** The context of each turn gives these values:

- `CurrentFile.AbsolutePath` — the open file, for example `/solution/Claims/caseplan.case`.
- `CurrentProject.AbsolutePath` — the open project, for example `/solution/Claims`.
- `CurrentWorkingDirectory` — the directory of the shell. It can differ from the project, so `cd` to the project first.

The target is the plan file the user names, else the plan file of the open project: `caseplan.case`, else `caseplan.json`. Below, `<Project>` is the folder of the target, and `<Plan>` is the file name of the target.

**The target plan is the single source of truth.** The user can change it in the designer between your turns. So never use a `.case.ts` from an earlier turn: decompile a fresh one every turn.

**Drafts live in `/solution/<Project>/.flow-sdk/`.** It keeps the source, the undo copy `original/<Plan>` and the `registry prepare` output. The source is always `.flow-sdk/<Project>.case.ts`, never named after `<Plan>`. Ignore any other `.case.ts` in `.flow-sdk/`: it is left over from an earlier turn and tells you nothing about the undo copy. The undo copy is the target as it was at the start of the last turn that edited it.

**Never delete or rename a file under `/solution`.** The project file system refuses both. Overwrite the file instead. `ls -l` shows every file there as 0 bytes: use `wc -c` for a size.

**A read-only page refuses every write.** When the page shows "Locked by you" and an Edit button, a write fails, sometimes as `[object Object]`. Tell the user to click Edit, then try again.

**The builder SDK can be off for this user.** When an SDK verb answers `ConfigError` "this host has no way to run …", the builder SDK is not enabled for this user. Say so, and stop.

Every `uip` call prints `[WARN] [Telemetry] applicationinsights package not available`. This warning is harmless.

### Commands in Studio Web

Some commands in the references do not work in Studio Web. Use this table:

| Command | In Studio Web |
| --- | --- |
| `uip maestro case check`, `compile`, `decompile` | Work, inside the page. |
| `uip maestro case validate` | Works, with `--strict` and `--sdd`. |
| `uip maestro case sdd convert` | **Do not use as a build path.** Output has flat connector inputs (`CASE_MGMT_CONNECTOR_INPUT_FLATTENED`), unresolved cross-task references, and no `registry prepare` — `validate` will reject it. If used as a seed, decompile its output, author the TypeScript source, then check → compile → validate. Never submit the convert output directly. |
| `uip maestro case registry pull` | Works — **this is the one you need** for case resource discovery (action apps, processes, agents). Pulls tenant resource indexes to `~/.uip/case-resources/`. Not the same as `uip maestro registry pull` below. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | **No-op in Studio Web** (the connector library of the session is always loaded). Not the same as `uip maestro case registry pull` above — that one pulls case resources and works. |
| `uip solution resources add`, `list` | Work. |
| `uip solution resources refresh`, `remove` | Not available: no local `.uipx`. Add connections with `resources add` (the [Validation loop](#validation-loop)). |
| `uip solution publish`, `uip solution deploy run` | Work. Studio Web packages and signs in for `publish`. |
| `uip maestro case debug "<Project>" --inputs '{}'` | Works: a real run of the case saved in the open solution (step 8 of the [Workflow](#workflow)). Without `--inputs` it waits on a dialog. |
| `uip maestro case instances get`, `element-executions`, `incidents` | Not useful: 400 (`PIMS-150001`) without `--folder-key`, 404 or empty with the debug folder's key. Read a run with `uip traces spans get` (step 8 of the [Workflow](#workflow)). |
| `uip maestro case pack`, `uip solution pack`, `upload`, creating a solution | Not available. Studio Web owns the solution. |
| `uip login` | Not available. You are already signed in to the tenant of the user. |
| `node -e` | Works for a small script with `fs`. It has no `crypto` and no `uuidgen`. |
| `npm`, `npx`, the `flow-sdk` bin, `python3` | Not available. |

When a reference tells you to run a command that is not available, use the Studio Web route that this guide gives. If there is no route, tell the user.

<!--skill-flavor:host-setup:end-->

<!--skill-flavor:workflow-scaffold:start-->
1. The project already exists: the open project in `/solution`, with its plan
   file, `project.uiproj` and package files ([Studio Web](#studio-web)). Run
   `uip maestro case init <Project>` from `/solution` only for a new project
   the user asks for, and never create a solution.
2. Keep the source at `/solution/<Project>/.flow-sdk/<Project>.case.ts`, and run
   every command from `/solution/<Project>`.
<!--skill-flavor:workflow-scaffold:end-->

<!--skill-flavor:workflow-build:start-->
5. Seed the source every turn by decompiling the target instead of hand-writing the skeleton: `uip maestro case decompile <Plan> -o .flow-sdk/<Project>.case.ts --no-pipeline`. A new project's plan is the one Studio Web or `case init` seeded: decompile it too. It carries the case id, `.name`, `.identifier` and `trigger_1` the product already assigned; `entry-points.json` references that trigger id. Compile back into the target, never a second plan beside it: Studio Web reads only one. Compile with plain `-o <Plan>` and no `--bindings <Plan>` ([Brownfield](references/case-runtime.md#brownfield-editing)). Author inside the chain; the trailing `preserveCaseJson(...)` is decompiler-owned wire data — never hand-edit it, and leave it in place. For shape, copy the closest staged `examples/*.case.ts`.
6. Run `uip maestro case check .flow-sdk/<Project>.case.ts --source` before every compile, gate edits included (`skipWhen`, a rule `expression`); fix every error (non-zero exit) first. For instance, `check` reports a `vars.<id>` read of an undeclared variable as `EXPR_UNDECLARED_REF`.
7. Compile into the target, then validate, then make sure each connection is in the solution — the [Validation loop](#validation-loop). Never run `uip solution resources refresh` or `remove`: both fail here.
8. Run live debug only when the user asks for it and tenant resources are available. A debug run is a REAL run: it sends emails, posts messages and calls APIs.

   ```bash
   uip maestro case debug "<Project>" --inputs '{}'
   uip maestro case debug "<Project>" --inputs '{"claimId": "C-1"}'
   ```

   `<Project>` is a project name in the open solution, not a path. Debug runs the plan saved in the open solution, so there is no pack or upload step. Always pass `--inputs`: the input values as inline JSON, or `'{}'` when the case takes none; `@file` is not supported. Without `--inputs`, Studio Web opens its Debug configuration dialog and the run waits for the user to click **Save & Debug**. The output is plain text, not JSON: the status, `Trace ID: <id>` when one was found, the run logs and the execution trace. Exit 1 means `Faulted` or `Failed`. `TimedOut after <N>s` also exits 1, but the run is still going in Studio Web: do not troubleshoot it, and do not run it again. Tell the user to follow the run in Studio Web.

   To read a run, use `uip traces spans get <TraceId> --output json`: the debug output cuts the trace off, and the `case instance` verbs do not work here. The Trace ID is the instance id. A stage or task with no span did not start.
<!--skill-flavor:workflow-build:end-->

<!--skill-flavor:api-index-location:start-->
Indexed in the SDK that Studio Web ships, not here. Its package root is
`/plugins/bundled/uipath-studio-web/flow-sdk/`, and a row's path is relative to
it. `dist/api-members.md` is keyed by field or method name (`sla`), and
`dist/api-index.md` by exported symbol (`CaseBuilder`). Match one name with
`grep` — do not read either file end to end — then read the span it gives you:
the whole declaration, doc comment included.
<!--skill-flavor:api-index-location:end-->

<!--skill-flavor:validation-loop:start-->
Every change is the same round trip through the target plan. Run it from the
project folder.

Step 1, the seed: once per turn, before the first edit. It writes an undo
copy of the target, then a fresh source:

```bash
cd /solution/<Project>
mkdir -p .flow-sdk/original
cp <Plan> .flow-sdk/original/<Plan>
uip maestro case decompile <Plan> -o .flow-sdk/<Project>.case.ts --no-pipeline
```

Steps 2 and 3, repeated until clean:

```bash
cd /solution/<Project>
# 2. Edit .flow-sdk/<Project>.case.ts narrowly, then check until clean
uip maestro case check .flow-sdk/<Project>.case.ts --source
# 3. Compile back into the target, then the product's own check
uip maestro case compile .flow-sdk/<Project>.case.ts -o <Plan>
uip maestro case validate <Plan> --strict --sdd <sdd.md> --output json  # SDD supplied
uip maestro case validate <Plan> --strict --output json                 # no SDD
```

- **Never re-run the seed after an edit or compile in the same turn.** It
  replaces the undo copy with the compiled plan and the source with a fresh
  decompile, which discards your edits. When a later step fails, fix the
  source and start again at step 2.
- **The designer re-renders the open plan after each write.** Always finish
  with the compile into the target; never `uip solution upload`.
- **To undo the last turn's change**, copy `.flow-sdk/original/<Plan>` back
  over the target before this turn's seed (the seed overwrites the copy),
  then validate again. Restore the copy instead of removing the change by
  hand, and write no other copy of the plan.
- **A case with connector work** needs each connection in the solution. After
  step 3, read each `connection` row in `bindings_v2.json`. For each one that
  `uip solution resources list --source local --output json` does not list,
  run `uip solution resources add --source remote --kind connection --cloud-key <ConnectionId> --output json`.
  A connection that is not in the solution fails at run time with a binding
  error. Never run `uip solution resources refresh` or `remove`: both fail here.
<!--skill-flavor:validation-loop:end-->

<!--skill-flavor:library-pull:start-->
In Studio Web the connector library of the session is always loaded, so
`check` reads it with no pull: `uip maestro registry pull` has no effect.
<!--skill-flavor:library-pull:end-->
