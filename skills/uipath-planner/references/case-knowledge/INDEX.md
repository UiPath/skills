# Case Knowledge — shared single-source layer

Every cross-skill Case Management fact and rule lives here exactly once. `uipath-planner` owns this
directory on disk; `uipath-maestro-case` reaches the same files via `references/case-knowledge` (symlink —
identical content, no copy). Downstream references CITE rules by ID (e.g. `(K-STG-2)`), never restate them.
Restating a `K-*` rule outside this directory is a defect the knowledge lint rejects.

## Files

| File | Owns | ID prefix |
|---|---|---|
| [facts/types.yaml](facts/types.yaml) | Task/node/trigger/variable type enums, name-mapping table | `K-TYP` |
| [facts/pairing.yaml](facts/pairing.yaml) | Lifecycle gates: legal WHEN rules per slot, Marks-Complete pairing, exit types | `K-PAIR` |
| [facts/naming.yaml](facts/naming.yaml) | Display-name character rules, uniqueness scopes | `K-NAME` |
| [facts/sla.yaml](facts/sla.yaml) | SLA units/bounds, escalation fields, response model, breach/at-risk selector | `K-SLA` |
| [semantics/stages.md](semantics/stages.md) | Stage lifecycle, secondary stages, global events, case completion | `K-STG` |
| [semantics/sequencing.md](semantics/sequencing.md) | Task activation modes, sequential/parallel/adhoc grammar | `K-SEQ` |
| [semantics/edges-retired.md](semantics/edges-retired.md) | Edges retired; condition-only reachability | `K-EDGE` |
| [semantics/expressions.md](semantics/expressions.md) | Expression namespaces, conditionExpression scope | `K-EXPR` |
| [semantics/variables-io.md](semantics/variables-io.md) | Variables doctrine: task xref default, declare-vs-xref, outputs grammar | `K-VAR` |
| [contracts/sdd-contract.md](contracts/sdd-contract.md) | What a build-ready `sdd.md` contains; receipt check | `K-SDD` |
| [contracts/handoff.md](contracts/handoff.md) | The design-handoff protocol between the two skills | `K-HOF` |
| [contracts/resolution-ledger.md](contracts/resolution-ledger.md) | `registry-resolved.json` / resolution-ledger entry shape | `K-LEDG` |
| [errors/validate-codes.md](errors/validate-codes.md) | Verified `uip maestro case validate` failures → cause → fix | `K-ERR` |

## Conventions

1. One rule = one ID = one definition. Definitions are marked `**[K-XXX-n]**` (YAML: the `id` key).
2. Version- or behavior-sensitive claims carry `(as of <version/date>)` anchors. Expired anchor = re-verify,
   not false. Probe evidence: `docs/case-knowledge-ledger.md` (repo root).
3. Authority order for corrections: `uip maestro case validate` behavior (`@uipath/case-schema`) >
   PO.Frontend source > CLI local types. The CLI's authoring subcommand allow-lists lag the v27 schema.
4. Consumers: planner design files cite design-relevant IDs; maestro-case phase/plugin files cite
   emit-relevant IDs. Both audit scripts (`audit_sdd.py`, `audit_plan.py`) read `facts/*.yaml` directly.

<!-- END: INDEX.md -->
