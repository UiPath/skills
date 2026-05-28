---
name: uipath-solution
description: "Always invoke for `.uipx` files. UiPath Solution Design Document (SDD) authoring from PDDs and `uip solution` lifecycle. Covers `sdd.md`/`pdd.md`/`.uipx` files and `uip solution init/pack/publish/deploy/activate/upload/project add|import/resource refresh`. Selects scope (single product or multi-project Solution: RPA/Flow/Case/Agents/Apps/API Workflows), writes implementation-ready SDD, then packs and ships the `.uipx`. For task derivation across multiple skills→uipath-planner. For non-solution Orchestrator/IS/resources/auth/traces→uipath-platform. For .xaml/.cs→uipath-rpa. For .flow→uipath-maestro-flow. For .bpmn→uipath-maestro-bpmn. For agent.json and .py agents→uipath-agents. For caseplan.json→uipath-maestro-case."
when_to_use: "User mentions sdd.md / pdd.md / Process Design Document / Solution Design Document / SDD / PDD / .uipx / 'uip solution' / 'pack the solution' / 'publish the solution' / 'deploy the solution' / 'activate' / multi-project / Solution scope / Solution Folder. Fires for 'design this automation', 'architect the solution', 'generate SDD', 'analyze this PDD', 'turn this PDD into code', and for 'pack and publish my solution', 'deploy to dev', 'create a new solution', 'add project to solution'. Load BEFORE editing .uipx or running uip solution commands."
---

# UiPath Solution — Design + Lifecycle

> **Two entry points.** Use the **Design half** for PDD → SDD authoring; use the **Operate half** for `uip solution` lifecycle (init, pack, publish, deploy, activate). The two halves share no workflow — pick the right one from "When to Use" before applying any rule.
>
> This skill nests Critical Rules and Workflow under each half — Design and Operate — rather than at the top level.

## When to Use This Skill

### Design entry — PDD → SDD

- User provides a PDD (PDF, docx, markdown) and asks to design or build from it
- User asks to design / architect / generate an SDD for a UiPath automation
- User describes a complex automation involving multiple products (RPA + Agents, Flow + API Workflows, etc.) and wants architecture before code
- A skill or main agent detected a PDD and redirected the user here

**Skip the Design half** when:
- The request is a simple, well-defined single-skill task (e.g., "create a workflow that sends an email") — load the specialist (`uipath-rpa`, `uipath-agents`, etc.) directly.
- An SDD already exists and the user wants the implementation task list — load `uipath-planner` directly with the SDD path.
- The user's input is not a PDD (no process steps, application inventory, or exception handling) — clarify intent or redirect to `uipath-planner`.

### Operate entry — `uip solution` lifecycle

- User has a `.uipx` solution and wants to pack / publish / deploy / activate / upload
- User wants to create a new solution (`uip solution init`), add or remove projects, or refresh solution resources
- User asks to set up a CI/CD pipeline that builds, publishes, and deploys a UiPath solution
- User mentions deploy configs, environment promotion, or activating a deployed solution
- A skill or main agent detected a `.uipx` file and redirected the user here

**Skip the Operate half** when:
- The deployable is a single non-solution package (e.g., a one-off RPA library or coded app) — those use `uip rpa publish` / `uip codedapp publish` and route through `uipath-platform` or the relevant specialist.
- The task is non-solution Orchestrator work (folders, jobs, assets, queues, IS connections) — load `uipath-platform`.

---

## Design — PDD → SDD

Transform a Process Design Document (PDD) into an implementation-ready Solution Design Document (SDD). Select the right UiPath scope — either a single product (RPA Process/Library/Test Auto, Maestro Flow, Case Management, Agents, Coded Apps, or API Workflows) or a multi-project Solution composing several of them — based on PDD signals.

