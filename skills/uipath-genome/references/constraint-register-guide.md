# Constraint Register Guide — classifying what gets enforced, and where

Rules. Every SHACL shape, every rename and every applied default becomes a register
row. The register is the reviewable half of the data model: a reader scans it row by
row and sees what was decided, what was defaulted, and what was deliberately left
open.

Read whole when the inventory reports ≥1 shape. Router:
[data-model-guide.md](data-model-guide.md).

## Where non-determinism comes from

Four sources. Process context is only the last, and conflating them is what makes
the phase boundary hard to see.

| # | Source | Resolved by | Examples here |
|---|---|---|---|
| 1 | **Convention** | fixing a rule once, repo-wide | the naming algorithm; collision suffixes; which side a one-to-one picks |
| 2 | **Source metadata** | reading the inventory harder | `lengthLimit` from a mapped `VARCHAR(n)`; `decimalPrecision` from a column's scale |
| 3 | **Domain & governance** | a data owner, today, with no automation designed | system of record vs replica; `displayField`; `owl:oneOf` → choice set or lookup entity; tenant vs folder scope |
| 4 | **Process context** | the automation's design | `level`; `isRequired` under incremental writes; normalization; consolidation; federated views |

1 and 2 are only *apparently* non-deterministic — they resolve the moment a
convention is fixed or the input is read properly. **3 is a genuine judgement that is
not process-dependent**, which is why Author mode can close most of it with declared
defaults instead of deferring it.

**The phase test is "who can answer it?"**

| Answerable by | Phase |
|---|---|
| nobody — it is a convention | Author |
| the inventory already says | Author |
| a data owner, with no automation in sight | Author, via declared defaults + overrides |
| only the automation's design | Phase 2 |

Every row records which category it came from, in `source`. A row with
`source: process` and a non-null `level` is a defect — Author mode guessed.

## The three axes

One verdict is not enough. Three columns, decided at different times.

| Axis | Values | Decided |
|---|---|---|
| **`expressible`** — can a Data Fabric field option state this at all? | `yes` / `no` | **Author**, mechanically, from § The capability table |
| **`locus`** — who enforces it? | `uipath` / `external` / `none` | Author by default; Phase 2 on evidence |
| **`level`** — how? | `state` / `transition` / `monitor` / `assumed` | **Phase 2** |

`expressible: no` **forecloses `level: state`.** A constraint the platform cannot
hold at state level is enforced by an operation, surfaced, or trusted — never by the
schema. That single implication is what makes the axes mechanical rather than a
matter of taste.

`monitor` is the level most often wanted and most often missing from a two-value
vocabulary: **the platform checks the constraint and surfaces a violation, but does
not block.** It is distinct from `assumed`, where nothing checks at all. See
§ Surface, do not block.

## Systems of record and systems of engagement

The question "who enforces this?" has a standard answer shape. The upstream
application is the **system of record**; the automation platform sitting on its data
is a **system of engagement** (it drives work) or a **system of insight** (it
analyses). An ontology describes the domain. **It does not say which layer owns
enforcement** — that is a deployment fact, and it is why `locus` cannot be read off
the inputs.

The pattern is well established, and recognising which one you are in usually settles
`locus` for a whole entity at once:

| Shape | System of record | Engagement / insight layer | What the layer owes |
|---|---|---|---|
| NHS Federated Data Platform | trust EPR / PAS (Epic, Oracle Health, System C) | FDP ontology of patients, episodes, beds, waiting lists | an episode with two admitting consultants is **flagged, not rejected** — the EPR is the authority |
| Health Cloud over an EHR | Epic — demographics, encounters, orders | Salesforce flows for care coordination and outreach | "an order needs an authorised prescriber" is already guaranteed; re-checking adds nothing |
| Core banking plus CRM | Temenos / FIS / Thought Machine ledger | Financial Services Cloud, nCino | "debits equal credits" is a real invariant the CRM **cannot even evaluate** — it never sees postings |
| Process mining over an ERP | SAP S/4HANA — vendor master, matching tolerances, posting periods | Celonis object-centric model, action flows | write-back is the interesting case: SAP will reject an invalid change anyway (§ When the consumer re-checks) |
| Ops platform over a PSS or MRO | Amadeus Altéa, Sabre, AMOS, TRAX | disruption management, predictive maintenance | "a serialised part is installed on one aircraft at a time" is the MRO's to hold |

