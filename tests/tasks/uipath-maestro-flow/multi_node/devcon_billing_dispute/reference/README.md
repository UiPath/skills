# DevCon BillingDisputeResolution — reference scenario

> **Reference material for skill debuggers — NOT agent-facing.** The two tasks in
> the parent folder (`billing_invoice_lookup`, `billing_discrepancy_detector`) are
> narrow slices of this flow. This dir is here so a human debugging the
> `uipath-maestro-flow` skill (or these tasks) can see the known-good source. The
> grader never reads it; the agent under test is not pointed at it.

## What `BillingDisputeResolution.flow` is

The 24-node DevCon "BillingDisputeResolution" demo Maestro Flow. Exported from
Studio Web, so its connector nodes are real, working examples (Data Service
query + Outlook). The two e2e tasks reproduce just the Data Service lookup +
compute portion as greenfield builds graded by `flow validate` + `flow debug`.

Caveat: the export carries the original author's tenant values — real connection
GUIDs, emails, and an absolute path. Those are stale (see "discover at build
time" below); treat them as illustrative, not copy-pasteable.

## Verified known-good recipe (the part the skill currently gets wrong)

Confirmed 2026-06-03 by hand-building both task flows from this reference and
running the actual check scripts to a pass (`flow debug` → `Completed`, oracle
values matched).

1. **Connection binding NAME must match the definition placeholder.** The
   runtime resolves the connection from the connector node's *definition*
   `model.context` entry `{ "name": "connection", "value": "<bindings.X>" }`. In
   a Studio-Web export `X` = `uipath-uipath-dataservice connection`. So the
   top-level `bindings[]` entry for the connection must have:
   - `name` = `uipath-uipath-dataservice connection` (the placeholder-looking
     form — NOT the IS connection display name)
   - `default` / `resourceKey` = the real connection GUID

   If `name` is anything else, `flow validate` still passes but `flow debug`
   faults: incident `102010`, `'Connection' has an invalid GUID value:
   '<bindings.uipath-uipath-dataservice connection>'`. The skill's
   `data-fabric/impl.md` Step 3 currently says the opposite — that is the bug
   behind the eval failures.

2. **`queryExpression` uses `=js:` when filtering by a runtime variable** — e.g.
   `` =js:`invoiceNumber = '${$vars.start.output.invoiceNumber}'` ``. The
   "raw CEQL, no `=js:`" note in impl.md only covers a static literal.

3. **Connection GUIDs are tenant/connection-specific — discover at build time**
   via `uip is connections list --all-folders`. This reference's GUID
   (`8b273e5a-…`) is stale; the live eval-tenant connection is a different one.

4. A clean 3–4 node flow is enough (`start → query → End`, or
   `start → ERP → CRM → End`). No merge/script node needed — compute outputs in
   the End node's `=js:` output `source` expressions.

## Seeded data oracle (verified via `uip df records list`)

- `BillingDisputeERP`, invoice `MCS-2026-04872` → exactly **8** line items; line
  5 ("Custom Integration Build") `amount` 2590 → `300 × 14 − 2590 = 1610`.
- `BillingDisputeCRM`, account `ACCT-98201-NE` → `accountTier` **Enterprise**.
