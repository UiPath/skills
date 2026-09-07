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
