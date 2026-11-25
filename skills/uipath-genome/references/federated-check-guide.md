# Federated Check Guide — phase 7, the check report and the reconciliation

Phase 7 of [federated-entity-pipeline-guide.md](federated-entity-pipeline-guide.md): validate the artifact set as a whole and report every place the declared model and the discovered system disagree. Read it when the target YARRRML is written. The phase contracts, the ledger and the hard constraints stay in the pipeline guide.

Two halves, and they fail differently. The **validation** half asks whether the artifacts are consistent, and a failure there is usually a defect to fix — except at the two sites below, where the shipped rule is wrong and the artifact is right. The **reconciliation** half asks where the business model and the system of record disagree, and nothing there is a failure at all: it is the finding the pack was walked to produce, never a gate.

## Where the report lives

`<MODEL_NAME>-check.json`, beside the `.ofn`. **Its shape — every field, its type, whether it is required, and a worked example — is [federated-artifact-shapes-guide.md § Shape — the check report](federated-artifact-shapes-guide.md); this guide owns what each part means.** The parts, in the order the shape lists them: `verdict`, `expectedRejections`, `datatypeAgreement`, `reconciliation`, `coverage`, `openItems`, `handChecks`, `notPerformed`.

The report is machine-read, like every artifact of the pack: nothing in it is rendered for a person, and a `state` string is a value a parser branches on rather than a sentence. **`verdict[].state` is `clear` or `blocked` and nothing else** — a verdict of "mostly clear" is not checkable — with the expected-rejection count beside it in `expectedRejections` and the blocking exceptions in `blockedBy`.

The reconciliation half is a **view over the ledger** — it re-presents decision and exception rows by subject and introduces no fact the ledger does not carry. Every row of it names the record it is about by id, so the walk from a reconciliation row back to the property, the cell and the field it came from is a traversal rather than a name match.

## What is checked, and what has no checker

| Part | State |
|---|---|
| the cross-file rules between the `.ofn`, the SHACL file and the target YARRRML | **exists** — `uip ont validate <ONTOLOGY_NAME> --local --output json`. `--local` is required: without it the command fails (`validate.ts` returns `failLocalRequired("validate")`), it does not act on the service instead. It runs the local rules and **then calls the ontology service only for an ontology whose local rules passed**: an ontology with an ERROR violation reports `"serviceValidation": "Skipped"`, and where no ontology passed, the service is never called and **no login is needed**. So the login is a precondition of a clean local pass, not of the command. Read `serviceValidation` per entry before reading a pass as complete — `Skipped` means half the check did not run. `uip ont artifacts check <FILE> --output json` is the per-file convention check only, one file at a time |
| the datatype-agreement rule | **does not exist** — the run writes it (§ The agreement rule) |
| the declared-versus-observed reconciliation | **does not exist** — the run writes it, as a view over the ledger (§ Declared, observed, enforced) |
| anything over the source YARRRML | **does not exist** — the shipped checks were built for artifacts whose `table:` names an entity that already exists, and they do not know this file. Its half of the obligation — the block bound of phase 3 and the subject keys — is checked by the run |

## Four ERROR rules the run must clear

Shipped, ERROR, and none of them a false positive — each is the run's to satisfy, and a run hit all four. Check the first three at ingest, where the fix is cheap; OFN-002 fires earlier still, at `ont files add`.

