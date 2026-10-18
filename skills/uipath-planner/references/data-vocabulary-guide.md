# Data Vocabulary Guide — printing entities from a compiled entity spec

A **compiled entity spec** is the output of a tool that parsed a shared vocabulary (an ontology or an
industry standard) and matched it to the customer's own data. It holds, per entity, the complete
Data Fabric create body, already checked against the platform's naming rules, plus the provenance of every
field (source column, vocabulary or standard element, value map). Parsing and matching are done by code, not
by this skill: the spec is the answer, and the planner's job is to carry it into the SDD and the tasks
unchanged.

## When it applies

Only when the user **passes a spec explicitly** — a path or link, e.g. *"use the compiled entity spec at
`<path-or-url>`"*. The file is JSON:

```json
{ "entities": [ { "name": "<Entity>", "class": "LDO | VDO", "status": "ready | blocked",
                  "body": { "displayName": "…", "description": "…", "fields": [ … ] },        // VDO: "externalFields"
                  "relationships": [ { "field": "…", "referenceEntity": "…", "kind": "…" } ],
                  "blockedReason": "…",                                                      // when blocked
                  "provenance": [ { "field": "…", "vocabulary": "…" } ] } ],
  "choiceSets": [ { "name": "…", "forField": "<Entity>.<field>", "values": [ { "name": "…", "displayName": "…" } ] } ],
  "createOrder": [ "<Entity>", … ],
  "renames": [ { "entity": "…", "sourceColumn": "…", "name": "…", "reason": "…" } ] }
```

Optional keys (`class`, `status`, `choiceSets`, `createOrder`, `blockedReason`) may be absent in older specs;
absent `class` means LDO and absent `status` means ready.

Read exactly the file you were given. Do not search the workspace or call any endpoint for a spec that was
not passed. Do not read ontology files (`.ofn`, `.ttl`, `.owl`) to derive fields yourself — if the user
passes only an ontology, say that it needs compiling first and plan from the PDD's §6 and the request as
today, gaps marked `[SME REVIEW]`.

## Rules

- **The body is sent as given.** Each `platform:<Solution>:entity:<Entity>` task's create body is the entry's
  `body`, verbatim — names, types, `lengthLimit`, `decimalPrecision`, `isRequired`, `isUnique`, field
  `displayName` and `description`. Do not rename, retype, add or drop fields; do not add keys. The entity name
  is the task's subject (`name`), not a body key.
- **Order by `relationships`.** An entity whose relationships name another entity in the spec is blocked by
  that entity's task. A `foreign-key column (plain field)` stays a plain field in the body; list the link
  under the SDD's `#### Relationships`.
- **Renames are already done.** The `renames` table records names the platform would reject and what they
  became (reserved `Id`, names under 3 characters, keywords); copy it into the SDD as the rename record —
  never raise a rename as a question.
- **Only the entities the request needs.** The spec may hold more entities than the process uses; print the
  ones the PDD or request names.
- **Choice sets come first.** When the spec has `choiceSets[]` (each `{name, forField, values[{name, displayName}]}`),
  emit one `platform:<Solution>:choiceset:<name>` task per choice set with its values, and make every entity task
  whose body uses it `Blocked by` that task.
- **Placeholders stay verbatim.** Values such as `"[RESOLVE AT BUILD: choice set X]"` or
  `"[RESOLVE AT BUILD: entity Y]"` (in `choiceSetId`, `referenceEntityId`, `referenceFieldId`) are ids the platform
  skill resolves when it executes the task, after the referenced choice set or entity exists. Keep them as written
  and add the `Blocked by` edge; never invent an id.
- **Class and status.** `class` is `LDO` (Native) or `VDO` (Federated). An entry with `status: "blocked"` (e.g. a VDO
  whose source system is not selected) still gets its entity task, with `Status: [!] blocked` and
  `**Blocked reason:**` set to the entry's `blockedReason`; its `[SME REVIEW …]` placeholders go to the SDD's SME
  review items. Do not drop it and do not fill the placeholders.
- **`createOrder`**, when present, is the order of the ready LDO tasks.
- **Platform rejects a body** → stop and report the platform's error against the spec entry; do not patch
  the body.

## Where it lands

- **SDD** — `### Data model` → `#### Data Fabric entities` rows from each body; `#### Relationships` from
  `relationships`; a source note naming the spec path, and the provenance (source column → standard element)
  per field when present. Standard element ids appear only as provenance.
- **Tasks** — in the [plan-and-tasks-format.md](plan-and-tasks-format.md) task shape. The skeleton is fixed and
  parsed by downstream tools — every task, choice sets and blocked entries included:
  - heading `## Task T<N> — <skill> — <title>` (level-2 heading, sequential `T<N>`; never `### Task: …`);
  - rows `**Identity:**`, `**Status:**`, `**Blocked by:**` (task ids `T<N>` only, or `none`), and for a blocked task
    a separate `**Blocked reason:**` row (the reason never goes in `Blocked by`);
  - then the body block. With these exact parts:
  - **Identity** uses the typed-resource form: `platform:<Solution>:choiceset:<ChoiceSetName>` for a choice set,
    `platform:<Solution>:entity:<EntityName>` for an entity, and `solution:<Solution>:resources:Entity:<EntityName>`
    for its solution resource. Never the skill's full name (`uipath-platform:…`) and never a bare subject without
    the kind.
  - **Body** is the spec entry's `body` copied into a fenced ` ```json ` block, verbatim (for a choice set: its
    `name` and `values`). Not a table, not prose, not a summary — the platform skill sends that block as the
    create body. The canonical body keys are those of [pdd-driven-lane-guide.md](pdd-driven-lane-guide.md) rule 8
    and [non-pdd-lane-guide.md](non-pdd-lane-guide.md) Step 5.
  - **One solution resource task per entity**, `Blocked by` that entity's task.
  - **Folder**: only the one the request or the spec names; a system of record (e.g. "AP Workflow", "ERP") is not
    a folder. No folder named → leave it to the solution's default and say so; never invent one.
  - **Status** `[ ] pending`, or `[!] blocked` with `**Blocked reason:**` for blocked entries.

  Example (one entity task):

  ````markdown
  ## Task T13 — uipath-platform — Create entity SupplierInvoice
  **Identity:** `platform:InvoiceProcessing:entity:SupplierInvoice`
  **Status:** [ ] pending
  **Blocked by:** T1, T2
  **Entities:** SupplierInvoice (write) — created here

  ```json
  { "displayName": "Supplier Invoice", "fields": [ { "name": "invoiceNumber", "displayName": "Invoice Number",
    "type": "STRING", "lengthLimit": 200, "isRequired": true } ] }
  ```
  ````
- **Never in the PDD** — the PDD stays business-level; this guide does not edit it.
