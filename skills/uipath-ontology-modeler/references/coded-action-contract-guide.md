# Coded Action Contract

A coded action is a write operation whose new values are computed by a job at invoke time instead of being spelled out as SQL ahead of time. The action definition still lives in the ontology as a W3C FnO TTL artifact; what changes is that `ont:statements` names a job rather than carrying the SQL, and the platform compiles the edits the job returns into single-row writes.

**[`action-table-contract-guide.md`](action-table-contract-guide.md) is the base contract and this
is the delta.** Its envelope, type mapping and validation rules all hold; what follows is only what
a coded action adds. Use the base alone when the rubric returns SQL.

Each coded action pairs two files: the TTL definition `{name}-{actionName}.ttl` and the job source `{workdir}/jobs/{actionName}.ts`. They are one contract in two places, and the contract check compares them.

## What the skill needs to know

| Question | TTL construct | Notes |
|---|---|---|
| What's the mutation called? | `{ns}:{camelCaseVerb}` + file `{ontology}-{name}.ttl` | Verb phrase describing what changes (e.g. `tagOverdueTicket`, not `ticketTagger` or `action2`) |
| Which job runs it? | `ont:statements ( "func:{name}(args)" )` | Exactly one marker; the marker is the job's whole input signature |
| Which entities are involved? | `{{Entity}}` in each read's `ont:statement`, plus the entity names the job puts on each edit | Every one must match a `Declaration(Class(:...))` in `{name}.ofn`. Reading one entity and writing another is normal for a coded action |
| What data must the job see before it decides? | `ont:reads` list of `{ns}:read.{name}.{bind}` nodes | One node per bind; each carries `ont:bindsTo` and a `SELECT *` `ont:statement` |
| Which fields can the job ever write? | `ont:writes`, repeated triples | The union over every branch, not the fields one run happens to touch. See the ont:writes declaration section |
| How is a written row identified? | `id` in each edit's `properties` | The job returns the primary key on every edit, creates included; the platform builds the WHERE clause from it |
| What inputs does the caller provide? | `fno:expects` list + `{ns}:param.*` blocks | Only facts the caller legitimately owns. Facts about stored data come from reads |
| Which Orchestrator release holds the job? | `ont:process` | `PascalCase(actionName) + "Process"`. Nothing about where it is deployed belongs in the artifact |
| What runtime computes it? | `ont:processType "CODED_FUNCTION"` | Required whenever `ont:language` is `"CODED"`. One value today; naming it means a second runtime later needs no migration |
| What does an AI agent need to know to pick this action? | `rdfs:comment` on the action node | What it changes, how many rows, the branch that writes nothing, when to use it over alternatives |

## PDD table format (when structured)

The PDD may use this table format for a coded operation. When it does, map fields to the semantic questions above. When the PDD uses prose instead, extract the same concepts from the description.

```
Coded action: {Human-readable title}
┌──────────────┬────────────────────────────────────────────────────┐
│ Name         │ {camelCase action name}                            │
│ Entities     │ {classes read and written, comma-separated}        │
│ Rules        │ {prose statement of the decision logic}            │
│ Reads        │ {bindName: SELECT statement}, one per line         │
│ Writes       │ {Entity.field, ... union over every branch}        │
│ Identifier   │ {PK field of each written entity}                  │
│ Inputs       │ {name (type, required), ...}                       │
│ Process      │ {PascalCase(Name) + "Process"}                     │
│ Description  │ {what it does, used by AI agents}                  │
└──────────────┴────────────────────────────────────────────────────┘
```

**Deterministic shortcut:** When the PDD uses the structured 9-row table, map fields directly, skip inference. The semantic questions above are for prose or non-standard formats.

| PDD Field | TTL construct | Notes |
|---|---|---|
| Name | `{ns}:{value}` + file `{ontology}-{value}.ttl` | Use value directly as action identity; also the `func:` marker name and the job filename `jobs/{value}.ts` |
| Entities | `{{value}}` in each read's SQL, and the `entity` on each edit the job returns | Every value must match a class in `{name}.ofn`, never real table names. More than one entity is legal here |
| Rules | Job source, plus `rdfs:comment` on the action node | The rules are the job's body; the TTL only summarizes them for callers |
| Reads | `ont:reads ( {ns}:read.{name}.{bind} ... )`, each node carrying `ont:bindsTo "{bind}"` and `ont:statement "SELECT * FROM {{Entity}} WHERE ..."` | Every bind name must also appear as an argument in the `func:` marker, otherwise the rows never reach the job |
| Writes | `ont:writes "{Entity.field}", ...` as repeated triples | Union over every branch. Each `{Entity.field}` must match a DataProperty in `{name}.ofn` |
| Identifier | The `id` key in each edit's `properties` | Not a separate TTL construct; the job supplies it, and it is exempt from `ont:writes` |
| Inputs | `fno:expects` list + `{ns}:param.*` blocks | Types derived from the field's XSD type in `{name}.ofn`. A multi-valued input adds `ont:paramMultiple true` and binds with `IN :param` in the read |
| Process | `ont:process "{value}"` | Derive as `PascalCase(Name) + "Process"` when the PDD leaves it blank |
| Process type | `ont:processType "CODED_FUNCTION"` | Constant today, and required |
| Description | `rdfs:comment` on the action node | Use value directly; ensure it covers scope, the multi-row case, and the no-op branch |

