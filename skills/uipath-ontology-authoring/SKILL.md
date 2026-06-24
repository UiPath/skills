---
name: uipath-ontology-authoring
description: "UiPath Data Fabric ontology authoring — build an OWL 2 QL ontology (.ofn) AND its R2RML mappings (.ttl) from existing folder-level entities. Reads entities via uip df (folder-scoped); the author picks folders then entities; the skill asks business-language questions — never field/schema terms — and itself maps business concepts to the entities/fields. Generates the ofn + r2rml, syntactic-verifies (uip ontology verify), and publishes via uip ontology create / files put. Use to turn Data Fabric entities into a published ontology with data mappings, e.g. 'map my entities to an ontology', 'build an ontology over these entities', 'author an ontology over my Data Fabric data'."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Ontology Authoring

Build a published OWL 2 QL ontology **and** its R2RML mappings over **existing
UiPath Data Fabric entities**. The author describes meaning in plain business
language; the skill reads the entity schema, **owns the mapping** from business
concepts to entities/fields, and produces two files:

- `<name>.ofn` — the ontology (OWL 2 QL), semantics from the author's answers.
- `<name>.r2rml.ttl` — the mappings, binding each ontology term to the entity /
  field / join it comes from.

> **Preview** — under active development. v1 publishes the `owl` and `r2rml`
> slots only.

## When to Use This Skill

- The author has Data Fabric entities and wants an ontology **plus** mappings over them.
- "Map my entities to an ontology", "build an ontology over these entities", "generate R2RML for my Data Fabric data".
- The author can describe the business but should **not** have to know table/field names.

Not this skill: a business doc with no entities and no mappings wanted → use `ontology-from-context`.

## Core principle

**The author speaks only in business terms. Mapping business language to
entities and fields is the skill's job, never the author's.**

- Ask in business words ("Does a customer place many orders?"), never schema words ("what type is `CustomerId`?").
- The skill keeps a private alignment: each business concept ↔ the entity/field it maps to. It confirms correspondences in business words, surfacing a guess for a yes/no.
- The ontology's **meaning** comes from the author's answers. The R2RML **binding** is produced entirely by the skill from the schema.

## Critical Rules

1. **Ontology meaning traces to a business statement; never invent it from the schema.** A type/rule/relationship the author didn't state is not added. Unstated field type → `xsd:string` + an `rdfs:comment` recording the assumption.
2. **R2RML binding traces to a real entity/field.** If a business concept has no backing field, **flag the gap** — do not invent a column. Never bind by name where an id is required.
3. **Resolve relationships and choice values by UUID / NumberId, never by name** (the CLI requires it). The skill looks the ids up itself.
4. **Folder-level entities only.** The agent does **not** support tenant-level entities. Never offer a "Tenant level" option, never list tenant-level entities, and never run `entities list` without a `--folder-key`. Every entity modeled must come from a folder the author selected.
5. **Strict selection sequence — MANDATORY, in this exact order; do not reorder, skip, or merge the steps:** (a) show **all** folders and let the author select **one or more** (multi-select) — entities live in folders and may span several; (b) **list the entities** from the selected folder(s) by running `entities list --folder-key <key>` once per chosen folder; (c) **the author selects** entities from a picker of the actual entity names. Never list or let the author pick entities before folders are chosen.
6. **Never editorialize, recommend, default, truncate, or group the folder list OR the entity list.** Show **every** folder (Phase 1) and **every** entity in the chosen folders (Phase 2) as its own selectable option, multi-select. Do NOT recommend a folder or pre-pick a default, do NOT push folders into an "Other / type something" catch-all, do NOT group entities into domains/areas/clusters, do NOT summarize ("I found N entities, most look like…"), do NOT decide there are "too many to list", do NOT ask "which area do you want to model". If a list exceeds one picker's capacity, print the full numbered list (or use successive picker batches / a name filter) — never a summary, a default, or a business grouping.
7. **Pick-or-create, never auto-create.** If a folder or ontology name the author didn't approve is needed, present existing options as a selectable picker (`AskUserQuestion`, never a markdown list) and ask "use one of these, or create new?".
8. **One confirmation of the digest before generating** (Phase 4). Outside the blockers below, proceed without asking.
9. **Do not publish until `uip ontology verify` exits 0**, and not before self-checking the R2RML.
10. **STOP only on real blockers:** not logged in; no folder chosen; no entities selected; the business description is self-contradictory; `verify` reports an issue you cannot fix from the file; the ontology name already exists; a `create` / `files put` call fails.

