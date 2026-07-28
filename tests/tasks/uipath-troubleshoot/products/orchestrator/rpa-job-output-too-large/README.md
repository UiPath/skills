# Could Not Retrieve Result — Output Too Large

Reproduces the **output-too-large** case of the `job-output-too-large`
playbook: a job runs to completion but faults at result hand-back
because a bulk `OutputArguments` payload exceeds the result-message
limit.

```
Could not retrieve the result of the job execution. This might be
because a message was too large to process.
```

## What this scenario uncovers

**Root Cause:** `InvoiceExtractor` returns a ~184,000-row DataTable
as the output argument `Out_AllInvoices`. The workflow finishes (all
activities Succeeded in traces), but the executor cannot return that
payload to Orchestrator. Fix: write the payload to a Storage Bucket
/ queue / Data Fabric and return only a reference.

Maps to:
`references/products/orchestrator/playbooks/job-output-too-large.md`.

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` + `m/uip.cmd` | shared from `../../../_shared/mock_template/` |
| `process/` | minimal UiPath project that declares a `DataTable` output argument `Out_AllInvoices` |
| `data/m/r/*.json` | **synthetic** canned `uip` responses (jobs get/list/logs, **jobs traces** proving the workflow completed) |
| `data/m/r/manifest.json` | dispatch table |

> Fixtures authored from the playbook signature, not captured from a
> real session.

## Distinguishing fingerprint

The Info names *result retrieval / message size*, and `jobs traces`
shows the workflow **completed** — so this is a result hand-back
failure (output too large), not a mid-run logic fault. The specific
bulk output argument (`Out_AllInvoices`, DataTable) is read from the
process source; the graded fix is returning a reference instead of
the payload.

## Success criteria

Scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill.
- Agent identified the oversized DataTable output argument as the
  root cause (workflow completed; hand-back failed) and recommended
  returning a reference (Storage Bucket / queue / Data Fabric)
  instead of the bulk payload.
