<!--skill-flavor:host-setup:start-->
**In Studio Web the builder SDK is built in.** `uip maestro case check`, `compile`, `decompile` and `validate` run `@uipath/maestro-builder-sdk` inside the page. Install nothing: there is no `npm` or Node here. `examples/` holds authored examples, and `references/` the details this guide routes to.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another. Each project is a folder `/solution/<CaseName>/`. Write `<Name>.case.ts` in `/solution` (beside the Case project folder, not inside it).

### Commands in Studio Web

Some commands in the references do not work in Studio Web. Use this table:

| Command | In Studio Web |
| --- | --- |
| `uip maestro case check`, `compile`, `decompile` | Work, inside the page. |
| `uip maestro case validate` | Works. |
| `uip maestro case init` | Works: creates the Case project inside `/solution`. |
| `uip maestro case registry pull`, `sdd resolve` | Work: already authenticated. |
| `uip maestro case spec`, `tasks describe` | Work: metadata reads. |
| `uip maestro case debug` | Works: a real run of the case. Ask first — it executes real emails, messages, and API calls. |
| `uip maestro registry search`, `describe`, `prepare` | Work: the connector library. Run `prepare` from the project folder. |
| `uip maestro registry pull` | Answered by the CLI, with no effect: it confirms the library of the session, ignores its options, and writes no `./connectors/<key>.ts` modules. |
| `uip solution resources add`, `list`, `remove` | Work. |
| `uip solution resources refresh` | Fails: no local `.uipx`. Add connections with `resources add`. |
| `uip solution publish` | Works. Studio Web packages and signs in for `publish`. |
| `uip solution pack`, `upload`, `init` | Not available. Studio Web owns the solution. |
| `uip login` | Not available. You are already signed in to the tenant of the user. |
| `npm`, `node` | Not available. |

When a reference tells you to run a command that is not available, use the Studio Web route that this guide gives. If there is no route, tell the user.

**The solution manifest (`.uipx`) belongs to Studio Web.** Never run `uip solution init`, `uip solution pack`, or any command that creates or replaces a `.uipx` file. The workspace already has exactly one; a second manifest is never recoverable in-session. After `validate` passes, stop — do not attempt to package, export, or download the solution.

Every `uip` call prints a harmless `[WARN] [Telemetry] applicationinsights package not available`.
<!--skill-flavor:host-setup:end-->

<!--skill-flavor:workflow-scaffold:start-->
1. Scaffold the project inside the open solution: `cd /solution && uip maestro case init <CaseName>`. Studio Web already has a solution — never run `uip solution init`. Write `<Name>.case.ts` in `/solution` (beside the Case project folder, not inside it). The SDK is pre-installed; do not run `npm install`.
<!--skill-flavor:workflow-scaffold:end-->

<!--skill-flavor:workflow-build:start-->
5. Seed the source by decompiling the plan `case init` seeded (`caseplan.case`) instead of hand-writing the skeleton: `uip maestro case decompile <project>/<plan> -o <Name>.case.ts --no-pipeline`. It carries the case id, `.name`, `.identifier` and `trigger_1` the product already assigned; `entry-points.json` references that trigger id. Compile back into that same `<plan>`, never a second plan beside it. Compile with plain `-o <project>/<plan>` and no `--bindings <plan>`. Author inside the chain; the trailing `preserveCaseJson(...)` is decompiler-owned wire data — never hand-edit it, and leave it in place. For shape, copy the closest staged `examples/*.case.ts`.
6. Run `uip maestro case check <Name>.case.ts --source` before every compile, gate edits included (`skipWhen`, a rule `expression`); fix every error (non-zero exit) first. For instance, `check` reports a `vars.<id>` read of an undeclared variable as `EXPR_UNDECLARED_REF`.
7. Compile into the scaffolded Case project, then validate. Compile syncs existing sidecars; add connections with `uip solution resources add` (not `resources refresh`, which fails here) before validate.
8. Run live debug only when requested and tenant resources are available.
<!--skill-flavor:workflow-build:end-->

<!--skill-flavor:api-index-location:start-->
**Every signature, option shape and field is indexed in the SDK that Studio Web ships**, not in this guide. Its package root is `/plugins/bundled/uipath-studio-web/flow-sdk/`, and a row's path is relative to it:

| you have | look in | a row gives you |
| --- | --- | --- |
| a field or method — `sla`, `stage` (the usual case) | `dist/api-members.md` | the shape that declares it, and the lines that do |
| an exported symbol — `CaseBuilder`, `casePlan` | `dist/api-index.md` | its kind, area, and the lines that declare it |

**Match one name; do not read either file end to end** — `grep` it. Then read the span (e.g. `dist/case/builder.d.ts:42-60`): the whole declaration with its doc comment, so one read answers the question. A name in neither index is probably a RUNTIME output key, which the node references carry.
<!--skill-flavor:api-index-location:end-->

<!--skill-flavor:validation-loop:start-->
```bash
uip maestro case check <Name>.case.ts --source
uip maestro case compile <Name>.case.ts -o <project>/<plan>
uip maestro case validate <project>/<plan> --strict --sdd <sdd.md> --output json
uip maestro case validate <project>/<plan> --strict --output json
uip solution resources remove <orphan-key> --solution-folder /solution --output json
uip solution resources add --source remote --kind connection --cloud-key <ConnectionId>
```
Do not run `uip solution resources refresh` — it fails in Studio Web. Add each connection with `resources add` instead.
<!--skill-flavor:validation-loop:end-->

<!--skill-flavor:library-pull:start-->
Before `check` on a Case with connector work, run `uip maestro registry pull`:
with no library cached these rules stay silent, so a clean `check` proves
nothing about the connector. `registry pull` in Studio Web confirms the
library of the session; it does not write local `./connectors/<key>.ts`
modules. To prepare a connector, run `uip maestro registry prepare` from the
project folder.
<!--skill-flavor:library-pull:end-->
