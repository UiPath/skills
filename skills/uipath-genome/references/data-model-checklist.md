# Data Model Checklist

Conformance checklist for the data-model extension of Author mode. Two uses: the
authoring agent ticks it before offering edits, and a contributor changing the
extension checks nothing regressed.

Subject homes: [data-model-guide.md](data-model-guide.md) routes; each row names the
guide that states its rule in full.

## A — Inputs recognised

- [ ] A1 Ontology file detected (`.ofn`, or `.owl`/`.ttl` carrying OWL axioms) — [ontology-sources-guide.md](ontology-sources-guide.md) § Detection
- [ ] A2 R2RML mapping detected and read as `source.r2rml` — § Detection
- [ ] A3 SHACL shapes detected — § Detection
- [ ] A4 A bundle missing one of the three is reported, with what cannot be derived without it — § Missing inputs
- [ ] A5 `source.r2rml` copied to `target.r2rml` before any derivation, and never written again in the run — [data-model-guide.md](data-model-guide.md) § Artifacts
- [ ] A6 `ontology-inspect.py` run; the inventory JSON is the only reading of the three files the derivation uses — § The inventory is the contract

## B — Deterministic derivation

- [ ] B1 Every `owl:Class` with ≥1 mapped property became an entity — [entity-derivation-guide.md](entity-derivation-guide.md) § Classes and properties
- [ ] B2 Every datatype property became a field with a type from the type table, and no UI-broken type was emitted — § Types
- [ ] B3 Every functional / max-1 object property became a `RELATIONSHIP` on the many side — § Object properties
- [ ] B4 Every many-to-many object property became a junction entity with `derivation: junction` — § Junctions
- [ ] B5 Field and entity names pass the name rules; every rename has a register row — § Naming
- [ ] B6 Self-references discarded; any remaining cycle failed the run, naming its members — § Cycles
- [ ] B7 Every object carries `provenance` with a non-empty `from[]`, or sits in `notCovered` — § Provenance
- [ ] B8 A non-`direct` derivation carries a non-empty `because` — § Provenance
- [ ] B9 Coverage check passes both ways: class → entities, entity → classes — § Coverage
- [ ] B10 Re-running the emitter on unchanged inputs produces a byte-identical `entities.json` — [data-model-guide.md](data-model-guide.md) § Determinism

## C — Constraints classified

- [ ] C1 Every SHACL shape has a register row — [constraint-register-guide.md](constraint-register-guide.md) § The register
- [ ] C2 Every row carries `expressible`, set mechanically from the capability table — § Expressible
- [ ] C3 `expressible: no` rows carry no `level: state` — § The three axes
- [ ] C4 Every row names which of the four non-determinism categories it came from — § Where non-determinism comes from
- [ ] C5 The four defaults were declared to the user before being applied — § Defaults and overrides
- [ ] C6 Every applied default produced a row with `resolution: default-applied` — § Defaults and overrides
- [ ] C7 Process-dependent rows are `resolution: deferred` with `level: null`, never guessed — § What Author mode may not decide

## D — Normalization

- [ ] D1 Weakly connected components computed; each carries a component id — [normalization-guide.md](normalization-guide.md) § The unit of work
- [ ] D2 The emitted form is the FD-dictated normalized form; nothing was denormalized without evidence — § Conservative means normalized
- [ ] D3 Platform limits applied as pruning, recorded as envelope rows, not as proposals — § Platform limits prune first
- [ ] D4 No `consolidation`, `decomposition` or `federated-view` entity was emitted in Author mode — § What Author mode may not decide
- [ ] D5 `target.r2rml` is byte-identical to `source.r2rml` at the end of Author mode — § Revision has a deadline

## E — Emission

- [ ] E1 `entities.json` written and validated against its schema — [datafabric-emission-guide.md](datafabric-emission-guide.md) § entities.json
- [ ] E2 Choice-set `numberId` values pinned, unique within the set, `nextNumberId` recorded — § Choice sets
- [ ] E3 Entities created with `uip df entities create --local`, scalar fields only — § The applier
- [ ] E4 Relationship and choice-set fields emitted as **open items**, never written into the resource file — § The two tiers
- [ ] E5 Each open item names the entity, the field, the target and the exact command the engineer runs — § Open items for the complex tier
- [ ] E6 `uip df entities validate --local` exits 0 — § Validation gates
- [ ] E7 `uip solution pack --dry-run` exits 0 — § Validation gates
- [ ] E8 Nothing was written to a tenant — [data-model-guide.md](data-model-guide.md) § Boundaries
- [ ] E9 Every Workflow step whose `**Data:**` line traverses a relationship is flagged as unbuildable until that field exists — § The two tiers

