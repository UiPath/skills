# Coded Actions: Worked Examples

Read this only if a gate or contract check fails and you need a concrete reference, or you judge [`coded-action-contract-guide.md`](coded-action-contract-guide.md) alone is not enough for this request. These are full worked pairs, not templates to copy verbatim: the names, fields, and rules below are specific to the Support and Classification domains.

Both pairs were verified end to end against a real tenant, and the job listings below are those sources verbatim. Each shows a TTL definition and its job side by side, because the two are one contract. The contracts are plain interfaces behind the SDK's `type<T>()` marker; the JSON Schema the platform validates against is derived from those interfaces at deploy time by `tools/entry_points.py`.

---

## tagOverdueTicket (Support)

A single-row action with clock arithmetic, a corrective write, and a converged no-op. The caller supplies only the ticket id; every fact the rule turns on comes from the read.

### support-tagOverdueTicket.ttl

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix sup:   <https://ontology.uipath.com/support#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

sup:tagOverdueTicket
        a                   fno:Function ;
        rdfs:label          "Tag an overdue ticket" ;
        rdfs:comment        "Recomputes a ticket's due date from its priority (sev1 four hours, sev2 twenty hours, sev3 five days), correcting it if the stored value has fallen out of step, and adds TICKET_OVERDUE to its tags once that deadline has passed. Closed tickets are left alone, and a ticket with nothing to correct and nothing to tag is not written at all." ;
        ont:kind            "ACTION" ;
        ont:language        "CODED" ;
        ont:processType     "CODED_FUNCTION" ;
        ont:statements      ( "func:tagOverdueTicket(ticketId, ticket)" ) ;
        ont:reads           ( sup:read.tagOverdueTicket.ticket ) ;
        ont:writes          "Ticket.tags", "Ticket.dueAt" ;
        ont:process         "TagOverdueTicketProcess" ;
        fno:expects         ( sup:param.tagOverdueTicket.ticketId ) ;
        fno:returns         ( sup:out.tagOverdueTicket.rowsAffected ) .

sup:read.tagOverdueTicket.ticket
        a              ont:Read ;
        ont:bindsTo    "ticket" ;
        ont:statement  "SELECT * FROM {{Ticket}} WHERE {{Ticket.id}} = :ticketId" .

sup:param.tagOverdueTicket.ticketId
        a              fno:Parameter ;
        ont:paramName  "ticketId" ;
        ont:paramType  "xsd:string" ;
        rdfs:comment   "The ticket to check. The only thing the caller supplies: priority, age and existing tags are all read from the row." ;
        ont:required   true .

sup:out.tagOverdueTicket.rowsAffected
        a              fno:Output ;
        ont:paramName  "rowsAffected" ;
        ont:paramType  "xsd:integer" ;
        ont:required   true .
```

Why the notable lines look like this:

- `ont:statements ( "func:tagOverdueTicket(ticketId, ticket)" )` is the job's entire input signature. `ticketId` resolves to the declared param, `ticket` resolves to the read's `ont:bindsTo`. Nothing else reaches the job, and the arguments resolve by name rather than by position.
- `ont:reads` is a list containing one node; `ont:writes` on the next line is repeated triples. The two are written differently on purpose. `ont:writes ( "Ticket.tags" "Ticket.dueAt" )` would parse as a list node and the runtime would see zero writable targets.
- `ont:writes` names both fields even though most runs write at most one. `dueAt` is only written when the stored value has drifted, and `tags` only when the deadline has passed and the tag is absent. The declaration is the union over both branches.
- `ticketId` is the only `fno:expects` param because every other input to the decision (priority, creation time, existing tags) is a fact about stored data. A caller can lie about those, so they are read.
- `ont:processType "CODED_FUNCTION"` names the runtime that computes the edits, and is required whenever the language is `"CODED"`. The artifact carries no folder and no URL: where the release is deployed is a tenant fact, and the runtime resolves it from the ontology at invoke time.
- The `SELECT *` in the read is deliberate: it hands the job the whole row and keeps the SQL trivial, at the cost of the rows arriving under physical column names. The job absorbs that cost, in versioned TypeScript.

### jobs/tagOverdueTicket.ts

```typescript
import { defineFunction, type } from '@uipath/coded-functions-js-sdk';

