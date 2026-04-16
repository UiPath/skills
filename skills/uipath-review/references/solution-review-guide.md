# Solution Review Guide

Review guide for UiPath solutions (`.uipx`) — multi-project packages deployed as a single unit.

> **Windows-Legacy compatibility guard:** `.uipx` solutions are NOT supported for Legacy projects. If any detected executable in the repo is Windows-Legacy (`expressionLanguage: "VisualBasic"` with no or `Legacy` `targetFramework`), **do NOT flag missing `.uipx` and do NOT recommend creating one**. Recommend migration to Modern compatibility (Windows / Cross-platform) if solution bundling is desired — that is the prerequisite, not the finding. Review each Legacy project independently.

## Solution Structure Validation

### Expected Files

A valid solution directory contains:

```
MySolution/
├── MySolution.uipx           # Solution definition (required)
├── config.json               # Environment configuration (recommended)
├── ProjectA/                 # One or more project subdirectories
│   ├── project.json          # or agent.json, *.flow, etc.
│   └── ...
└── ProjectB/
    └── ...
```

### Validation Steps

1. **Read the `.uipx` file** — it lists all projects in the solution
2. **Verify each listed project exists** on disk with its required files
3. **Check for orphan projects** — directories with `project.json` / `agent.json` / `.flow` that are NOT listed in `.uipx`
4. **Run `uip solution pack`** to verify the solution can be packaged:

```bash
uip solution pack <SOLUTION_DIR> <OUTPUT_DIR> --output json
```

### Structural Checks

