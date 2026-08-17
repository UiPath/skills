# `uip maestro case validate` — verified failures and invisible defects

Single source for validate behavior claims. Message-quoted, version-anchored — the SDK path
(`@uipath/case-schema`) surfaces MESSAGES, not `CASE_MGMT_*` codes; never cite bare codes as validate
behavior. All rows verified on uip 1.198.0-preview.102 (2026-07-31 / 2026-08-17 probes;
`docs/case-knowledge-ledger.md`).

**[K-ERR-1] Verified failure messages → cause → fix**

| Message (as emitted) | Cause | Fix |
|---|---|---|
| `Variable 'vars.X' does not exist` | Reference to an undeclared name: partial output entry (K-VAR-4), trigger output without root companion (K-VAR-3), or typo | Emit the full bare-mint output shape; add the §1.5/root companion for trigger fields; fix the reference |
| `SLA name is missing` | SlaRuleEntry without `displayName` | K-SLA-2 — id + displayName on every entry |
| `Invalid input: expected string, received undefined` at `…slaRules.N.id` | SlaRuleEntry without `id` | Same |
| `One of your stage SLAs has a validation error` | Out-of-range duration (e.g. `min` < 15 or > 1000), or other entry-level violation | K-SLA-2 bounds; never silently clamp (K-NAME-5) |
| `Stage exit rule '<name>' has no task(s) marked as required` | `required-tasks-completed` over a stage with zero `isRequired: true` tasks | K-PAIR-5 — mark the real completer required |
| `Case rule '<name>' has no required stage(s) selected` | `required-stages-completed` with no `isRequired: true` primary stage (absent ≡ false) | K-PAIR-5 — explicit `isRequired: true` on required stages |
| `The escalation referenced by rule … no longer exists` | At-risk rule borrowing another SLA's escalation, or the `any` sentinel | K-SLA-3 — same-SLA at-risk escalation, or drop `escalationId` for breach |
| `The SLA referenced by rule … no longer exists` | Dangling `slaId` | Reference an SLA declared on the row's target |
| `Case has no completion rules` | No `caseExitRules[]` entry with `marksCaseComplete: true` | K-PAIR-6 |
| `connector activity missing` | Bare `wait-for-connector` rule without `uipath` + `context` | Splice the `case spec` scaffold; stub placeholders keep an empty-outputs `uipath` block |

**[K-ERR-2] Defects validate CANNOT see** — green run, broken case; all on the author:

1. A task with no entry condition never starts (`entryConditions: []` and absent key both pass — K-SEQ-5).
2. `start-task` authored as a stage-entry row re-runs every `shouldRunOnlyOnce: false` task on re-entry (K-SLA-5).
3. A breach rule "completed" with an escalation becomes an at-risk rule — behavior change, still green (K-SLA-3).
4. A non-interrupting lane promoted to a regular stage silently joins the completion contract (K-STG-3).
5. An envelope field nested inside `data` (e.g. `skipCondition`) passes and is dead config.
6. Two secondary stages with identical entry rules pass (probe p07b) — ambiguous routing stays a design defect (K-STG-6).
7. A connector rule's `context` internals are unchecked beyond `connectorKey` + `operation` presence — a wrong `serviceType` passes; Studio Web is the real connector judge.

**[K-ERR-3] Validate cadence.** Intermediate authoring states are expected-invalid: run validate once at
the end of prototyping (informational) and once at the validation phase (authoritative); every retry must
be preceded by a fix edit — validate → validate with no intervening edit is a defect. `--skeleton` runs
structural checks only (`--skeleton-v2` does not exist as of 1.198.0-preview.102).

<!-- END: validate-codes.md -->