interface TicketRow {
  TicketId?: string;
  TicketNumber?: string;
  Subject?: string;
  Sev?: string;
  Status?: string;
  CreatedAt?: string;
  DueAt?: string;
  Labels?: string;
  [column: string]: unknown;
}

interface Input {
  ticketId: string;
  ticket: TicketRow[];
}

interface DeclaredEdit {
  op: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: string;
  properties: Record<string, unknown>;
}

interface Output {
  edits: DeclaredEdit[];
}

const SLA_HOURS: Record<string, number> = {
  sev1: 4,
  sev2: 20,
  sev3: 120, // five days
};

const OVERDUE_TAG = 'TICKET_OVERDUE';
const HOUR_MS = 60 * 60 * 1000;

const iso = (ms: number) => new Date(ms).toISOString().slice(0, 19) + 'Z';

export default defineFunction({
  name: 'tagOverdueTicket',
  description:
    'Recomputes a ticket due date from its severity and appends TICKET_OVERDUE once that deadline has passed. Closed tickets are left alone.',
  method: 'POST',
  path: '/tagOverdueTicket',
  input: type<Input>(),
  output: type<Output>(),
  handler: async (input) => {
    const row = input.ticket[0];
    if (row.Status === 'closed') {
      return { edits: [] };
    }

    const dueAt = Date.parse(row.CreatedAt) + SLA_HOURS[row.Sev] * HOUR_MS;
    const properties: Record<string, unknown> = { id: input.ticketId };

    if (Date.parse(row.DueAt) !== dueAt) {
      properties.dueAt = iso(dueAt);
    }

    const tags = row.Labels.split(',').filter(Boolean);
    if (Date.now() > dueAt && !tags.includes(OVERDUE_TAG)) {
      properties.tags = [...tags, OVERDUE_TAG].join(',');
    }

    if (Object.keys(properties).length === 1) {
      return { edits: [] };
    }

    const edits: DeclaredEdit[] = [{ op: 'UPDATE', entity: 'Ticket', properties }];
    return { edits };
  },
});
```

Why the notable lines look like this:

- `Input` names `ticketId` and `ticket` as its fields, matching the marker exactly, and declares no index signature. It therefore lowers to `additionalProperties: false`, so a rename on either side faults the job before the handler body runs, with no user log line to explain it.
- `ticket` is `TicketRow[]`, an array, because a read returns rows. This action expects one, and `input.ticket[0]` takes it.
- `TicketRow` lists physical column names, not the ontology's logical field names. Two of them diverge outright: the federated entity exposes the logical `priority` as the column `Sev` and `tags` as `Labels`. The mapping reconciles the pair, and the edit the job returns is written in the logical names.
- `TicketRow` ends with `[column: string]: unknown` because `SELECT *` also carries extra physical columns the interface does not name, and those columns are legal. The index signature lowers to a permissive `additionalProperties` on the row object. It points in two directions on purpose: closed at the top-level `Input` is the drift detection, open on the row is what admits the columns the contract never promised to name.
- Both early returns produce `{ edits: [] }`. Zero edits is a first-class outcome: `rowsAffected` comes back 0 with no failed step, which is a no-op and not a refusal.
- `properties` starts holding only `id`, and the `Object.keys(properties).length === 1` test is how the job detects that neither branch added anything. `id` is always present because every edit carries the primary key, and it is exempt from `ont:writes` since it targets the WHERE clause.
- The writes are absolute values (`iso(dueAt)`, the whole recomputed tag string), never increments. The runtime's generated SQL is `UPDATE SET col = literal WHERE pk = literal` with no read-modify-write available, and absolute values plus the no-op branch make repeat invocation idempotent.
- The edits array is annotated `const edits: DeclaredEdit[]`, using the type inferred from the schema. Returning the same object inline would widen `op` from `'UPDATE'` to `string` and fail the typecheck against `Output`.

---

## flagBigOrder (Classification)

The shape variant: a per-row loop, one entity read and a different entity written, and a batch of N edits from a single invocation.

### classification-flagBigOrder.ttl

```turtle
@prefix fno:   <https://w3id.org/function/ontology#> .
@prefix ont:   <https://ontology.uipath.com/ont#> .
@prefix cls:   <https://ontology.uipath.com/classification#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .

