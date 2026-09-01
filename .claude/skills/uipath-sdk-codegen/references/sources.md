# Sources of truth — read this before generating anything

Six sources describe "what the platform accepts". They **disagree with each other right
now**, and each moves independently. Every wrong gap number produced in this repo came
from reading a convenient source instead of an authoritative one — most recently by
auditing against a copy of `@uipath/case-schema` that `uip` never loads.

## Trust hierarchy

`uip maestro case validate` does **not** load the `@uipath/case-schema` your repo
installed. It runs two things: the CLI's own `case-tool` checks, and a case-schema
copy **bundled inside `@uipath/maestro-tool`'s `dist/tool.js`** (37 MB). That bundled
copy is far newer than what a downstream repo pulls.

| rank | source | where | trust |
| --- | --- | --- | --- |
| 1 | **`uip maestro case validate`** | run it, read the verdict | **authoritative** |
| 2 | **maestro-tool's bundled schema** | `~/.bun/.../@uipath/maestro-tool/dist/tool.js` | what rank 1 executes — enumerable |
| 3 | **CLI `case-tool` source** | `~/src/cli/packages/case-tool/src/services/case-validate-service.ts` | the CLI-layer vocabulary (`VALID_*` sets), readable + git-historied |
| 4 | **mainline zod** | `~/src/PO.Frontend/src/types/case-mgmt-zod/**` | **preview** — read it always; label it; never emit it |
| 5 | **repo `@uipath/case-schema`** | `typescript/node_modules/**` | **downstream; lags badly** |
| 6 | **published `.d.ts`** | `dist/index.d.ts` | **do not use** |

## The OTHER axis: behaviour

The table above answers "will this be accepted?". It cannot answer "what will it then do?",
and treating it as if it can is how this program twice reported a capability absent that the
platform in fact specifies. Behaviour has its own hierarchy and its own sources.

| rank | source | where | trust |
| --- | --- | --- | --- |
| 0 | **a running instance** | `uip maestro case debug` → Completed | **terminal** |
| 1 | **behaviour fixtures** | `~/src/dmnscheduler/test-cases/<NN>/` | **input event + the exact required output**, with negative cases |
| 1b | unit tests | `~/src/dmnscheduler/{Scheduler,DmnExecutor}.Tests/` | executable assertions about the evaluators |
| 2 | evaluator source + slot schema | `~/src/dmnscheduler/Scheduler/Evaluators/`, `schemas/CaseDeterministicRules.schema.json` | the code that decides |
| 3 | PIMS | `~/src/PO.BpmnEngine/src/Pims/**` | **storage and read only** — rules are opaque strings there |
| 4 | inference from shape | — | guessing |

A fixture is a triple: `case-deterministic-rules.json` + `<NN>-input.json` +
`<NN>-output.json`. It states what the scheduler is *required to decide*, which no schema and
no probe can tell you. `07-sla-direct-task-trigger` specifies that a task with an
`SlaStatusChange` entry condition runs **even when its stage was never entered** — and pairs
it with a negative case proving the rule is selective. That single file answers a question
this program had previously answered wrongly, then under-confidently.

## Consult fastest-first — which is also most-scriptable-first

The expensive mistake is not using a bad source. It is using a good source *late*, after
spending turns on a slower one. Cost and automatability are the same axis here — the fastest
sources are the ones a script can run every time, the slowest need a person:

1. **Fixtures** (`dmnscheduler/test-cases/`) — grep the rule names first; they read as
   specifications (`"Run when Review SLA breaches, even if Watcher not entered"`). Minutes.
2. **The published grid** (`@uipath/scheduler-types`) — machine-readable, pinned, no probing.
3. **Evaluator source** — when no fixture covers the case.
4. **Probe `uip`** — for SHAPE questions the above cannot answer. Probing is the slowest of
   these and answers the narrowest question, so it is fourth, not first.
5. **Ask a human** — only for intent, policy or roadmap.

This session ran that list almost exactly backwards: probing first, fixtures last, having
already cited the fixtures directory as rank 1 hours earlier. Nothing about the individual
steps was wrong; the ORDER cost most of a day.

### Re-measured 2026-09-01 — the gap is unchanged, the labels are not

