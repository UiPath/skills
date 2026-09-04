// A contract declared with zod instead of type<T>(), which is the one thing this fixture is for.
//
// The pipeline stages a manifest derived from plain interfaces, and a Standard Schema carries its
// own schema instead, so there is nothing to lower. `input-strictness` must fail and
// `input-matches-marker` must skip and point at it rather than blame the job twice.
//
// The handler is deliberately shape-only: it assigns exactly the two fields the action declares in
// ont:writes, so writes-cover-edits still passes and the zod contract is the only thing under test.
// How a real job computes those values is the worked examples' job, not this file's.
import { defineFunction } from '@uipath/coded-functions-js-sdk';
import { z } from 'zod';

const TicketRow = z.object({
  TicketId: z.string(),
  Sev: z.string(),
  CreatedAt: z.string(),
  DueAt: z.string(),
  Labels: z.string(),
}).passthrough();

const Input = z.object({
  ticketId: z.string(),
  ticket: z.array(TicketRow),
}).strict();

const DeclaredEdit = z.object({
  op: z.enum(['CREATE', 'UPDATE', 'DELETE']),
  entity: z.string(),
  properties: z.record(z.string(), z.unknown()),
}).strict();

const Output = z.object({ edits: z.array(DeclaredEdit) }).strict();

type DeclaredEdit = z.infer<typeof DeclaredEdit>;

export default defineFunction({
  name: 'tagOverdueTicket',
  description: 'Declares its contract with zod, which this pipeline cannot deploy.',
  method: 'POST',
  path: '/tagOverdueTicket',
  input: Input,
  output: Output,
  handler: async (input) => {
    const row = input.ticket[0];
    const properties: Record<string, unknown> = { id: input.ticketId };
    properties.dueAt = row.DueAt;
    const tags = row.Labels.split(',').filter(Boolean);
    properties.tags = tags.join(',');
    const edits: DeclaredEdit[] = [{ op: 'UPDATE', entity: 'Ticket', properties }];
    return { edits };
  },
});