## Generated TTL structure

**The two-prefix rule is the base guide's, unchanged** — platform predicates resolve by full URI, so the wrong namespace silently drops the action. A coded action adds six platform predicates (`reads`, `bindsTo`, `statement`, `writes`, `process`, `processType`) and the `ont:Read` class, and adds read nodes to the `{ns}:` terms.

`func:` in the marker is not a declared prefix. The marker is app-level syntax matched by regex inside the string literal, and no `@prefix func:` line belongs in the file.

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix {ns}:  <https://ontology.uipath.com/{ontology-name}#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

{ns}:{name}
        a                   fno:Function ;
        rdfs:label          "{Action title}" ;
        rdfs:comment        "{What it changes, how many rows, the branch that writes nothing, when to use it.}" ;
        ont:kind            "ACTION" ;
        ont:language        "CODED" ;
        ont:processType     "CODED_FUNCTION" ;
        ont:statements      ( "func:{name}({arg1}, {arg2})" ) ;
        ont:reads           ( {ns}:read.{name}.{bind1} ) ;
        ont:writes          "{Entity}.{field1}", "{Entity}.{field2}" ;
        ont:process         "{PascalCaseName}Process" ;
        fno:expects         ( {ns}:param.{name}.{p1} ) ;
        fno:returns         ( {ns}:out.{name}.rowsAffected ) .

{ns}:read.{name}.{bind1}
        a              ont:Read ;
        ont:bindsTo    "{bind1}" ;
        ont:statement  "SELECT * FROM {{Entity}} WHERE {{Entity.keyField}} = :{p1}" .

{ns}:param.{name}.{p1}
        a              fno:Parameter ;
        ont:paramName  "{p1}" ;
        ont:paramType  "xsd:{type}" ;
        rdfs:comment   "{What the caller supplies, and why the job cannot derive it from a read.}" ;
        ont:required   true .

{ns}:out.{name}.rowsAffected
        a              fno:Output ;
        ont:paramName  "rowsAffected" ;
        ont:paramType  "xsd:integer" ;
        ont:required   true .
```

Construct-by-construct:

- `ont:language "CODED"` is the wire value the backend parser matches. There is no alias: the service refuses anything else for a job-computed action.
- `ont:processType "CODED_FUNCTION"` names the runtime that computes the edits, and is **required** whenever the language is `"CODED"`. `ont:language` says only that a job computes them; this says what kind of job. Absent on declarative (SQL) actions.
- `ont:statements` holds exactly one marker, `func:{name}(arg1, arg2)`. It is the job's whole input signature: nothing it does not name reaches the job. Marker arguments resolve by name, never by position. Each argument must match either a declared `fno:expects` param (the caller supplies it) or a read's `ont:bindsTo` (the platform runs that read and supplies the rows). A param consumed only inside a read's WHERE clause is legal and simply never reaches the job.
- `ont:reads` is an RDF list, written `( ... )`, of read nodes. So are `ont:statements`, `fno:expects`, and `fno:returns`.
- `ont:writes` is repeated triples, `ont:writes "A.x", "A.y" ;`, and never a list. `ont:writes ( "A.x" "A.y" )` parses as a list node, and the runtime then sees zero writable targets.
- `ont:process` names the Orchestrator release, matched on Name or ProcessKey and never on version. **Nothing in the artifact says where that release is deployed.** The folder follows from the ontology at invoke time, so a portable artifact carries no tenant coordinate and survives a re-release unchanged.
- `fno:returns` is constant across every coded action: one output node with paramName `rowsAffected`, paramType `xsd:integer`, required true. It does not vary with what the action writes.

## Job contract

This section holds what is true of a coded-action job in any language.

The job's input mirrors the marker exactly. The SDK validates the incoming payload with `additionalProperties: false`, so a renamed, dropped, or extra field faults the job before the handler body runs, and no user log line appears to explain it. Marker drift is therefore a deploy-time failure with a silent-looking symptom, which is why the contract check compares the marker against the job's declared input.

Reads are `SELECT *`, and the rows arrive carrying the source's physical column names rather than the ontology's logical field names. The two can diverge outright when a federated entity renames a column. The row type therefore needs an escape hatch for the columns the job did not declare, and adapting physical names to logical ones is the job's work, not the SQL's.

Edits go back in logical ontology field names. An edit is `{ op: CREATE | UPDATE | DELETE, entity, properties }`, and `properties` carries the primary key under `id` for every op, creates included: ids are client-generated and the platform never assigns keys. The job's output is `{ edits }`. Zero edits is a first-class outcome, a no-op, and is distinct from a refusal: `rowsAffected` 0 with no failed step means the action ran and decided nothing needed changing.

The default idiom is to write absolute values and to include a no-op branch: compute the target state, return no edits when that state already holds, and return the absolute value otherwise. This makes the action idempotent under repeat invocation, which matters because the runtime's write shapes are bounded and permanent: `INSERT (cols) VALUES (literals)`, `UPDATE SET col = literal WHERE pk = literal`, and `DELETE WHERE pk = literal`. There is no read-modify-write in the generated SQL, so every increment has to be resolved inside the job. A batch of N edits compiles to N statements and N steps.

The job makes no network calls, reads no database, and holds no credentials. Input in, edits out.

## Supported languages: TypeScript

TypeScript is currently the only supported language for coded-action jobs. Contracts are declared as plain interfaces behind the SDK's `type<T>()` marker, which is what the verified jobs use.

```typescript
import { defineFunction, type } from '@uipath/coded-functions-js-sdk';

