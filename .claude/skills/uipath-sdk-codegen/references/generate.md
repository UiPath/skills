# Writing the emitter — JSDoc, the generate/hand-write split, and the router

## The JSDoc technique (the reason this pays off)

The chain already exists in this repo and the generator must feed it:

```
JSDoc in TypeScript source
  → tsc emits it into dist/**/*.d.ts
    → scripts/lib/extract-decls.mjs lifts the declaration + its JSDoc
      → scripts/gen-case-skill.mjs fills <!-- GEN:… --> in SKILL-case.template.md
        → SKILL-case.md, which is what the authoring agent reads
```

So a sentence written once in the generator reaches the agent authoring cases. That is
the whole leverage: **closed unions and their doc comments become exhaustive-by-
construction in the doc**, which is what stopped this doc from being wrong.

**Rules:**

- **Every generated declaration carries JSDoc.** A method without it is a silent
  regression in `SKILL-case.md` — the GEN block emits a bare signature and the authoring
  agent loses the only explanation it had.
- **Put the non-obvious fact in the JSDoc, not in the generator's own comments.** The
  `serviceType` default, the units, the "not `.required()`" gotcha — those must travel.
- **Emit doc comments on union members too** where the member name isn't self-evident.
- After generating: `node scripts/gen-case-skill.mjs --check` must pass. It is a hard CI
  gate, so a stale generated doc cannot merge.

Worth knowing what this costs. Adding prose to the skill doc measurably increases agent
turns (~+20% on a 14-task suite, at flat pass rate) because cache reads dominate token
spend and every extra line is re-paid on every subsequent turn. **Generated JSDoc earns
its place by replacing exploration; decorative prose does not.** Keep it to what a reader
cannot derive from the signature.

## Generate the leaves, hand-write the grammar

| generate from schema | hand-write |
| --- | --- |
| task kinds + per-kind `data` payload params | the fluent grammar, chaining, `build()` |
| closed unions: `TaskKind`, `CaseRuleType`, `SlaUnit`, `StageExitType` | rule **placement** (which rule in which slot) |
| enum members, `serviceType` defaults, binding shapes | `check.ts` semantic rules |
| per-version differences | error messages that teach |

**This boundary is not stylistic.** The schema carries *shape*. It does not carry: which
rule is legal in which slot; "every task needs an entry rule"; "`required-tasks-completed`
needs a required task"; DNF grouping; or that two exits with identical rules collide.
Those come only from `uip`. This is the same boundary Lombok's `@Builder` has — it
generates from fields and invents no invariants.

Corollary: **generation cannot close a semantic gap**, so don't let a generated builder
imply the checker is unnecessary. They cover disjoint failure classes.

## Provenance header (required)

Every generated file starts with the Step 0 pin. Without it the output is unreviewable —
you cannot tell whether a member is missing because the platform lacks it or because the
generator ran against an old package.

```ts
/**
 * GENERATED — do not edit. Regenerate with:
 *   node .claude/skills/uipath-sdk-codegen/scripts/extract-schema.mjs
 *
 * cli:        uip 1.202.0                    (launcher — NOT what validates)
 * authority:  @uipath/maestro-tool 1.198.0   (bundled validator — what DOES validate)
 * package:    @uipath/case-schema@0.859.0    (audited copy; 0.1016.2 and 0.1052.3 also installed)
 * schema:     V20 (emitted)  |  V13 (highest the authority bundles)
 * mainline:   PO.Frontend 0b11f5660 (V31) — forecast only, NOT generated
 * generated:  2026-09-01
 *
 * Members below were confirmed by `uip maestro case validate`; the verdict text for
 * each is in scripts/probe-results.json. Members present in the schema but NOT
 * confirmed are omitted, not commented out — an omission is honest, a commented-out
 * method invites someone to uncomment it.
 */
```

## The router

```
typescript/sdk/src/case/generated/
  v20/{task-kinds.ts, unions.ts, meta.json}
  v23/…
  index.ts        ← router
```

