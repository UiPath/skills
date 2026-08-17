# Case authoring core — inputs, authority, provenance, review items

Cross-activity rules for authoring a case SDD. Shared facts/semantics live in
[case-knowledge/](../case-knowledge/INDEX.md) — cited by `K-*` ID, never restated here.

> **Phase legend.** Phase 0 = this design lane. Phase 1 = the build skill's planning pass (verify-only
> when this lane already resolved resources). Phase 2/3 = its prototyping/implementation passes. Checks
> marked "enforced at build" run in `uipath-maestro-case`.

## Inputs

| Input | Purpose |
|---|---|
| User chat messages | Primary source — verbatim values, types, exits, SLAs |
| User-supplied docs (paths, paste, attachments) | Secondary — read on Listen, parsed for case shape |
| [`case-sdd-template.md`](../../assets/templates/case-sdd-template.md) | Structural mold for the rendered `sdd.md` |
| Platform case schema constraints | The design-relevant subset lives in [case-knowledge/facts/](../case-knowledge/INDEX.md) |
| Tenant registry cache map ([case-design-lane-guide.md § Tenant grounding](../case-design-lane-guide.md#tenant-grounding--full-resolution-at-design-time)) | Which `~/.uip/case-resources/` index answers each resource type |
| Tenant registry (`~/.uip/case-resources/`) | Resolves deployed processes / agents / actions / connectors |
| Tenant IS cache (`~/.uipath/cache/integrationservice/`) | Resolves connector identity, connections, activities, triggers |

Platform schema is truth: choices conflicting with it are schema-invalid regardless of source.

## Content authority hierarchy

When signals conflict, top wins:

1. **Platform schema constraints** — schema-invalid values never ship. Examples: task `type` outside the enum (K-TYP-1); `Marks Stage Complete: Yes` + `selected-tasks-completed` (K-PAIR-2).
2. **Regulatory / compliance constraint** stated or implied (ECOA, NCQA, GDPR, HIPAA, SOC 2, FCRA, FINRA, …). Forces types — [task-typing.md § Override priority](task-typing.md#task-type-override-priority).
3. **Tenant evidence** from the registry cache — a deployed resource matching described work. Prefer its type/identity; never add stages/tasks or rename business work to match tenant inventory.
4. **User-stated preference** in chat (verbatim "set the task to agent").
5. **Doc-extracted values** from user-shared docs.
6. **Inferred defaults** per the assumption playbook ([case-design-lane-guide.md § Sketch](../case-design-lane-guide.md#sketch--best-assumption-every-field)).
7. **General-practice fallback.**

A higher tier overriding a lower one is applied AND surfaced in the confirmation's `Decisions I Made`
table with provenance `(source: <higher-tier>-override)`.

## Render policy — `—`, `<UNRESOLVED>`, banned

- **Template shape is part of the render contract.** A valid model is not enough if the file collapses
  into a prose summary — the rendered `sdd.md` preserves the full template structure (K-SDD-1, K-SDD-2);
  the compact Phase 0 confirmation is never an SDD substitute.
- **Allowed `—`** (untouched by the user, Phase 1 defaults safely): case-level Description, variable
  defaults, persona scope notes, app-view detail, secondary-stage description, optional `IF`
  conditionExpressions, business calendars on timers.
- **Allowed `<UNRESOLVED>`** (gaps Phase 1 / post-build resolves): registry IDs (`taskTypeId`,
  `connectionId`, `actionAppId`, `agentId`, `processOrchestrationId`) when resolution was skipped,
  deferred at the gate, or returned 0 matches. Pair EVERY `<UNRESOLVED>` with a review item.
- **Banned** on every required cell named in the render rules: populate concretely, keep the identity
  `<UNRESOLVED>` (build emits a placeholder), or Ask.
- **Forbidden SDD-body vocabulary.** No narrative cell may contain skill-internal terms: `Pattern C`,
  `bridge`, `companion`, `inputOutputs[]`, `=jsonString:` (outside connector `Operation Configuration`
  cells), `groupOperator`, `essentialConfiguration` (as prose), `savedFilterTrees`, `dispatcher`,
  `Phase 2 validator`, `Phase 3 dispatcher`, `Finding #N`, `io-binding`, `aliased into/from`, `reassign`,
  `originalVar`, `auto-mint`. These live in skill references, never in `sdd.md`.

## Domain fidelity

Narrative cells (descriptions, persona/stage/task names, button labels, §3/§4 prose) preserve the user's
domain vocabulary verbatim — this skill transcribes business terms, never paraphrases.

**Preserve verbatim** (no synonym swaps, ever):

- Customer-named roles (`CFO`, `Underwriter II`, `Triage Nurse`) — never `Approver`/`Reviewer`/`Manager` substitutes.
- Customer-named domain nouns (`Vendor`, `Claim`, `Loan File`, `Member`) — never homogenized to `Record`/`Item`.
- Customer-named stage labels (`Triage`, `Adverse Action Notice`) — user's casing and word choice.
- Customer-named decision outcomes (`Approve` / `Decline` / `Needs Info` — not `Reject`/`Pending`).
- Customer-named integration shortnames (`Workday`, never "the HR system").

**Allowed normalization** (mechanical, ledger reason `mechanical:<derivation>`): PascalCase Case Name,
2–4 char identifier prefix, camelCase variable names (K-NAME-4).

**Detection:** a term the user wrote once surfaces in the ledger as `verbatim:"<quote>"`; the
confirmation's tables render it verbatim — that display is the spelling check. **Anti-paraphrase rule:**
when the urge strikes to write `the manager approves the request` and the user said `the senior
underwriter signs off`, use the user's phrase. Synonyms are a fidelity bug, not polish.

## Source ledger (provenance)

Two surfaces: inline in `sdd.md` (italic attribution — `Manual _(source: user-stated)_`; omit for
`user-stated`) and the confirmation's `Decisions I Made` table.

**Rationale is durable, not chat-only.** Provenance says where a value came from; rationale says why the
choice fits. Persist rationale in each stage/task `Design Rationale` field and each SLA rationale field —
Phase 1 copies it to the matching `tasks.md` T-entries so implementers can review without the original
conversation.

| Kind | When |
|---|---|
| `user-stated` | User wrote the value in chat (no annotation). Paraphrase acceptable. |
| `verbatim:"<quote>"` | Rendered cell is exactly the user's phrase — strongest signal; preferred for customer-named entities. Quote truncated at 40 chars in the ledger. |
| `user-doc:<filename>` | Lifted from a user-shared doc |
| `mechanical:<derivation>` | One-step derivation (`mechanical:PascalCase→prefix`) |
| `compliance-override:<rule>` | Regulatory constraint forced the value (`compliance-override:ECOA→action`) |
| `tenant-registry:<resource-name>` | Resolved from the registry cache |
| `connector-priority:<connector>` | Tier 4 selected `execute-connector-activity` over `api-workflow` |
| `inferred-default:<reason>` | Defaulted with no matching source (sparingly) |

A non-`user-stated`, non-`verbatim` field without provenance is a validation error — Approve blocks until
annotated.

## Review items

Structured gap escalations: emitted whenever a field could not be fully resolved but the build's planning
pass needs the context. They live in the in-memory model and surface ONLY as confirmation `Review Flags`
rows — never in the `sdd.md` body; the build's Phase 1 persists them into `tasks/registry-resolved.json`
under the task's `review_items[]` (K-LEDG-4).

```jsonc
{
  "id": "rev_<short-slug>",
  "target": "<sdd.md section path or task name>",
  "issue": "<one-sentence problem>",
  "severity": "high" | "medium" | "low",
  "next_step": "<what the user must do to resolve>"
}
```

| Level | Definition | Examples |
|---|---|---|
| **high** | Blocks Phase 1 / `caseplan.json` build until resolved | Missing `connectionId` / `actionAppId` / deployed runnable; a resolved resource's required input unbound (`rev_unbound_input_<task>_<field>`); an extract naming a field the resource never emits (`rev_phantom_output_<task>_<field>`); unresolved lineage; missing trigger config; unreconciled compliance override |
| **medium** | Phase 1 defaults with a prompt | Missing escalation recipient (default = owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | Missing case description; missing secondary-stage description; stylistic placeholder |

**Confirmation gate behavior:** any `high` items relabel the Build option `Build despite N flagged items`
— the user must pick it; silently building past `high` is forbidden. `medium`/`low` surface as advisory
rows, no acknowledgment. Never downgrade a `high` to pass the gate — severity moves only when the issue
actually resolves.

<!-- END: authoring-core.md -->
