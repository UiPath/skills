---
name: uipath-ontology-authoring
description: "Ontology Authoring Skill v1 — author or improve a UiPath Data Fabric ontology package (OWL 2 QL .ofn + R2RML .ttl + USAGE POLICY block) engineered for NL-to-SQL agents that consume the files as raw prompt text. Two modes: CREATE from existing entities (business-language interview + data-verified facts) and IMPROVE a published ontology (failure-driven enrichment, allow-list preserved). Every fact is verified against real data before it enters the files; generation follows the measured three-layer model (facts on OWL constructs, behavior in one bounded policy block, physically correct mapping with a joinCondition per FK). Verifies, gate-checks, and publishes via uip ontology. Use for 'build/author an ontology over these entities', 'improve my ontology', 'my ontology agent answers wrong — fix the ontology', 'add mappings/joins/value domains to my ontology'. For a pure business-doc→ontology with no entities→ontology-from-context."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# uipath-ontology-authoring (v1)

Author a UiPath Data Fabric **ontology package** that measurably improves NL-to-SQL
agents. A package is three layers in two files:

1. **OWL (.ofn, OWL 2 QL)** — the knowledge layer: verified facts placed on the
   construct they describe (labels, comments, value domains, code lists, grain).
2. **R2RML (.ttl)** — the physical layer: correct table/column bindings and a
   `rr:joinCondition` for every FK.
3. **USAGE POLICY** — one bounded `#` comment block at the top of the R2RML: the
   behavior layer (routing, join/output/literal discipline).

The consuming agent reads both files as **raw prompt text**, so placement,
phrasing, and verified literals decide accuracy. Method measured at +8 to +14
points over entities-only baselines across four databases (evidence:
`Documentation-Confluence/Guide-Authoring-OWL-Ontologies-for-NL-to-SQL.md` and
`…R2RML-Mappings…`).

## Modes

- **CREATE** — build a new package over existing Data Fabric entities (Phases 0–9).
- **IMPROVE** — enrich a published package from failure signal or on request
  (Phases 0, I1–I4). The entity allow-list is preserved; existing verified facts
  are never dropped.

## Core principles

1. **The author speaks business language only.** Mapping business words to
   entities/fields is the skill's job; never ask schema-typed questions.
2. **Facts / behavior / physical are separate layers.** A fact goes on its OWL
   construct; a rule goes in the policy block; a binding goes in the mapping.
   Never narrate behavior in the OWL; never bury facts in the policy.
3. **No literal enters the package unverified.** Every value domain, code,
   format, scale, and grain claim is checked against the actual data first
   (Phase 5). One wrong literal costs more than ten missing annotations.
4. **Ontology meaning traces to a business statement or a verified data fact —
   never invented from field names.** R2RML bindings trace to real fields;
   business concepts with no backing field are flagged, not fabricated.

## Critical rules

1. **Folder-level entities only.** Every `entities list` carries `--folder-key`;
   never offer a tenant-level option.
2. **Strict selection sequence (CREATE):** show ALL folders (multi-select) →
   list the selected folders' entities → the author picks entities. Never
   truncate, group, summarize, recommend, or default either list; if a picker
   overflows, print the full numbered list.
3. **Pick-or-create, never auto-create** folders or ontology names — always via
   an `AskUserQuestion` picker.
4. **Resolve relationships and choice values by UUID / NumberId, never by name.**
5. **A `rr:joinCondition` for EVERY foreign key.** Missing joins were the single
   costliest defect measured (ontologies with zero joins added ~0 points).
