# Solution Review Guide

Review UiPath solutions (`.uipx`): multi-project packages deployed as one unit.

> **Windows-Legacy compatibility guard:** `.uipx` solutions are NOT supported for Legacy projects. If any detected executable has `project.json` with no `targetFramework` or `targetFramework: "Legacy"`, **do NOT flag missing `.uipx` and do NOT recommend creating one**. Recommend migration to Modern compatibility (Windows / Cross-platform) if solution bundling is desired. Review each Legacy project independently.

## 1. Solution Structure and Packaging

Expected layout:

```text
MySolution/
├── MySolution.uipx           # required solution definition
├── config.json               # recommended environment configuration
├── ProjectA/                 # one or more project subdirectories
│   ├── project.json          # or agent.json, *.flow, etc.
│   └── ...
└── ProjectB/
    └── ...
```

Solutions bundle **executable** projects (processes, agents, flows). Libraries are reusable components published to a NuGet feed and consumed by dependencies; they are not executables and do not belong in solution wrappers.

### Validate

1. Read the `.uipx` file; it lists all projects.
2. Verify every listed project directory and required file exists.
3. Check for orphan executable directories containing `project.json`, `agent.json`, or `.flow` that are not listed in `.uipx`.
4. **Run `uip solution pack <SOLUTION_DIR> <OUTPUT_DIR> --output json`** to verify packaging.
5. **Run** `ls <OUTPUT_DIR>/*.zip` and verify a successful pack produces a `.zip`.

A pack error identifies the failing project.

### Findings

| Check | Severity | Detection/action |
|---|---|---|
| `.uipx` exists but a referenced project directory is missing | Critical | Read `.uipx`; check every path |
| `uip solution pack` fails | Critical | Non-zero pack exit code |
| `.uipx` missing and 2+ co-located executable projects (process/agent/flow) | Info | Count executable `project.json`/`agent.json`/`.flow`; recommend bundling for unified deployment |
| `.uipx` missing and only one executable, with or without libraries | Not a finding | One deployable unit needs no solution |
| Executable is not listed in an existing `.uipx` | Warning | Compare executable directories with `.uipx` entries |
| Co-located library is not in `.uipx` | Not a finding | Libraries publish to NuGet and are consumed through dependencies |
| `config.json` missing | Info | `ls config.json`; only a problem when multi-environment deployment is needed |

Do not treat a library beside its consumer as a missing-solution problem. A library uses `outputType: "Library"`, is published to NuGet, and is consumed by a process through a pinned dependency such as `dependencies: { "MyLibrary": "[1.5.3]" }`.

## 2. Architecture and Dependencies

### Dispatcher–Performer

- Dispatcher reads source data and creates queue items; it does not process them.
- Performer processes one queue item at a time with retry, handles `TransactionItem`, and calls `SetTransactionStatus` on success and failure.
- Keep Dispatcher and Performer separate.
- Configure queue name, max retries, and auto-retry; use a consistent queue name and do not hardcode it instead of using assets.

Flag combined dispatch and processing, missing max retry, inconsistent queue names, or missing failure status.

### Main Process and Libraries

- Main Process is `outputType: "Process"` and orchestrates workflows.
- Libraries are `outputType: "Library"`, referenced as NuGet dependencies, and use pinned versions.
- Do not allow circular library dependencies.

### Orchestrated Solution (Flow + Resources)

- Flow is the orchestration layer; RPA Processes and Agents are published resources invoked by it.
- Verify every resource is published and available; no `core.logic.mock` placeholder nodes exist; the Flow validates; resource input/output schemas match; and every resource node has error handling.

### Solution recommendation

Recommend a `.uipx` when multiple executable projects must deploy together: 2+ RPA processes, dispatcher plus performer, process plus Flow plus Agent, or multiple agents sharing configuration. Shared queues, assets, or process flow indicate a logical unit; shared Maestro/Flow orchestration makes the recommendation **Warning**, otherwise it is **Info**.

Do not recommend a solution for one executable, a library with consumers, a library published independently, or a standalone process. Do not use solution bundling to fix library version drift.

### Cross-project dependencies

