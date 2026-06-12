# case (root) — Planning

The root case definition — the top-level container that every other node lives inside. Created exactly once per project. Under the JSON strategy the case plugin **also owns project scaffolding** (the 5 boilerplate files written by `uip maestro case init` on the CLI path) — see [impl-json.md](impl-json.md).

## When to Use

Always. This plugin is invoked for the very first T-entry (`T01`) in every `tasks.md`. It creates the case file and the implicit Trigger node.

## Required Fields from sdd.md

| Field | Source | Notes |
|-------|--------|-------|
| `name` | sdd.md case title | Human-readable. |
| `file` | Derived: `<SolutionDir>/<ProjectName>/caseplan.json` | **Literal filename `caseplan.json`** — do not substitute project name. |
| `case-identifier` | sdd.md (optional; defaults to `name`) | The runtime identifier. |
| `identifier-type` | sdd.md (optional; default `constant`) | `constant` \| `external`. Use `external` when sdd.md says the identifier comes from an upstream system. |
| `case-app-enabled` | sdd.md (default `false`) | `true` if the sdd.md says the case is exposed via the Case App UI. |
| `directly-pass-task-outputs` | sdd.md (default `true`) | Passes task outputs through messages instead of shared variables, avoiding parallel-task race conditions. `false` only if sdd.md explicitly requests shared-variable passing. |
| `description` | sdd.md case description |  |

## identifier-type Guidance

- `constant` — **Default.** Use when sdd.md does not mention external identifier sources. The identifier is a fixed 2-4 char prefix; runtime emits `<prefix>-<generated>`.
- `external` — Use when sdd.md says the identifier comes from upstream data ("identified by the incoming PO number", "uses the external ticket ID"). `case-identifier` becomes a `=`-prefixed expression; runtime evaluates it and the result IS the case external id.

When ambiguous, use **AskUserQuestion** with both options + "Something else".

### External identifier value

`case-identifier` is carried verbatim from sdd.md — one of two forms (no other engine):

- **Bare var** — `=vars.<varId>`, where `<varId>` is a single variable declared in the §4.2.1 block. It MUST be an **In** argument or a **Variable** — not an **Out** argument (produced at case end).
- **`=js:` expression** — for string ops / concatenation, e.g. `` =js:`${metadata.InstanceId}-${vars.region}` ``. May read `vars.<id>` and `metadata.InstanceId` / `metadata.FolderKey` / `metadata.ProcessKey` — never `metadata.ExternalId` (the field being set).

A referenced variable must have its own §4.2.1 T-entry (the completeness cross-check requires it).

## Registry Resolution

**None.** The root case has no registry representation — no `taskTypeId`, no enrichment.

## Trigger Node — Emitted by Triggers Plugin (T02)

The case plugin writes a pure skeleton at T01 — no trigger node. The primary trigger is added by the triggers plugin at T02 via the matching [triggers plugin](../triggers/). Every case (single-trigger or multi-trigger) has at least one T02 entry for the primary trigger.

## tasks.md Entry Format

```markdown
## T01: Create case file "<name>"
- file: "<SolutionDir>/<ProjectName>/caseplan.json"
- case-identifier: "<identifier>"
- identifier-type: constant
- case-app-enabled: false
- directly-pass-task-outputs: true
- description: "<one-sentence description>"
- order: first
- verify: Confirm caseplan.json written and parses; id matches /^case-[A-Za-z0-9]{10}$/, version == "23.0.0", nodes == [], edges == []
```

> **External variant.** Replace the two identifier lines with `identifier-type: external` + `case-identifier: "=vars.<varId>"` (or a `=js:` expression). See § External identifier value.

## Project Structure Prerequisites

The case file lives inside a solution + project structure. After T01 completes, the layout is:

```
<directory>/
  <SolutionName>/
    <SolutionName>.uipx            ← created by `uip solution init` (Step 6.0, CLI)
    <ProjectName>/                 ← created + populated by T01 (case plugin)
      project.uiproj               ← § Scaffold writes
      operate.json                 ← § Scaffold writes
      entry-points.json            ← § Scaffold writes (empty entryPoints[])
      bindings_v2.json             ← § Scaffold writes
      package-descriptor.json      ← § Scaffold writes
      caseplan.json                ← § Write caseplan.json writes
```

Planning-phase contract: T01 emits all 5 scaffold files + `caseplan.json` inside `<SolutionDir>/<ProjectName>/`. CLI `uip solution init` and `uip solution project add` bookend T01 as Step 6.0 and Step 6.0b.

See [implementation.md Step 6](../../implementation.md) for the authoritative 3-step execution sequence.
