# Case Authoring Principles

Cross-activity rules for authoring a Case Management SDD. Model semantics: [model.md](model.md).
Data flow: [variables.md](variables.md). SLAs: [slas.md](slas.md). Confirmation + pre-render checks:
[review.md](review.md). Conversation flow: [case-design-lane-guide.md](../case-design-lane-guide.md).

## Inputs

| Input | Purpose |
|---|---|
| User chat messages | Primary source — verbatim values, types, exits, SLAs |
| User-supplied docs (paths, paste, attachments) | Secondary — read on Listen, parsed for case shape |
| [case-sdd-template.md](../../assets/templates/case-sdd-template.md) | Structural mold for the rendered `sdd.md` |
| Tenant registry cache (`~/.uip/case-resources/`) | Resolves deployed processes / agents / actions / connectors — [grounding.md](grounding.md) |
| Tenant IS cache (`~/.uipath/cache/integrationservice/`) | Resolves connector identity, connections, activities, triggers |

## Content authority hierarchy

When signals conflict, the highest tier wins:

1. **Platform schema constraints** — schema-invalid values never ship, regardless of source. Examples: a task `type` outside the closed enum, an illegal WHEN ↔ Marks-Complete pair ([model.md § Lifecycle gates](model.md#lifecycle-gates)).
2. **Regulatory / compliance constraint** stated or implied (ECOA, NCQA, GDPR, HIPAA, SOC 2, FCRA, FINRA, …) — forces task types ([authoring.md § Task-type override priority](authoring.md#task-type-override-priority)).
3. **Tenant evidence** — a deployed resource in the registry cache matching described work. Prefer its type and identity; never add stages/tasks or rename business work to match tenant inventory.
4. **User-stated preference** in chat (verbatim "set the task to agent").
5. **Doc-extracted values** from user-shared documents.
6. **Inferred defaults** per the assumption playbook ([case-design-lane-guide.md § Sketch](../case-design-lane-guide.md#sketch--best-assumption-every-field)).
7. **General-practice fallback.**

Apply a higher-tier override AND surface it in the confirmation's `Decisions I Made` table with
provenance `(source: <tier>-override)`.

## Render policy

**Template shape is part of the contract.** A valid in-memory model is not enough: the rendered `sdd.md`
preserves the full template structure ([render-case-definition.md](render-case-definition.md),
[render-stages-tasks.md](render-stages-tasks.md)). A prose summary is never an SDD; the compact
confirmation is never an SDD substitute.

- **Allowed `—`** (user left it untouched; the build defaults safely): case-level Description, variable defaults, persona scope notes, app-view detail, secondary-stage description, optional `IF` expressions, business calendars on timers.
- **Allowed `<UNRESOLVED>`** (a later run resolves): registry identity ids (`taskTypeId`, `connectionId`, `actionAppId`, `agentId`, `processOrchestrationId`) when resolution was skipped, deferred at the gate, or returned zero matches. Pair every `<UNRESOLVED>` with a review item.
- **Banned on required cells** (the render rules name them): populate concretely, keep only the identity `<UNRESOLVED>` (the build emits a placeholder), or ask the user.
- **Forbidden SDD-body vocabulary.** Narrative cells (descriptions, rationales, notes) never carry skill-internal terms: `Pattern C`, `bridge`, `companion`, `inputOutputs[]`, `=jsonString:` (outside connector `Operation Configuration` cells), `groupOperator`, `essentialConfiguration` (as prose), `savedFilterTrees`, `dispatcher`, `io-binding`, `aliased into/from`, `reassign`, `originalVar`, `auto-mint`. These belong in skill references, never in `sdd.md`.

## Domain fidelity

The skill transcribes business terms; it never paraphrases them.

**Preserve verbatim** (no synonym swaps):

- Customer-named roles (`CFO`, `Underwriter II`, `Triage Nurse`) — never substitute `Approver`/`Reviewer`/`Manager`.
- Customer-named domain nouns (`Vendor`, `Claim`, `Loan File`, `Member`) — never homogenize to `Record`/`Item`.
- Customer-named stage labels (`Triage`, `Adverse Action Notice`) — user's casing and word choice.
- Customer-named decision outcomes (`Approve` / `Decline` / `Needs Info` — not `Reject`/`Pending`).
- Customer-named integration shortnames (`Workday`, never "the HR system").

**Allowed mechanical normalization** (ledger reason `mechanical:<derivation>`): PascalCase Case Name from
a spaced phrase, 2–4 char UPPER identifier prefix, camelCase variable names.

**Anti-paraphrase rule:** when the user said `the senior underwriter signs off`, write exactly that —
never `the manager approves the request`. Synonyms are a fidelity defect, not polish. A term the user
wrote once is captured with provenance `verbatim:"<quote>"`; the confirmation's tables render it exactly,
and that display is the spelling check.

## Source ledger (provenance)

Two surfaces: inline italic attribution in `sdd.md` (`Manual _(source: user-stated)_`; omit for
`user-stated`) and the confirmation's `Decisions I Made` table.

**Rationale is durable, not chat-only.** Provenance says where a value came from; rationale says why the
choice fits. Persist rationale in each stage/task `Design Rationale` field and each SLA rationale field —
the downstream build copies it into its plan entries so implementers can review choices without the
original conversation.

| Kind | When |
|---|---|
| `user-stated` | User wrote the value in chat (no annotation needed). Paraphrase acceptable. |
| `verbatim:"<quote>"` | Rendered cell is exactly the user's phrase — strongest signal; preferred for customer-named entities. Truncate the quote at 40 chars in the ledger. |
| `user-doc:<filename>` | Lifted from a user-shared document |
| `mechanical:<derivation>` | One-step derivation (`mechanical:PascalCase→prefix`) |
| `compliance-override:<rule>` | Regulatory constraint forced the value (`compliance-override:ECOA→action`) |
| `tenant-registry:<resource-name>` | Resolved from the registry cache |
| `connector-priority:<connector>` | Tier 3/tenant evidence selected `execute-connector-activity` over `api-workflow` |
| `inferred-default:<reason>` | Defaulted with no matching source (use sparingly) |

A non-`user-stated`, non-`verbatim` field without provenance blocks the confirmation until annotated.

## Review items

Structured gap escalations, emitted whenever a field could not be fully resolved but the downstream build
needs the context. They live in the in-memory model and surface ONLY as `Review Flags` rows in the
confirmation — never in the `sdd.md` body. The build persists them under the matching task's
`review_items[]` in its resolution audit file.

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
| **high** | Blocks the downstream build until resolved | Missing `connectionId` / `actionAppId` / deployed runnable; a resolved resource's required input unbound (`rev_unbound_input_<task>_<field>`); an extract naming a field the resource never emits (`rev_phantom_output_<task>_<field>`); open variable lineage; missing trigger config; unreconciled compliance override |
| **medium** | Build defaults with a prompt | Missing escalation recipient (default = owner group); missing variable default; ambiguous recipient |
| **low** | Cosmetic | Missing case description; missing secondary-stage description; stylistic placeholder |

**Gate behavior:** any open `high` item relabels the confirmation's Build option
`Build despite N flagged items` — the user must pick it; silently building past `high` is forbidden.
`medium`/`low` surface as advisory rows, no acknowledgment needed. Never downgrade a severity to pass the
gate — it moves only when the underlying issue actually resolves.