> **Solutions bundle EXECUTABLE projects** (processes, agents, flows) into a single transport package. Libraries are NOT executables — they are reusable components published to a NuGet feed and consumed by other projects. A repo containing `MyLibrary/` next to `MyProcess/` (where `MyProcess` depends on `MyLibrary`'s published package) is the correct architecture, not a missing-solution problem.

| Check | Severity | Detection |
|---|---|---|
| `.uipx` exists but referenced project directory missing | Critical | Read `.uipx`, check each path exists |
| `uip solution pack` fails | Critical | Non-zero exit code from pack command |
| `.uipx` missing AND 2+ executable projects co-located (process/agent/flow) | Info | Count executable `project.json`/`agent.json`/`.flow` — recommend bundling as solution for unified deployment |
| `.uipx` missing AND only single executable (with or without libraries) | Not a finding | Single deployable unit — no solution needed |
| Executable project not listed in existing `.uipx` (true orphan) | Warning | Compare executable directories vs `.uipx` entries |
| Library co-located with consumer (not in `.uipx`) | Not a finding | Libraries are published to NuGet and consumed via dependencies — they do NOT belong in solution wrappers |
| `config.json` missing | Info | `ls config.json` — only a problem if multi-environment deploy is needed |

## Multi-Project Architecture Patterns

### Dispatcher-Performer

The most common UiPath pattern for queue-based processing:

- **Dispatcher** — reads data from a source, creates queue items
- **Performer** — processes queue items one at a time with retry

**Review checklist:**
- [ ] Dispatcher and Performer are separate projects
- [ ] Queue is properly configured (name, max retries, auto-retry)
- [ ] Performer handles TransactionItem correctly (SetTransactionStatus on success and failure)
- [ ] Dispatcher does not process items — only creates them
- [ ] Queue name is consistent between Dispatcher and Performer

**Common issues:**
- Dispatcher also processes items (should be split)
- Queue name hardcoded instead of using assets
- No max-retry configured on the queue
- Performer does not set transaction status on failure

### Main Process + Libraries

A main orchestration process with reusable library packages:

- **Main Process** — entry point, orchestrates workflow
- **Libraries** — reusable activities (API wrappers, utility functions)

**Review checklist:**
- [ ] Libraries have `outputType: "Library"` in project.json
- [ ] Main process has `outputType: "Process"` in project.json
- [ ] Libraries are referenced as NuGet dependencies in the main process
- [ ] Library version is pinned (not floating)
- [ ] No circular dependencies between libraries

See "Library Architecture and Versioning" section below for in-depth library review criteria.

### Orchestrated Solution (Flow + Resources)

A Flow orchestrating multiple RPA processes, agents, or apps:

- **Flow** — the orchestration layer
- **RPA Processes** — published processes invoked by the flow
- **Agents** — published agents invoked by the flow

**Review checklist:**
- [ ] All resources referenced in the flow are published and available
- [ ] No `core.logic.mock` placeholder nodes remain
- [ ] Flow validates without errors
- [ ] Resource input/output schemas match flow expectations
- [ ] Error handling exists for each resource node

## Library Co-Existence vs Solution Bundling

A common review mistake is flagging "missing `.uipx`" as a finding whenever multiple `project.json` files exist in a repo. This is wrong.

### When a Solution IS Recommended

A `.uipx` solution wrapper is recommended when **multiple executable projects** must be deployed together as one transport unit:

- 2+ RPA processes that share data via queues
- A dispatcher process + a performer process
- An RPA process + an orchestrating Flow + an Agent invoked by the Flow
- Multiple agents that share configuration

These are deployable units. A solution lets them version, transport, and deploy as one package.

| Signal | Recommendation |
|---|---|
| 2+ executable `project.json`/`agent.json`/`.flow` co-located | **Info:** Recommend solution bundling for unified deployment |
| Co-located executables share a queue, asset, or process flow | **Info:** Solution recommended — they're a logical unit |
| Co-located executables share a Maestro/Flow orchestration | **Warning:** Solution recommended — orchestration implies tight coupling |

### When a Solution is NOT Needed

A solution is NOT needed — and flagging its absence is a **review error** — in these cases:

- A single executable project (with or without sibling library projects)
- A library project (`outputType: "Library"`) co-located with one or more consumers
- A library project that publishes independently to a NuGet feed
- A standalone process that does not coordinate with siblings

### The Library + Consumer Pattern

This is the normal architecture and should NOT be flagged:

```
MyRepo/
├── MyLibrary/                         # outputType: "Library", published to NuGet
│   └── project.json
└── MyProcess/                         # outputType: "Process", consumes MyLibrary
    ├── project.json                   # dependencies: { "MyLibrary": "[1.5.3]" }
    └── Main.xaml
```

The library is published to a feed (Orchestrator tenant feed, host feed, or custom NuGet). The consumer references it via the `dependencies` block in its `project.json`. They do not need to be wrapped in a `.uipx`.

### Real Concern: Library Version Drift

The legitimate concern when local library source co-exists with consumer is **version drift**:

| Check | Severity | How to Verify |
|---|---|---|
| Local library `project.json` `projectVersion` matches the version pinned in consumer's `dependencies` | Info | Compare library `projectVersion` to consumer's pinned version range |
| If local source version > consumer pinned version, document which is authoritative for production | Info | Check release notes, deployment docs |
| If consumer is consuming an older published version while local source is being modified, verify the local source has been published before deployment | Warning | Check publishing history / NuGet feed |
| Local library source is reachable from consumer's NuGet feed (not just on disk) | Warning | Verify library is published, not just locally available |

> **Do NOT recommend "wrap as a solution" to fix version drift.** Solutions don't solve drift between local source and published packages — they bundle different deployable units. The fix for drift is publishing the updated library and updating the consumer's pinned version.

## Cross-Project Dependency Checks

### Finding Dependencies

1. **RPA projects:** Read `project.json` → `dependencies` object. Check if any dependency name matches another project in the solution.
2. **Flows:** Read `.flow` → `nodes` array. Resource nodes (`uipath.core.rpa-workflow.*`, `uipath.core.agent.*`) reference published packages — verify they match solution projects.
3. **Solutions:** Check if Project A depends on Project B's output (e.g., queue items created by A, processed by B).

### Dependency Issues to Flag

| Issue | Severity | Description |
|---|---|---|
| Circular dependency | Critical | Project A depends on B, B depends on A |
| Version mismatch | Warning | Library referenced at version X but solution contains version Y |
| Missing dependency | Critical | Referenced library not included in solution |
| Implicit ordering dependency | Info | Project A must run before Project B but no explicit orchestration enforces this |

## Configuration Review

### config.json Checks

| Check | Severity | Detection |
|---|---|---|
| Hardcoded production URLs | Warning | Grep for `https://` in config values |
| Plaintext credentials | Critical | Grep for `password`, `secret`, `token`, `key` in config values |
| Missing environment differentiation | Info | Only one environment section when multiple are expected |
| Connection strings in config | Warning | Should use Orchestrator assets or Integration Service connections instead |

### Asset Management Review

- [ ] Sensitive values (credentials, API keys) use `Credential` or `Secret` asset type — not `Text`
- [ ] Asset names follow a consistent convention (e.g., `ProjectName_AssetPurpose`)
- [ ] Per-robot assets are used only when different robots genuinely need different values
- [ ] Assets that change between environments (URLs, paths) are externalized — not hardcoded

## Packaging Validation

### Pre-Pack Checks

1. **Version management:** Check if the solution version is being bumped appropriately
2. **All projects build:** Each project should pass its own validation independently
3. **No debug artifacts:** Check for leftover debug files, test data, or `.local/` caches that should not be packaged

### Pack and Verify

```bash
# Pack the solution
uip solution pack <SOLUTION_DIR> <OUTPUT_DIR> --output json

# Verify output
ls <OUTPUT_DIR>/*.zip
```

A successful pack produces a `.zip` file. If pack fails, the error output identifies which project is causing the issue.

## Solution-Level Antipatterns

### One-Artifact-Per-Solution Scatter (Anti-consolidation)

**Symptom:** Organization has N solutions, each containing exactly one agent, one flow, or one RPA process that would naturally deploy together. E.g., "CustomerSupportAgent.uipx" + "TriageFlow.uipx" + "RefundProcess.uipx" — all three ship together, coordinate business logic, share configuration, but each is its own solution.

**Impact:** Each solution deploys, versions, and transports independently. Version drift between tightly-coupled artifacts. Cannot `uip solution pack` the bundle as one unit. Increases operational surface (N pipelines, N deployments, N config files). FDE experience at large customer deployments confirms this is a common scaling pain point.

**Detection:** List all `.uipx` solutions in the organization. For each solution, count the executables inside (processes + agents + flows). If many solutions contain only one executable AND those executables coordinate business logic / share queues / share data, flag the consolidation opportunity.

**Recommendation:** Consolidate tightly-coupled artifacts into a single `.uipx` solution. The heuristic: if artifact A fails in production, do you also need to investigate/roll back artifact B? If yes → same solution.

**Severity:** Info — this is an architecture recommendation, not a deployment blocker. Flag as Warning if version drift between related single-solution artifacts has already caused incidents.

### Duplicate UUIDs in entry-points.json

**Symptom:** Two or more entries in `entry-points.json` share the same `uniqueId` GUID.

**Impact:** Publishing fails or produces an ambiguous package. Entry-point lookup at runtime picks the first match silently — the other entry becomes unreachable. Documented Studio Web bug that blocks publishing.

**Detection:** Parse each `entry-points.json`:

```bash
# For each entry-points.json, check for duplicate uniqueId values
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); ids=[e['uniqueId'] for e in d.get('entryPoints',[])]; dups=[x for x in set(ids) if ids.count(x)>1]; print('DUPLICATES:',dups) if dups else print('OK')" <entry-points.json>
```

**Fix:** Regenerate affected entries in Studio (delete + recreate the entry point) so a fresh UUID is assigned, or manually assign new GUIDs and update any references.

**Severity:** Critical — blocks publishing.

### Monolith Solution

**Symptom:** Solution contains 15+ projects, many of which are unrelated.

**Detection:** Count project directories, check if projects share data or dependencies.

**Recommendation:** Split into multiple solutions grouped by business domain. Flag as **Info** unless it causes packaging failures.

### Orphan Projects

**Symptom:** **Executable** project directory (process, agent, flow) exists in solution folder but is not listed in `.uipx`.

**Detection:** Compare filesystem directories vs `.uipx` project list. Check `outputType` in each `project.json`:
- `outputType: "Process"` → executable, can be orphan
- `outputType: "Tests"` → executable, can be orphan
- `outputType: "Library"` → NOT an orphan even if outside `.uipx`; libraries are consumed via NuGet, not bundled in solutions

**Recommendation:** Either add the executable project to `.uipx` or move it to a separate location. Flag as **Warning**.

**Do NOT flag libraries as orphans.** Libraries living next to a consumer project is the normal pattern — the library publishes to a feed and the consumer depends on it via NuGet.

### Configuration Drift

**Symptom:** Different projects within the same solution use different patterns for configuration (some use assets, some use config.json, some hardcode values).

**Detection:** Check each project for how it accesses configuration values.

**Recommendation:** Standardize on one approach (Orchestrator assets for runtime, config.json for deployment-time). Flag as **Warning**.

### Missing Entry Points

**Symptom:** `project.json` has no `entryPoints` array or the array references files that don't exist.

**Detection:** Read `project.json` → `entryPoints`, verify each `filePath` exists.

**Recommendation:** Fix entry points to match actual workflow files. Flag as **Critical** — the project cannot be published without valid entry points.

## Solution Lifecycle and Transport

### Deployment Configuration Separation

| Check | Severity | How to Verify |
|---|---|---|
| Environment-specific values (URLs, credentials, queue names) are in deployment config, not hardcoded | Warning | Check config.json for environment-specific overrides |
| Solution can be deployed to a new environment without code changes | Warning | Verify all env-specific values are configurable at deploy time |
| Credential mappings documented per environment | Warning | Check deployment documentation for credential mapping steps |
| Asset, queue, and connection mappings defined per target environment | Warning | Check solution deployment config |

### Versioning and Transport

| Check | Severity | How to Verify |
|---|---|---|
| Solution version follows semantic versioning aligned with release milestones | Warning | Check `.uipx` version field |
| All project versions within solution are consistent | Warning | Compare project versions across `project.json` files |
| Rollback procedure documented and tested | Warning | Check deployment documentation for rollback steps |
| Release notes maintained per version | Info | Check for changelog or release notes |
| CI/CD pipeline automates transport and deployment | Info | Check for automated deployment pipeline |

### Pre-Deployment Verification

| Check | Severity | How to Verify |
|---|---|---|
| Solution tested in non-production environment before promotion | Warning | Verify test/UAT deployment exists |
| All dependencies available in target environment (packages, connections, assets) | Critical | Verify target environment readiness |
| `uip solution pack` succeeds without errors | Critical | Run pack command |
| Audit trail maintained (who deployed what, when, where) | Info | Check deployment records |

## Solution Accelerator Customization

When a solution uses a UiPath Marketplace Accelerator as its base:

| Check | Severity | How to Verify |
|---|---|---|
| Accelerator matches the target business process | Warning | Compare accelerator capabilities to requirements |
| Core accelerator workflows NOT modified (extensions layered on top) | Warning | Check if original accelerator files were edited vs extended |
| Customizations applied via Config files, not code changes | Warning | Check where customizations are stored |
| All customizations documented (for future accelerator updates) | Warning | Check documentation listing what was changed |
| Update path from Marketplace understood (can receive accelerator updates) | Info | Verify customization approach preserves upgrade capability |
| Prerequisites and dependencies verified for target environment | Critical | Check accelerator documentation for requirements |

## Library Architecture and Versioning

For solutions that contain libraries (`outputType: "Library"`) or consume them.

### Library Project Quality

| Check | Severity | How to Verify |
|---|---|---|
| Library has a clear, single purpose (not a grab-bag of unrelated helpers) | Warning | Read library README/description and exposed workflows |
| Public workflows are deliberately chosen — internal helpers marked Private | Warning | Check workflow visibility settings (Public vs Private) |
| Library name is descriptive and scoped (e.g., `Company.Email.Utilities` not `Helpers`) | Info | Check library name in `project.json` |
| Activity names use verb-noun convention (`SendNotificationEmail`, `ValidateInvoice`) | Info | Review public workflow names |
| Each public workflow has a description visible in activity panel | Warning | Check workflow annotations |
| Each argument has a description (becomes tooltip for consumers) | Warning | Check argument metadata |
| README documents purpose, usage, prerequisites, breaking changes between versions | Info | Check for README in library project |
| `ContinueOnError` NEVER used inside library workflows (consumer should decide) | Critical | Grep library `.xaml` files for `ContinueOnError="True"` |
| Library throws meaningful exceptions — does not swallow errors | Warning | Review error handling — `BusinessRuleException` for input validation, system exceptions propagate |

### Semantic Versioning

| Check | Severity | How to Verify |
|---|---|---|
| Library version follows SemVer (Major.Minor.Patch) | Warning | Check `project.json` projectVersion |
| Breaking changes only in major version bumps (renamed args, removed workflows) | Critical | Compare current version's interface to previous version |
| Minor version bumps are backward compatible (new workflows, new optional args) | Warning | Compare interfaces — additive only |
| Patch bumps are interface-unchanged (bug fixes, internal changes) | Info | Verify patch versions don't change activity signatures |
| Old versions remain available on the feed (consumers may not upgrade immediately) | Warning | Check feed history — old versions not deleted |
| Release notes accompany each version | Info | Check for changelog or release notes in library |
| Git tags created per published version | Info | Check `git tag --list` for version tags |

### Library Patterns

Reviewers should recognize these patterns and flag misuse:

| Pattern | Use When | Anti-Pattern |
|---|---|---|
| Wrapper Pattern | Reducing boilerplate for common activity sequences (Excel, Email) | Wrapping a single activity (no value added) |
| Connector Pattern | Centralizing all interactions with one external system (CompanyERP.Library) | Multiple competing libraries for same system |
| Framework Pattern | Providing scaffolding consumers extend (REFramework-style) | Hard-coding business logic in framework |
| Data Access Pattern | Centralizing DB/API access (`GetCustomerById` returns DataRow) | Leaking data source details to consumers |

### Feed Management

| Check | Severity | How to Verify |
|---|---|---|
| Feed scope appropriate (Tenant for project-team libs, Host for org-wide) | Info | Check where library is published |
| Custom NuGet feed (Artifactory, Azure Artifacts) used for advanced governance | Info | Check feed configuration |
| Publishing permissions restricted to designated maintainers | Warning | Check feed access controls |

### Consumer Usage

| Check | Severity | How to Verify |
|---|---|---|
| Production projects pin to specific versions (`[1.2.3]` not `[1.2.3, )`) | Warning | Read consumer `project.json` dependencies — exact version brackets |
| Unused library references removed from `project.json` | Info | Check dependencies vs actual usage |
| Library upgrades follow Dev → Test → Prod promotion | Warning | Check deployment process for library updates |
| Major version upgrades include consumer regression testing | Warning | Check test execution evidence before major version adoption |
| Projects use libraries instead of copy-pasting common logic | Warning | Look for duplicated workflows that should reference a library |

### Library Governance

| Check | Severity | How to Verify |
|---|---|---|
| Ownership clear (CoE for org-wide, team for team-specific) | Warning | Check CODEOWNERS or library catalog |
| Library catalog maintained (purpose, owner, current version) | Info | Check for org library inventory documentation |
| Code review required for changes to corporate libraries | Warning | Check PR review requirements |
| Major version bumps require architectural review (impact analysis) | Warning | Check governance process for breaking changes |