A UiPath solution authored from an ontology is almost always the engagement layer.
That is why default D1 asks per entity whether this store is the system of record.

## When the consumer re-checks

Default: **trust and monitor.** Set `locus: uipath` on an entity whose system of
record is elsewhere only in these four cases — they are the whole list.

| # | Case | Why the layer must check |
|---|---|---|
| 1 | **Write-back** — the automation writes to the source | pre-validating gives a usable message instead of a failed API call |
| 2 | **Cross-system invariant** — the rule spans several sources | no single upstream system can see enough to enforce it |
| 3 | **Sync lag** — the copy can be stale or transiently inconsistent | the guarantee held upstream but may not hold here, now |
| 4 | **Risky automation** — the action is unsafe if the invariant does not hold | the platform needs a guard of its own, regardless of who owns the data |

Outside those four, re-checking buys nothing and costs something: a constraint the
source already accepted, rejected here, produces **divergence** — a record that
exists upstream and cannot exist here, which is a defect in the copy, not a catch.

## Surface, do not block

For a replica, the engagement layer's job is to make a violation **visible**, not to
refuse the data.

| Level | The build writes | On violation |
|---|---|---|
| `state` | a field option | the insert fails |
| `transition` | a Business Rule on the writing step | the operation is refused, with a reason |
| `monitor` | a validation step that records a finding | the record is accepted; the finding is reported |
| `assumed` | nothing | nothing — the query trusts the data |

`monitor` is the right default for a constraint whose `locus` is `external` and whose
violation would matter to someone: the run records it against the record's business
key and carries on. Author mode may propose `monitor` as a `candidate`; Phase 2
confirms it, because whether anyone reads the finding is a process question.

**The failure mode to avoid is silent `assumed`.** A constraint downgraded to
`assumed` because nobody decided is indistinguishable from one deliberately trusted.
That is what `resolution` is for.

### Why three and not one

OWL makes the open-world assumption; SHACL validates under the closed-world
assumption; a Data Fabric entity mid-ingestion is a *third* world that may be
legitimately incomplete. A constraint crosses two gaps before it can become
`isRequired`, and only the first is carried in the inputs
([data-model-guide.md § Three completeness assumptions](data-model-guide.md)).

`locus` answers the second gap — is this store the thing that owes the guarantee?
`level` answers how it is paid. Collapsing them loses the case the whole extension
exists for: a constraint that is **mandatory in the business world and must not be
enforced here**, because the system of record already guarantees it and this store
holds partial copies.

## The capability table

Mechanical. Set `expressible` from this and nothing else.

| SHACL | `expressible` | Lands as, when `locus: uipath` and `level: state` |
|---|---|---|
| `sh:datatype` | yes | the field `type` |
| `sh:minCount >= 1` | yes | `isRequired` — **but see § The isRequired trap** |
| `sh:maxCount = 1` on an object property | yes | `RELATIONSHIP` rather than a junction |
| `sh:maxLength` | yes | `lengthLimit` |
| `sh:minInclusive` / `sh:maxInclusive` | yes | `minValue` / `maxValue`, `DECIMAL` only |
| `sh:in` | yes | a choice set + `CHOICE_SET_SINGLE` / `_MULTIPLE` |
| `owl:hasKey` / inverse-functional over one property | yes | `isUnique` |
| `sh:pattern` | **no** | — no field option exists |
| `sh:minLength` | **no** | only `maxLength` has a counterpart |
| `sh:lessThan`, `sh:equals`, `sh:disjoint` | **no** | cross-field; inherently an operation |
| `sh:not`, `sh:or`, `sh:xone`, `sh:and` | **no** | — |
| `sh:minCount > 1` | **no** | no "at least N links" constraint exists |
| `owl:hasKey` over ≥2 properties | **no** | `isUnique` is per field — no composite uniqueness |
| pair-uniqueness on a junction | **no** | same reason |
| `sh:nodeKind`, `sh:class` | partial | satisfied by `RELATIONSHIP` typing, nothing further |
| anything in `parserNotes` | **no** | not understood; `candidate: assumed`, and say so |

`sh:pattern` is the cleanest proof the axes earn their keep: a format constraint that
is unambiguously mandatory in the domain still cannot be state-enforced here.

