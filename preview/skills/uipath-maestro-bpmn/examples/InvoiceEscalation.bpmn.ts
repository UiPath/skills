/**
 * InvoiceEscalation — an invoice approval **written by nesting**: every relationship
 * that `InvoiceApproval.bpmn.ts` spells as an id reference is written here as
 * structure, so the file reads in execution order and no `attachedTo`, `default:` or
 * join gateway is named by hand.
 *
 * | it demonstrates | as |
 * | --- | --- |
 * | two lookups at once | `.fork('enrich', [ … ])` — a parallel split and its join |
 * | a reminder that does not cancel the approval | `t.onTimer('P2D', { interrupting: false }, …)` in the human task's body |
 * | a failure exit for the approval itself | `t.onError(true, { errorVar: 'approvalError' }, …)` |
 * | a three-way decision, one arm looping back | `.choose('route', [ … ])` with `when` / `otherwise` arms and `.goto('approve')` |
 * | a safety net for the whole process | `.eventSubProcess('failures', { error: true, errorVar: 'failure' }, …)` |
 * | classification on the caught error | a `.choose()` inside the net reading `vars.failure.code` |
 *
 * | the process written top to bottom | `.flowMode('sequence')` — no `.sequenceFlow()` anywhere |
 *
 * What the nesting buys, concretely: the same graph written the explicit way needs
 * two parallel gateways, two exclusive gateways each with a named `default:` flow, two
 * `.boundaryEvent()` calls each naming the task they attach to, a sub-process flagged
 * `triggeredByEvent` with its error start event written by hand, and twenty-two
 * `.sequenceFlow()` calls. Here there are none: the scope is in sequence mode, so each
 * element continues to the next, and the constructs imply the rest. The lowering is
 * identical — this compiles to the same 19 elements and 22 flows the explicit form
 * would, so `check`, `validate`, `merge` and `decompile` see nothing new.
 *
 * Read `uip maestro bpmn check InvoiceEscalation.bpmn.ts --graph` to see the wiring that
 * resulted, implied edges marked `~>`. The first version of this file, written in the
 * default explicit mode, forgot the one edge out of `approve` into `route` — every gate
 * passed, and the graph printer was what showed `approve` with no outgoing flow.
 * `check` now warns `DEAD_END` for that shape.
 *
 * Three rules the file relies on, all enforced by `.build()`:
 *
 *   - In a `sequence` scope, consecutive elements are wired in order, an element with
 *     an explicit outgoing flow is left alone, and an element nothing leads into is
 *     refused. Here `approve` continues into `route`, and `post` into `done`, by
 *     position.
 *   - An INTERRUPTING handler's path rejoins at the statement after its activity
 *     (`onError` here continues into `route`), because the activity's own token is
 *     gone. A NON-INTERRUPTING one must end on its own (`onTimer` ends at `reminded`),
 *     because its token runs beside one that reaches that statement anyway.
 *   - A `choose` needs no join gateway named: arms rejoin at the next statement, through
 *     `route_join` only if more than one arm actually gets there. Here the `approved`
 *     arm falls through, `rejected` ends, and `needsInfo` leaves with `.goto()`, so no
 *     join is emitted and `post` follows `approved` directly. The loop back does give
 *     `approve` two incoming flows, which `check` notes as FAKE_JOIN — a warning, since the
 *     platform accepts the implicit merge.
 *
 * Compile with `uip maestro bpmn compile InvoiceEscalation.bpmn.ts -o InvoiceEscalation.bpmn`,
 * then `uip maestro bpmn validate`. Nothing here needs the connector library.
 */
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('invoice-escalation')
  .name('InvoiceEscalation')
  .flowMode('sequence')
  .input('invoiceId', 'string', { name: 'Invoice ID' })
  .var('decision', 'string', { default: 'Pending' })
  .var('outcome', 'string', { default: 'RUNNING' })
  .var('reminders', 'number', { default: 0 })
  .startEvent('start', { name: 'Invoice received' })
  // Two lookups at once. `fork` opens a parallel gateway, runs each arm, and joins
  // them through `enrich_join` before `approve` — the join is derived from the id
  // the author wrote, so an explicit `.sequenceFlow('enrich_join', …)` could still
  // reach it, and `merge` keys on it like any other element. Each lookup's response
  // lands in `<id>_response` with no `.var()` needed.
  .fork('enrich', [
    (b) =>
      b.http('vendorLookup', {
        name: 'Vendor lookup',
        method: 'GET',
        url: '=js:"https://erp.example.com/vendors/by-invoice/" + vars.invoiceId',
      }),
    (b) =>
      b.http('poLookup', {
        name: 'Purchase order lookup',
        method: 'GET',
        url: '=js:"https://erp.example.com/purchase-orders/by-invoice/" + vars.invoiceId',
      }),
  ])
  // The approval, with its boundary events declared ON it. Nothing names `approve`
  // as `attachedTo`: the handlers belong to the task whose body they are written in.
  .humanTask(
    'approve',
    {
      name: 'Approve invoice',
      app: 'InvoiceApproval',
      title: '=js:"Invoice " + vars.invoiceId',
      actions: ['Approve', 'Reject', 'Needs info'],
      input: { invoiceId: '=vars.invoiceId', vendor: '=vars.vendorLookup_response', purchaseOrder: '=vars.poLookup_response' },
      outputs: { decision: '=Action' },
    },
    (t) => {
      // Every two days the approval stays open, nudge — and keep waiting. Non-interrupting,
      // so this path may not rejoin the main flow; it ends at its own end event.
      t.onTimer('P2D', { interrupting: false, name: 'Still waiting' }, (b) =>
        b.task('nudge', { name: 'Send reminder', set: { reminders: '=js:vars.reminders + 1' } }).endEvent('reminded', { name: 'Reminder sent' }),
      );
      // If the task itself fails — app unavailable, assignment impossible — record it and
      // fall through to the decision with `decision` still `Pending`. Interrupting, so
      // this path continues into whatever follows `approve`.
      t.onError(true, { errorVar: 'approvalError', name: 'Approval failed' }, (b) =>
        b.task('recordApprovalError', { name: 'Record approval error', set: { outcome: '=js:"APPROVAL_FAILED: " + vars.approvalError.message' } }),
      );
    },
  )
  // A three-way decision written in place. `when` arms carry their condition on the
  // flow; the `otherwise` arm IS the gateway's default. `needsInfo` sends the invoice
  // back to the approver; `rejected` ends the process; `approved` continues.
  .choose('route', [
    {
      when: '=vars.decision == "Approve"',
      label: 'Approved',
      body: (b) => b.task('markApproved', { name: 'Mark approved', set: { outcome: 'APPROVED' } }),
    },
    {
      when: '=vars.decision == "Needs info"',
      label: 'Needs info',
      body: (b) => b.task('requestInfo', { name: 'Ask the vendor', set: { outcome: 'AWAITING_VENDOR' } }).goto('approve'),
    },
    {
      otherwise: true,
      label: 'Rejected or failed',
      body: (b) => b.task('markRejected', { name: 'Mark rejected', set: { outcome: '=js:vars.decision == "Reject" ? "REJECTED" : vars.outcome' } }).endEvent('rejected', { name: 'Rejected' }),
    },
  ])
  .scriptTask('post', {
    name: 'Post to ledger',
    script: 'return { response: { posted: true, invoiceId: invoiceId } };',
    inputs: { invoiceId: '=vars.invoiceId' },
  })
  .endEvent('done', { name: 'Posted' })
  // The safety net. An event sub-process has no incoming flow; it starts when an error
  // nothing closer caught is raised anywhere in this process, and — sitting at process
  // level — ends the whole run. Its body chains from the synthesized `failures_start`.
  .eventSubProcess('failures', { error: true, errorVar: 'failure', name: 'Failure net' }, (h) =>
    h.choose('failureKind', [
      {
        when: '=js:String(vars.failure.code || "").indexOf("ERP") >= 0',
        label: 'ERP outage',
        body: (b) => b.task('flagOutage', { name: 'Flag ERP outage', set: { outcome: 'FAILED_ERP_OUTAGE' } }).endEvent('outage', { name: 'Escalated to IT' }),
      },
      {
        otherwise: true,
        label: 'Anything else',
        body: (b) => b.task('flagUnknown', { name: 'Flag for finance', set: { outcome: '=js:"FAILED: " + vars.failure.message' } }).endEvent('unhandled', { name: 'Escalated to finance' }),
      },
    ]),
  )
  .build();