| Rule | Site | Demands | What fails it |
|---|---|---|---|
| **XF-003** | `cross-file-rules.ts`, `checkIris` | the schema IRI **equals** `https://ontology.uipath.com/<ONTOLOGY_NAME>`, compared as strings | an IRI last segment that is not the ontology resource's name character for character — a PascalCased `<MODEL_NAME>` over a lowercase segment is the usual way in (pipeline guide § Artifacts). The same rule refuses any other `ontology.uipath.com` namespace in any artifact: a shapes prefix must be `https://ontology.uipath.com/shapes#`, never `<schema IRI>/shapes#`, and the `ont:` prefix of the mapping and of every constraints file must be `<schema IRI>#` |
| **XF-006** | `checkMappingTerms` | every `ont:` term the mapping uses is declared in the schema | a schema that declares its terms with the **`ont:` prefix instead of `:`**. `parseSchema` captures only `Declaration(Class(:…))`, `Declaration(DataProperty(:…))` and `Declaration(ObjectProperty(:…))`, so an `ont:`-declared model parses to **no declared terms at all** and every term the mapping writes is undeclared — class or property, whatever the mapping writes |
| **XF-014** | `checkJoinProperties` | every join's property is a declared object property | the same parse. An `ont:`-declared model declares none, so every join fails beside every term |
| **OFN-002** | `file-rules.ts`, `checkOfn` — per file, at `ont files add` | every **data** property's local name is `<Class>.<property>` | a bare local name: `:accountNumber` where the owning class is `ServiceAccount`. Object properties are outside this rule |

**XF-006 and OFN-002 interact, and the interaction hides a defect.** OFN-002 matches `Declaration(DataProperty(:<name>))` — `:`-prefixed terms only — so a model declared entirely in `ont:` never reaches it and attaches with **no violation**. The dotted-name rule then goes unchecked while XF-006 and XF-014 reject every term and every join. A run in that state reports `"serviceValidation": "Skipped"` and **must not read that as a pass**: the cross-file layer refused the model wholesale and the per-file layer never looked (§ Stops rule 3).

So: declare every term with the bare `:` prefix and give every data property the dotted local name. Classes keep their bare local name, and the `ont:` prefix stays bound in the mapping and in every constraints file — XF-003 requires it there, and XF-008 reads `sh:targetClass`, `sh:path` and `sh:class` through it.

## Three rejections to expect, by site

`uip ont validate` runs the shipped cross-file rules. Three sites were written for a model where one class maps to one table, and **each refuses or drops a check on a target mapping this lane is required to produce.** They are not defects in the generated artifact, not a reason to rewrite a block, and not a stop. Expect them by name:

| Site | What it does | What it rejects here |
|---|---|---|
| **XF-015**, `packager-tool-ontology/src/rules/cross-file-rules.ts` (~line 980) | demands `condition: { function: equal }` on every join — `if (!join.isEqual \|\| child === undefined \|\| parent === undefined)` returns the error | the folded-class same-row join: a `mapping:` reference with **no** `condition:`, which R2RML §8 permits precisely because both queries are the same table ([federated-mapping-guide.md § An intra-entity join is not represented](federated-mapping-guide.md)). The CLI parser already models the shape (`isEqual: false` in `yarrrml.ts`); only the rule refuses it |
| **`firstMappingByClass`** resolving the **range** side, same file (line 916, used at line 999 as `blockOf`) | resolves the property's range class to its **first** block, then `joinProblems` compares `join.target !== to.name` | every join whose `mapping:` names a block of the range class that is not that class's first — the message is *"The join for ont:X reads the mapping Y; its range ont:Z is mapped by W"*, and it is false: the join names the one block whose entity holds the matching column, which is what [federated-mapping-guide.md § Object-property joins](federated-mapping-guide.md) requires |
| **`firstMappingByClass`** resolving the **domain** side, same lines | resolves each class to its **first** block | every later block of a class that has more than one — both the folded host/guest pattern and the multi-source pattern. No message: the join checks silently skip those blocks, so a pass on a multi-block class is not evidence its later blocks are right |

All three are correct for a 1:1 native model and all three break at the federated step.

**Three is the cross-file count, not the ceiling.** A per-file rule can reject a correct artifact the same way and is recorded the same way — observed: `SHC-002` counts the string `sh:targetClass` inside a Turtle `#` comment as a shape with no matching `a sh:NodeShape`, so a constraints file whose shapes are all well-formed is refused for a comment. Record it as a decision with the site named, and report the fix as the CLI's. A rejection that is a **real** input defect is the other thing and not this — `OFN-001` on an ontology IRI outside `https://ontology.uipath.com/` is an exception against the model, blocking every artifact derived from it (pipeline guide phase 1 § Check the model's IRI).