interface {Entity}Row {
  // Physical column names, and every one OPTIONAL. See below: a required row field is rejected
  // before the handler runs if the read spells the column differently.
  {PhysicalColumn}?: string;
  [column: string]: unknown;
}

interface Input {
  {p1}: string;
  {bind1}: {Entity}Row[];
}

interface DeclaredEdit {
  op: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: string;
  properties: Record<string, unknown>;
}

interface Output {
  edits: DeclaredEdit[];
}

export default defineFunction({
  name: '{actionName}',
  description: '{one sentence, mirrors the action rdfs:comment}',
  method: 'POST',
  path: '/{actionName}',
  input: type<Input>(),
  output: type<Output>(),
  handler: async (input) => { /* ... */ },
});
```

`Input` is the TypeScript restatement of the marker: its top-level keys must name exactly the marker's arguments.

**`type<T>()` is inert on its own, and something has to lower it.** The marker carries no runtime schema; the JSON Schema the platform validates against lives in the project's `entry-points.json`. Studio Web's packer derives that file from the interfaces, and `uip functions pack` cannot (it refuses with `A function declares a type<T>() contract that was not lowered to a JSON Schema`, on every tested SDK version). So the deploy skill derives it instead, with `tools/entry_points.py`, whose output is byte-identical to Studio Web's for both verified jobs. `uip solution pack` reads no TypeScript, so the derived manifest alongside the job is all it needs. **The interfaces are therefore the contract, and the manifest is generated from them on every stage** rather than being written by hand.

**The interfaces must stay inside the grammar the deriver can lower**: `string`, `number`, `boolean`, a union of string literals, `Record<string, unknown>`, an array of any of those, or another interface declared in the same file. Anything else (a `Date`, an inline object type, a generic, an undeclared name, a recursive interface) is refused rather than approximated, because a manifest that disagrees with the interfaces faults the job before its handler runs. `coded_action_preflight.py` runs the deriver as its `input-strictness` gate, so an unlowerable contract fails at authoring time instead of at pack time.

**Every field on a row interface is OPTIONAL — `Tags?: string`, never `Tags: string`.** This is the
one rule here learned by breaking it against a live tenant. A required field becomes `required` in
the derived manifest, the platform validates the job's input against that manifest *before the
handler runs*, and a `SELECT *` read's physical column spelling is not knowable at authoring time:
the same entity answered `Tags` through the Data Fabric records API and its schema field name
through the ontology's own read. So a required row field is a guess, and a wrong guess faults the
job with no log line of yours ever appearing:

```
ErrorCode: JsCodedFunction.ValidationFailed
Info:      Input validation failed
           ticket.0.Tags: must have required property 'Tags'
