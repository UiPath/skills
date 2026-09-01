---
name: uipath-sdk-codegen
description: Generate a version-pinned fluent Case/Flow builder SDK for a target UiPath CLI version. Loads that version's schema and validator vocabulary (plus dated hints from prior versions), interviews for what no artifact can answer, then emits the builder with JSDoc that flows into the generated skill doc. Use when adding builder coverage, re-pinning to a newer schema version, or auditing what the builder cannot express.
---

# The version chase — generating a version-pinned fluent SDK

The builder is a **projection** of the platform schema. Hand-writing that projection is
why coverage gaps and stale assertions keep appearing. Generate it and the gaps close by
construction; the audit collapses into a staleness check.

**This solves a chase, not a lookup.** Six artifacts describe what the platform accepts
and they version independently — the launcher, the validating tool, the schema bundled
inside it, the package a repo installs, that package's hand-written header, and mainline.
No two are guaranteed to agree today. There is no fixed truth to look up; there is a
moving target, and the job is tracking it at machine cost rather than human cost. That is
why every fact recorded here carries a version pin and a verdict — a claim without both is
a claim about a platform that has already moved.

**Read `references/sources.md` before anything else.** Getting the source wrong is the
failure this skill exists to prevent — every wrong number produced in this repo came
from reading a convenient artifact instead of an authoritative one, most recently by
auditing against a copy of `@uipath/case-schema` that `uip` never loads.

Three phases. Do not start one before the previous is closed out.

---

## Start here

```bash
node scripts/survey.mjs
```

One command. It runs every cheap tier in cost order and prints where you stand, then lists
what is left — naming the exact slower command for each remaining gap. Run it first, every
time. If it says nothing is outstanding, the cheap tiers settled everything recorded and you
have no reason to reach for a probe.

It exists because ordering that lives only in prose gets run backwards. This skill had eleven
scripts and eight documented commands, and this program spent a day probing a validator
(tier 4, minutes per cell) to answer questions the fixtures (tier 2, seconds) answer outright
— having already written down that fixtures come first. `survey` makes the order the default
rather than the instruction.

Two other commands are worth knowing by name:

```bash
node scripts/discover-resources.mjs        # which tenant resources a task may reference
cd typescript/sdk && npm run demo:case-compat   # what the SDK can express, proved live
```

Everything else is reached through what `survey` tells you to do next.

## Before Phase 1 — precedence is fastest-first, which is also most-scriptable-first

The ordering that matters is **cost**, and the useful accident is that cost and
automatability are the same axis: the fastest sources are the scriptable ones, the slowest
need a human. Ordering by speed therefore also orders by how much runs unattended.

| # | source | answers | cost | scriptable? |
|---|---|---|---|---|
| 1 | installed schema + slot grid (`@uipath/scheduler-types`, maestro-tool bundle) | what is expressible; the placement grid | **ms** | fully — `extract-schema`, `extract-scheduler-grid` |
| 2 | fixtures — `~/src/dmnscheduler/test-cases/<NN>/` | what the platform MUST decide, with negative cases | **seconds** | fully — JSON triples; grep the rule names |
| 3 | source read — evaluators, PO.Frontend converter | what the code does where no fixture covers it | **minutes** | partly |
| 4 | probe `uip maestro case validate` | what is accepted — **shape only** | **minutes/cell** | yes but slow |
| 5 | a running instance (`debug`) | what actually happens | **minutes to never** | no — needs a tenant robot |
| 6 | ask a human | intent, policy, roadmap | **hours to days** | never |

Top-down it is a funnel: each tier is cheap enough to run against everything, and what it
settles narrows the tiers below. Bottom-up it is a budget: **tier 6 is the only
irreplaceable one**, so every question pushed upward stops costing a person's attention.

