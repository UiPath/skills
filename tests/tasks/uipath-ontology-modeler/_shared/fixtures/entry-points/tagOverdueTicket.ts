import { defineFunction, type } from '@uipath/coded-functions-js-sdk';

interface TicketRow {
  TicketId: string;
  TicketNumber: string;
  Subject: string;
  Sev: string;
  Status: string;
  CreatedAt: string;
  DueAt: string;
  Labels: string;
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