1. For RPA projects, read `project.json` → `dependencies`; match dependency names to projects.
2. For Flows, read `.flow` → `nodes`; inspect `uipath.core.rpa-workflow.*` and `uipath.core.agent.*` resource references and verify they match published solution resources.
3. Check output dependencies such as queue items created by one project and processed by another.

| Issue | Severity |
|---|---|
| Circular dependency | Critical |
| Referenced library missing from the solution | Critical |
| Library referenced at version X while solution contains version Y | Warning |
| Project ordering required without explicit orchestration | Info |

## 3. Configuration and Assets

### `config.json`

| Check | Severity | Detection |
|---|---|---|
| Hardcoded production URLs | Warning | Grep for `https://` in config values |
| Plaintext credentials | Critical | Grep for `password`, `secret`, `token`, `key` in config values |
| Missing environment differentiation | Info | One environment section when multiple are expected |
| Connection strings in config | Warning | Use Orchestrator assets or Integration Service connections |

### Assets

- Sensitive values must use `Credential` or `Secret`, not `Text`.
- Use a consistent naming convention such as `ProjectName_AssetPurpose`.
- Use per-robot assets only when robots genuinely need different values.
- Externalize environment-dependent URLs and paths.
- Standardize configuration: Orchestrator assets for runtime values and `config.json` for deployment-time values. Mixed patterns are **Warning**.

## 4. Entry Points and Pre-pack Checks

Before packaging:

1. Check that the solution version is bumped appropriately.
2. Validate every project independently.
3. Exclude debug files, test data, and `.local/` caches that should not be packaged.
4. **Run** `uip solution pack <SOLUTION_DIR> <OUTPUT_DIR> --output json`.
5. **Run** `ls <OUTPUT_DIR>/*.zip`.

### Entry points

If `project.json` has no `entryPoints` array, or an entry references a missing `filePath`, flag **Critical**. Read `project.json` → `entryPoints` and verify every `filePath` exists; the project cannot publish until corrected.

### Duplicate UUIDs in `entry-points.json`

Parse each `entry-points.json` and check duplicate `uniqueId` values:

```bash
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); ids=[e['uniqueId'] for e in d.get('entryPoints',[])]; dups=[x for x in set(ids) if ids.count(x)>1]; print('DUPLICATES:',dups) if dups else print('OK')" <entry-points.json>
```

Duplicate `uniqueId` values are **Critical**: publishing may fail or create ambiguous lookup, with the first entry potentially winning silently. Regenerate entries in Studio by deleting and recreating them, or assign new GUIDs and update references.

## 5. Library Co-Existence, Versioning, and Governance

Do not flag local library source beside a consumer as a solution problem.

### Version drift

| Check | Severity | Verification |
|---|---|---|
| Library `projectVersion` matches the consumer’s pinned `dependencies` range | Info | Compare both values |
| Local source version exceeds consumer’s pinned version | Info | Document which is authoritative for production using release notes/deployment docs |
| Consumer uses an older published version while local source changes | Warning | Verify local source was published before deployment |
| Library is not reachable from the consumer’s NuGet feed | Warning | Verify it is published, not merely on disk |

Fix drift by publishing the updated library and updating the consumer’s pinned version; do not wrap them in a solution.

### Library quality

| Check | Severity |
|---|---|
| Clear single purpose; no unrelated grab-bag helpers | Warning |
| Deliberate public workflows; internal helpers marked Private | Warning |
| Descriptive scoped library name, e.g. `Company.Email.Utilities` rather than `Helpers` | Info |
| Public workflow names use verb–noun form, e.g. `SendNotificationEmail`, `ValidateInvoice` | Info |
| Public workflows have descriptions/annotations | Warning |
| Arguments have descriptions/tooltips | Warning |
| README documents purpose, usage, prerequisites, and breaking changes | Info |
| `ContinueOnError="True"` is absent from library `.xaml` files | Critical |
| Meaningful exceptions are thrown; errors are not swallowed; use `BusinessRuleException` for input validation and propagate system exceptions | Warning |

### Semantic versioning

