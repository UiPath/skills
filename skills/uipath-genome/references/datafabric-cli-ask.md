# Data Fabric CLI Ask — what would let the complex tier ship in the solution

A scoped request against `uip df`, written from what this extension measured rather
than from what its docs say. Not a design for the CLI; a statement of the gap, the
evidence, and the smallest interface that closes it.

Owner: the `uip` CLI, not this skill. This file exists so the ask is precise and so
[datafabric-emission-guide.md](datafabric-emission-guide.md) can be collapsed in one
edit when the gap closes.

## The gap

An ontology produces three kinds of field. Two of them cannot ship inside a solution.

| Field kind | Local authoring | Consequence here |
|---|---|---|
| scalar (`STRING`, `DECIMAL`, `BOOLEAN`, `DATE`, `DATETIME_WITH_TZ`, …) | `uip df entities create --local` | ships in the solution; becomes a table at deploy |
| `RELATIONSHIP` | **none** | an open item the engineer runs post-deploy |
| `CHOICE_SET_SINGLE` / `_MULTIPLE` | **none**, and the choice set itself has no local form | two open items: create the set, then add the field |

For a typical domain ontology this is most of the structure. Every `owl:ObjectProperty`
becomes a relationship and every `sh:in` becomes a choice set, so a model with ten
classes and a dozen associations ships as ten tables and two dozen manual steps.

## Evidence

Measured against the installed CLI on a throwaway solution, not inferred.

**1 · The CLI refuses the types on create.** Documented, and consistent with the
`--local` help.

**2 · Hand-authoring them into the resource file does not work either.** Appending a
field object to `spec.resourceJson` in exactly the shape the CLI itself writes, then
validating:

```
$ uip df entities validate --local --output json
FIELD_TYPE_NOT_ALLOWED  Field 'Supplier' uses an unsupported type combination
                        (Relationship / UNIQUEIDENTIFIER).
FIELD_TYPE_NOT_ALLOWED  Field 'Tier' uses an unsupported type combination
                        (ChoiceSetSingle / INT).
```

So the restriction is in the validator, not only in the create path — which is the
right place for it, and which is why this is an ask rather than a workaround.

**3 · Choice sets have no local representation at all.** `uip df choice-sets create`
takes `--folder-key` but no `--local`, so even a validating field would have nothing
in the solution to point at.

**4 · The blocker is identity, not capability.** Both field kinds need a UUID that
only exists after the target object is created on a tenant — `referenceEntityId`,
`referenceFieldId`, `choiceSetId`. A solution on disk has no tenant, so there is no
id to write. That is the whole of the problem.

## What already solves the same problem elsewhere

The CLI has an answer to "an id that does not exist yet": the **unassigned-folder
sentinel** `99999999-9999-9999-9999-999999999999`, written into `resourceJson.FolderId`
for every locally authored entity and replaced at deploy. The deploy already resolves
a placeholder into a real id.

The resource format also already carries symbolic names beside ids —
`ReferenceEntity` is `{Name, Id, FolderId}`, not a bare id — and solution resources
are already linked by `{kind, name}` in `resource.dependencies`, which is how a
locally authored resource refers to a sibling today.

So the mechanism exists. What is missing is permission to use it for these two field
kinds.

## The ask

**A · A local form for choice sets.**

```
uip df choice-sets create <Name> --local [--project-name <P>]
uip df choice-set-values create <Name> <Value> --local [--project-name <P>]
uip df choice-sets list|get|delete --local
```

Writes `resources/solution_folder/choiceSet/<Name>.json`, assigning `NumberId`
0-based in creation order — the same contract the tenant path has, with the author
holding the pen. Deploy creates the set and the numbers travel with it.

**B · Symbolic references on a local entity.** Accept, on `entities create --local`
and `entities update --local`, a reference by **name** where the tenant path takes a
UUID:

```jsonc
{"name": "Supplier",  "type": "RELATIONSHIP",
 "referenceEntityName": "Supplier",            // instead of referenceEntityId
 "referenceFieldName":  "SupplierNumber"}      // instead of referenceFieldId

{"name": "Tier", "type": "CHOICE_SET_SINGLE",
 "choiceSetName": "SupplierTier"}              // instead of choiceSetId
```

Resolution is solution-local and total: entity names are already solution-wide
unique, and `resource.dependencies` already expresses the ordering. Deploy resolves
each name to the id it just minted, exactly as it already resolves the folder
sentinel.

**C · The validator follows.** `validate --local` accepts the two type combinations
**when** the reference is symbolic and names a sibling resource in the same solution,
and gains two diagnostics rather than losing one:

| Code | When |
|---|---|
| `REFERENCE_NOT_IN_SOLUTION` | `referenceEntityName` / `choiceSetName` names nothing the solution authors |
| `REFERENCE_FIELD_NOT_FOUND` | `referenceFieldName` is not a field of the named entity |

A reference carrying a raw UUID on a local entity stays refused — that is a tenant
id in a document that has no tenant, and it is the thing worth keeping out.

**D · Cycles.** Symbolic references make a solution-level dependency graph, so
`validate --local` should reject a cycle among authored entities, naming its members.
This extension already refuses to emit one; the CLI is the right place to enforce it
for every author.

## Scope

| In | Out |
|---|---|
| `RELATIONSHIP`, `CHOICE_SET_SINGLE`, `CHOICE_SET_MULTIPLE` on local entities | federated entities — they need a live connection by definition |
| choice sets and their values, locally | `referenceFolderKey` — a local entity has no folder until deploy |
| name-based resolution within one solution | cross-solution references |

## What changes here when it lands

`entities.json` already carries `relationships` and `choiceSetFields` with symbolic
targets, because the model was derived before the limit was known. So:

1. `apply-entities.py` emits them in pass 1's body and drops pass 3;
2. `datafabric-emission-guide.md` § The two tiers collapses to one;
3. the checklist's E4, E5 and E9 go;
4. nothing in the derivation, the register or the normalization rules changes.

That is the test of whether this ask is scoped right: the extension's model is
already in the shape the CLI would need, so closing the gap deletes code here rather
than adding it.
