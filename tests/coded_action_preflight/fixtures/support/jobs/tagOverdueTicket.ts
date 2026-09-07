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

const SLA_HOURS: Record<string, number | undefined> = {
  sev1: 4,
  sev2: 20,
  sev3: 120, // five days
};

const OVERDUE_TAG = 'TICKET_OVERDUE';
const HOUR_MS = 60 * 60 * 1000;

const iso = (ms: number) => new Date(ms).toISOString().slice(0, 19) + 'Z';

/**
 * The first of `names` the row actually carries, as a string, or '' if it carries none.
 *
 * Row fields are optional because a `SELECT *` read's physical column spelling is not
 * knowable at authoring time, so every read goes through here rather than off the interface.
 */
function column(row: TicketRow, ...names: string[]): string {
  for (const name of names) {
    const value = row[name];
    if (value !== undefined && value !== null) return String(value);
  }
  return '';
}

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
    if (column(row, 'Status', 'status') === 'closed') {
      return { edits: [] };
    }

    // Severity and creation time are the two the job cannot proceed without, so they are
    // checked here, where the error can name the column and what the row did carry.
    const createdAt = Date.parse(column(row, 'CreatedAt', 'createdAt'));
    const sev = column(row, 'Sev', 'sev');
    const slaHours = SLA_HOURS[sev];
    if (Number.isNaN(createdAt) || slaHours === undefined) {
      throw new Error(
        `ticket ${input.ticketId}: no due date is computable from CreatedAt=` +
          `${column(row, 'CreatedAt', 'createdAt')} Sev=${sev}; the row carried ` +
          Object.keys(row).join(', '),
      );
    }

    const dueAt = createdAt + slaHours * HOUR_MS;
    const properties: Record<string, unknown> = { id: input.ticketId };

    if (Date.parse(column(row, 'DueAt', 'dueAt')) !== dueAt) {
      properties.dueAt = iso(dueAt);
    }

    const tags = column(row, 'Labels', 'labels').split(',').filter(Boolean);
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
