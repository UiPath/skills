# Final Resolution

---

**Root Cause:** The `InvoiceExtractor` process returns its entire
result set as a **DataTable output argument** (`Out_AllInvoices`,
~184,000 rows). The workflow runs to completion, but the executor
cannot hand the result back to Orchestrator because that
`OutputArguments` payload exceeds the maximum result-message size —
so the job faults at the very end with `Could not retrieve the
result of the job execution. This might be because a message was too
large to process.` This is the **output-too-large / bulk output
argument** case of the `job-output-too-large` playbook. The
automation logic is fine; the fault is in returning a large payload
through the result channel.

**What went wrong:** Job `bbdd5566-...-3344` (InvoiceExtractor,
FinanceOps) faulted at `2026-06-24T04:03:52Z`. `jobs traces` shows
every activity — including `Assign Out_AllInvoices` — Succeeded and
the Main sequence reached its end. `jobs get` shows `OutputArguments`
empty (the result could not be serialized/returned). The Robot log
is explicit: "output argument 'Out_AllInvoices' (System.Data.
DataTable, ~184000 rows) exceeds the maximum result message size.
The workflow completed; only the result hand-back to Orchestrator
failed." The process source confirms `Out_AllInvoices` is a
`System.Data.DataTable` output argument (`project.json`
`entryPoints[].output` / `entry-points.json`).

**Why:** `OutputArguments` are transported to Orchestrator over a
size-limited result-message channel. A ~184k-row DataTable far
exceeds that limit, so the return fails even though the run
succeeded.

**Ruled out:**
- **Workflow-logic fault** — traces show all activities Succeeded;
  the run reached its end. The failure is post-completion hand-back.
- **Generic exit-code / crash** — no exit-code or exception; the
  Info specifically names result retrieval / message size.

---

**Evidence:**

### Orchestrator
- Failing job `bbdd5566-...-3344` — InvoiceExtractor, Faulted at
  `2026-06-24T04:03:52.640Z`, `OutputArguments: ""`
- Job `Info`: `Could not retrieve the result of the job execution.
  This might be because a message was too large to process.`
- Robot log: `Failed to serialize/return job result: output argument
  'Out_AllInvoices' (System.Data.DataTable, ~184000 rows) exceeds the
  maximum result message size. The workflow completed; only the
  result hand-back to Orchestrator failed.`
- `jobs traces`: `Main Sequence`, `Extract all invoices`, and
  `Assign Out_AllInvoices` all **Succeeded** — workflow finished
- Process source: `Out_AllInvoices` is a `System.Data.DataTable`
  output argument (`project.json` `entryPoints[].output`)

---

**Immediate fix:**

1. **Stop returning the bulk DataTable as an output argument;
   return a reference instead.**
   - **Why:** `OutputArguments` ride a size-limited result channel.
     A large DataTable overflows it. Writing the payload to durable
     storage and returning only a small pointer keeps the result
     message tiny.
   - **Where:** In `InvoiceExtractor`, write the invoices to a
     **Storage Bucket** (or a **Queue** / **Data Fabric** entity)
     inside the workflow, and change `Out_AllInvoices` to return the
     **bucket key / file path / reference** (a string) instead of
     the DataTable. Callers read the payload from that reference.
   - **Who:** Automation developer
   - **Source:**
     `products/orchestrator/playbooks/job-output-too-large.md`

2. **Rerun** the job after the change; the result hand-back now
   carries only the reference and succeeds.

---

**Alternative fix:**

- If a reference pattern is not viable, **trim or paginate** the
  output — return only the fields/rows the caller needs so the
  payload fits the result-message limit. Ensure the returned type is
  serializable.

---

**Preventive fix:**

1. **Design** — Treat `OutputArguments` as a control channel, not a
   data channel: pass IDs/references, never bulk payloads. Cap
   output-argument size in design review.
   - **Source:**
     `products/orchestrator/playbooks/job-output-too-large.md`
     (Prevention)

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Output-too-large: bulk DataTable returned as an output argument (job-output-too-large playbook) | High | Confirmed | Yes | Info = "could not retrieve result / message too large"; traces show workflow completed; Robot log names Out_AllInvoices (~184k-row DataTable) over the result-size limit; process declares a DataTable output argument | Return a reference (Storage Bucket / queue / Data Fabric) instead of the DataTable; rerun |
| H2 | Workflow-logic fault mid-run | Low | Refuted | No | Traces show all activities Succeeded; run reached its end | n/a |

---

Would you like help applying the fix — wiring the extract step to a
Storage Bucket and changing `Out_AllInvoices` to return the bucket
reference?