## The `isRequired` trap

`sh:minCount >= 1` → `isRequired: true` is the most tempting rule in the mapping, and
it is wrong wherever the store ingests partial records — a staging buffer, a queue, a
replica completed over time. The insert fails on arrival for a field the domain
rightly calls mandatory.

So `isRequired` is **never set from SHACL alone**:

| `locus` | `isRequired` in Author mode |
|---|---|
| `uipath` (system of record — the default) | `true` |
| `external` (replica; the source of record guarantees it) | `false`, with a register row stating the domain claim |
| `none` | `false`, register row |

And `level` stays `null` until Phase 2 confirms the write sites. A `uipath` row whose
Phase 2 evidence shows incremental writes is flipped to `transition`, and the field
option is dropped.

## Read the enforcement annotations before defaulting

OWL cannot carry enforcement: under open-world semantics a cardinality axiom
documents an expectation, it does not check anything. **SHACL can**, and a bundle
whose author thought about this will say so. Read these before applying any default —
a declared answer beats a defaulted one.

| In the shapes | Read as |
|---|---|
| `sh:deactivated true` | documented, deliberately not enforced → `locus: none`, `level: assumed`, `resolution: override` |
| `sh:severity sh:Violation` (or absent) | enforce where the locus allows → `candidate: state` or `transition` |
| `sh:severity sh:Warning` / `sh:Info` | **surface, do not block** → `candidate: monitor` |
| an authoritative-source annotation on the shape or its target class | that system is the system of record → `locus: external`, and the entity is a replica of it |
| an enforcement-mode annotation (`authoritative` / `precheck` / `monitor`) | `level` directly: `state`-or-`transition` / `transition` on write-back / `monitor` |

The authoritative-source and enforcement-mode predicates are **not standardized** —
every bundle names them in its own vocabulary. The inspector records any annotation
on a shape it does not otherwise interpret, and the derivation accepts the predicate
IRIs to treat as authoritative-source and enforcement-mode through the overrides
file:

```jsonc
{ "annotations": {
    "authoritativeSource": "https://example.invalid/meta#authoritativeSource",
    "enforcementMode":     "https://example.invalid/meta#enforcementMode" } }
```

Given none, every row falls through to the defaults below, and the report says the
bundle carried no enforcement metadata — which is itself worth telling the user,
because adding it upstream is cheaper than answering per entity forever.

## Defaults and overrides

Category 3 is answerable without process context but not affordable to ask
exhaustively — roughly two questions per entity. So Author mode **declares four
defaults once, to the user, before applying any of them**, and takes a named-override
list. Same pattern the skill already uses for configuration questions.

| # | Default | Override by naming |
|---|---|---|
| D1 | every entity is the **system of record** | the entities that are replicas, and of what |
| D2 | scope is **tenant** | the entities that are folder-scoped, and the folder |
| D3 | `displayField` is the first required `STRING`, else the first `STRING`, else `Id` | the entity and its display field |
| D4 | an `owl:oneOf` class becomes a **choice set** | the classes that should be lookup entities instead |

Declare them as one message, not four questions. The user answers with overrides or
with "take the defaults"; either is an answer, and both are recorded.

**Every application of a default is a register row with `resolution:
default-applied`.** A silently applied default is worse than a deferred decision: a
deferred decision is visible in the worklist, a silent one is indistinguishable from
a derived fact.

D1 is the load-bearing one. It decides `locus` for every constraint on that entity,
and it is the only question that can legitimately put connector-backed federation on
the table at all — a replica has no ingestion path to choose against.

## The register row

```jsonc
{ "id": "R1",
  "source": "process",             // convention | metadata | domain | process
  "from": "<SHACL_SHAPE_IRI|ONTOLOGY_IRI|null>",
  "subject": "<EntityName>.<FieldName>",
  "statement": "<the constraint in plain words>",
  "expressible": "no",
  "locus": "uipath",
  "level": null,                   // parked — Phase 2
  "candidate": "transition",       // what Author mode believes, unasserted
  "resolution": "deferred",        // default-applied | override | deferred | decided
  "evidence": { "r2rml": { "logicalTable": "<TABLE>", "column": "<COLUMN>" } },
  "note": "sh:pattern has no Data Fabric field option" }
```

