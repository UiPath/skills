# IxP Extraction Node — Planning

IxP Extraction nodes invoke a **trained, published** UiPath Intelligent eXtraction Platform (IxP) model to pull structured fields out of unstructured or semi-structured documents (PDFs, photos, scanned forms). They are tenant-specific resources that appear in the registry after `uip login` + `uip maestro flow registry pull`.

In the IxP product these published models are also called **runtime projects** — the bundle published to the tenant runtime and callable from a flow. Treat "what IxP models do I have", "what runtime projects do I have access to in flow", and "list published extractors" as the same listing question — see [Listing Available Models / Runtime Projects](#listing-available-models--runtime-projects).

## Node Type Pattern

`uipath.ixp.{modelName}.{fullyQualifiedName}`

Unlike other resource plugins that use the `uipath.core.*` prefix, IxP nodes use `uipath.ixp.*` and a **two-segment tail**: `{modelName}` is the model's display name, and `{fullyQualifiedName}` is the model's fully-qualified name on the tenant (e.g. `Shared/invoice-model`). Both segments are sanitized — see [impl.md](impl.md) for the rule and concrete examples. Model versioning is a separate input field (`versionTag`), not part of the node type.

## When to Use

Use an IxP node when the flow needs to extract **named fields** (invoice totals, contract parties, receipt line items, form values) from documents whose **layout varies across inputs** and which are not already machine-readable.

### IxP vs Script/Connector/HTTP/Agent Decision Table

| Use an IxP node when... | Use something else when... |
| --- | --- |
| Source is a PDF, scanned document, photo, or email attachment | Source is already structured (CSV, JSON, database row) — use [Script](../script/planning.md) |
| Fields have variable layout across documents (e.g. invoices from many vendors) | Layout is fixed and parseable by regex/XPath — use [Script](../script/planning.md) |
| A trained IxP model exists for this document type | No model exists — flag as a prerequisite and use `core.logic.mock` until the model is trained |
| Need field-level extraction with per-field confidence scores for downstream HITL review | Need free-form summarization, classification, or reasoning over text — use [Agent](../agent/planning.md) |

### Anti-Pattern

Don't use IxP as a generic OCR. IxP is field-oriented — it extracts named fields against a trained taxonomy. Running IxP to get raw text back and then parsing the text downstream throws away the part of IxP that's actually valuable.

### When NOT to Use

- **Model not yet trained or published** — use `core.logic.mock` and surface in Open Questions that a model must be trained on the IxP product before the flow can run.
- **Structured input (CSV/JSON/DB row)** — use [Script](../script/planning.md) or [Decision](../decision/planning.md). IxP adds latency and model-inference cost for no gain.
- **Free-form summarization, classification, or reasoning** — use [Agent](../agent/planning.md). An IxP model trained for field extraction will not produce useful output for those tasks.
- **Manual external API call** — use [Connector](../connector/planning.md) or [HTTP](../http/planning.md).

## Prerequisites

- `uip login` — IxP nodes only appear in the registry after authentication.
- `uip maestro flow registry pull --force` must be run to cache IxP model node types locally.
- A trained, published IxP extraction model must exist on the tenant. If none exists, surface it in the **Open Questions** section of the architectural plan so the user can train one while reviewing.

## Ports

| Input Port | Output Port(s) |
| --- | --- |
| `input` | `success`, `error` (the visible `error` port / edge target is gated by `inputs.errorHandlingEnabled`; the `outputs.error` schema entry on the node instance is always required — see [impl.md Authoring rule #4](impl.md#authoring-rules)) |

## Output Variables

- `$vars.{nodeId}.output` — the extraction-result object directly. The BPMN serializer maps the service's `result` field with `source: '=result'`, so **the `result` wrapper is stripped** at runtime. Top-level keys: `ExtractionResult`, `ExtractorPayloads`, `BusinessrulesResults`. Field-level values live under `output.ExtractionResult.ResultsDocument.Fields[]` / `Tables[]`; exact field names depend on the trained model's taxonomy. See [impl.md — Accessing Output](impl.md#accessing-output) for the canonical access path.
- `$vars.{nodeId}.error` — populated when the `error` port is wired and extraction fails. Mapped from the IxP service response's `Error` field (`source: '=Error'`) — see [impl.md — Accessing Output](impl.md#accessing-output).

## Discovery

```bash
uip maestro flow registry pull --force
uip maestro flow registry search "uipath.ixp" --output json
```

Requires `uip login`. Only published IxP models from your tenant appear. The returned node type uses a **two-segment tail** (`{modelName}.{fullyQualifiedName}`), unlike `uipath.core.*` siblings which use a single-segment tail. Both tail segments are sanitized: lowercase, then runs of any character outside `[a-z0-9]` → single `-`. So an FQN of `Shared/invoice-model` lands as `shared-invoice-model`. See [impl.md](impl.md) for the full rule and worked examples.

### If `Data: []` → plan for a mock + Open Question

If the search returns no `uipath.ixp.*` nodes, no IxP extraction model is published on this tenant. Plan the architecture around a `core.logic.mock` placeholder for the extraction step, and surface the missing model in **Open Questions** so the user can train and publish it. Do not iterate on registry searches — the mock is the planning answer until the model exists. See [impl.md — If the Model Does Not Exist Yet](impl.md#if-the-model-does-not-exist-yet) for the implementer-side procedure.

## Listing Available Models / Runtime Projects

Q&A use case: user asks "what IxP models do I have?", "what runtime projects do I have access to in flow?", "what document extractors can I access in flow?", "which document extractors are published?".

Read-only listing — **do not** scaffold a solution, init a flow, or write a `.flow` file:

1. Confirm `uip login status --output json`. Without login, only OOTB nodes are returned and tenant IxP models will not appear.
2. Refresh the cache and search:
   ```bash
   uip maestro flow registry pull --force
   uip maestro flow registry search "uipath.ixp" --output json
   ```
3. Format `Data[]` as a table — `DisplayName`, `NodeType`, `Version`. Each entry is one published model / runtime project. See [impl.md — Listing Published Models](impl.md#listing-published-models) for parsing details.

Search term must be `"uipath.ixp"` (lowercase). Do NOT use `"runtime"`, `"document extractor"`, `"extractor"`, or `"IXP"` — these miss extraction nodes.

If `Data: []`, answer directly that no IxP models are published on the tenant. Do not propose a `core.logic.mock` workaround — the mock is for build-time planning, not for listing-time Q&A.

## Planning Annotation

In the architectural plan:

- If the model exists: note as `resource: <model-name> (ixp-extraction)` with the intended document type (e.g. "resource: vendor-invoices (ixp-extraction) — extract invoice header + line items")
- If it does not exist: note as `[CREATE NEW] <description>` and flag in Open Questions that an IxP model must be trained before the flow can run
