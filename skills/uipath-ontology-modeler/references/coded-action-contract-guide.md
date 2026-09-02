# Coded Action Contract

A coded action is a write operation whose new values are computed by a job at invoke time instead of being spelled out as SQL ahead of time. The action definition still lives in the ontology as a W3C FnO TTL artifact; what changes is that `ont:statements` names a job rather than carrying the SQL, and the platform compiles the edits the job returns into single-row writes.

Use this guide when the classification rubric returns CODED for an operation, and [`action-table-contract-guide.md`](action-table-contract-guide.md) when it returns SQL.

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
| Which Orchestrator release holds the job? | `ont:process` + `ont:processFolderId` | Process name is `PascalCase(actionName) + "Process"`; the folder id is written as `"PENDING_DEPLOY"` at generation time |
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
| Process | `ont:process "{value}"` + `ont:processFolderId "PENDING_DEPLOY"` | Derive the value as `PascalCase(Name) + "Process"` when the PDD leaves it blank. The folder id is always the placeholder at generation time |
| Description | `rdfs:comment` on the action node | Use value directly; ensure it covers scope, the multi-row case, and the no-op branch |

## Generated TTL structure

**Two prefixes required.** `ont:` = platform namespace (`https://ontology.uipath.com/ont#`), carrying every platform predicate: `kind`, `language`, `statements`, `reads`, `bindsTo`, `statement`, `writes`, `process`, `processFolderId`, `paramName`, `paramType`, `paramMultiple`, `required`, and the `ont:Read` class. A separate `{ns}:` prefix carries the ontology's own terms: the action node and its read, param, and output nodes. The parser resolves platform predicates by full URI, so the wrong namespace silently drops the action.

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
        ont:language        "IMPERATIVE" ;
        ont:statements      ( "func:{name}({arg1}, {arg2})" ) ;
        ont:reads           ( {ns}:read.{name}.{bind1} ) ;
        ont:writes          "{Entity}.{field1}", "{Entity}.{field2}" ;
        ont:process         "{PascalCaseName}Process" ;
        ont:processFolderId "PENDING_DEPLOY" ;
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

- `ont:language "IMPERATIVE"` is the wire value the backend parser matches. It is the one place the old word survives; everywhere else the feature is called coded actions.
- `ont:statements` holds exactly one marker, `func:{name}(arg1, arg2)`. It is the job's whole input signature: nothing it does not name reaches the job. Marker arguments resolve by name, never by position. Each argument must match either a declared `fno:expects` param (the caller supplies it) or a read's `ont:bindsTo` (the platform runs that read and supplies the rows). A param consumed only inside a read's WHERE clause is legal and simply never reaches the job.
- `ont:reads` is an RDF list, written `( ... )`, of read nodes. So are `ont:statements`, `fno:expects`, and `fno:returns`.
- `ont:writes` is repeated triples, `ont:writes "A.x", "A.y" ;`, and never a list. `ont:writes ( "A.x" "A.y" )` parses as a list node, and the runtime then sees zero writable targets.
- `ont:process` names the Orchestrator release, matched on Name or ProcessKey and never on version.
- `ont:processFolderId` is the numeric Orchestrator folder id. Generation always writes the placeholder `"PENDING_DEPLOY"`; the deploy skill patches the real id in after the job is published.
- `fno:returns` is constant across every coded action: one output node with paramName `rowsAffected`, paramType `xsd:integer`, required true. It does not vary with what the action writes.

## Job contract

This section holds what is true of a coded-action job in any language.

The job's input mirrors the marker exactly. The SDK validates the incoming payload with `additionalProperties: false`, so a renamed, dropped, or extra field faults the job before the handler body runs, and no user log line appears to explain it. Marker drift is therefore a deploy-time failure with a silent-looking symptom, which is why the contract check compares the marker against the job's declared input.

Reads are `SELECT *`, and the rows arrive carrying the source's physical column names rather than the ontology's logical field names. The two can diverge outright when a federated entity renames a column. The row type therefore needs an escape hatch for the columns the job did not declare, and adapting physical names to logical ones is the job's work, not the SQL's.

Edits go back in logical ontology field names. An edit is `{ op: CREATE | UPDATE | DELETE, entity, properties }`, and `properties` carries the primary key under `id` for every op, creates included: ids are client-generated and the platform never assigns keys. The job's output is `{ edits }`. Zero edits is a first-class outcome, a no-op, and is distinct from a refusal: `rowsAffected` 0 with no failed step means the action ran and decided nothing needed changing.

The default idiom is to write absolute values and to include a no-op branch: compute the target state, return no edits when that state already holds, and return the absolute value otherwise. This makes the action idempotent under repeat invocation, which matters because the runtime's write shapes are bounded and permanent: `INSERT (cols) VALUES (literals)`, `UPDATE SET col = literal WHERE pk = literal`, and `DELETE WHERE pk = literal`. There is no read-modify-write in the generated SQL, so every increment has to be resolved inside the job. A batch of N edits compiles to N statements and N steps.

The job makes no network calls, reads no database, and holds no credentials. Input in, edits out.

## Supported languages: TypeScript

TypeScript is currently the only supported language for coded-action jobs. Contracts are declared with zod: `uip functions pack` compiles a zod schema into the JSON Schema the platform validates against, and zod is the only contract idiom the CLI packer can lower.