**A prediction that never fired is not a prediction confirmed.** Each row carries `reached`, because a run blocked before the cross-file rules ran — `uip ont files add` attaches nothing while one artifact fails its per-file ruleset, and `uip ont validate` then reports `XF-001: found 0` with `"serviceValidation": "Skipped"` — reports every cross-file site `false`, and that is a check not performed rather than three rejections expected and met.

**What to do, in order:**

1. **Record each as a ledger decision, not an exception** — with the site, the blocks it touches and the reason the artifact is right. An exception blocks an artifact; these block nothing (pipeline guide § The ledger rule 6).
2. **Report the fix as the CLI's, and do not work around it.** XF-015 must permit `isEqual: false` when both blocks' `table:` sets are identical — the R2RML §8 rule restated, which doubles as a star-membership check — and `firstMappingByClass` must stop assuming one block per class. Rewriting the mapping to satisfy the shipped rule means writing a `condition:` that re-joins a flat row against itself, which is anti-pattern 2 of the mapping guide.
3. **Check the skipped blocks by hand.** Because `firstMappingByClass` drops them, the join checks never ran on them: for every class with several blocks, check `str1` against that block's own columns and `str2` against the target block's, block by block. Record each in the report's `handChecks`, keyed by the block's `blk:` id — an unperformed check reported as a pass is worse than the rejection.

**The self-join fallback is not the move here.** [federated-mapping-guide.md § An intra-entity join](federated-mapping-guide.md) keeps an explicit self-join on the shared key for an ontology *service* that refuses the omission at runtime — a different failure, found by running something, not by validating. The fallback is a legal mapping, but adopting it to quiet XF-015 bakes a workaround into a committed artifact and nothing later takes it out.

## The vocabulary bridge — `xsd` to Data Fabric

