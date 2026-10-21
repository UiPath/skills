# Execution Maps — Turn-Budgeted Build Journeys

Read once per build. Happy path, including the final report: **greenfield ≤5 turns, brownfield ≤5**; one repair cycle adds ≤2. Each T-row is one assistant message: all tool calls in one message cost one turn; one call per message costs N.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
> **Tool vocabulary.** `Edit` = in-place replacement, `Write` = full-file write, `Read`/`Glob`/`Grep` = read/search, `Bash` = shell. Map these Claude Code names to the harness equivalents. If parallel calls are unavailable, preserve each grouping as consecutive calls; CLI chains still collapse round-trips.

If a harness rejects a batch for permissions, treat it as an approval gate, not a CLI failure; do not split it to evade approval. For Claude Code Bash calls, offer `/uipath:install-permissions` to install the curated allowlist with user approval; use the harness permission mechanism otherwise.

## Source precedence — every activity you author

Use, in order:
1. **Card** — [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md)
2. **Agent memory** — validated prior-session snippet (see [§ Cross-session memory](#cross-session-memory))
3. **Rule 21 triple** — `activities find` → `<Activity>.md` read → `get-default-xaml`, fanned out inside T1/T2

`validate` + `build` gate all three. Card/memory hits skip discovery, never the gate.

## Gate ≠ runtime proof

A clean `validate` + `build` does not prove runtime behavior. Silent failures that pass both include C# `//` in child/CDATA `InvokeCode` `Code` swallowing later code, `WriteTextFile` with explicit `Encoding` emitting a BOM, and stripped UIA `N*` `Version` failing only at runtime ([xaml/common-pitfalls.md](xaml/common-pitfalls.md)). For observable outputs (written files or entry-point out-arguments) with no external systems/UI, run exactly one `uip rpa run --skip-build`, then `cat` every output file; judge that chain in the report turn. Neither run nor output check gets another turn; see T4/T5 below.

## Sequential gates — never batch across these

- Run `templates search` before `init` (Rule 2) only when the user names a template or domain pattern; use its result, including an `AskUserQuestion`, to choose `--template-package-id`.
- Ask the Rule 2a framework/language question when the request has no signal.
- Keep every `AskUserQuestion` and consent gate sequential.
- Keep UIA state advances and indication sequential (see [§ Journey: UIA capture + build](#journey-uia-capture--build-xaml)); capture screens require real application state.

## Journey: Greenfield XAML (no UIA)

Skip project discovery: no `project.json` exists before T1, only the untouched scaffold after it ([environment-setup.md § Skip gate](environment-setup.md)). The parent-directory `ls` is the first link of T1's `Bash` chain, not a turn. Write `project-context.md` and `AGENTS.md` at T5.

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | Run one `Bash` chain: `uip rpa init --name "<NAME>" --location "<PARENT_DIR>" --template-id BlankTemplate --expression-language <VisualBasic\|CSharp> --target-framework <Windows\|Portable> --output json` (Rule 2a; both flags explicit) `&&` `uip rpa analyzer-rules list --project-dir "<PROJECT_DIR>" --output json` `&&` one `uip rpa packages versions --package-id <PackageId> --include-prerelease --project-dir "<PROJECT_DIR>" --output json` per request-known package `&&` `node -e "require('fs').rmSync(process.argv[1],{force:true})" "<PROJECT_DIR>/Main.xaml"`; in parallel, plain full-`Read` ALL THREE, never a subset: [common-activity-card.md](common-activity-card.md), [common-pattern-card.md](common-pattern-card.md), [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) (Rule 22); `Grep` `^## ` on [xaml/common-pitfalls.md](xaml/common-pitfalls.md) for headings (Rule 22, step 1); recall memory; and fan out Rule 21 `activities find` for off-card activities. |
| **T2 — Vet** | In parallel, `Read` every [xaml/common-pitfalls.md](xaml/common-pitfalls.md) section whose T1 heading matches a planned activity, property, or feature; when unsure, read it (Rule 22, step 2); `Read` `project.json`; read needed [xaml/xaml-editing-catalog.md](xaml/xaml-editing-catalog.md) entries for operations beyond the cards; and perform Rule 21 doc `Read`s plus `get-default-xaml` for off-card activities. Do not read `Main.xaml`; T1 deleted the scaffold. This is the only pitfalls-gate turn. |
| **T3 — Author + install** | For row processing, make the design fork first: complex bulk processing (per-row parse + validate + branch + accumulate) escalates to code per [data-manipulation-guide.md § Code vs activity chains](data-manipulation-guide.md); the pattern card's `ForEach` shapes cover only the simple one-`If`/`Switch` case. Then `Write` one complete file per workflow (Rule 18), `Edit` `project.json` for `fileInfoCollection` test cases (Rule 10), and run ONE `Bash` `uip rpa packages install` for all needed packages at T1-chosen versions, using [cli-reference.md § packages install](cli-reference.md#packages-install); on `Invalid packages input`, run `uip rpa packages install --help` again. `dependencies` remains CLI-owned. |
| **T4 — Gate** | Run one sequential `Bash` chain/loop for every edited file: `uip rpa validate --file-path "<RELATIVE_FILE>" --project-dir "<PROJECT_DIR>" --output json` per file `&&` `uip rpa build "<PROJECT_DIR>" --output json` `&&`, when outputs are observable and no external system/UI is needed, `uip rpa run --file-path "<RELATIVE_FILE>" --project-dir "<PROJECT_DIR>" --skip-build --output json` on the entry point (`--file-path` required) `&&` `cat` every requested output file. This output check is part of the chain. `--file-path` is relative to the project directory; absolute paths falsely fail due to a separator bug ([cli-reference.md § validate](cli-reference.md#validate)). |
| **T5 — Report** | Send one message with no shell calls. Judge T4 verdict fields and `cat` output against the request; wrong/empty output with a clean gate indicates silent failure (§ Failure exits). In that message, make parallel calls: `Write` `.claude/rules/project-context.md` and `Write` `AGENTS.md` with paths, metadata, and markers per [environment-setup.md § Project Context Discovery](environment-setup.md) step 3 (first line `<!-- discovery-metadata: cs=N xaml=N deps=N -->`; put the same block in `AGENTS.md` between `<!-- PROJECT-CONTEXT:START -->` / `<!-- PROJECT-CONTEXT:END -->`; do not `Read`/`Grep` first), qualifying memory `Write`s, and § Completion Output. Run nothing afterward. |

T1 is one message: `init`, every read, cards, [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md), and the pitfalls-heading `Grep` all ride together; only section reads wait for T2. Do not open any other reference before T3, including `environment-setup.md`. The first chain call pays the cold Helm restore (30–90 s); do not split it to check progress. `init` may return `success: false` while creating files; check that `project.json` exists before retrying ([environment-setup.md](environment-setup.md)). Install dependencies only through `packages install`; never hand-edit `project.json` `dependencies`.

**Repair cycle (validate/build failure):** use one turn for an `Edit` fixing one root cause (Rule 19, Package first: a skipped `packages install` fails before activity issues), then one turn to rerun the batched gate. Card-covered failures do not reopen discovery; recheck the card. Retain each validation result and build only when all files are error-free. If >2 errors have ambiguous origin, bisect by stubbing half the new activities and re-validating. Maximum 5 attempts per loop (Rule 3).

## Journey: Brownfield XAML edit

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Context** | Run SKILL.md § Precondition context check: skip gate first, then the discovery subagent, which writes `project-context.md` + `AGENTS.md` ([environment-setup.md § Project Context Discovery](environment-setup.md)). In parallel, `Read` `project.json`, target `.xaml`, cards, and [xaml/xaml-basics-and-rules.md](xaml/xaml-basics-and-rules.md) (Rule 22, plain full read); `Grep` `^## ` on [xaml/common-pitfalls.md](xaml/common-pitfalls.md); run ONE `Bash` `analyzer-rules list --project-dir "<PROJECT_DIR>" --output json`; recall memory; and fan out off-card `activities find`. |
| **T2 — Vet** | `Read` matching [xaml/common-pitfalls.md](xaml/common-pitfalls.md) sections (Rule 22), needed [xaml/xaml-editing-catalog.md](xaml/xaml-editing-catalog.md) entries, and off-card Rule 21 docs. |
| **T3 — Edit** | Batch `Edit`s, anchoring each on its own target block; same-file edits serialize and overlapping anchors fail. Run `packages install` in `Bash` when dependencies are new. |
| **T4 — Gate** | Run one sequential `Bash` chain/loop covering every edited file: per-file `validate` with relative `--file-path` `&&` `build` `&&` optional `run --file-path "<RELATIVE_FILE>" --skip-build` `&&` `cat` every output file, per § Gate ≠ runtime proof. |
| **T5 — Report** | Send one message with no shell calls: judge T4 verdict and `cat` output; emit § Completion Output and qualifying memory `Write`s in parallel. The discovery agent wrote context files in T1: do not read, edit, or rewrite them after the gate. The next session judges staleness by file/dependency counts ([environment-setup.md § Project Context Discovery](environment-setup.md)). If the skip gate tripped, write both files exactly as greenfield T5 does. |

## Journey: Greenfield coded

`init` always scaffolds XAML; use the same command and flags as above, then add `.cs` files ([environment-setup.md](environment-setup.md)).

| Turn | Emit in ONE assistant message |
|---|---|
| **T1 — Scaffold + context** | Run ONE `Bash` chain: `init` with the XAML journey flags `&&` `analyzer-rules list` `&&` `packages versions` per known package. In parallel, `Read` [assets/codedworkflow-template.md](../assets/codedworkflow-template.md) and [coded/operations-guide.md § Coding Guidelines](coded/operations-guide.md#coding-guidelines), then recall memory. |
| **T2 — Author + install** | `Write` each `.cs` (Rules 13–19); `Read` `project.json`; `Edit` it for `entryPoints` (Rule 15) and `fileInfoCollection` (Rule 10); run `packages install` in `Bash`; read `.local/docs/packages/<PackageId>/coded/coded-api.md` for installed services. |
| **T3 — Gate** | Run one sequential `Bash` chain/loop over every edited file: per-file relative-`--file-path` `validate` `&&` `build` `&&` optional `run --file-path "<RELATIVE_FILE>" --skip-build` `&&` `cat` every output file, per § Gate ≠ runtime proof. |
| **T4 — Report** | Send one message with no shell calls, using greenfield XAML T5's shape: judge T3 verdict and `cat` output, then parallel `Write`s for both context files, qualifying memory, and § Completion Output. |

## Journey: Brownfield coded edit

Use the brownfield XAML journey with coded reads and no pitfalls-vet turn: T1 `Read` target `.cs` plus `.local/docs/.../coded/coded-api.md` for touched services; T2 `Edit`s plus install; T3 gate; T4 report.

## Journey: UIA capture + build (XAML)

Budget: **~3 fixed turns + ~3 turns per capture-screen + 2-turn debug cycle.** Serialize capture across screens by application state (Complete-then-advance, the target-capture orchestration reference routed from the UIA package guide); never batch across an advance. Route concrete UIA CLI syntax through `{PROJECT_DIR}/.local/docs/packages/UiPath.UIAutomation.Activities/ui-automation-guide.md` § Documentation.

| Turn | Emit in ONE assistant message |
|---|---|
| **T0 — Reads + pre-flight** | In parallel, `Read` [uia-starter-guide.md](uia-starter-guide.md), the UIA package core guide (Rule 7), and its mandated target-capture orchestration reference, all in full; check prerequisites ([uia-starter-guide.md § UIA Prerequisites](uia-starter-guide.md), Rule 7a); run ONE `Bash` window-baseline via the UIA snapshot CLI; build the element inventory/checklist from the user's manual steps. |
| **Per capture-screen** | Run the `uia-configure-target` flow once for ALL checklist elements on the screen through OR registration; make ONE state advance with the interact CLI only to reach the next screen, never to test behavior. |
| **T-author — after ALL screens captured** | Complete Capture-First Fast Path scaffolding/authoring prerequisites; batch-author every screen's activities once (Rule 18), embedding the OR target-attachment path. |
| **T-gate** | Run one sequential `Bash` chain/loop over every edited file: per-file relative-`--file-path` `validate` `&&` `build`. |
| **Debug cycle (consent-gated, [uia-starter-guide.md § Running UI Automation Workflows](uia-starter-guide.md))** | Run ONE `Bash` chain: window baseline `&&` `debug start` `&&` `execution cancel` `&&` re-list windows. In the next turn, diff and close stray windows via one interact-CLI `Bash`; in that same message report with parallel context-file `Write`s, qualifying memory `Write`s, and § Completion Output as in greenfield T5. Read the verdict from the `debug start` envelope; never redirect it to a file and parse it in extra turns. |

Batch Object Repository definition updates, registration, and linking as sequential CLI loops/chains in one `Bash` call per phase, not one turn per entry. Split only when later calls need returned references or a file edit; keep screen-before-element linking and verify links in files. State advances and consent remain gates.

For coded mode, install needed packages and `Write` the empty `[Workflow]` stub (SKILL.md § Capture-First Fast Path step 2) BEFORE T0's window-baseline `Bash`. The first `uip rpa` command that loads the project snapshots coded partials from the packages and `.cs` files present at that moment; if the stub is missing then, authoring gets `CS0246`/`CS0103`. Begin T-author with ONE `Bash` per-file `validate` to regenerate `.local/.codedworkflows/ObjectRepository.cs`, then `Read` it; author targets as `Descriptors.*`, never string names.

Default to author-once-after-capture; all OR refs are then in conversation. For long captures (5+ screens) with real context pressure, interleave per-screen authoring instead; run `validate`/`build` once at the end either way. For later screens in the same window, carry the prior OR screen reference into the next `uia-configure-target` invocation to skip OR-screen lookup; use the package's invocation guide routed from package-guide § Documentation. Keep indication fallback (physical user click) and every interact advance sequential, never batched or parallel. At debug-time selector failure, run the recover selector flow; never hand-edit selectors.

## Failure exits

| Symptom | Open |
|---|---|
| `validate` structural/reference errors | [cli-reference.md § Validation Iteration Loop](cli-reference.md#validation-iteration-loop) |
| XAML activity gotcha (property conflicts, scope) | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) |
| Clean gate but wrong/empty runtime output | [xaml/common-pitfalls.md](xaml/common-pitfalls.md) silent-failure sections: § InvokeCode Code Property — Attribute Form Only, § WriteTextFile Emits a UTF-8 BOM, § UIA `N*` Activities Carry a `Version` |
| Coded `CS*` errors | [coded/operations-guide.md § Common Issues and Fixes](coded/operations-guide.md#common-issues-and-fixes) |
| CLI `timeout`, `EPIPE`, `401`, or `not in the project folder` | [cli-reference.md § CLI Error Recovery](cli-reference.md#cli-error-recovery) |
| Card snippet rejected by validate/build | Use the Rule 21 triple for that activity; report the stale entry via `/uipath-feedback` |
| UIA selector fails at debug time | Use the recover selector flow per [uia-starter-guide.md § Runtime Selector Failure Recovery](uia-starter-guide.md#runtime-selector-failure-recovery); never hand-edit |

## Cross-session memory

Use memory only when the harness provides persistent memory; otherwise skip silently.

**Recall — T1 of every journey.** Match entries by activity class + package `major.minor`. A hit skips that activity's Rule 21 triple; `validate`/`build` still gate.

**Save — after a clean project `build`, in the report turn.** Emit all qualifying saves as parallel `Write`s in the report message; never use a separate memory turn or one memory file per turn. A first-try clean gate on card-covered activities qualifies nothing. Save only:

1. Validated XAML snippet for each off-card activity, keyed by activity class + package `major.minor` + date.
2. Error→root-cause→fix triples costing >1 validate attempt.
3. Cross-version package gotchas.

Never save project facts (paths, asset names, connections; use `project-context.md`), UIA selectors/targets/OR references (per-app), UIA CLI syntax (package-owned/co-versioned), `uip rpa` flag shapes or run/debug payload fields ([cli-reference.md](cli-reference.md) owns them; report gaps via `/uipath-feedback`), or secrets. Process-level UIA lessons, such as a failure mode and fix direction, may be saved.

**Expiry:** if a recalled snippet fails validation, delete or overwrite it and fall back to the Rule 21 triple.