| Field | Rule |
|---|---|
| `id` | `R<n>`, stable across runs — assigned in sorted subject order, never by discovery order |
| `source` | which of the four categories; required |
| `subject` | the emitted name, not the IRI — `from` carries the IRI |
| `expressible` | from § The capability table; required |
| `level` | `null` in Author mode for every `source: process` row |
| `candidate` | Author mode's belief, always unasserted; Phase 2 confirms or reverses |
| `resolution` | `decided` only when a rule or an override settled it, never by inference |
| `evidence` | facts only — a column, a cardinality, an override the user gave. Never a rationale |

Rows are emitted for: every SHACL property shape; every rename and collision suffix;
every applied default; every `parserNotes` line; every arbitrary pick (a one-to-one
side, a `decimalPrecision` with no evidence).

## What a verdict lands as

Once `locus` and `level` are both set — Phase 2 for most rows:

| `locus` | `level` | Lands as |
|---|---|---|
| `uipath` | `state` | a field option on the entity |
| `uipath` | `transition` | a Business Rule on the writing step **plus one acceptance criterion** |
| `uipath` | `monitor` | a validation step that records a finding against the record's business key, **plus an acceptance criterion that the finding is raised** — not that the record is refused |
| `uipath` | `assumed` | nothing built; a recorded query-side assumption |
| `external` | `monitor` | the same validation step; the system of record still owns the guarantee |
| `external` | `transition` | only under one of the four cases in § When the consumer re-checks — most often write-back |
| `external` | `assumed` | the system of record holds it; recorded only |
| `none` | `assumed` | an accepted risk → an open item |

The `transition` row is the one with genome consequences: it writes into the genome's
Business Rules under the step that performs the write, and derives an acceptance
criterion one-to-one, exactly as every other business rule does
([genome-format-guide.md § Business Rules](genome-format-guide.md),
[§ Acceptance Criteria](genome-format-guide.md)).

In Author mode, a row that is already `locus: uipath, level: transition` by rule —
anything `expressible: no` on a system-of-record entity — produces its Business Rule
and criterion immediately. The rest wait.

## What Author mode may not decide

| Not decided | Why | Row carries |
|---|---|---|
| `level` for any `source: process` row | needs the write sites | `level: null`, `resolution: deferred` |
| `locus` where the user gave no override | D1 applies | `resolution: default-applied` |
| whether to denormalize | needs access patterns | — see [normalization-guide.md](normalization-guide.md) |
| whether a constraint is worth enforcing | a business call | `resolution: deferred` with the trade stated |

**A run that emitted a model and deferred nothing has guessed.** Check the register
before reporting.

## The Phase 2 worklist

`derivation` and `resolution` together are the handoff. Phase 2 does not re-walk the
ontology; it walks:

1. every row with `resolution: deferred` — set `level`, confirm `locus`;
2. every row with `resolution: default-applied` and `source: domain` — confirm against
   what the process shows;
3. every entity whose `derivation` is not `direct` — the composition decisions;
4. nothing else.

That is why the register is worth its weight: it converts "redo the analysis with
more context" into a finite, ordered list.

## Anti-patterns

1. **Setting `isRequired` from `sh:minCount` alone** (§ The `isRequired` trap). The
   single most expensive error available here.
1a. **Re-enforcing a constraint the system of record already holds**, outside the
   four cases in § When the consumer re-checks. Rejecting data the source accepted
   creates divergence — a record that exists upstream and cannot exist here. The
   layer's job is to surface the violation, not block it.
1b. **Defaulting `locus` without reading the shapes' enforcement annotations**
   (§ Read the enforcement annotations before defaulting). A declared answer beats a
   defaulted one, and overriding a declared one silently is worse than either.
2. **Applying a default without declaring it** (§ Defaults and overrides).
3. **Writing a `level` for a `source: process` row in Author mode.** That is a guess
   wearing a verdict's clothes.
4. **Collapsing `locus` and `level` into one column.** Loses the mandatory-but-not-
   enforced-here case the extension exists for.
5. **Putting a rationale in `evidence`.** Evidence is facts; the reasoning belongs in
   `note`.
6. **Omitting a row for a `parserNotes` line.** A construct nobody understood is a
   constraint nobody enforced.