```
Phase 0  Auth           → uip login status; announce org/tenant
Phase 1  Choose folders → list ALL folders; author multi-selects (folder-level only — NO tenant option) — no commentary, no truncation
Phase 2  List & select  → list entities from the selected folder(s) via --folder-key; author picks from the actual entity list (no grouping/summary)
Phase 3  Ask what's needed → business-language questions, guided by the schema
Phase 4  Confirm digest  → read back once
Phase 5  Build OFN        → OWL 2 QL, meaning from the answers
Phase 6  Build R2RML      → bind each term to entity/field/join
Phase 7  Verify           → uip ontology verify + R2RML self-check
Phase 8  Publish          → uip ontology create + files put owl + files put r2rml
```

---

## Phase 0 — Auth

```bash
uip login status --output json
```

`Data.Status` is not `"Logged in"` (or the command errors, or `ExpirationDate`
is in the past) → STOP: "The uip CLI is not logged in. Run `uip login` for the
default environment, or `uip login --authority <url>` for another (e.g.
`https://alpha.uipath.com`) and pick the tenant at the prompt — add `--tenant
<name>` to skip the prompt. Then reply 'logged in'." There is **no `--it` flag**.
Announce the active `Organization` / `Tenant` from the status output so the
author can confirm they're in the right environment. Do not discover or list
entities here.

## Phase 1 — Choose folder(s) (always first; never skipped)

Before listing any entity, show the author **all** the folders and let them pick
**one or more** — entities can come from several folders. List every folder:

```bash
uip or folders list --all --output json
```

Present **every** returned folder as its own selectable option, **multi-select**,
each labeled `<Name> — <Path>`. Rules for this step:

- **Folder-level only.** Do **not** add a "Tenant level" option — the agent does not support tenant-level entities (Critical Rule 4).
- **Show all folders.** Never truncate the list and never push folders into an "Other / type something" catch-all.
- **Multi-select.** The author may pick several folders.
- **No commentary.** Do not recommend a folder, do not pre-pick a default, do not describe which folders are Personal/Debug/Solution. Just list them and let the author choose.
- If the folders exceed one picker's capacity, print the full numbered list (`<Name> — <Path>`) and ask the author to reply with the ones they want — still showing every folder. Use a multi-select `AskUserQuestion` when they fit.
- If the author already named the folder(s), skip the picker, resolve the key(s), and announce "Using folder(s) <Name…>".

Do **not** list entities yet.

## Phase 2 — List the selected folders' entities, then select

List entities from **each** selected folder (one call per folder — always with
`--folder-key`, never tenant-level), then combine. `--native-only` excludes
read-only federated entities (not valid relationship/mapping targets):

```bash
# one call per selected folder:
uip df entities list --native-only --folder-key <FolderKey> --output json
```

Run one call per selected folder, then present the **combined** set: **every**
entity as its own option in a multi-select `AskUserQuestion` picker, labeled
`<Name> — <folder>`. Do
not group, cluster, summarize, recommend, or declare them "too many to list" (see
Critical Rule 5). If they exceed one picker's capacity, print the full numbered
list or show successive batches / a name filter — still listing the actual
entities. The author's selection is **both** the ontology's scope **and** the
R2RML binding targets, and it may span folders (cross-folder relationships carry
the target's folder key — see Phase 6).

Each list response carries every entity's full `Fields[]` inline (see
[references/entity-schema-guide.md](references/entity-schema-guide.md)). **Cache
this JSON** — it is both the scaffold for the Phase 3 questions and the source
for the R2RML binding. Re-fetch one with `uip df entities get <id> [--folder-key
<key>] --output json` if needed.

## Phase 3 — Ask what the skill needs (business language, schema-guided)

The skill already holds the schema, so it knows what to ask about. It asks the
author focused questions **in business terms** and never shows field/column
names. For each selected entity, it pre-fills what the schema implies and asks
the author to confirm, correct, or add meaning:

- **What it is** — one business sentence per entity → class identity + `rdfs:comment`.
- **What matters** — which attributes are business-meaningful (drop system/internal ones).
- **Value meaning** — units, formats, code meanings, what a flag's true/false means.
- **Relationships** — for each link the schema shows, the business cardinality, direction, and name ("an order is placed by exactly one customer"); inverse name if any.
- **Choice values** — pull the real values with `uip df choice-sets list-values <set-id> [--folder-key <key>] --output json`, then ask what each means. Resolve labels↔NumberIds yourself.
- **Rules** — disjointness ("a customer is never a supplier"), required, subclassing, uniqueness.