| Check | Severity |
|---|---|
| `projectVersion` uses SemVer (Major.Minor.Patch) | Warning |
| Breaking changes (renamed arguments or removed workflows) require a major bump | Critical |
| Minor bumps are backward-compatible and additive (new workflows or optional arguments) | Warning |
| Patch bumps do not change interfaces | Info |
| Old feed versions remain available | Warning |
| Each version has release notes/changelog | Info |
| Git tags exist per published version | Info |

### Library patterns

| Pattern | Use when | Anti-pattern |
|---|---|---|
| Wrapper | Reducing boilerplate for common activity sequences | Wrapping one activity without added value |
| Connector | Centralizing one external system | Multiple competing libraries for the same system |
| Framework | Providing extensible scaffolding, such as REFramework | Hard-coded business logic in the framework |
| Data Access | Centralizing DB/API access, such as `GetCustomerById` returning `DataRow` | Leaking data-source details to consumers |

### Feed and consumer governance

- Feed scope: Tenant for project-team libraries; Host for organization-wide libraries (**Info**).
- Use Artifactory, Azure Artifacts, or another custom NuGet feed for advanced governance (**Info**).
- Restrict publishing permissions to designated maintainers (**Warning**).
- Production dependencies must pin exact versions such as `[1.2.3]`, not floating ranges such as `[1.2.3, )` (**Warning**).
- Remove unused dependencies (**Info**).
- Promote library upgrades Dev → Test → Prod (**Warning**).
- Regression-test major upgrades (**Warning**).
- Reuse libraries instead of copy-pasting common workflows (**Warning**).
- Define ownership: CoE for organization-wide libraries and team ownership for team-specific libraries (**Warning**).
- Maintain a library catalog with purpose, owner, and current version (**Info**).
- Require code review for corporate-library changes (**Warning**).
- Require architectural review and impact analysis for major bumps (**Warning**).

## 6. Solution Antipatterns

### One-artifact-per-solution scatter

If many solutions contain exactly one executable and those executables coordinate business logic, share queues/data/configuration, or ship together, flag consolidation as **Info**; use **Warning** when version drift has caused incidents. Detect by listing all `.uipx` solutions, counting processes, agents, and flows in each, and assessing coupling. Consolidate tightly coupled artifacts when failure of A would require investigating or rolling back B.

### Monolith solution

A solution with 15+ unrelated projects is an **Info** finding. Count project directories and inspect shared data/dependencies; split by business domain unless packaging failures justify higher severity.

### Orphan projects

An executable directory outside `.uipx` is an **Warning** finding. For each `project.json`, inspect `outputType`: `"Process"` and `"Tests"` are executable; `"Library"` is not. Add the executable to `.uipx` or move it elsewhere. Never flag libraries as orphans.

## 7. Lifecycle, Transport, and Deployment

### Deployment configuration

| Check | Severity |
|---|---|
| URLs, credentials, queue names, and other environment-specific values are deployment-configurable, not hardcoded | Warning |
| Solution deploys to a new environment without code changes | Warning |
| Credential mappings are documented per environment | Warning |
| Asset, queue, and connection mappings are defined per target environment | Warning |

### Versioning and transport

| Check | Severity |
|---|---|
| `.uipx` version follows semantic versioning aligned with release milestones | Warning |
| Project versions within a solution are consistent | Warning |
| Rollback procedure is documented and tested | Warning |
| Release notes exist per version | Info |
| CI/CD automates transport and deployment | Info |

### Pre-deployment

| Check | Severity |
|---|---|
| Non-production testing occurs before promotion | Warning |
| Target environment has all packages, connections, and assets | Critical |
| `uip solution pack` succeeds | Critical |
| Audit trail records who deployed what, when, and where | Info |

## 8. Solution Accelerator Customization

For a UiPath Marketplace Accelerator base:

| Check | Severity |
|---|---|
| Accelerator matches the business process | Warning |
| Core accelerator workflows remain unmodified; extensions are layered on top | Warning |
| Customization uses config files rather than code changes | Warning |
| All customizations are documented for future updates | Warning |
| Marketplace update path remains viable | Info |
| Accelerator prerequisites and dependencies are verified in the target environment | Critical |