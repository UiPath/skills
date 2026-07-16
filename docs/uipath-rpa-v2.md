# uipath-rpa v2 — Reference Consolidation Plan

Reduce per-task latency of the `uipath-rpa` skill by merging reference files that are always read together, trimming duplicated content, and keeping every file ≤ ~12k tokens (≈48k chars). Each `Read` of a routed reference costs one model turn; coded RPA eval tasks routinely spend 25–30 of a 40-turn budget (`tests/experiments/smoke.yaml`). SKILL.md mandates full-file reads and chains 2–3 references per Task Navigation row — merging co-read files removes 2–4 turns per task.

## Problem measurements (base: `main` @ 70ace525c)

- SKILL.md: ~16.1k tokens — over the ~12k cap; loaded on every activation.
- `references/xaml/common-pitfalls.md`: ~16.0k tokens — over cap; contains a byte-identical duplicated section (lines 773–806 = 807–840, ~620 tokens).
- Same content restated up to 4× (`NGetText` skip-tax: SKILL.md Rule 21, `xaml/workflow-guide.md` §1.2, `validation-guide.md`, `xaml/xaml-basics-and-rules.md`).
- Reads per flow: XAML create 6–9 · UIA 3–4 · coded 3–5 · legacy project create 5 · IS-connector XAML 2.

## Stage 1 — merge references (this PR)

Every merge absorbs into the surviving file's existing name. No new filenames except none; absorbed files are deleted and all inbound links rewritten.

### Modern track

| Survivor | Absorbs | Post-merge target |
|---|---|---|
| `references/cli-reference.md` | `validation-guide.md`, `publishing-guide.md`, CLI-pitfalls § of `xaml/common-pitfalls.md` | ≤ ~10k |
| `references/xaml/xaml-basics-and-rules.md` | `xaml/workflow-guide.md` (ConnectorActivity internals move out to IS guide) | ≤ ~11k |
| `references/xaml/canvas-layout-guide.md` | `xaml/flowchart-guide.md`, x:Reference-naming § of `common-pitfalls.md` | ≤ ~10k |
| `references/xaml/csharp-activity-binding-guide.md` | `xaml/csharp-expression-pitfalls.md` | ~2.7k |
| `references/ui-automation-guide.md` | `uia-prerequisites.md`; sheds OR-as-UI-Library § → library guide; stub-§ compressed | ≤ ~11.5k |
| `references/uia-configure-target-workflows.md` | `uia-elements-interaction-guide.md`, UIA gotchas §§ of `common-pitfalls.md` | ≤ ~8.5k |
| `references/coded/operations-guide.md` | `coded/coding-guidelines.md` | ≤ ~11k |
| `references/coded/codedworkflow-reference.md` | `coded/inspect-package-guide.md`, `coded/third-party-packages-guide.md` | ≤ ~5.5k |
| `references/environment-setup.md` | `project-structure.md`, `project-structure-guide.md` | ≤ ~7.5k |
| `references/is-connector-xaml-guide.md` | `connector-capabilities.md`, IS gotchas § of `common-pitfalls.md`, ConnectorActivity internals from `xaml-basics-and-rules.md` | ≤ ~10.5k |
| `references/library-authoring-guide.md` | OR-as-UI-Library § from `ui-automation-guide.md` | ~4.3k |
| `assets/codedworkflow-template.md` | `testcase-template.md`, `helper-utility-template.md`, `before-after-hooks-template.md` (`json-template.md` stays — config snippets, linked by Rule 10 + LRW guide) | ~2.6k |

`xaml/common-pitfalls.md` lands ≤ ~12k after the section moves + duplicate removal. `tenant-library-search-guide.md` stays standalone (Rule 9 reads it alone).

### Legacy track

| Survivor | Absorbs |
|---|---|
| `references/legacy/cli-reference.md` | `environment-setup.md`, `project-structure.md`, `discovery-workflow.md`, `validation-and-fixing.md` (~10.1k) |
| `references/legacy/xaml-basics-and-rules.md` | `common-pitfalls.md` (~9k after trims) |
| `references/legacy/selector-guide.md` | `activity-docs/UIAutomation.md` (~4.9k) |
| `references/legacy/testing-guide.md` | `test-data-guide.md`, `activity-docs/Testing.md` (~5.8k) |

NOT merged: per-package legacy activity docs (read one-at-a-time), `AllActivities.md` (breadth catalog, complementary — ~25–40% overlap only), `_INDEX.md` (sole reachability path for per-package files), on-demand deep dives (`_XAML-GUIDE`, `_REFRAMEWORK`, `_DU-PROCESS`, `_INVOKE-CODE`, `_PATTERNS`), modern single-topic guides (`debugging`, `error-handling-guide`, `testing-guide`, `data-manipulation-guide`, `trigger-pattern-guide`, `reframework-guide`, `powershell-interop-guide`, `xaml/jit-custom-types-schema`, `xaml/long-running-workflow-guide`, `coded/integration-service-guide`), `agents/uipath-project-discovery-agent.md` (spawned, never read inline).