| | task types | rules | authority version |
| --- | --- | --- | --- |
| maestro-tool (validates) | **14** (V13) | **15** | 1.198.0 — unmoved |
| mainline PO.Frontend | 14 (to V31) | 16 (`api-event` PREVIEW) | 0.1049.0 |
| repo case-schema (audited) | 11 | 14 | 0.859.0 — unmoved |

The evidence did not move in four weeks; only `uip --version` did. Note also that
**three** copies of `@uipath/case-schema` are installed on this machine, and
nearest-`node_modules` resolution silently picks between them:

    0.859.0    flow-builder-sdk/typescript/node_modules      what vitest audits against
    0.1016.2   ~/src/cli/.../packager-tool-case/node_modules  nested; what packaging resolves
    0.1052.3   ~/src/cli/node_modules                         CLI dev-checkout root

None of these is the authority — `uip maestro case validate` reads neither, it reads the
bundle inside `maestro-tool`. Pin which copy a check loads or the check is unattributable.

### Measured gap between rank 2 and rank 5 (2026-08-06)

| | task types | rules | `sla-status-change` |
| --- | --- | --- | --- |
| maestro-tool 1.198.0 (validates) | **14** | **15** | yes |
| repo case-schema 0.859.0 (audited) | 11 | 14 | no |

Auditing against rank 5 under-reports by three task types — `document-extraction`,
`flow-process`, `function` — and makes shipped features look "mainline-only". Every
*the CLI accepts it but the published package rejects it* puzzle was two different copies of
the same package being compared.

**Versions do not agree with each other, either.** `uip --version` reports **1.202.0**
while the maestro-tool performing case validation is **1.198.0** (2026-09-01). The launcher
and the validating tool version independently — record both.

The gap is widening, which is the point: on 2026-08-06 it was 1.200.0/1.198.0, two
versions. Four weeks later the launcher had moved four more and the validator none. A
launcher version is therefore not even a weak proxy for what validates.

### Rank 3 is under-used and it is cheap

`case-validate-service.ts` holds `VALID_RULE_TYPES`, `VALID_TASK_TYPES`,
`VALID_EXIT_CONDITION_TYPES`, `VALID_SLA_UNITS`, `VALID_ESCALATION_TRIGGER_TYPES`,
`VALID_TRIGGER_SERVICE_TYPES` as plain `Set`s. Reading it corroborated three unions
the header got wrong and corrected a classification probing alone had produced:
`timer`/`condition`/`stage-complete` return `Invalid input` at task entry but ARE in
`VALID_RULE_TYPES`, so they are `illegal-in-slot`, not unknown rules.

It is also **git-historied**, which probing is not — `git log -S` dates every
vocabulary change (e.g. `refactor(case-tool): migrate case schema from V19 to V20`).

### Why rank 6 is disqualified

Its build step is literally `cp packages/converter/src/index.d.ts packages/converter/dist/`.
Hand-maintained, pinned to an older schema version. **Three of three unions checked were
wrong in it, every time understating the platform:**

| union | header says | reality |
| --- | --- | --- |
| `CaseManagementNodeTaskType` | 10 members | validator accepts **14** |
| `SlaRule.unit` | `h｜d｜w｜m` | `min｜h｜d｜w｜m` (CLI `VALID_SLA_UNITS` agrees) |
| `CaseManagementNodeExitRuleType` | omits `exit-only`; lists `terminal`, `send-to-stage` | `exit-only` **Valid**; the other two **Invalid** (CLI `VALID_EXIT_CONDITION_TYPES` agrees) |

In all three the **builder was right and the header was wrong**.

### Why rank 5's zod is not sufficient either

`validateCaseDiskJsonSchema` is a real validator — it rejects a missing `version`, a
bogus `node.type`, a missing node id. But it is **lenient on nested enums**: for
`slaRules[].unit` it accepts `"zzz"`, `""`, `null`, and `42`.

So: enumerate from rank 2, corroborate with rank 3, decide with rank 1 — and **always read
rank 4**, labelling what it adds as PREVIEW.

### Rank 4 is an input, not a curiosity

`extract-schema` auto-detects a sibling `PO.Frontend` clone and diffs it against the
validating bundle. Members present only in mainline are **preview**: real, scheduled, and
never emitted — a type the installed converter rejects produces invalid caseplans.

