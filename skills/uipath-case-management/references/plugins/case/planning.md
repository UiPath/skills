# case (root) — Planning

The root case definition — the top-level container that every other node lives inside. Created exactly once per project. The case plugin **also owns project scaffolding** (the 5 boilerplate files written alongside `caseplan.json`) — see [impl-json.md](impl-json.md).

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `name` | sdd.md case title | Written to `root.name`. Human-readable. |
| `file` | Derived: `<SolutionDir>/<ProjectName>/caseplan.json` | **Literal filename `caseplan.json`** — do not substitute project name. |
| `case-identifier` | sdd.md (optional; defaults to `name`) | Written to `root.caseIdentifier`. The runtime identifier. |
| `identifier-type` | sdd.md (optional; default `constant`) | Written to `root.caseIdentifierType`. `constant` \| `external`. Use `external` when sdd.md says the identifier comes from an upstream system. |
| `case-app-enabled` | sdd.md (default `false`) | Written to `root.caseAppEnabled`. `true` if the sdd.md says the case is exposed via the Case App UI. |
| `description` | sdd.md case description | Written to `root.description`. |

## identifier-type Guidance

- `constant` — **Default.** Use when sdd.md does not mention external identifier sources. The case identifier is fixed across instances (typically matches `name`).
- `external` — Use when sdd.md says something like "the case is identified by the incoming PO number" or "the case uses the external ticket ID." Runtime will pull the identifier from case data.

When ambiguous, use **AskUserQuestion** with both options + "Something else".

## Registry Resolution

**None.** The root case has no registry representation — no `taskTypeId`, no enrichment.

## Trigger Node — Emitted by Triggers Plugin (T02)

T01 writes a pure skeleton — no trigger node. The primary trigger is added by the triggers plugin at T02 via the matching [triggers plugin](../triggers/). Every case (single-trigger or multi-trigger) has at least one T02 entry for the primary trigger.

## tasks.md Entry Format

```markdown
## T01: Create case file "<name>"
- file: "<SolutionDir>/<ProjectName>/caseplan.json"
- case-identifier: "<identifier>"
- identifier-type: constant
- case-app-enabled: false
- description: "<one-sentence description>"
- order: first
- verify: Confirm caseplan.json written and parses; root.id == "root", nodes == [], edges == []
```

## Project Structure Prerequisites

The case file lives inside a solution + project structure. After T01 completes, the layout is:

```
<directory>/
  <SolutionName>/
    <SolutionName>.uipx            ← created by `uip solution new` (Step 6.0)
    <ProjectName>/                 ← created + populated by T01 (case plugin)
      project.uiproj               ← § Scaffold writes
      operate.json                 ← § Scaffold writes
      entry-points.json            ← § Scaffold writes (empty entryPoints[])
      bindings_v2.json             ← § Scaffold writes
      package-descriptor.json      ← § Scaffold writes
      caseplan.json                ← § Write caseplan.json writes
```

Planning-phase contract: T01 emits all 5 scaffold files + `caseplan.json` inside `<SolutionDir>/<ProjectName>/`. `uip solution new` and `uip solution project add` bookend T01 as Step 6.0 and Step 6.2.

See [implementation.md Step 6](../../implementation.md) for the authoritative 3-step execution sequence.