**Probing is fourth**, and that is the uncomfortable part — it is the technique this skill was
built around. It answers the narrowest question of the six and costs minutes per cell. Reach
for it when the cheaper tiers structurally cannot answer, not first. This skill's own session
ran the list backwards (probed first, fixtures last, having already cited the fixtures as
authoritative) and the order cost about a day.

Two questions, and one table cannot serve both: **shape** (tiers 1, 4) and **behaviour**
(tiers 2, 3, 5). A tier-4 pass means "nothing has objected yet", never "this is correct".
Full tables, and the sources disqualified outright, in
[references/sources.md](references/sources.md).

**Verify the binding, not the checker** — see
[references/verify.md](references/verify.md#verify-the-binding-not-the-checker). Every
measurement failure recorded here was a correct check bound to the wrong data, and none was
caught by re-reading the code that produced it. Step into a different representation: unpack
the tarball, read the emitted artifact, open someone else's fixtures.

## Phase 1 — LOAD the target version

Everything downstream is scoped to a `(CLI, schema)` pair. Pin it explicitly; a
generator that isn't version-aware confidently emits invalid caseplans.

### 1a. Pin, and record all of it

```bash
uip --version | tail -1                                              # launcher
node -p "require(process.env.HOME+'/.bun/install/global/node_modules/@uipath/maestro-tool/package.json').version"
grep -o "_version = '[0-9.]*'" typescript/sdk/src/case/case-sdk.ts   # document version WE emit
(cd ~/src/PO.Frontend && git log --oneline -1)                       # mainline, if cloned
```

**The launcher and the validating tool version independently** — observed `uip` 1.202.0
against `maestro-tool` 1.198.0 (2026-09-01; was 1.200.0/1.198.0 on 2026-08-06 — the
launcher moved four versions, the validator did not move at all). Record both or the
provenance is a fiction.

### 1b. Enumerate the target's schema (what exists)

```bash
node .claude/skills/uipath-sdk-codegen/scripts/extract-schema.mjs \
  [--bundle <path>] [--source ~/src/PO.Frontend/src/types/case-mgmt-zod]
```

Defaults to the bundle that **actually validates** (`maestro-tool/dist/tool.js`) and
says which source it used. To target a version other than the installed one, point
`--bundle` at that version's tool bundle.

### 1c. Mine prior versions for dated hints

```bash
node .claude/skills/uipath-sdk-codegen/scripts/mine-history.mjs --ref v1.198.0 --dates
```

Reads the CLI validator's `VALID_*` vocabulary **at any ref** and dates each member from
git history. This is the only way to get semantics for a version you cannot run, and the
commit subjects carry the version scoping directly — `adhoc` arrives with "v12 schema",
`required-tasks-completed` with "update case schema to V16".

Use it to answer "was this always true, or did it change?" before treating today's
behaviour as timeless.

**Absence in the CLI layer is not absence from the platform.** `case-tool` has never
contained `sla-status-change`, yet `uip` accepts it — maestro-tool bundles its own
case-schema that also validates. Cross-check 1b against 1c; where they disagree, probe.

### 1c-bis. Read the fixtures BEFORE probing

```bash
node scripts/read-fixtures.mjs --type SlaStatusChange
node scripts/read-fixtures.mjs --grep sla --show 07
```

Tier 2. Every question a fixture answers is a question the probe loop below does not have to
ask, at seconds instead of minutes per cell — and fixtures answer a question probing cannot
reach at all, because they state what the platform is REQUIRED to decide rather than what it
merely accepts. Negative cases come free.

Record what you find as `fixture-specified`, not `validator-confirmed`. The grades are not
interchangeable: a probe verdict licenses emitting a member; a fixture licenses a claim about
BEHAVIOUR, which no probe ever can.

### 1d. Close the gap list

```bash
node scripts/semantics-gaps.mjs                 # what is unknown
node scripts/run-probes.mjs                     # probe it — dry run, report only
node scripts/run-probes.mjs --apply             # record the verdicts
```

`semantics-gaps` reports drift, schema members with no semantics entry, unprobed
(rule, slot) cells, and the questions no artifact can answer. `run-probes` then **does
the probing**: emits a minimal case per cell, runs `uip`, classifies the verdict, and
with `--apply` writes it back. The full grid is ~48 cells in under a minute.

Three things it gets right that a hand-rolled loop does not, each learned from a real
mistake:

- **It supplies each rule's payload.** Without one you cannot separate "illegal here"
  from "I forgot a field" — both surface as a semantic error.
- **It separates OUR gate from THE PLATFORM'S.** If `check.ts` or `build()` rejects
  first, `uip` never answered, so there is no verdict: that is `blocked-by-builder`, and
  it is never recorded.
- **`inconclusive` is never written as `legal:false`.** Only `accepted` and `rejected`
  become cells.

Anything probing cannot reach, work **docs → interview**, in that order, and record it:

```bash
node scripts/semantics-update.mjs --cell "adhoc@stage-exit" --legal true --verdict "Status: Valid"
```

> **What the first full grid found, and it matters for phase 3.** The validator accepts
> **35 of 48** combinations, including meaningless ones like `case-entered@task-entry`.
> Only `timer`/`condition`/`stage-complete` (all slots) and
> `selected-tasks-completed@stage-entry` are rejected. **Placement is almost entirely
> unenforced** — so the placement tables in `SKILL-case.md` and in `uipath-maestro-case`
> are authoring guidance, not validator behaviour. `check.ts` may hard-error only on
> cells recorded `legal:false`; everything else is at most a warning. And accepted does
> not mean sensible: validation is not execution.

`references/verify.md` has the probe recipe and the verdict-class table;
`references/acquire.md` has the doc-mining sources, including the CLI history above and
the `uipath-maestro-case` skill, which is organised **as a placement matrix** and gives
you ~13 slot assignments to verify rather than guess.

### 1e. Discover what the tenant can actually be referenced

The schema tells you a `process` task takes a `name` and a `folderPath`. It does not tell you
which processes exist. A reference-mode task is just those two strings on the wire, so **the
validator cannot distinguish an invented name from a published one** — a case full of
plausible names validates, packs, uploads, and dies on its first task.

```bash
uip maestro case registry pull                 # ~/.uip/case-resources/ — the hard gate
node scripts/discover-resources.mjs            # per SDK task kind
node scripts/discover-resources.mjs --kind agent --grep contract --json
```

This is a different KIND of ground truth from everything else in Phase 1. The schema and the
probes tell you what is *expressible*; this tells you what is *referenceable on one tenant
right now*. It is therefore **environment state, not a semantic fact** — never write it into
`semantics/case-semantics.json`, which is meant to be true of a version, not of a tenant on a
Tuesday. Discovery is re-run per authoring session; semantics is versioned knowledge.

Rules carried over from `~/src/skills/.../registry-discovery.md`, each earned:

- **A missing index file is a pull failure, not an empty tenant.** Treating one as the other
  turns a precondition error into a confident false negative.
- **The cache never refreshes itself** — the same trap as `uip maestro flow registry`, which
  has already produced a wrong diagnosis in this repo (a "registry vs corpus era conflict"
  that was one three-day-old cache).
- **Read the index files directly.** `uip maestro case registry search` returns empty for
  types that are present in the cache.

**Phase 1 exit criterion:** every member you intend to generate is `confirmed` with a
recorded verdict, or consciously deferred.

---

## Phase 2 — INTERVIEW for what no artifact can answer

Only intent, policy, scope and roadmap. **Never interview for something probeable** — a
human recalling platform behaviour produced this repo's two worst wrong answers, both
confident, both agreed with by a second party, both false.

`semantics-gaps.mjs` generates the questions and only generates ones that qualify; each
states *why a human* and *what it changes*. Standing examples: is the V20 pin deliberate
or inertia; are any schema task types intentionally not authorable (editor-internal)
rather than gaps.

```bash
node scripts/semantics-update.mjs --interview version-pin-intent --answer "…" --who <person>
```

Recorded as **`asserted`**, never `confirmed`; `--who` is mandatory. Answering a
`knownUnknown` attaches context but **leaves it open** — a human answer is not a
settlement. **Never invent an attribution.**

Ask a question whose answer doesn't change the work and you have wasted the one channel
that costs someone else time. Batch them; don't drip-feed.

**Phase 2 exit criterion:** no blocking question remains unanswered, and every answer is
attributed.

---

## Phase 3 — WRITE the builder (you write it; the script writes the facts)

**You are the author. The scripts are the substrate.** Template codegen can emit closed
unions and constant tables; it cannot write an ergonomic fluent API that matches the
conventions of the surrounding code. That part is yours. What is NOT yours is inventing
facts — every method you write must trace to a `confirmed` entry in semantics.

### 3a. Emit the facts-as-code (deterministic, reproducible, diffable)

```bash
node .claude/skills/uipath-sdk-codegen/scripts/emit-sdk.mjs --version V13 --pin V12
```

Produces, per schema version: `unions.ts`, `task-kinds.ts` (data shapes + defaults),
`placement.ts` (the checker's ILLEGAL table, built from probe verdicts), `task-methods.ts`
(the interface you must satisfy), `meta.json` (provenance + what was skipped and why),
and the version router.

**`task-methods.ts` is a contract, not a suggestion.** It declares one method per
probe-confirmed task type. Have `TaskBuilder` implement `GeneratedTaskMethods` and the
compiler refuses to build until every confirmed kind exists. That is coverage-by-
construction enforced by `tsc` rather than by an audit script anyone can ignore.

### 3b. Read before you write

Never author against the schema alone. Read, in this order:

1. `meta.json` — what was emitted, what was skipped, and the version pin.
2. The **existing** builder (`case-sdk.ts`) — naming, option-object shape, how `.process()`
   / `.agent()` / `.connector()` are written. **Match the neighbours.** A generated method
   that reads differently from its siblings is a defect even if it compiles.
3. `serialize.ts` — every new task kind needs an arm in `taskData()`. A builder method
   with no serializer arm compiles and emits nothing.
4. The semantics entry for each kind — `doc`, `defaults`, `reuse`, `guidance`. These
   become the JSDoc, which reaches the authoring agent through `SKILL-case.md`.

### 3c. Write

For each confirmed task kind: the `TaskKind` union member, the builder method, the
serializer arm, and JSDoc carrying the non-obvious facts. Then wire `placement.ts` into
`check.ts` so the ILLEGAL table stops being hand-maintained.

**The rule that governs the rest: make illegal states unrepresentable.**

A constraint belongs as far up the stack as the evidence allows. Production → runtime
check → build-time check → **the type system**. Each rung converts a *detected* failure
into an *impossible* one, and only the top rung costs the author nothing: no error to
read, no doc to consult, no turn spent recovering. Turns are what we pay in.

So when you have a confirmed constraint, ask in this order:

1. **Can the wrong call be unwritable?** A closed union, a narrowed parameter type, a
   method absent from the slot's interface. Prefer this always.
2. **If not, can `tsc` refuse to build?** An emitted `interface` the builder must
   `implement` beats an audit script, because a compile error cannot be skipped and a
   script can.
3. **Only if neither: a table the checker reads.** This is the consolation prize. Write it,
   and note what it would take to promote it to rung 1 or 2.

Concretely: `UNREACHABLE_PLACEMENTS` is rung 3 today. Rung 1 is `.onStageExit()` not
*accepting* a `caseEntered(...)` rule at all. If you are wiring placement and the grammar
lets you make the slot types distinct, do that instead of adding to the table.

**The counter-rule, which matters just as much:** only encode what has been *earned*. A
guess promoted into a type is unfalsifiable by the author — strictly worse than a warning,
because they cannot even discover it is wrong. Grade first, then choose the rung. And stop
at the authoring boundary: no type prevents an SLA from breaching, so behavioural facts
stay observations, never invariants.

**Hard rules.**

- **No fact that is not in semantics.** If you need a default, a shape, or a legality that
  isn't recorded `confirmed`, stop and go back to phase 1 and probe it. Do not infer it
  from a sibling, from the docs, or from what would be reasonable.
- **Reuse before inventing.** `bindings` already resolves through the mechanism
  `.connector()` uses. A second mechanism for the same job is a bug.
- **Prefer explicit over default.** Where a converter fallback exists but the designer's
  intent may differ (`external-workflow`: fallback sync, intent reportedly async), emit
  the field explicitly rather than relying on the fallback.
- **Every method carries JSDoc.** A method without it is a silent regression in the skill
  doc, which is the whole leverage.
- **Do not widen a union to make something pass.** If `uip` rejects it, the generator is
  right and the test is wrong.

### 3d. Pop to a human — only for these

Ask when the answer cannot be obtained by probing or by reading the existing code. Batch
the questions; do not drip-feed. Everything else, decide and note the decision.

| Trigger | Why it is not yours |
| --- | --- |
| A needed fact is `unknown`, or only `asserted` | Promoting it requires evidence you cannot produce offline |
| Two `confirmed` facts conflict | Something changed; a human must say which era we target |
| A naming/ergonomics choice with **no precedent** in the existing builder | Public API surface — someone owns that |
| The change would break existing public API | Not a generation decision |
| Scope: is this type meant to be authorable at all? | Product intent; the schema cannot say |

**Not triggers:** anything probeable (probe it), anything with a precedent (follow it),
anything the semantics file already records (use it).

### 3e. Verify before claiming done

```bash
cd typescript/sdk && npm run build && node scripts/gen-case-skill.mjs --check
node scripts/emit-sdk.mjs --check          # generated facts are not stale
node scripts/audit-schema-coverage.mjs
cd ../ && npx vitest run tests/case-*.test.ts tests/sdk-codegen.test.ts
```

Then author a real case using each new method and round-trip it through `./compile.sh`.
**Generation that compiles but does not validate is not done.** Where the schema accepts
something meaningless, note that acceptance is not execution — nothing below runtime
inspects placement.

- [ ] `TaskBuilder implements GeneratedTaskMethods` — compiler enforces coverage.
- [ ] Every new kind has a serializer arm, not just a builder method.
- [ ] Every method's JSDoc states the default and where it came from.
- [ ] `check.ts` reads `placement.ts`; no hand-maintained ILLEGAL table remains.
- [ ] An authored case per new kind round-trips to `Status: Valid`.
- [ ] Anything you had to assume is recorded in semantics with its grade, not left in a
      commit message.

---

## Reference

| file | read it when |
| --- | --- |
| `references/sources.md` | **always first** — six-rank trust hierarchy, version lag, traps |
| `references/acquire.md` | phase 1d/2 — probe → docs → interview, CLI-history mining |
| `references/verify.md` | phase 1d — the probe recipe and the failed-guess trap |
| `references/generate.md` | phase 3 — JSDoc, generate-vs-hand-write, router shape |

| script | phase | does |
| --- | --- | --- |
| `extract-schema.mjs` | 1b | enumerate unions per schema version from the validating bundle |
| `mine-history.mjs` | 1c | CLI vocabulary at any ref + dated introductions |
| `semantics-gaps.mjs` | 1d | drift, unprobed cells, human-only questions |
| `run-probes.mjs` | 1d | probe the grid against `uip`, classify, `--apply` to record |
| `semantics-update.mjs` | 1d/2 | record a probe verdict or an attributed answer |
| `emit-sdk.mjs` | 3 | emit unions + task kinds + router; `--check` gates staleness |

`semantics/case-semantics.json` is the single source the emitter, the doc generator and
`check.ts` all read. Before it existed each restated the others in prose, and they
drifted apart three separate times.