```

Optional keeps the documentation — the manifest still lists the properties, so a reader sees the
shape the job expects — while letting a differently-spelled column arrive as `undefined` instead of
a rejection. Then pick columns in the handler, tolerating the spellings one might arrive under:

```typescript
function column(row: {Entity}Row, ...names: string[]): string {
  for (const name of names) {
    const value = row[name];
    if (value !== undefined && value !== null) return String(value);
  }
  return '';
}

const due = Date.parse(column(row, 'DueAt', 'dueAt'));
```

A field the job genuinely cannot proceed without is checked in the handler, where the failure can
say which column was missing and what the row did carry. That is a diagnosable error; a manifest
rejection is not.

**The index signature is load-bearing, and it points in two directions.** A row interface ends with `[column: string]: unknown`, which lowers to a permissive `additionalProperties` on that object: reads are `SELECT *`, so rows carry arbitrary extra physical columns, and those columns are legal. `Input` itself has no index signature, and lowers to `additionalProperties: false`, which is what faults a drifted, renamed, or extra input field before the handler runs. Open on rows makes the extra columns legal; closed at the top is the drift detection.

Build edits through an annotated array, not an inline object literal:

```typescript
const edits: DeclaredEdit[] = [{ op: 'UPDATE', entity: 'Ticket', properties }];
return { edits };
```

Returning an edit as an inline literal widens `op` from the `'UPDATE'` literal type to `string`, which then fails the typecheck against `Output`. The annotation on the `const` pins the literal type.

### Where the job lives, and what it depends on

Generation writes the job to `{workdir}/jobs/{actionName}.ts`, beside the artifacts. At deploy time the deploy skill stages it as the Solution project's root `main.ts`, which is the layout the verified export shipped and what `uipath.json`'s functions map and the derived manifest's `filePath: content/main.ts` both name. `@uipath/coded-functions-js-sdk` is a devDependency of that project, for local typechecking only: `type<T>()` is erased at compile time and `defineFunction` is supplied by the runtime, so nothing in the deploy path installs it. The `@uipath` npm scope resolves from GitHub Packages rather than npmjs, but nothing in the deploy path installs it and staging strips any `.npmrc` it finds, so generation declares nothing about registries.

Typechecking is the `typecheck` gate of `tools/coded_action_preflight.py`, which compiles the job against a stub of the SDK, and is skipped with a reason when no TypeScript compiler is reachable. The job imports nothing beyond the SDK, so no package needs installing for the gate to run.

### The idiom this pipeline refuses

The SDK also accepts a Standard Schema (zod, arktype, valibot) or a JSON Schema literal in place of the marker. Such a contract carries its own schema and needs nothing derived, which is exactly why this pipeline cannot deploy it: what gets staged is a manifest derived from the interfaces, and only `type<T>()` can be lowered. A Standard-Schema contract has no interfaces to read, so nothing can be derived and there is no manifest to stage.

`coded_action_preflight.py` fails `input-strictness` for such a job and names both the library and the consequence. Do not work around it by hand-writing an `entry-points.json`: a manifest that disagrees with the job faults it before the handler runs, which is harder to diagnose than the refusal.

## Validation rules

**Every base-guide rule applies**, including input types matching the field's XSD type, the
mandatory `fno:returns` `rowsAffected`, and param/output nodes resolving through the platform `ont:`
namespace. Resolve every entity and field against the local `{name}.ofn` schema; no live service is
involved at generation time. Rules 1 and 2 widen because a coded action is not single-entity, and
the rest are additions:

1. Every entity named in a read's `{{Entity}}` template, and every entity a job edit targets, must match a `Declaration(Class(:...))` in `{name}.ofn`.
2. Every field reference, in a read's WHERE clause and in each `ont:writes` value, must match a `Declaration(DataProperty(:Entity.field))` in `{name}.ofn`.
3. Every logical field name the job puts in an edit's `properties`, other than `id`, must match a declared DataProperty on that edit's entity and must appear in `ont:writes`.
4. Every marker argument must resolve by name to either a declared `fno:expects` param or a read's `ont:bindsTo`. An argument matching neither is a contract break.
5. Every read's `ont:bindsTo` value must appear as a marker argument, otherwise the read runs and its rows go nowhere.
6. A multi-valued input declares `ont:paramMultiple true` and binds with `IN :param` in the read.
7. Every `:paramName` used in a read's SQL must be a declared `fno:expects` param. The reverse does not hold: a param consumed only by a read is legal and never reaches the job.
8. `ont:writes` must be repeated triples, never an RDF list.
9. `ont:statements` must hold exactly one `func:` marker.
10. `ont:language` must be the literal `"CODED"`, and `ont:kind` the literal `"ACTION"`.
11. `ont:process` must be present. `ont:processFolderId` and `ont:processUrl` are **not part of the vocabulary** and must not be emitted.
12. `ont:processType` must be present and must be `"CODED_FUNCTION"`.
13. **Every entity a job edit targets needs exactly one identity property** — a `{Class}.id` annotated `ont:datatype "key"` in `{name}.ofn`. That is a schema rule, which is why it lives in [`owl-patterns-guide.md`](owl-patterns-guide.md), but the `entity-identity-declared` gate fails the coded pair without it, and the runtime otherwise refuses every write *after* the job has run, reporting `rowsAffected: 0` — indistinguishable in a summary from a legitimate no-op.

## What a read can and cannot do

A read is one `SELECT` against one entity, run before the job starts. Three constraints close off
the route a generating agent will reach for first, and it is worth stating all three because each
one alone looks like it has a workaround:

1. **Reads all run before the job.** A parent's storage id is therefore unknown when a child read
   that would need it is issued. There is no chaining and no second round of reads.
2. **`{{Entity.field}}` resolves data properties only.** An object property is not addressable, so
   the foreign key cannot be named even though the column exists:
   `Template references unknown field: {Child}.{objectProperty}`.
3. **A read statement is scoped to one entity.** `IN` parses, but a cross-entity subquery fails
   with `Unable to validate SQL: … Object '{Parent}' not found`.

And an unbounded scan is refused outright: `Selecting all columns without a WHERE or LIMIT clause
is not supported` (`SQL_PARSING`).

So a child that can only be identified through its parent is read as
`SELECT * FROM {{Child}} LIMIT {n}` and filtered **inside the job**.

**A job reading at the limit must refuse rather than compute.** If the row count comes back equal to
the limit, the view may be truncated and any total derived from it is wrong. A short total written
confidently is worse than a failed invocation, so return no edits and say why:

```typescript
if (input.lines.length >= LIMIT) {
  throw new Error(`read hit the ${LIMIT}-row limit; refusing to compute from a possibly truncated view`);
}
```

## Values a write cannot carry

**No control characters.** A `\n`, `\t` or `\r` anywhere in a written value fails the whole
statement — `Parameter value contains illegal control character at position N` — and it fails
*after* the job has run. An append-style audit trail therefore joins with a visible separator:

```typescript
const notes = [existing, entry].filter(Boolean).join(" | ");   // not "\n"
```

## The ont:writes declaration

Instruct the generating agent in exactly these terms.

The declaration is the union over every branch the job could take, never a prediction of one run. An edit touching any (entity, field) pair outside it is refused whole at the 'Preparing write statement' step with `SQL_GUARD_REJECTED`, after the job has already run, with nothing written. Always declare the worst case: every field any code path can emit. Over-declaring is harmless; under-declaring fails closed at invoke time. `id` is exempt, because it targets the WHERE clause rather than a written column.

## Full worked examples

Complete pairs, `tagOverdueTicket` (single row, corrective no-op) and `flagBigOrder` (per-row loop, reads one entity and writes another, batch of N edits), are in [`coded-action-example.md`](coded-action-example.md). Read it only if a gate or contract check fails and you need a concrete reference to self-correct, or you judge the templates above are not enough to proceed confidently for this request.

## Common mistakes

| Mistake | Correct form |
|---|---|
| `ont:writes ( "A.x" "A.y" )` | Repeated triples: `ont:writes "A.x", "A.y" ;` |
| `ont:reads "..."` as a bare string | RDF list of `ont:Read` nodes: `ont:reads ( {ns}:read.{name}.{bind} )` |
| More than one `func:` marker in `ont:statements` | Exactly one marker; it is the whole input signature |
| Marker argument matching neither a param nor a bind | Every argument resolves by name to a `fno:expects` param or a read's `ont:bindsTo` |
| Declaring only the fields the happy path writes | Declare the union over every branch |
| Any deployment coordinate in the artifact | Neither `ont:processFolderId` nor `ont:processUrl` exists. The artifact names the release, never its folder |
| `ont:language "CODED"` with no `ont:processType` | Add `ont:processType "CODED_FUNCTION"`; the service refuses the action without it |
| `ont:language "SQL"` on a coded action | `ont:language "CODED"` |
| A type outside the lowerable grammar | keep to the grammar above; `tools/entry_points.py` refuses the rest, and it runs as a preflight gate |
| Edits returned as inline object literals | Build them through `const edits: DeclaredEdit[] = [...]` |
| Deriving a value from a caller parameter that the data already holds | Read it, then compute; a caller can lie about any fact concerning the data |
| Omitting `id` from a CREATE edit's properties | Every op carries the primary key; the platform never assigns keys |