cls:flagBigOrder
        a                   fno:Function ;
        rdfs:label          "Classify invoices by order size" ;
        rdfs:comment        "For each of the given invoices, sets its status to 'Big Order' when its lines add up to more than 100 units total, and 'Small Order' otherwise. Writes one row per requested invoice, including invoices with no lines at all." ;
        ont:kind            "ACTION" ;
        ont:language        "CODED" ;
        ont:processType     "CODED_FUNCTION" ;
        ont:statements      ( "func:flagBigOrder(invoiceIds, lines)" ) ;
        ont:reads           ( cls:read.flagBigOrder.lines ) ;
        ont:writes          "ErpInvoice.status" ;
        ont:process         "FlagBigOrderProcess" ;
        fno:expects         ( cls:param.flagBigOrder.invoiceIds ) ;
        fno:returns         ( cls:out.flagBigOrder.rowsAffected ) .

cls:read.flagBigOrder.lines
        a              ont:Read ;
        ont:bindsTo    "lines" ;
        ont:statement  "SELECT * FROM {{ErpInvoiceLine}} WHERE {{ErpInvoiceLine.invoiceId}} IN :invoiceIds" .

cls:param.flagBigOrder.invoiceIds
        a                  fno:Parameter ;
        ont:paramName      "invoiceIds" ;
        ont:paramType      "xsd:string" ;
        ont:paramMultiple  true ;
        rdfs:comment       "The invoices to classify: one or more ErpInvoice ids." ;
        ont:required       true .

cls:out.flagBigOrder.rowsAffected
        a              fno:Output ;
        ont:paramName  "rowsAffected" ;
        ont:paramType  "xsd:integer" ;
        ont:required   true .
```

Why the notable lines look like this:

- The read targets `ErpInvoiceLine` and `ont:writes` names `ErpInvoice.status`. Reading one entity and writing another is normal for a coded action, and is one of the things the SQL surface cannot express.
- One read fetches every line of every requested invoice in a single query, using `IN :invoiceIds`. The grouping by invoice happens in the job, not in SQL.
- `ont:paramMultiple true` is what makes `invoiceIds` a list rather than a scalar. It pairs with the `IN` in the read statement.
- `ont:writes` names one field, and that single declaration covers the whole batch: both branches of the classification write `ErpInvoice.status`, and an invoice with no lines still writes it rather than being skipped.
- `fno:returns` is the same constant `rowsAffected` block as in the single-row action. It does not scale with the batch; the count of affected rows is a runtime result, not a declaration.
- `ont:process "FlagBigOrderProcess"` is `PascalCase(flagBigOrder) + "Process"`, the derivation the guide's PDD table specifies.

### jobs/flagBigOrder.ts

```typescript
import { defineFunction, type } from '@uipath/coded-functions-js-sdk';

/**
 * One whole ErpInvoiceLine row, exactly as Ontology's read hands it over.
 *
 * Ontology's declared read is a bare `SELECT * FROM ErpInvoiceLine WHERE InvoiceId IN (...)`, so
 * these are the real physical Data Fabric column names, not the ontology's logical field names
 * (`quantity`, `lineId`). The SQL stays a plain `SELECT *`; adapting to the physical shape is this
 * file's job. The index signature covers the extra system columns `SELECT *` carries along — the
 * SDK validates input against this interface with `additionalProperties: false`, so an undeclared
 * column would otherwise fault the job before the handler runs.
 */
