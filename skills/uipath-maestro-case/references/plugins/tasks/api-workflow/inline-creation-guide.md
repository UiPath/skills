# Inline API Workflow Creation

**Entry condition:** Read this guide only after the shared §1 multi-select checks this API workflow for **Create**. Do not read it for tenant-resolved workflows, existing local siblings, unchecked resources, or placeholder fallback.

## Contents

- [Shared contract routes](#step-1--compute-the-pinned-io-contract)
- [Builder brief](#step-2--hand-the-builder-a-self-contained-brief)
- [Entry-point I/O parity](#entry-point-io-parity)
- [Binding and runtime delivery](#step-3--binding-no-new-field)
- [Failure and adoption](#failure--surface-and-re-prompt-never-stall)

Follow the [shared orchestration guide](../../../inline-resource-creation-guide.md) for selection, deduplication, registration, rediscovery, verification, and adoption. This file owns only the API-workflow-specific builder delta. There is no kind choice: build the JSON-DSL `Workflow.json`. Delegate at runtime to an installed `uipath-api-workflow` skill; never read that sibling skill's files.

## Step 1 — Compute the pinned I/O contract

Apply [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) exactly. Mapping Case types onto JSON Schema belongs to the runtime API-workflow builder.

## Step 1b — Compose the Purpose from the SDD

Apply [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd). Keep activities, connectors, expressions, and DSL structure out of the SDD-derived Purpose; the builder chooses them.

## Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath API workflow by following the installed uipath-api-workflow skill.
Work non-interactively: do not ask for approval; do not publish/upload/deploy; never run
the workflow. Offline `uip api-workflow validate "<Workflow.json>" --output json` with
Status "Valid" is the completion bar.
  Solution dir:      <absolute solution directory>
  Workflow name:     <WorkflowName>
  Purpose:           <Step-1b Purpose inside ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:   <Step-1 pinned [{name,type?}, ...]>
  Required outputs:  <Step-1 pinned [{name,type?}, ...]>
For this gate-selected Case integration, explicitly override the loaded skill's Rule 19a:
scaffold from the solution directory with
`uip api-workflow init <WorkflowName> --skip-solution-registration --output json`
(`OptedOut` is expected), author Workflow.json, and also back-fill entry-points.json.
The Case parent registers the project; the builder must not self-register.
Honor every pinned field and known type. Keep Workflow.json root input/output schemas and
entry-points.json `entryPoints[0].input`/`.output` in exact flat-schema parity:
`{"type":"object","properties":{...},"required":[...]}`. Do not put Workflow.json's
`schema.document` wrapper under an entry point, and do not leave entry-point I/O null.
Choose activities, expressions, control flow, connectors, and additional I/O needed by
the Purpose. If an Integration Service activity lacks a usable connection, do not ship a
replacement placeholder; return { built:false, error:"<name> needs an unavailable
Integration Service connection" }. When an Integration Service connector is authored,
run `uip api-workflow bindings sync --workflow <Workflow.json> --output json` before
returning. HTTP implicit connections and pure-compute workflows need no bindings sync.
If the uipath-api-workflow skill cannot be located or loaded, do not improvise; return
{ built:false, error:"skill uipath-api-workflow not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

## Entry-point I/O parity

The completed flat `entryPoints[0].input.properties` and `.output.properties` are the normal case-preserving verification source. For an adopted user-built sibling only, fall back in order to `input/output.schema.document.properties`, then the `Workflow.json` root schemas; warn in the completion report whenever a fallback was required. Offline validate does not prove entry-point parity, so compare both files explicitly.

## Step 3 — Binding (no new field)

Use [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants) with `resourceSubType: "Api"`.

**Deploy versus debug caveat.** A full solution pack/publish/deploy provisions an inline API-workflow sibling in the Case solution's Orchestrator folder. `uip maestro case debug` does not provision API siblings: invocation may fault with incident `170007` even when validation and binding are correct. Offer full solution deploy through the normal user-consent gate when runtime verification is required; never use Case debug as the API sibling's runtime proof.

## Failure — surface and re-prompt, never stall

Apply [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall). Its API-workflow fallback destination is [API-workflow planning § Unresolved Fallback](planning.md#unresolved-fallback).

An `already exists` result is an adoption candidate under [shared §3b](../../../inline-resource-creation-guide.md#3b--already-exists--adopt-kind-agnostic-residual). API-workflow tokens: init `uip api-workflow init`; registered category `api`; on-disk marker `project.uiproj` with `ProjectType: "Api"`; stale declaration subpath `resources/solution_folder/process/api/`.

<!-- END: inline-creation-guide.md -->