```typescript
import { defineFunction } from '@uipath/coded-functions-js-sdk';
import { z } from 'zod';

const {Entity}Row = z.object({
  // physical column names, exactly as the read's SELECT * returns them
}).passthrough();

const Input = z.object({
  {p1}: z.string(),
  {bind1}: z.array({Entity}Row),
}).strict();

const DeclaredEdit = z.object({
  op: z.enum(['CREATE', 'UPDATE', 'DELETE']),
  entity: z.string(),
  properties: z.record(z.string(), z.unknown()),
}).strict();

const Output = z.object({
  edits: z.array(DeclaredEdit),
}).strict();

type Input = z.infer<typeof Input>;
type DeclaredEdit = z.infer<typeof DeclaredEdit>;
type Output = z.infer<typeof Output>;

export default defineFunction({
  name: '{actionName}',
  description: '{one sentence, mirrors the action rdfs:comment}',
  method: 'POST',
  path: '/{actionName}',
  input: Input,
  output: Output,
  handler: async (input) => { /* ... */ },
});
```

The `Input` schema is the TypeScript restatement of the marker: its top-level keys must name exactly the marker's arguments. Derive the static types from the schemas with `z.infer`; do not maintain a parallel set of interfaces.

**Strictness is load-bearing, and it points in two directions.** The top-level `Input` object must carry `.strict()`: that is what emits `additionalProperties: false` into the packed schema, and that flag is what faults a drifted, renamed, or extra input field before the handler runs. A bare `z.object()` packs without it (verified both ways), and the drift guard silently disappears. Row objects are the opposite case: reads are `SELECT *`, so rows carry arbitrary extra physical columns, and those columns are legal. A row schema therefore ends with `.passthrough()`, which admits undeclared keys, while the `Input` object containing the row array stays `.strict()`. Strict at the top is the drift detection; passthrough on rows is what makes the extra columns legal.

Build edits through an annotated array, not an inline object literal:

```typescript
const edits: DeclaredEdit[] = [{ op: 'UPDATE', entity: 'Ticket', properties }];
return { edits };
```

Returning an edit as an inline literal widens `op` from the `'UPDATE'` literal type to `string`, which then fails the typecheck against `Output`. The annotation on the `const` pins the literal type.

### Where the job lives, and what it depends on

Generation writes the job to `{workdir}/jobs/{actionName}.ts`, beside the artifacts. At deploy time the deploy skill stages it to `<Project>/functions/{actionName}.ts` inside the Solution project: `uip functions pack` discovers jobs by scanning the project's `functions/` directory, and a source file anywhere else is invisible to it. `zod` and `@uipath/coded-functions-js-sdk` are dependencies of that project, and the `@uipath` npm scope resolves from GitHub Packages, not npmjs; the deploy skill's scaffold owns the project's `.npmrc`, so generation declares nothing about registries.

Typechecking is the `typecheck` gate of `tools/coded_action_preflight.py`, which compiles the job against a stub of the SDK. The job imports `zod` for real, so the gate is skipped with a reason when zod is not resolvable near the workdir.

### type<T>(), the idiom generation must not emit

The SDK also offers `input: type<Input>()` / `output: type<Output>()` over plain interfaces. That idiom packs only in Studio Web: `uip functions pack` cannot lower it to a JSON Schema on any tested SDK version (0.4.4, 0.5.0, 0.6.4) and refuses with `A function declares a type<T>() contract that was not lowered to a JSON Schema`. It exists and is recognized when found in existing sources, but it is never what generation produces.

## Validation rules

Resolve every entity and field against the local `{name}.ofn` schema. No live service is involved at generation time.

1. Every entity named in a read's `{{Entity}}` template, and every entity a job edit targets, must match a `Declaration(Class(:...))` in `{name}.ofn`.
2. Every field reference, in a read's WHERE clause and in each `ont:writes` value, must match a `Declaration(DataProperty(:Entity.field))` in `{name}.ofn`.
3. Every logical field name the job puts in an edit's `properties`, other than `id`, must match a declared DataProperty on that edit's entity and must appear in `ont:writes`.
4. Every marker argument must resolve by name to either a declared `fno:expects` param or a read's `ont:bindsTo`. An argument matching neither is a contract break.
5. Every read's `ont:bindsTo` value must appear as a marker argument, otherwise the read runs and its rows go nowhere.
6. Every `:paramName` used in a read's SQL must be a declared `fno:expects` param. The reverse does not hold: a param consumed only by a read is legal and never reaches the job.
7. Input types must match the field's XSD type from `{name}.ofn`. A multi-valued input declares `ont:paramMultiple true` and binds with `IN :param`.
8. `ont:writes` must be repeated triples, never an RDF list.
9. `ont:statements` must hold exactly one `func:` marker.
10. `ont:language` must be the literal `"IMPERATIVE"`, and `ont:kind` the literal `"ACTION"`.
11. `ont:process` must be present, and `ont:processFolderId` must be `"PENDING_DEPLOY"` in a generated artifact.
12. `fno:returns` with the `rowsAffected` output is mandatory and constant.
13. Param/output nodes use `ont:paramName`/`ont:paramType`/`ont:required`, resolved via the shared platform `ont:` namespace (`https://ontology.uipath.com/ont#`).

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
| A real folder id in a generated artifact | `ont:processFolderId "PENDING_DEPLOY"`; the deploy skill patches it |
| `ont:language "SQL"` on a coded action | `ont:language "IMPERATIVE"` |
| `type<T>()` contract in a generated job | zod schemas; `uip functions pack` cannot lower `type<T>()` |
| Bare `z.object()` for the input schema | `.strict()` on the top-level `Input` object; without it `additionalProperties: false` is lost from the packed schema |
| Row schema without `.passthrough()` | End row objects with `.passthrough()`; reads are `SELECT *` and rows carry undeclared physical columns |
| Edits returned as inline object literals | Build them through `const edits: DeclaredEdit[] = [...]` |
| Deriving a value from a caller parameter that the data already holds | Read it, then compute; a caller can lie about any fact concerning the data |
| Omitting `id` from a CREATE edit's properties | Every op carries the primary key; the platform never assigns keys |
