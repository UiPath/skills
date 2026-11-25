<!--skill-flavor:critical-rules-extra:start-->
13. A new process goes into a project's main file in `/solution`: the `.bpmn` its `entry-points.json` names, `Process.bpmn` in a project Studio Web created (`uip maestro bpmn init` included). Studio Web packages any other `.bpmn` only as a non-default entry point and shows nothing outside `/solution`. Before writing a `.bpmn`:
    1. Pick the project: the one the request names (`B`, or `A/B`, names `/solution/B`), else the open one; create a missing one by step 3.
    2. When its main file already holds a process (not empty, and after `decompile`, `check --graph` lists a node besides one start and one end event, all an `init` template has), never build over it unasked. If the request named this project, ask whether to replace its process or use a new project; on *new project*, step 3 settles the name and its question joins this one; on *replace*, build into its main file through the [Validation loop](#validation-loop). When the request says nobody will answer questions, or the project is only the open one, go to step 3 without asking whether to replace.
    3. Settle `<NewProject>` before running `uip maestro bpmn init <NewProject>` from `/solution` or the platform's `CreateProjects` tool (same name): the name the user gave in step 2's answer, else the project the request named in step 1 when step 2 did not send you here, else the request's `.bpmn` name without `.bpmn`. Use it as given, never your own, unless `/solution` already has it: then ask for another (when nobody will answer, add a suffix and list it on `Assumed:`). A process description ("an invoice approval process") is not a name. With no name, ask for one before `init`, offering a short process name as default, inside step 2's question when asked; only when nobody will answer, use that short name. Never pass `--force`.

    A `.bpmn` file name, working directory or "local" project in the request changes none of this, however firmly it says "main file": never add a `.bpmn` of that name or repoint `entry-points.json` at one. Nor does a nested path (`A/B`, `A/B/B.bpmn`): `/solution` projects are flat, so `uip maestro bpmn init A/B` fails; never `mkdir`/`cp` the layout by hand, since a `.bpmn` in a folder under `/solution/B` is not its main file, so the template `Process.bpmn` stays the entry point and fails `validate` (`MISSING_DI_SHAPE`). `init B` answering `already exists` means the project exists: apply step 2, never copy it. Name the project and file used on the final report's `Assumed:` line. An existing `.bpmn` outside `/solution` is edited through a copy ([Studio Web](#studio-web)).
<!--skill-flavor:critical-rules-extra:end-->

<!--skill-flavor:host-setup:start-->
## Studio Web

**The builder SDK is built in.** `uip maestro bpmn check`, `compile`, `decompile` and `merge` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: no `npm`, Node process or Python.

**The open solution is the workspace.** `/solution` is the user's open Studio Web solution; never create another. Each project is a folder `/solution/<Project>/` with its `.bpmn`, `project.uiproj` and package files. Create a BPMN project only when the user asks for one or [Critical Rule 13](#critical-rules) needs one: `uip maestro bpmn init <Project>` from `/solution`. `Data.AutoCreatedSolution` in the response means `init` ran outside the open solution: rerun it from `/solution` and report the stray directory.

**Edit the open process.** Each turn's context gives:

- `CurrentFile.AbsolutePath` — the open file (`/solution/Approval/Process.bpmn`).
- `CurrentFile.IsCurrentFileEmpty` — `true` when the open `.bpmn` holds no process yet.
- `CurrentProject.AbsolutePath` — the open project (`/solution/Approval`).
- `CurrentWorkingDirectory` — the shell's directory; it can differ from the project, so `cd` to the project first.

The target is the `.bpmn` the user names, else the one at `CurrentFile.AbsolutePath`. Check a named `.bpmn` with `ls <path>`: no such file means a new process, built where [Critical Rule 13](#critical-rules) says; a file outside `/solution` stays the target: follow [an existing `.bpmn` outside a `/solution` project](#studio-web). Below, `<Project>` is the target's folder, `<Name>` its file name without `.bpmn`, and `<Draft>` is `/tmp/bpmn-draft/<Project>/<Name>`.

**The target `.bpmn` is the single source of truth.** The user can change it on the canvas between turns, so never reuse a `.bpmn.ts` from an earlier turn: decompile a fresh one every turn.

**Drafts live in two places.** `/solution/<Project>/.flow-sdk/` keeps `<Name>.bpmn.ts`, the undo copy `original/<Name>.bpmn` and the `registry prepare` output. `<Draft>/baseline/` and `<Draft>/edited/` hold throw-away copies, rebuilt each turn; a page reload clears `/tmp`.

**An existing `.bpmn` outside a `/solution` project** (mounted, for example under `/sandbox`, or loose in `/tmp`) has no `project.uiproj`. Outside `/solution` and `/tmp`, file tools, `cp` and `validate` reach it; `decompile`, `compile`, `merge` and `node` answer `ENOENT`, `the builder SDK works only on files under /solution and /tmp` or `path is outside /solution and /tmp`. Ignore the hint to pass a copy under `/solution`: copying it into a project fails (`binary writes are not supported`). Edit a copy:

1. Run `cd /tmp && mkdir -p /tmp/bpmn-work/<Name>` and copy the target there as `<Name>.bpmn`. That folder replaces `/solution/<Project>` in the [Workflow](#workflow) and [Validation loop](#validation-loop); `<Draft>` is `/tmp/bpmn-draft/<Name>`.
2. Run the loop there without `refresh`, whatever the rules say: with no `project.uiproj` it fails. Keep a seeded `.metadata({ entryPointId: false })`: only `refresh` needs the id, and deleting it stamps a new one on the start event. Skip the loop's **A process with connectors** bullet: it reads `bindings_v2.json`, which only `refresh` writes.
3. `cp` the result back over the target (`node` cannot reach it), then `validate` the target and `grep` it for what the edit added (for example `bpmn:subProcess`), since `validate` also passes on an unchanged file. To undo, `cp` the work folder's `.flow-sdk/original/<Name>.bpmn` back over the target.

Never hand-edit the target's XML with `node`, `sed` or a regex instead: a command that answers an error did not run, so the edit is missing and the report must not claim it.

Never run `init` to give an existing file outside `/solution` a project: the user did not ask for one, and its template is a second process that fails `validate`.

**Never delete or rename a file under `/solution`;** the file system refuses both, so overwrite it. `ls -l` shows every file there as 0 bytes: use `wc -c` for a size.

**A read-only page refuses every write.** When the page shows "Locked by you" and an Edit button, writes fail, sometimes as `[object Object]`: tell the user to click Edit, then retry.

**The builder SDK can be off for this user.** An SDK verb answering `ConfigError` "this host has no way to run …" means it is not enabled: say so, and stop.

Every `uip` call prints `[WARN] [Telemetry] applicationinsights package not available`: harmless.

### Commands in Studio Web

Some reference commands do not work in Studio Web:

| Command | In Studio Web |
| --- | --- |
| `uip maestro bpmn check`, `compile`, `decompile`, `merge` | Work in the page; `merge` takes only `--original`, `--baseline` and `-o`. Check a compiled `.bpmn` with `validate`. |
| `uip maestro bpmn format`, `refresh`, `validate` | Work. `format` adds only missing shapes; `format --relayout` lays out the whole diagram again ([Validation loop](#validation-loop)). |
| `uip maestro bpmn registry search`, `get`, `list`, `pull` | Work: the extension-type catalog. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | No effect: the session's library is always loaded. |
| `uip solution resources add`, `list` | Work. |
| `uip solution resources refresh` | Fails: no local `.uipx`. Add connections with `resources add` (the [Validation loop](#validation-loop)). |
| `uip solution publish`, `uip solution deploy run` | Work. Studio Web packages and signs in for `publish`. |
| `uip maestro bpmn debug "<Project>" --inputs '{}'` | Works: a real run of the process open in the designer ([`references/operate.md`](references/operate.md)). |
| `uip maestro bpmn debug-instances variables`, `variables-all`, `incidents` | Work, with the `Trace ID` that `debug` prints. |
| `uip maestro bpmn pack`, `uip solution pack`, `upload` | Not available. Studio Web owns the solution. |
| `uip maestro bpmn eval` | Not available ([Evaluating a process](#evaluating-a-process)). |
| `uip login` | Not available: you are already signed in to the user's tenant. |
| `node -e` | Works for a small `fs` script; no `crypto` or `uuidgen`. |
| `npm`, `npx`, the `flow-sdk` bin, `python3` | Not available. |

For an unavailable command a reference gives, use this guide's Studio Web route; with none, tell the user.

<!--skill-flavor:host-setup:end-->

<!--skill-flavor:workflow-scaffold:start-->
1. Find the project and its main file before you write a `.bpmn`
   ([Critical Rule 13](#critical-rules)).
2. Keep the source at `/solution/<Project>/.flow-sdk/<Name>.bpmn.ts`, and run
   every command from `/solution/<Project>`.
<!--skill-flavor:workflow-scaffold:end-->

<!--skill-flavor:workflow-seed:start-->
4. Seed the source every turn by decompiling the target, never a hand-written skeleton:
   `uip maestro bpmn decompile <Name>.bpmn -o .flow-sdk/<Name>.bpmn.ts --style nested`.
   A new project's `.bpmn` is the template Studio Web or `init` wrote: decompile it too.
   When its source has `.metadata({ entryPointId: false })` and the target is in a project, delete that key, or `refresh` fails; the SDK then derives the id, as the canvas does for a start event without one. A [target outside a project](#studio-web) keeps the key.
<!--skill-flavor:workflow-seed:end-->

<!--skill-flavor:workflow-compile:start-->
5. Run `uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --source` after each edit, and fix
   every error it prints (it exits non-zero) before you compile. `compile` writes what
   the source says; `check` reports probable mistakes, such as a `vars.<id>`
   read of a variable nothing declares (`EXPR_UNDECLARED_REF`) or a declared variable
   read without `vars.` (`EXPR_BARE_VAR_REF`; fix: `=js:vars.<id>`). For two of these, a read in an
   `errorMapping` condition and a bare `=amount`, `check` is the only offline gate:
   `bpmn validate` accepts both. Studio Web ships its own SDK: an older one refuses the
   read in `compile` itself.
6. Compile the edit into `<Draft>/edited/`, merge it into the target, then
   `refresh` and `validate`, in that order, every time; the [Validation loop](#validation-loop)
   says when to lay out the diagram. `compile` writes no diagram; `merge` keeps the target's shapes.
   The project holds exactly one `<Name>.bpmn`, the target; compile straight over it only when it
   is empty. A requested main file `<X>.bpmn` changes nothing: build into the target, never
   copy or compile to `<X>.bpmn` beside it ([Critical Rule 13](#critical-rules)).
<!--skill-flavor:workflow-compile:end-->

<!--skill-flavor:workflow-merge:start-->
8. Every change is a targeted edit of the target, so every change goes through
   the merge pipeline of the [Validation loop](#validation-loop).
<!--skill-flavor:workflow-merge:end-->

<!--skill-flavor:api-index-location:start-->
Indexed in the SDK Studio Web ships, not here; a row's path is relative to its root
`/plugins/bundled/uipath-studio-web/flow-sdk/`. `dist/api-members.md` is keyed by
field or method name (`gateway`), `dist/api-index.md` by exported symbol (`BpmnBuilder`).
`grep` one name, never read either file end to end, then read the span it gives:
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
uip maestro bpmn decompile .flow-sdk/original/<Name>.bpmn -o <Draft>/<Name>.baseline.bpmn.ts --style nested
uip maestro bpmn compile <Draft>/<Name>.baseline.bpmn.ts -o <Draft>/baseline/<Name>.bpmn
# 2. Edit .flow-sdk/<Name>.bpmn.ts narrowly, then check until clean
uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --source
uip maestro bpmn check .flow-sdk/<Name>.bpmn.ts --graph   # the resolved wiring, implied edges marked ~>
# 3. Compile the edit, then merge the delta into the target
uip maestro bpmn compile .flow-sdk/<Name>.bpmn.ts -o <Draft>/edited/<Name>.bpmn
uip maestro bpmn merge <Draft>/edited/<Name>.bpmn --original <Name>.bpmn --baseline <Draft>/baseline/<Name>.bpmn -o <Name>.bpmn
# 4. The package files, then the product's own check on the file the canvas shows
uip maestro bpmn refresh . --output json
uip maestro bpmn validate <Name>.bpmn --output json
# 5a. Only when step 1 seeded a template, the target was empty, or the user chose *replace*: lay out the whole diagram, then run step 4 again
uip maestro bpmn format <Name>.bpmn --relayout
# 5b. Only when step 4 reports BPMN_PARSE_ERROR with No diagrams found, MISSING_DI_SHAPE or MISSING_DI_EDGE: add the missing shapes, then run step 4 again
uip maestro bpmn format <Name>.bpmn
```

- **Run `validate` as its own command, after every change to the `.bpmn`.** Never chain it after `merge`, `format` or `refresh` in one `&&` command. The final report says *validated* only when a `validate` run after the last `.bpmn` change reported `Status: Valid`; else *not validated*, with the reason on `Unverified:`.
- **Step 1 runs once per turn,** except its two baseline lines in the recovery below. When a later step fails, fix the source and
  restart at step 2; rerunning step 1 would copy the merged file over the undo
  copy and the baseline.
- **The baseline is the compile of `.flow-sdk/original/<Name>.bpmn`, never a copy of the target or a compile of the edited `.flow-sdk/<Name>.bpmn.ts`.**
  `merge` treats what the baseline holds and the edit lacks as deleted: a target copy
  holds pools, lanes and diagram the SDK does not model, so `merge` deletes them; the
  edited file shows no change, so `merge` writes the target back unchanged.
  After step 3, run `diff -q <Name>.bpmn .flow-sdk/original/<Name>.bpmn`. No output means `merge` changed nothing and the baseline holds the edit
  (an add, a removal and a property change each make the file differ); judge by this, never by the `Authored` or `Removed` counts.
  When `merge` cannot open the baseline or `diff -q` prints nothing, run `mkdir -p <Draft>/baseline`, rerun step 1's two baseline lines,
  then compile the edit and run step 3's `merge` again; leave step 1's other lines unrun, since they would overwrite the edit.
  When `diff -q` still prints nothing, stop: run no other step, send no final report, and tell the user in one sentence that the edit did not reach `<Name>.bpmn` and the file is as it was.
- **Step 5b keeps the user's layout.** `merge` keeps every target shape where the user
  placed it. A newer SDK also draws new elements; with an older one step 4 reports
  `MISSING_DI_SHAPE` or `MISSING_DI_EDGE` (no diagram at all: `BPMN_PARSE_ERROR` with
  `No diagrams found`). Only then run step 5b: it adds missing shapes and edges, keeping drawn ones.
- **A template or a replaced process takes step 5a** (Studio Web's Tidy up of the whole
  diagram), then step 4, after the merge: step 1's source has no node besides one start
  event and at most one end event (as Studio Web or `init` writes it), or the user chose
  *replace* (Critical Rule 13 step 2), so no user layout exists and step 5b changes nothing.
  If `format` rejects `--relayout` (`unknown option`), run it with no flag. Never pass
  `--relayout` on any other process: it moves every shape the user placed.
- **An empty target** gives `decompile` nothing to read. Write
  `.flow-sdk/<Name>.bpmn.ts` from [Minimal shape](references/minimal-shape.md), run step 2,
  compile it straight to `<Name>.bpmn`, then run step 5a and step 4.
- **To undo the merge**, copy `.flow-sdk/original/<Name>.bpmn` back over the
  target, then run step 4.
- **The canvas re-renders the open file after each write.** Always finish with
  the merge into the target; never `uip solution upload`.
- **A process with connectors** needs each connection in the solution. After
  step 4, for each `connection` row in `bindings_v2.json` that
  `uip solution resources list --source local --output json` does not list,
  run `uip solution resources add --source remote --kind connection --cloud-key <ConnectionId>`.
  Never run `uip solution resources refresh`: it fails here.
  `check` does not read `.flow-sdk/bindings.json`; `compile` reports a binding
  name the file does not declare.
<!--skill-flavor:validation-loop:end-->

<!--skill-flavor:operating:start-->
Debug, publish, deploy, run a deployed process, inspect a job, and drive an
instance's lifecycle; you are already signed in to the user's tenant.
Before every publish or debug, run `uip maestro bpmn refresh .` and make sure
each connection is in the solution ([Validation loop](#validation-loop)).
Run the process with `uip maestro bpmn debug "<Project>" --inputs '{}'`; its
`Trace ID` is the debug instance id: report a value read with
`uip maestro bpmn debug-instances variables <Trace ID> --output json`, never
one from the process logic.
Publish the open solution with `uip solution publish` (destination is the
user's choice). `bpmn debug` is a REAL run, not validation. Every
mutation needs the user's decision for that action. Read
**[`references/operate.md`](references/operate.md)**.
<!--skill-flavor:operating:end-->

<!--skill-flavor:evaluating:start-->
Evaluations are not available in Studio Web: `uip maestro bpmn eval` (evaluators, eval sets, simulations, eval runs) is not a command here, so do not follow [`references/evaluate.md`](references/evaluate.md).
When asked to evaluate a process, tell the user evaluations run from the `uip` CLI on their own machine.
<!--skill-flavor:evaluating:end-->

<!--skill-flavor:evaluate-row:start-->
| Evaluate a process: evaluators, eval sets, data points, simulations, eval runs | Not available in Studio Web | [Evaluate](references/evaluate.md) says what to tell the user | — |
<!--skill-flavor:evaluate-row:end-->

<!--skill-flavor:draft-upload-summary:start-->
Outside plan mode, a mermaid diagram or outline in chat is not the deliverable; the validated target `.bpmn` on the canvas is.
The skeleton goes into the open target and makes no `registry` calls.
The canvas shows it, so there is no upload: the gate reply names the target path, and *Build it* ends with the [final report](references/final-report-template.md).
<!--skill-flavor:draft-upload-summary:end-->