## F — Genome integration

- [ ] F1 A `## Data Model` section exists in the genome, with its stub line when no ontology bundle was given — [genome-format-guide.md](genome-format-guide.md) § Data Model
- [ ] F2 Each entity appears as a Platform Dependency row — § Platform Dependencies
- [ ] F3 Register rows with `locus: uipath, level: transition` produced a Business Rule and an acceptance criterion — [constraint-register-guide.md](constraint-register-guide.md) § What a verdict lands as
- [ ] F4 `check-genome.py --profile strict` passes — [data-model-guide.md](data-model-guide.md) § Validation gates
- [ ] F5 Open decisions were listed to the user with their defaults, and the deferred set named — § Closing the run

## Skill-build checklist

Tracked while the extension itself is authored. Not run at runtime.

- [x] S1 Router guide with discovery points — `data-model-guide.md`
- [x] S2 Input detection and the inventory contract — `ontology-sources-guide.md`
- [x] S3 Deterministic mapping rules — `entity-derivation-guide.md`
- [x] S4 Normalization rules and platform pruning — `normalization-guide.md`
- [x] S5 Non-determinism taxonomy and the register — `constraint-register-guide.md`
- [x] S6 Emission, resource shape, applier, gates — `datafabric-emission-guide.md`
- [x] S7 Deterministic tool: parse the three sources → inventory — `scripts/ontology-inspect.py`
- [x] S8 Deterministic tool: inventory → `entities.json` — `scripts/derive-entities.py`
- [x] S9 Deterministic tool: `entities.json` → solution resources — `scripts/apply-entities.py`
- [x] S10 `SKILL.md` Mode Detection recognises an ontology bundle
- [x] S11 `SKILL.md` § Read Plans rows for all six guides
- [x] S12 `SKILL.md` Critical Rule naming the subject and its home
- [x] S13 Subject rows in the skill's `CLAUDE.md`
- [x] S14 `## Data Model` section, stub line and population-matrix row in `genome-format-guide.md`
- [x] S15 `## Data Model` in both templates
- [ ] S16 `check-genome.py` grades the `## Data Model` section — *deferred: needs the section contract to settle on a real bundle first*
- [ ] S17 Task under `tests/tasks/uipath-genome/data_model/` — *deferred: write after S16*
- [ ] S18 Verify no native query-time join against a live tenant — *blocks the hop-cost rule in `normalization-guide.md` § Platform limits. Needs a tenant; not settled.*
- [x] S19 Verify `validate --local` accepts hand-authored complex fields — **FALSIFIED.** Probed against `uip` on a throwaway solution: a hand-authored `RELATIONSHIP` fails `FIELD_TYPE_NOT_ALLOWED — Field 'X' uses an unsupported type combination (Relationship / UNIQUEIDENTIFIER)`, and a hand-authored `CHOICE_SET_SINGLE` fails the same way (`ChoiceSetSingle / INT`). `uip df choice-sets` has no `--local` flag at all. The repo fixture that suggested otherwise is a test's `_setup` input and is never validated. **Design changed to the two tiers** — [datafabric-emission-guide.md § The two tiers](datafabric-emission-guide.md).
- [x] S20 Verify the real CLI resource shape against the spec — **done, spec corrected.** The CLI emits a far richer field object than the repo fixture (18 keys per field plus 5 reference keys on non-system fields), materializes the five system fields, adds `locks`/`files`/`EntityTypeId` to the envelope, sets `resource.key` equal to `resourceJson.Id`, writes the folder sentinel at entity level, and serializes `resourceJson` compactly in insertion order.
- [x] S21 CLI enhancement ask, scoped and written — `references/datafabric-cli-ask.md`
- [ ] S22 Enforcement-locus literature folded into the register — *iteration 3*
- [ ] S23 Worked example (OFN + SHACL + R2RML + process description) shipped as an asset — *iteration 3*