After the SDD is written, hand off to `uipath-planner`. The planner reads the SDD, derives the per-skill task list, and routes execution to the correct specialists (including this skill's Operate half for solution-scope deploy).

### Critical Rules

1. **The SDD is implementation-oriented, not a PDD mirror.** Reorganize the PDD content into a structure a coding agent can execute against. Do not copy PDD sections verbatim.
2. **Never invent selectors, UI targets, or element identifiers.** The SDD covers architecture only — selectors require application inspection at development time.
3. **Follow the phased interaction model.** Read the full PDD first, recommend a product, present a summary with clarifying questions, get architecture approval, then generate the complete SDD. See [SDD Generation Guide](references/design/sdd-generation-guide.md).
4. **Fill gaps with `[DEFAULT]` or `[SME REVIEW]`.** Use `[DEFAULT]` for industry-standard patterns (retry counts, timeouts). Use `[SME REVIEW]` for gaps requiring business knowledge. Never silently invent business rules.
5. **The Project Structure section is the most important section.** It must list every workflow file (or node / stage / tool / page / step) with its responsibility, inputs, outputs, and which PDD steps it covers. Run Level 2.5 (Project Decomposition) BEFORE designing project structure — see Levels guide.
6. **RPA data definitions follow the implementation mode.** For Coded C# or Hybrid mode: use C# `record` (immutable) or `class` (mutable). No inheritance. Max 15 properties per type. Default to `string` unless the PDD specifies numeric, date, or boolean operations. For XAML mode: use dictionary keys or DataTable columns.
7. **Non-RPA products use their native type system.** For Agents, Coded Apps, Flow, Case Management, and API Workflows: use the JSON schema or type definition appropriate to that product's template.
8. **Write the `## Planner Handoff` header AND the `<!-- planner-handoff:v1 -->` marker into every SDD.** This is a load-bearing contract — `uipath-planner` detects SDDs by either signal. The marker sits adjacent to the heading in every template; both must survive into the generated file so a hand-edit that renames the heading still leaves the marker for detection. Fields: Execution autonomy, SDD scope, Project list section, Tasks file, Generated by, Generation date.
9. **Select the primary scope BEFORE designing architecture.** The scope (single product or Solution) determines the template(s) and project structure. Use the [Product Selection Guide](references/design/product-selection-guide.md) Level 1 → Level 1.5 (RPA sub-type) → Level 1.75 (Solution composition) → Level 2.5 (project decomposition). Present the recommended scope first with single-product alternatives and "Solution (customize)" below. The skill that builds the workflows/nodes/tasks owns the final detailed decisions.
10. **Write the SDD to the current working directory AND honour the template's section structure as a hard superset contract.** For single-product scope, one file at `<PROCESS_NAME_KEBAB>-sdd.md`. For Solution scope, a `<SOLUTION_NAME_KEBAB>-solution-sdd.md` overview plus one `<PROJECT_NAME_KEBAB>-sdd.md` per project in the unified project list. If the user specifies a path, use that instead. **After writing, diff the generated SDD's H2/H3 headings against the template's Table of Contents — the generated set MUST be a superset of the template's TOC headings (you may add subsections, never drop one).** If any template-required H2 (e.g., `## 4. Business Rules`, `## 5. Data Definitions`, `## 7. Exception Handling`, `## 8. Error Handling`, `## 17. Testing Strategy`) is missing, regenerate that section before declaring done. A missing template section is an SDD defect, not an `[SME REVIEW]` item.
11. **Do not generate an Implementation Plan inside the SDD.** Implementation tasks are owned by `uipath-planner`. The SDD ends with a `## Next Steps` section pointing at the planner. Architecture only — no task lists, no skill routing prompts, no *implementation* `TaskCreate` calls. (The Phase 1 Step 0.5 *progress-tracking* `TaskCreate` calls are explicitly allowed — they track SDD-generation progress, not implementation work, and are subject to Rule G-8.)
12. **Always generate a thorough §17 Testing Strategy.** Cover happy path, edge cases, error scenarios, and (for Master Projects) end-to-end pipeline tests. Test depth is non-negotiable — never offer the user a "happy path only" option. Implementation specialists may scope down at execution time if needed.
13. **Use AskUserQuestion for Agent/Coded App gaps.** If the primary product is Agents or Coded Apps and the PDD lacks required details (framework, tools, pages, flows), use `AskUserQuestion` to ask if the user wants to proceed with gap-filling or use a different product. Never auto-fallback.
14. **All user questions use numbered-choice format by default; use `multiSelect: true` only for Solution composition and Tenant Library Discovery.** Every `AskUserQuestion` uses a blockquote with numbered options and a `*(recommended)*` tag on the default choice. This applies to execution mode, language, product gap-filling, fallback selection, SME review resolution, RPA sub-type, and scope confirmation. The exceptions are Level 1.75 Pass A (Solution composition) and Step 2.5 Tenant Library Discovery, which use `multiSelect: true` so the user can check every product / library that applies.
15. **For "leverage / find shared libraries" requests (Step 2.5 or ad-hoc), search the tenant feed — not the local filesystem, project folder, NuGet.org, or keyword-permutation loops.** Run the auth preflight first (`uip resource libraries list --limit 1 --output json`); on `Result: Failure` with an auth message, take the manual fallback from the guide — do NOT retry silently. On success, run the keyword call `uip resource libraries list --limit 500 --output-filter "<JMESPath>" --output json`. On zero results from the filtered call, take the fallback branch — do not re-keyword. See [Tenant Library Search Guide](references/design/tenant-library-search-guide.md) for the full procedure.
16. **The terminal artefact of an SDD-driven build is a packed `.uipx` solution.** When implementation reports complete, the SDD's §18 Next Steps points the user back to this skill's Operate half: `uip solution init` → `uip solution project add` (one per project in the unified list) → `uip solution resource refresh` → `uip solution pack`. A bare project folder is not the deliverable. The Operate half owns this; the Design half flags it as the final step.

### Workflow

The SDD generation has 3 phases. Detail in the [SDD Generation Guide](references/design/sdd-generation-guide.md). All user questions use numbered-choice format.

1. **Phase 1 — PDD Analysis & Scope Selection.** Ask execution mode (Autonomous or Interactive). Read the full PDD, extract structured information, run Level 1 (primary scope) → Level 1.5 (RPA sub-type if applicable) → Level 1.75 (Solution composition if applicable) → Level 2.5 (project decomposition). In Interactive mode, present a summary with the recommended scope at the top and alternatives below. In Autonomous mode, proceed without pausing. For Agent/Coded App products with missing info, use `AskUserQuestion` for gap-filling or fallback (both modes).
2. **Phase 2 — Architecture Review.** Load the product-specific template. Generate the architectural core sections (template-specific — see Phase 2 Step 2 of the generation guide). In Interactive mode, present for review. In Autonomous mode, proceed without pausing.
3. **Phase 3 — Full SDD Generation.** Generate all remaining sections including the thorough §17 Testing Strategy. Resolve `[SME REVIEW]` items by asking the user before writing (both modes). Write the `## Planner Handoff` header. Write the SDD to disk. Tell the user to load `uipath-planner` next.

---

## Operate — `uip solution` lifecycle

Create, pack, publish, deploy, and manage UiPath Solution packages (`.uipx`) via the `uip solution` CLI surface. A Solution bundles multiple automation projects (processes, libraries, tests, agent projects, API workflows) into a single deployable unit.

> **Use the CLI. Don't roll your own REST for solution ops.** Hand-rolling HTTP calls misses the `X-UIPATH-OrganizationUnitId` folder header, OData filter shape, pagination envelope, `pipelinesInstall` deploy semantics, retry behavior, and the `Result/Code/Data` output contract. The CLI is the source of truth.

### CLI Surface Probe

Before the first `uip solution …` command in a session, probe the `solution` surface to detect pre- vs post-rename CLI:

```bash
uip solution init --help --output json
```

- Result `Success` → post-rename CLI (default). Use the commands and flags as documented in the references.
- `unknown command` / non-zero exit → pre-rename CLI. Translate via the table below before each call. Re-probe on any later `unknown command` error.
- `command not found` / `uip: not found` / `'uip' is not recognized` → CLI not installed. Tell the user to run `npm install -g @uipath/cli`, then `uip login`, and abort the Operate-half work until those succeed.

| Post-rename (default) | Pre-rename equivalent |
|---|---|
| `uip solution init <NAME>` | `uip solution new <NAME>` |
| `uip solution deploy run --parent-folder-path <PATH>` | `uip solution deploy run --folder-path <PATH>` |
| `uip solution deploy run --parent-folder-key <KEY>` | `uip solution deploy run --folder-key <KEY>` |

All other `solution` subcommands (`pack`, `publish`, `deploy activate/status/uninstall`, `upload`, `resource …`, `project add/import`) are unchanged on both surfaces.

### Critical Rules

1. **Probe the CLI surface before the first `uip solution` command in a session.** Run `uip solution init --help --output json`. `Success` = post-rename CLI (default); `unknown command` = pre-rename CLI — translate via the fallback table above. Re-probe on any later `unknown command` error.
2. **Always use `--output json`** for `uip solution` commands whose output you parse. JSON is compact and stable; the default for non-interactive runs.
3. **Use the CLI, never roll your own REST for solution operations.** Hand-rolled HTTP calls miss the `X-UIPATH-OrganizationUnitId` header, OData filter shape, pagination envelope, and `pipelinesInstall` deploy semantics. Only fall through to REST after confirming no `uip solution` command covers the task.
4. **Never hand-edit `resources/solution_folder/`.** It's auto-generated by `uip solution project add` / `import` and auto-cleaned by `project remove`. Manual edits desync from `.uipx` and produce silent failure modes. See [scenarios/manual-edits.md](references/operate/scenarios/manual-edits.md).
5. **`.uipx` and `resources/solution_folder/` must always agree on the project set.** Diffing them is the fastest way to detect corrupted state. If they disagree, fix via `uip solution project add/remove` — never by editing either side directly.
6. **Run `uip solution resource refresh` before `pack` or `upload`.** Bundled artefact files and `userProfile/<userId>/debug_overwrites.json` must reflect current cloud state. Skipping refresh ships stale bindings.
7. **Coded apps are NOT registered in `.uipx`.** `uip solution project add` does not apply to coded-app directories; they deploy independently via `uip codedapp publish / deploy`. A coded app folder can sit alongside a solution but is not part of its manifest.
8. **Verify the artifact after every CLI mutation.** Read `project.json`, `.uipx`, or `uip solution deploy status` output — exit codes lie. This mirrors the Design half's "verify the SDD after write" discipline.
9. **For multi-environment promotion, the deploy config (`-c <CONFIG_KEY>`) is the environment selector.** Same `.uipx` deploys to dev/staging/prod via different config keys, not different packages.

### Workflow

The typical lifecycle for a UiPath Solution:

```
1. init / project add  → Create solution, register projects (.uipx + resources/solution_folder/)
2. resource refresh    → Sync bundled artefacts and debug overwrites with cloud state
3. pack                → Produce deployable .zip package
4. login               → uip login (if not already authenticated)
5. publish             → Upload packed solution to UiPath
6. deploy run          → Promote to Orchestrator (auto-activates by default)
7. (optional) activate → Use --skip-activate on deploy, then activate explicitly
```

> **Coded apps in the project list deploy in parallel, not through `uip solution`.** Coded-app projects (Coded Web Apps and Coded Action Apps) have no `project.uiproj` / `project.json` and are NOT registered via `uip solution project add`. For each coded-app project in the unified list, run `uip codedapp publish` / `uip codedapp deploy` independently — the rest of the solution still goes through steps 1-7 above. See `uipath-coded-apps` for the coded-app lifecycle.

Two distinct distribution paths from the same source:
- **`pack` → `publish` → `deploy run`** — promotes a versioned package to Orchestrator.
- **`upload`** — pushes the solution to Studio Web for browser-based debugging only. Does not produce a published package and cannot be deployed via `deploy run`.

Authentication is a prerequisite. Run `uip login --output json` before any operate-half work; see `uipath-platform` for full auth options (interactive OAuth, client credentials, tenant switching).

---

## Reference Navigation

### Design references

| File | Purpose |
|------|---------|
| [SDD Generation Guide](references/design/sdd-generation-guide.md) | Phase orchestrator — Phase 1, 2, 3 step-by-step instructions |
| [PDD Analysis Guide](references/design/pdd-analysis-guide.md) | How to extract structured data from PDDs in any format |
| [Product Selection Guide](references/design/product-selection-guide.md) | Canonical home for **Level 1** (primary scope), **Level 1.75** (Solution composition), **Level 2.5 Part B** (cross-product project list merge), **Level 3** (capability add-ons), template mapping |
| [RPA Product Guide](references/design/rpa-product-guide.md) | RPA-only canonical home for **Level 1.5** (sub-type), **Level 2** (authoring mode), **Level 2.5 Part A** (RPA decomposition), R-07 naming convention, REFramework guidance. Load when Level 1 = RPA or a Solution includes RPA. |
| [Package Selection Guide](references/design/package-selection-guide.md) | NuGet package selection per Application Inventory; Integration Service vs NuGet decision rules; per-product dependency manager (RPA: NuGet, Coded Apps: npm, etc.). Load when filling §14 Packages or equivalent. |
| [Tenant Library Search Guide](references/design/tenant-library-search-guide.md) | Step 2.5 procedure for discovering deployed libraries via `uip resource libraries list` + JMESPath filtering. Covers auth preflight, keyword extraction, ranking, zero-results branch, and the manual fallback when unauthenticated. |

### Operate references

| File | Purpose |
|------|---------|
| [Solution Overview](references/operate/solution-overview.md) | What a Solution is, `.uipx` manifest, file structure, lifecycle diagram, command tree |
| [Develop a Solution](references/operate/develop-solution.md) | `uip solution init / project add / import / remove / resource refresh`; field-tested gotchas |
| [Pack and Deploy](references/operate/pack-and-deploy.md) | `pack / publish / deploy run`, deploy configs, CI/CD pipeline patterns |
| [Activate and Manage](references/operate/activate-and-manage.md) | `deploy activate / status / uninstall`, environment management |
| [Scenarios Index](references/operate/scenarios.md) | Failure modes and edge cases — manual edits, shared resources, virtual resources, name collisions |

### SDD templates

| File | Purpose |
|------|---------|
| [RPA Template](assets/templates/rpa-sdd-template.md) | SDD template for RPA Process / Library / Test Automation |
| [Flow Template](assets/templates/flow-sdd-template.md) | SDD template for Maestro Flow |
| [Case Management Template](assets/templates/case-sdd-template.md) | SDD template for Case Management |
| [Agent Template](assets/templates/agent-sdd-template.md) | SDD template for UiPath Agents |
| [Coded App Template](assets/templates/coded-app-sdd-template.md) | SDD template for Coded Apps (web) |
| [API Workflow Template](assets/templates/api-workflow-sdd-template.md) | SDD template for API Workflows |

---

## Anti-patterns

### Design anti-patterns

1. **Copying the PDD structure into the SDD.** The SDD must reorganize content for implementation, not mirror the PDD's document flow.
2. **Defaulting to RPA Process when the PDD describes something else.** Use the Product Selection Guide's decision tree. A PDD with AI reasoning signals should go to Agents; a PDD with stages/SLA/approval should go to Case Management.
3. **Inventing selectors from screenshots.** Screenshots help understand the UI flow but cannot produce reliable selectors. Leave selector work for development time.
4. **Generating the full SDD without user checkpoints.** Always present the product recommendation (end of Phase 1) AND the architecture (Phase 2) before generating the rest. The product choice and project structure are the hardest to fix later.
5. **Asking the user about every gap.** Use `[DEFAULT]` for standard patterns. Only escalate with `[SME REVIEW]` for business-knowledge gaps. Use `AskUserQuestion` only for Agent/Coded App gap-filling.
6. **Generating an Implementation Plan section inside the SDD.** Implementation tasks belong to `uipath-planner`. Every SDD ends with `## Next Steps` pointing at the planner. Do not include Task 1 / Task 2 / Task N task templates. Do not call `TaskCreate` for *implementation* tasks (the Phase 1 Step 0.5 progress-tracking tasks are a separate, allowed use). Architecture only.
7. **Asking the user about test coverage depth.** §17 Testing Strategy is always thorough — happy path, edge cases, error scenarios, e2e for Master Projects. The implementation specialist scopes down at execution time if the user wants a quick MVP; the SDD does not.
8. **Generating overly abstract workflow/node/task descriptions.** Each item in the inventory must have a concrete responsibility, specific PDD step references, and defined inputs/outputs.
9. **Auto-falling-back from Agents/Coded Apps to another product without asking.** If the PDD is missing product-specific details, use `AskUserQuestion` — the user chooses whether to proceed with gap-filling or pick a different product.
10. **Inlining HITL schema for Flow/Maestro/Agent products.** HITL for those products is owned by the `uipath-human-in-the-loop` skill. Flag touchpoints only. Case Management is the exception — it handles HITL tasks inline.
11. **Putting everything in a single RPA project when the PDD has distinct processing stages.** If the PDD describes email ingestion + data extraction + output generation + reporting, these are separate projects connected by Orchestrator queues — not one monolithic process. Run Level 2.5 Part A from the RPA Product Guide.
12. **Forcing a single-product scope when the PDD describes multiple coordinated projects.** If the PDD needs (for example) 2 RPA Libraries + 1 Test Automation project, or a Flow plus callable API Workflows, the correct scope is **Solution** — not a single-product SDD that buries the rest as "integrated components". Watch the Level 1 Solution Signals and offer Solution (customize) as an alternative on the recommendation screen.
13. **Ignoring REFramework for queue-based transactional processing.** REFramework is the standard UiPath framework for Performer projects that consume from Orchestrator queues. Custom frameworks for this pattern lead to fragile, non-standard implementations.
14. **Omitting NuGet package dependencies.** Developers need to know which packages to install. Infer packages from the Application Inventory and list them in §14 Packages — see the [Package Selection Guide](references/design/package-selection-guide.md).
15. **Renaming the `## Planner Handoff` heading or stripping the `<!-- planner-handoff:v1 -->` marker.** Either signal alone is sufficient for `uipath-planner` to detect the SDD, but both should remain — they are redundant on purpose. Removing both breaks Lane A silently.

### Operate anti-patterns

1. **Hand-rolling REST calls for `pack`, `publish`, `deploy run`, or `activate`.** The `uip solution` CLI handles auth, folder headers, pipeline semantics, and pagination correctly. Reach for REST only after confirming no command covers the task.
2. **Editing `resources/solution_folder/` directly.** It is auto-generated and auto-cleaned. Manual edits desync from `.uipx`. Use `uip solution project add/remove` instead.
3. **Skipping `uip solution resource refresh` before `pack` or `upload`.** Ships stale bindings and debug-overwrite state.
4. **Adding a coded-app directory via `uip solution project add`.** Coded apps have no `project.uiproj` / `project.json` and are not packed by `uip solution pack`. Deploy them independently via `uip codedapp publish / deploy`.
5. **Creating a new `.uipx` per environment instead of using deploy configs.** One solution package promotes to dev/staging/prod via different `-c <CONFIG_KEY>` values. Different `.uipx` files per environment defeats version tracking.
6. **Using `uip solution upload` (Studio Web) as a deployment path.** Upload is for browser-based debugging only — it does not produce a published package and cannot be promoted via `deploy run`. Use `pack` → `publish` → `deploy run` for real deploys. `upload` also lands the solution in Studio Web's **Cloud workspace** tab — not the Local tab; SW's Local tab is a separate registration not addressable by `uip solution`.
7. **Trusting exit codes alone after a mutation.** Always read the artefact (`project.json`, `.uipx`, deploy status) — a non-zero exit may indicate partial state and a zero exit can mask warnings.