Maintain the private business↔entity/field alignment as answers come in, and
confirm correspondences in business words ("you mentioned an order's total — I'll
bind that to the amount the system already stores on each order; correct?").
Flag both gaps: a business concept with no backing field, and an
entity/field the author never described (confirm drop). See
[references/entity-schema-guide.md](references/entity-schema-guide.md).

## Phase 4 — Confirm digest (the one check)

Read back, in business language, the assembled understanding: the classes, their
properties and meaning, the relationships, the rules, and the business→field
alignment. Get **one** confirmation. If the description is self-contradictory,
STOP and quote the conflict.

## Phase 5 — Build the OFN (OWL 2 QL)

Default path `~/Desktop/ontology-build/<name>.ofn`. Write with `Write`. Semantics
come from the Phase 3/4 answers — not from the schema. Stay in the OWL 2 QL
profile; encode value-format/naming rules and any QL-forbidden constraint as
`rdfs:comment`s. Add a provenance `rdfs:comment` naming the source entity/field
where it aids the mapping. Template:
[assets/templates/ontology-template.ofn](assets/templates/ontology-template.ofn).
Profile + type mapping:
[references/owl-and-r2rml-guide.md](references/owl-and-r2rml-guide.md).

## Phase 6 — Build the R2RML

Default path `~/Desktop/ontology-build/<name>.r2rml.ttl`. One `rr:TriplesMap` per
selected entity: entity `Name` = logical table, primary key `Id` = subject
template, each meaningful field `Name` = a column, each relationship = a
referencing object map joined on the FK → target `Id`, each choice field = its
NumberId column. Cross-folder relationships carry the target's folder
(`referenceFolderKey` semantics) — note it. Every map must trace to a real
field; flag gaps. Template:
[assets/templates/mapping-template.r2rml.ttl](assets/templates/mapping-template.r2rml.ttl).
Patterns: [references/owl-and-r2rml-guide.md](references/owl-and-r2rml-guide.md).

## Phase 7 — Verify

```bash
uip ontology verify <ofn-path>
```

`verify` is **syntactic only** (non-empty, balanced parens, has an `Ontology(...)`
declaration) — it does not reason and does not check R2RML. Exit 1 → read the
issue, fix with `Edit`, re-run. Then **self-check the R2RML**: valid Turtle;
every `rr:TriplesMap` names a selected entity; every `rr:joinCondition` child
column is a real FK field and the `rr:parentTriplesMap` exists; every
`rr:column` is a real field on that entity.

## Phase 8 — Publish

```bash
uip ontology get <name> 2>&1            # exists? → STOP and ask (new name / overwrite)
uip ontology create <name> --display-name "<display>" --description "<short>"
uip ontology files put <name> owl   <ofn-path>
uip ontology files put <name> r2rml <ttl-path>
uip ontology files get <name> owl 2>&1 | head -20   # round-trip check
```

Name regex `^[a-z][a-z0-9-]{0,63}$`. Folder comes from the scope chosen in Phase
0 (sent as the `x-uipath-folderkey` header, not in the body). On any failure,
STOP. Finish with a summary block: name, display name, scope/folder, selected
entities, local OFN + R2RML paths, and the confirm commands.

---

## Reference Navigation

- [references/entity-schema-guide.md](references/entity-schema-guide.md) — the `uip df` JSON shape, field types, how to read FK/relationship/choice/folder, and the df commands the skill calls.
- [references/owl-and-r2rml-guide.md](references/owl-and-r2rml-guide.md) — type mapping (`FieldDataType` → `xsd` + R2RML datatype), the OWL 2 QL allow/avoid list, R2RML TriplesMap patterns, and provenance.
- [assets/templates/ontology-template.ofn](assets/templates/ontology-template.ofn) — OWL 2 QL skeleton.
- [assets/templates/mapping-template.r2rml.ttl](assets/templates/mapping-template.r2rml.ttl) — R2RML skeleton.

## Anti-patterns (what NOT to do)

- **Don't offer tenant-level scope or list tenant-level entities.** The agent only supports folder-level entities — every `entities list` call carries `--folder-key`, and there is no "Tenant level" option.
- **Don't list entities before folders are chosen**, and don't skip the folder step. Order is always: choose folder(s) → list those folders → select.
- **Don't make folder selection single-select.** Entities can span folders — the folder picker is **multi-select**.
- **Don't recommend, default, truncate, or comment on the folder list.** Show **every** folder; no pre-picked default, no pushing folders into "Other / type something".
- **Don't cluster, group, or summarize the entity list.** No "I found N entities, most look like coherent business clusters", no "Audit / Salesforce / Sandbox" groupings, no "which area do you want to model", no "too many to list". List the actual entities and let the author pick.
- **Don't expose field/column names to the author or ask schema-typed questions.** Ask in business terms; do the mapping yourself.
- **Don't invent ontology meaning from the schema**, and **don't invent an R2RML column** for a business concept with no field — flag the gap.
- **Don't bind relationships or choice values by name.** Resolve UUID / NumberId yourself.
- **Don't auto-create** a scope, folder, or ontology name the author didn't approve — pick-or-create via a picker.
- **Don't publish** before `uip ontology verify` exits 0 and the R2RML self-check passes.
- **Don't reuse a bare property name across classes** (`name` on two classes leaks domain/range) — disambiguate (`customerName`, `supplierName`).
- **Don't treat `verify` as semantic** — it only checks OFN well-formedness; correctness of meaning comes from Phase 3/4, of binding from Phase 6.