`meta.json` per version holds the provenance and the probe verdicts, so the audit reads
generated facts instead of parsing a header.

Resolution, most specific first: explicit `casePlan(id, { schemaVersion })` → env
`UIPATH_CASE_SCHEMA_VERSION` → detected from the installed package → pinned default
(V20 today).

**Fail loudly on an unknown pair.** Do not fall back to the nearest version. Silent
fallback is how you emit a document the converter rejects while every local gate passes —
the exact shape of the bug this skill exists to prevent.

**Tag each fact with its provenance** (`confirmed` vs `enumerated`) and let consumers
choose: `check.ts` should hard-error only on `confirmed`, and warn on `enumerated`. A
hard gate built on an unverified fact is worse than no gate — one shipped here, blocking
emit for plans the platform accepted, and had to be removed.

## Adding a new task kind (worked shape)

For `external-agent` — enumerated in the published zod, and confirmed accepted:

1. **Enumerate** its data schema. In the bundle:
   `CaseManagementJsonTaskExternalAgentRunDataSchema = …extend({ serviceType: z.string().optional(), bindings: z.array(UiPathBindingJsonSchema).optional() })`
2. **Find the default** in the converter, don't guess:
   `serviceType = externalAgentData.serviceType || "Intsvc.SyncAgentExecution"`
   (`external-workflow` → `"Intsvc.SyncWorkflowExecution"`; async agent →
   `"Intsvc.AsyncAgentExecution"`.)
3. **Probe** it (`references/verify.md`) and record the verdict.
4. **Emit** the union member, the `TaskKind` entry, the builder method with JSDoc naming
   the default, and the serializer arm.
5. **Verify**: build → `gen-case-skill.mjs --check` → audit → `compile.sh` on a real case
   → `Status: Valid`.

Reuse before inventing: `bindings` is the existing `UiPathBindingJsonSchema` that
`.connector()` already resolves. A second binding mechanism would be a bug.

## What to emit: prefer impossible over detected

The emitter's job is not to describe the platform, it is to make the wrong call
unwritable. Rank every constraint you are about to encode:

| Rung | Form | When |
|---|---|---|
| **1** | A type the wrong call fails to satisfy — closed union, narrowed param, method absent from the slot's interface | Always, if the grammar allows it |
| **2** | An emitted `interface` the hand-written builder must `implement` | When the surface exists but coverage must be forced. `tsc` cannot be skipped; an audit script can |
| **3** | A table the checker reads at build time | Consolation prize. Record what would promote it |

Rung 1 has no error message, because there is no state to report. That is the point — the
author spends zero turns, and turns are the cost model this whole program is built on.

Worked example. `UNREACHABLE_PLACEMENTS` (13 cells the validator accepts and the
scheduler cannot evaluate) is rung 3. It is derived from **per-slot** unions, and slots are
positions in a fluent chain — so rung 1 exists: give each slot its own accepted-rule type
and `.onStageExit(caseEntered(...))` stops compiling. Reach for that before growing the
table.

**Earn it first.** A guessed constraint encoded as a type is unfalsifiable by the author —
worse than a warning, because they cannot discover it is wrong. `confirmed` gates rung 1
and 2; anything weaker gets rung 3 with its grade recorded, or gets omitted.

## Anti-patterns

- **Generating from `dist/index.d.ts`.** It is hand-written and wrong three times over.
- **Encoding an unearned constraint into a type.** Unfalsifiable beats wrong-and-visible
  only in appearance. Grade it, then pick the rung.
- **Adding to a checker table when the type system could have refused it.** A table is
  rung 3; check whether the constraint is expressible in the grammar first.
- **Widening a union to make a test pass.** If `uip` rejects it, the generator is right.
- **Emitting mainline-only members.** They produce caseplans the installed converter
  rejects. Forecast, don't generate.
- **Commenting out unconfirmed members.** Omit them.
- **Bumping `_version` as a side effect.** Re-pinning is deliberate and has migration
  consequences (V27 requires escalation `displayName`).