### Trims (no information loss)

- `common-pitfalls.md`: delete duplicated Array-Types section (−620 tok).
- `debugging.md`: "log level ≠ verdict" ×6 → once + anchors; Best Practices restating verb table; quoting caveat ×5 → once.
- `testing-guide.md`: drop reproduced `fileInfoCollection` JSON (canonical: `assets/json-template.md`) + Test Manager command block (canonical: `cli-reference.md § Test Manager`).
- `is-connector-xaml-guide.md`: metadataFile cache path ×3 → once.
- `coded/integration-service-guide.md`: comments restating adjacent prose.
- Legacy: VB.NET cheat-sheet dup (`common-pitfalls` vs `_PATTERNS`), deprecated-activities subset, Throw-escaping gotcha ×4 → canonical in merged XAML kit, type-mapping tables dup with `_XAML-GUIDE`.

### Found-along-the-way fixes (this PR)

1. Personal path `C:\Users\alexandru.roman\...` in `legacy/activity-docs/_REFRAMEWORK.md:7` and `_DU-PROCESS.md:340` — removed (repo rule: no personal paths). Forum "Sources" link dumps removed.
2. Cross-skill file links → skill-name pointers (self-containment): publishing content (5 links → uipath-solution/uipath-test) and `coded/integration-service-guide.md` (4 links → uipath-platform).
3. Broken pointer `coded/inspect-package-guide.md:3` (`references/<service>/examples.md`) — fixed to the real bundled path.
4. Bundled coded activity-doc triples (`references/activity-docs/<Pkg>/<ver>/coded/`) were orphaned (zero inbound links). Kept, wired as third-tier fallback: `.local/docs/.../coded/coded-api.md` → `packages inspect` → bundled `coded/` docs.
5. `skills/uipath-test/references/publish-and-link-guide.md` inbound link updated to `cli-reference.md § Pack & publish` (publishing-guide.md absorbed).

## Stage 2 — SKILL.md slim (separate stacked PR)

Keep every rule statement; delegate procedure bodies to the merged references. Targets: Rule 2 template-selection detail (−~390), Rule 3 validation detail (−~300), Rule 12 trigger placement (−~300), Rule 20 (−~200), Rules 21/21a (−~600), Rule 23 conversion procedure (−~200), Placeholder-stub § (−~300), Error-handling § TOC ×3 (−~150), Quick Reference tables duplicated from references (−~800), § Resolving Packages (−~250), UIA doc listing (−~350). Target ~12k. Higher risk: rule bodies look like past eval-failure patches — gate separately.

## Sequencing & risks

- Based on latest `main`, NOT `feat/uipath-rpa-execution-maps` (PR #1827). Known conflict surface with #1827: `SKILL.md`, `xaml/workflow-guide.md` (deleted here, edited there), `environment-setup.md`, `ui-automation-guide.md`, `uia-configure-target-workflows.md`. Whichever lands second rebases; the workflow-guide edits from #1827 port into `xaml-basics-and-rules.md`.
- Merged files raise tokens-read for flows that previously read only the smaller member; pairs were chosen for high co-read probability. The A/B tokens metric is the check.
- Frontmatter `description` untouched → no `activation-gate.yml` recall eval.

## Verification

1. Link integrity: every relative `.md` link under `skills/uipath-rpa/` resolves (no checker script exists; use grep + existence check).
2. Token caps: every changed file ≤ ~12.3k tokens (chars/4); all files < 2,000 lines (Read tool limit).
3. `hooks/validate-skill-descriptions.sh`, `python3 scripts/check-skill-status.py` clean.
4. CI: `smoke-rpa-skills.yml` runs Windows-tagged rpa tasks on the PR.
5. Speed A/B (after PR is up): `/skill-compare main feat/uipath-rpa-consolidate-refs uipath-rpa 3` — hypothesis: "Merging always-co-read references cuts per-task reference reads by 2–4 turns and reduces duration/tokens without reducing success rate." Decision per skill-compare Phase 8 (merge requires strictly more head-to-head wins, flip_rate 0, N≥3). Materiality bar for tokens: >10%.

## Expected effect

| Flow | Reads before | Reads after |
|---|---|---|
| XAML create | 6–9 | 4–5 |
| Flowchart | 3–4 | 2 |
| UI automation | 3–4 | 2 |
| Coded workflow | 3–5 | 1–2 |
| IS-connector XAML | 2 | 1 |
| Legacy project create | 5 | 1 |

Files: 105 non-activity-docs markdown files → 82 (12 modern refs + 3 assets + 8 legacy absorbed, publishing-guide absorbed).