The agreement rule compares three vocabularies: SHACL's `sh:datatype` (an `xsd:` IRI), the connector's declared field type (the connector's own vocabulary, in the discovery record) and the Data Fabric field type the CLI set on the created entity. Nothing bridges the first to the third, so **build the bridge before running the rule — it is this phase's first task.**

**The bridge has two layers, and only the second is observable.** The create body carries an `EntityFieldDataType` — `STRING`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ` — which is what `CONNECTOR_TYPE_MAP` (`data-fabric-tool`, `src/utils/federated-payload.ts`) maps the connector's declared type to. Nothing reads that layer back. What `uip df entities get` returns is the **stored document**, where a field carries `SqlType` and `FieldDisplayType`, not the `type` the create body took:

```bash
uip df entities get <ENTITY_NAME> --local --output json
```

Read `Fields[].Name`, `Fields[].SqlType.Name`, `Fields[].SqlType.LengthLimit` and `Fields[].SqlType.DecimalPrecision`, under `Data` in the command's JSON envelope. The two layers, end to end:

| Connector declares | `EntityFieldDataType` (create body) | `SqlType.Name` (observable) | Qualifiers observed |
|---|---|---|---|
| `string`, or anything unmapped | `STRING` | `NVARCHAR` | `LengthLimit: 200`, always |
| `integer`, `int` | `DECIMAL` | `DECIMAL` | `DecimalPrecision: 0` |
| `number`, `decimal`, `float`, `double` | `DECIMAL` | `DECIMAL` | `DecimalPrecision: 2` |
| `boolean` | `BOOLEAN` | `BIT` | — |
| `date` | `DATE` | `DATE` | — |
| `datetime` | `DATETIME_WITH_TZ` | `DATETIMEOFFSET` | — |

**Build the right-hand columns from the entity, not from this table**, for the types the model actually declares: the table is what the run that wrote it observed, and a wrong type name makes every agreement row wrong in the same direction.

**The `DATE` row is theoretical on these connectors.** No `DATE` and no `DATETIMEOFFSET` appeared anywhere in the run: every `xsd:dateTime` property landed on `NVARCHAR(200)`, because Salesforce, Snowflake and Database Hub each declare their date columns as `string` and the map keys off the connector's declaration. A date arrives as a date only where the connector says `date` — and none of the three does. Report every such property as a declared-versus-created reconciliation row, not as a defect.

Two questions the bridge no longer leaves open, both answered by the run:

- a string property with **no `sh:maxLength`** is given `NVARCHAR(200)`, the same as one with any `sh:maxLength`;
- `sh:maxLength` **exceeding** 200 is not an error and not a cap negotiation — the declaration is ignored and the column is `NVARCHAR(200)`. The excess is a reconciliation row, and values over 200 characters are a runtime question this lane does not own: flag it as a touch point.

## The agreement rule

Nothing in the shipped rules looks at a mapping's third element — there is no datatype rule in the cross-file set — so the run writes this one. Per cell of the correspondence matrix, gather four readings — they are the `declared`, `observed`, `created` and `authored` fields of a `datatypeAgreement` row, and a reading that is absent is `null`, never a passing comparison:

| # | Reading | From |
|---|---|---|
| 1 | **declared** | the property's `sh:datatype` |
| 2 | **observed** | the field's type in the discovery record — the prose type first where the declared type was flattened |
| 3 | **created** | the field's type on the created entity (`uip df entities get`) |
| 4 | **authored** | the third element of the `po:` pair in the target YARRRML; a two-element pair is `xsd:string` |

Then three comparisons, and they have different meanings:

| Comparison | Field | A disagreement is |
|---|---|---|
| 1 against 4 | `declaredVsAuthored` | a **defect in the generated artifact** — fix the mapping. These are the same vocabulary and must be equal |
| 1 against 2, through the bridge | `declaredVsObserved` | a **reconciliation row** — the model and the system of record disagree on the type. Never a fix |
| 1 against 3, through the bridge | `declaredVsCreated` | a **reconciliation row** — what the platform did with the type. Field types are read from the connection, not set by this pipeline |

**Where it degrades.** A connector that flattened its types (pipeline guide phase 2, limit 3) gives reading 2 nothing to compare: the comparison becomes a presence check and the row is reported **unverifiable**, never as agreement. Reporting a flattened `string` as agreeing with `xsd:string` is the exact failure this rule exists to prevent.

**With no constraints file** reading 1 is absent for every property, so the rule reports coverage only and the verdict says so (pipeline guide phase 1 § No constraints file).

## Declared, observed, enforced

Principle 3 of the pipeline guide as a procedure. **Every row is declared in the model whatever discovery found.** The *enforced* column records where the platform will not hold the line, which is a reason to report and never a reason to drop the declaration — letting the discovered schema quietly win throws away the one signal that says the business model and the system of record disagree.

| Declared fact | Discovery observes it | Enforced on a federated field | A mismatch means |
|---|---|---|---|
| `sh:datatype` | yes, as the field's type | mirrored from the connector's declaration, not from the source column | the model and the system disagree on the type — the highest-signal row |
| `sh:maxCount` on an object property | partly, through the source's own keys | not applicable | the model says to-one, the source permits many |
| `sh:in` | sometimes, through the field's `enum` | open — unverified whether a federated field can be a choice set, and this lane emits none | the source admits values the model forbids |
| `sh:minCount` | **no channel at all** — `describe` carries no nullable flag on any connector | open | nothing is observed, so nothing is a mismatch: the row reports coverage |
| `sh:maxLength` | **no channel at all** — `describe` carries no length on any connector; prose is the only trace | **no — every string column is `NVARCHAR(200)`, whatever was declared.** The length is hard-coded, not read from the model or the connection | nothing is observed, so nothing is a mismatch: the row reports coverage, and the 200 is reported as a flat loss |
| decimal scale behind `sh:datatype xsd:decimal` | only as prose, where the connector wrote the real type there | **no — the scale is the connector's declared type, not the column's.** `number` → `DECIMAL` precision 2, `integer` → precision 0, whatever the source's real scale | a declared `NUMBER(12,3)` arriving as `DECIMAL(,2)` is a silent scale loss, and this row is the only place it is recorded |

**One observation channel, not three.** `enum` is the whole budget (pipeline guide phase 2 § One observation channel). `sh:minCount` and `sh:maxLength` are carried as declarations with no observation, which this table reports as coverage — never as agreement and never as a mismatch. Claiming agreement from an absent channel is the same failure as reporting a flattened connector type as agreement (§ The agreement rule).

**Each row carries what the platform built, beside whether it holds the line.** `created` is the third reading — `NVARCHAR(200)`, `DECIMAL` precision 2 — and `enforced` is yes or no; they are not the same fact, and the created type is what a reader needs to see the loss rather than be told about it. The row's `subject` is a list, because one declaration contradicted the same way across six properties is **one** finding: six `xsd:dateTime` properties all landing on `NVARCHAR(200)` is the model and the system disagreeing about timestamps once, not six times.

**The inverse row.** A row may carry no declaration at all: where the **source** constrains values the model leaves open — Salesforce exposing a picklist on six properties that carry no `sh:in` — `declared` is null and the note says what was observed. It is a report to the model's owner, never an edit, and it is as much a finding as the rows where a declaration went unhonoured.

**The reconciliation is the report's substance, not a pass or a fail.** It lists every declaration the source does not honour and leaves them standing as declarations. The two constraints this lane pushes nowhere — `sh:in` and `sh:minCount` — still appear here: they are real facts about the model, and the only place they surface is this report.

## Coverage

Two counts, both reported rather than fixed.

1. **Label and comment coverage.** XF-007 — *every term carries `rdfs:label` and `rdfs:comment`* — is a shipped rule, and it **fails a model whose properties carry labels and no comments**, which is the common shape and what a real run hit: classes and object properties fully labelled and commented, data properties fully labelled and four of thirty-eight commented. Count terms with a label and terms with a comment **per kind** — class, data property, object property — and report the shortfall as an open item for the model's owner. A flat total reports the same shortfall and says nothing about where it sits, which is the only part anyone can act on. This pipeline never writes an `rdfs:comment` into the `.ofn` to pass a check (pipeline guide § Principles rule 8). Take the count at ingest, so the run knows before `uip ont validate` why the rejection arrived.
2. **Constraint coverage.** Data properties with no `sh:datatype`, object properties with no `sh:maxCount`, and classes with no `:sourceOfRecord` — each a count, and each the reason some other row of this report reads *unverifiable* rather than *agreed*.

## Stops

1. **An exception still open in the ledger blocks its artifact**, and the verdict table names which exception blocks what. A report that lists an open exception and still calls the artifact clear is wrong.
2. **A missing reading is not a passing comparison.** A cell with no observed type, an entity whose columns were never read back, a block the join checks skipped, a declared `sh:minCount` or `sh:maxLength` with no channel to check it against: each is reported as unverified, by name. A whole **check** that did not run goes in `notPerformed` with the reason — the cross-file rules when nothing attached, a hand check that was not needed, anything outside the lane. `handChecks` records what was performed; without `notPerformed` a check that never ran is indistinguishable from one that passed.
3. **`"serviceValidation": "Skipped"` is half a check, not a pass.** It means the local rules failed, so the ontology service never saw the artifacts. Fix the local ERROR violations and re-run before the verdict table calls anything clear.

## Anti-patterns

1. **Rewriting a correct mapping to satisfy XF-015**, or adopting the self-join fallback to quiet it (§ Three rejections to expect).
2. **Reporting a pass on a class with several blocks** without hand-checking the blocks `firstMappingByClass` skipped.
3. **Guessing a Data Fabric type name** into the bridge instead of reading it off a created entity (§ The vocabulary bridge).
4. **Reporting a flattened connector type as agreement** rather than unverifiable (§ The agreement rule).
5. **Treating the reconciliation as a pass/fail gate** and "fixing" the model to clear it (§ Declared, observed, enforced).
6. **Writing `rdfs:comment` into the `.ofn`** so XF-007 passes (§ Coverage).
7. **Calling an artifact clear while an exception against it is open** (§ Stops).