interface InvoiceLine {
  ErpInvoiceLineId: string;
  InvoiceId: string;
  Sku: string;
  Description: string;
  Quantity: number;
  UnitPrice: number;
  PoUnitPrice: number;
  [column: string]: unknown;
}

/**
 * The job's input, declared by flagBigOrder's `func:bigOrder(invoiceIds, lines)` marker: the
 * caller's own parameter first, then the rows of the action's one read statement. The marker is the
 * whole signature — nothing it does not name arrives here.
 */
interface Input {
  invoiceIds: string[];
  lines: InvoiceLine[];
}

interface DeclaredEdit {
  op: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: string;
  properties: Record<string, unknown>;
}

interface Output {
  edits: DeclaredEdit[];
}

const BIG_ORDER_THRESHOLD = 100;

/**
 * FlagBigOrderProcess
 *
 * The read fetches every line of every requested invoice in one query, so this function groups the
 * rows by invoice itself, sums each invoice's quantity, and classifies it: over the threshold is a
 * 'Big Order', at or under it a 'Small Order'. Every requested invoice therefore gets exactly one
 * edit — a batch, not a single write. Ontology compiles each edit to its own single-row primary-key
 * UPDATE.
 *
 * An invoice with no lines at all totals zero, so it classifies as 'Small Order' rather than being
 * skipped. Both outcomes write the same field, which is why ont:writes "ErpInvoice.status" still
 * covers the whole batch.
 *
 * Ontology checks every edit's (entity, field) here against flagBigOrder's declared ont:writes
 * before generating any SQL, so this function may only ever write ErpInvoice.status.
 */
export default defineFunction({
  name: 'flagBigOrder',
  description:
    "Classifies each given invoice's status as 'Big Order' or 'Small Order' by whether its total line quantity exceeds 100.",
  method: 'POST',
  path: '/flagBigOrder',
  input: type<Input>(),
  output: type<Output>(),
  handler: async (input) => {
    // Total quantity per invoice, from the flat row set the one read returned.
    const totalByInvoice = new Map<string, number>();
    for (const invoiceId of input.invoiceIds) {
      totalByInvoice.set(invoiceId, 0);
    }
    for (const line of input.lines) {
      const running = totalByInvoice.get(line.InvoiceId);
      // A line whose invoice was not asked for is ignored rather than silently classified.
      if (running === undefined) {
        continue;
      }
      totalByInvoice.set(line.InvoiceId, running + line.Quantity);
    }

    const edits: DeclaredEdit[] = [];
    for (const [invoiceId, totalQuantity] of totalByInvoice) {
      edits.push({
        op: 'UPDATE',
        entity: 'ErpInvoice',
        properties: {
          id: invoiceId,
          status: totalQuantity > BIG_ORDER_THRESHOLD ? 'Big Order' : 'Small Order',
        },
      });
    }
    return { edits };
  },
});
```

Why the notable lines look like this:

- `invoiceIds: string[]` mirrors the multi-valued param; `lines: InvoiceLine[]` is the flat row set the one read returned, not a per-invoice grouping. The regrouping is the first thing the handler does.
- The map is seeded from `input.invoiceIds` before any line is summed. That is what makes an invoice with zero lines classify as 'Small Order' instead of vanishing from the output, and it is why the action's row count matches the caller's request count.
- Lines whose invoice was not requested are skipped rather than classified, because the read's `IN` clause is the only thing scoping the row set and a widened read should not widen the writes.
- Each edit carries `id` alongside `status`. The id becomes the WHERE clause of that edit's own `UPDATE SET col = literal WHERE pk = literal`, and it is exempt from `ont:writes`.
- `status` is written as an absolute value on both branches, so re-invoking the action on unchanged data produces the same rows. This job does not take the no-op path that `tagOverdueTicket` does: it writes every requested invoice each run.
- `const edits: DeclaredEdit[] = []` is declared with its annotation before the loop, and `push` fills it. That keeps `op` at its literal type, the same reason `tagOverdueTicket` annotates its single-element array.
- N edits become N statements and N steps at runtime. `rowsAffected` reports the total.