6. **Conditional rules carry their condition and the explicit non-action**
   ("NULLs sort last in DESC → no filter for highest; add IS NOT NULL only for
   ascending ranks"). Unconditionally-phrased rules get over-applied and regress.
7. **The `(rr:tableName, uipath:folderPath)` allow-list is immutable in IMPROVE
   mode** — never add unprovisioned tables, never remove/rename/merge a
   TriplesMap.
8. **One digest confirmation before generating** (CREATE Phase 4). Otherwise
   proceed without asking.
9. **Do not publish until every gate passes** (Phase 8) — `uip ontology verify`,
   QL blacklist scan, cross-file predicate check, R2RML self-check, policy
   bounds, and the post-publish byte round-trip.
10. **STOP only on real blockers:** not logged in; no folder/entities selected;
    contradictory business description; a gate failure you cannot fix from the
    file; name collision; a publish call fails.

## CREATE mode — phases

```
Phase 0  Auth            → uip login status; announce org/tenant
Phase 1  Choose folders  → ALL folders, multi-select, no commentary/truncation
Phase 2  List & select   → entities per folder via --folder-key; author picks
Phase 3  Interview       → business-language questions ONLY for meaning the data
                           cannot show (what codes mean, domain semantics,
                           relationship names/cardinality, what matters)
Phase 4  Confirm digest  → read back once, in business words
Phase 5  Verify facts    → sample real data per fact type (references/
                           data-verification-guide.md); nothing unverified
Phase 6  Build OFN       → references/owl-authoring-guide.md + template
Phase 7  Build R2RML + POLICY → references/r2rml-and-policy-guide.md + template
Phase 8  Gate-check      → all gates below
Phase 9  Publish         → create + files put owl/r2rml + round-trip check
```

**Phase 0** — `uip login status --output json`. Not logged in → STOP with the
`uip login` instructions. Announce Organization/Tenant.

**Phase 1** — `uip or folders list --all --output json`. Every folder as its own
multi-select option `<Name> — <Path>`. No tenant option, no recommendations, no
"Other" catch-all. If the author already named folders, resolve and announce.

**Phase 2** — per selected folder: `uip df entities list --native-only
--folder-key <key> --output json`. Present the combined set, every entity its
own option. Cache the returned `Fields[]` JSON — it scaffolds Phases 3–7. See
references/entity-schema-guide.md.

**Phase 3** — ask only what data cannot answer: one business sentence per entity;
which attributes matter; what each code/flag/choice value *means* (values
themselves come from data in Phase 5); relationship names, direction, business
cardinality; domain semantics phrases imply ("'eligible for loans' means the
disposition is OWNER — a right, not an existing loan"); rules (disjointness,
uniqueness). Maintain the private business↔field alignment; confirm guesses in
business words; flag both gap directions.

**Phase 4** — one read-back: classes, properties, meanings, relationships,
rules, alignment. Contradiction → STOP and quote it.

**Phase 5** — run the verification recipes (references/data-verification-guide.md)
for the seven fact types: grain, value domains, code lists, formats/scales,
cryptic columns, lookalike disambiguation, NULL rates. Also mine the dataset's
own documentation (description files) — legitimate; example answers/gold
queries — never.

**Phase 6** — build the OFN at `~/Desktop/ontology-build/<name>.ofn` per
references/owl-authoring-guide.md and assets/templates/ontology-template.ofn.

**Phase 7** — build the R2RML (+ leading USAGE POLICY block) at
`~/Desktop/ontology-build/<name>.r2rml.ttl` per
references/r2rml-and-policy-guide.md and assets/templates/mapping-template.r2rml.ttl.

**Phase 8 — gates (all must pass):**
1. `uip ontology verify <ofn>` exits 0 (syntactic only — no reasoner exists).
2. QL-profile blacklist scan of the OFN (owl-authoring-guide §2) — zero hits.
3. Cross-file: every `rr:class` and `rr:predicate` in the R2RML is declared in
   the OFN (same namespace + local names).
4. R2RML self-check: valid Turtle; every TriplesMap names a selected entity;
   every `rr:column` is a real field (bare name, no expressions); every FK has a
   joinCondition whose child/parent columns exist.
5. Policy block ≤30 non-empty lines, rules only, every line references
   constructs that exist; body comments bounded.
6. Spot-recheck literals in annotations against the Phase-5 samples.

**Phase 9 — publish:**
```bash
uip ontology get <name> 2>&1          # exists? → STOP: new name or overwrite
uip ontology create <name> --display-name "<display>" --description "<short>"
uip ontology files put <name> owl   <ofn-path>
uip ontology files put <name> r2rml <ttl-path> --content-type text/turtle
```
Name regex `^[a-z][a-z0-9-]{0,63}$`; folder via the `x-uipath-folderkey` header.
Then **round-trip**: `files get` both slots and byte-compare (force UTF-8 when
fetching over HTTP — `text/turtle` decodes as Latin-1 by default; prefer
ASCII-only content). Finish with a summary block.

## IMPROVE mode — phases

```
Phase 0   Auth (as above)
Phase I1  Fetch & assess  → files get owl+r2rml; inventory: joins present per FK?
                            policy block present? which fact types are missing?
Phase I2  Failure-driven forensics (if failure signal exists) → classify each
            wrong answer: knowledge → OWL fact | behavior → policy rule |
            mapping → R2RML fix | engine-limit/data-quirk → accept & note
Phase I3  Verify & author → Phase-5 recipes for every new fact; edit surgically
            (upsert one comment per construct; append joins as separate
            `map:TM_x rr:predicateObjectMap [...] .` statements; keep the
            allow-list byte-identical; PORT every existing verified fact)
Phase I4  Gate-check + publish (Phases 8–9; skip `ontology create`)
```

Failure signal sources: user-reported wrong answers, agent traces, eval reports.
For each failure examine the agent's own SQL, never encode a specific question's
answer — every fix must be a schema-level fact or a general rule. When
re-measuring is possible, keep the best-scoring package and roll back regressions.

## Anti-patterns (measured, not theoretical)

- **Comment dumps / usage narration blobs** — worse than a compact policy block.
  One fact, one construct.
- **Facts in the policy block** (value lists, column meanings) — they belong on
  the OWL property.
- **Unverified "obvious" claims** — a truncated or paraphrased literal produces
  SQL filtering on wrong values.
- **Question-shaped rules** ("for questions like X, do Y") — leakage; doesn't
  generalize.
- **Unconditional phrasing of conditional rules** — gets over-applied (Critical
  Rule 6).
- **Documenting a discriminator column without bounding it** — invites filter
  invention; pair the fact with its non-action.
- **Dropping existing verified facts when updating** — rewrites that did this
  each lost 5–10 points. Port everything you can't attribute a removal reason to.
- **Global routing winners for duplicated attributes** — routing must be sided
  per question type.
- **Tenant-level listings, truncated/grouped pickers, auto-created names,
  name-based relationship binding, publishing before gates** — all inherited
  prohibitions from the selection machinery.
- **Reusing a bare property name across classes** (`name` on two classes) —
  disambiguate (`customerName`, `leagueName`).

## Reference navigation

- [references/owl-authoring-guide.md](references/owl-authoring-guide.md) — the
  knowledge layer: skeleton, QL fence, the seven fact types, rule expression.
- [references/r2rml-and-policy-guide.md](references/r2rml-and-policy-guide.md) —
  mapping correctness rules, USAGE POLICY template + content rules, gates.
- [references/data-verification-guide.md](references/data-verification-guide.md)
  — per-fact-type sampling recipes (`uip df` records / source SQL).
- [references/entity-schema-guide.md](references/entity-schema-guide.md) — the
  `uip df` JSON shape and which schema signal scaffolds which question.
- [assets/templates/ontology-template.ofn](assets/templates/ontology-template.ofn)
  · [assets/templates/mapping-template.r2rml.ttl](assets/templates/mapping-template.r2rml.ttl)