Reading it is not optional, because the alternative is worse than ignorance. Three
capabilities were filed as "not shipped" purely because the comparison was against a
downstream package rather than the validator; knowing what is in flight is what stops a
scheduled feature being recorded as a permanent CAPABILITY limit. Preview members belong
in `meta.json` and in the gap report, never in generated code.

As of 2026-08-07 the preview delta is **empty** — mainline and the validating bundle both
carry 14 task types and 15 rules. That is the expected steady state; a non-empty delta
means something is in flight, which is exactly what you want to see coming.

## Version lag — the axis that makes all of this necessary

Four version numbers move independently:

| thing | where | observed |
| --- | --- | --- |
| CLI launcher | `uip --version` | 1.198.0 → 1.200.0 in one session → **1.202.0** by 2026-09-01 |
| **validating tool** | `@uipath/maestro-tool` `package.json` | **1.198.0** — *behind the launcher* |
| schema the validator bundles | `…SchemaV<n>` in `maestro-tool/dist/tool.js` | **14 task types, 15 rules** |
| downstream package | repo `@uipath/case-schema` | 0.859.0 — 11 types, 14 rules |
| schema **we emit** | `case-sdk.ts` `_version` | **V20** |
| mainline schema | `PO.Frontend` root zod file | **V31** @ 0b11f5660 (2026-09-01) |

Six numbers, no two of which are guaranteed to agree. Pin all of them or the output is
unreviewable.

Nothing breaks at V20 because the converter **forward-migrates on ingest** — which is
precisely why seven versions of lag went unnoticed. Consequences:

- A capability that arrived after V20 will look like a platform limit if you test only
  V20 output. Check the version before classifying anything as impossible.
- Re-pinning `_version` is not a one-line change. **V27 makes escalation `displayName`
  required** (v26→v27 back-fills unnamed ones); our serializer does not emit it, so
  bumping without adding it produces invalid documents.

## Recorded traps

**Version suffixes on zod schemas are counterintuitive.** In
`CaseManagementJsonEscalationsSchema.ts`, `…ActionNotificationSchemaV0` carries the WIDE
enum `["notification","email","slack","teams","process"]` and `…SchemaV1` carries the
NARROW `["notification"]`. V0 is the **oldest**; the enum was *narrowed* at V1 and is
still narrow at V27. Reading the wide enum and concluding "the platform supports
slack/process escalations" is exactly backwards. **Always resolve which schema version a
declaration belongs to before believing it.**

**A schema type is not a capability.** zod accepting `type: "external-workflow"` proves
the *converter* accepts the shape. It does not prove the runtime executes it. Say
"validator-accepted", not "supported", unless a live run proved otherwise.

**Escalations notify; they do not create work — but that is not the whole story.**
`EscalationRuleAction.type` is `notification`-only (V1→V27, stable). It is tempting to
conclude "a deadline breach cannot start work". **Wrong.** The mechanism is a *rule*,
`sla-status-change`, which reacts to an `slaId`/`escalationId`. Two different objects;
reasoning about one told us nothing about the other.

**Not every union lives where you expect, and a rejection is not an absence.** The
header's `TransitionRuleType` (`condition｜stage-complete｜wait-for-connector｜timer`) is a
*different concept* from case entry/exit rules. Those three return `Invalid input` at
task entry, which reads like "unknown rule" — but the CLI's own `VALID_RULE_TYPES`
contains all three, so they are recognised rules rejected by the task-entry union. That
correction came from reading rank 3 (CLI source); probing alone had mis-classified them.

**Rule legality is slot-dependent and no type expresses it.** The same rule can be legal
at task entry and illegal at stage entry (`selected-tasks-completed` → "task selection
missing"). Placement is only knowable by probing `uip` per (rule, slot) cell.

## Confirmed CAPABILITY gaps (no schema version fixes these)

Verified against mainline V27, so they are not version lag — but mainline reached **V31**
on 2026-09-01, so each of these is a verdict trailing four schema versions. Re-verify
before citing as a current limit:

- **No business-day SLA unit.** `z.enum(["min","h","d","w","m"])` at V27. A "5 business
  days" requirement cannot be expressed exactly. Do **not** compute a calendar
  conversion — it depends on start weekday, holidays and region, and nothing in the
  toolchain catches it being wrong.
- **Escalation recipients are static literals.** No `=js:vars.*` binding, so "notify the
  requester" (a per-case address) is unreachable.
- **Escalation carries no message body.** `notify` targets only; no templating.
