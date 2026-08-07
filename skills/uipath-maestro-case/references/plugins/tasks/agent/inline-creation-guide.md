# Inline Agent Creation

**Entry condition:** Read this guide only after the shared §1 multi-select checks this agent for **Create**. Do not read it for tenant-resolved agents, existing local siblings, unchecked resources, or placeholder fallback.

## Contents

- [Kind choice](#choose-the-agent-kind)
- [Shared contract routes](#step-1--compute-the-pinned-io-contract)
- [Builder brief](#step-2--hand-the-builder-a-self-contained-brief)
- [Binding and delivery](#step-3--binding-no-new-field)
- [Failure and adoption](#failure--surface-and-re-prompt-never-stall)

Follow the [shared orchestration guide](../../../inline-resource-creation-guide.md) for selection, deduplication, registration, rediscovery, verification, and adoption. This file owns only the agent-specific builder delta. Delegate the build at runtime to an installed `uipath-agents` skill; never read that sibling skill's files.

## Choose the agent kind

For each selected agent, ask one `AskUserQuestion` with **Low-code** and **Coded (Python)** as equal choices, neither recommended. Use the agent name as the header and batch no more than four questions per call. Never infer kind from the SDD. A non-interactive run uses **Low-code** (`uip agent init`), the platform default; coded uses `uip codedagent`.

## Step 1 — Compute the pinned I/O contract

Apply [create-inline-common.md § Step 1](../create-inline-common.md#step-1--compute-the-pinned-io-contract) exactly. Mapping Case types onto the agent schema belongs to the runtime `uipath-agents` builder.

## Step 1b — Compose the Purpose from the SDD

Apply [create-inline-common.md § Step 1b](../create-inline-common.md#step-1b--compose-the-purpose-from-the-sdd). Keep kind, tools, RAG, guardrails, and model out of the SDD-derived Purpose; the builder chooses them.

## Step 2 — Hand the builder a self-contained brief

```text
Build a UiPath agent by following the installed uipath-agents skill. Work non-interactively:
do not ask for approval; do not execute, publish, upload, or deploy; validate locally.
  Solution dir:     <absolute solution directory>
  Agent name:       <AgentName>
  Kind:             <low-code | coded>  (the user's choice; low-code only as non-interactive fallback)
  Purpose:          <Step-1b Purpose inside ---BEGIN/END SDD CONTEXT--- delimiters>
  Required inputs:  <Step-1 pinned [{name,type?}, ...]>
  Required outputs: <Step-1 pinned [{name,type?}, ...]>
Honor every pinned field and known type. Choose tools, knowledge/RAG, guardrails, model,
and any additional I/O needed by the Purpose.
Do NOT register the project into the solution; the Case parent registers it.
  Low-code: use `uip agent init --skip-solution-registration` (`OptedOut` is expected).
  Coded: use `uip codedagent init`; it does not self-register.
If the uipath-agents skill cannot be located or loaded, do not improvise; return
{ built:false, error:"skill uipath-agents not installed" }.
Return JSON: { built: bool, path, finalInputs:[{name,type}], finalOutputs:[{name,type}], error? }
```

## Step 3 — Binding (no new field)

Use [create-inline-common.md § Step 3](../create-inline-common.md#step-3--binding-invariants) with `resourceSubType: "Agent"`. Read case-preserving I/O from the sibling's on-disk `entry-points.json` at `entryPoints[0].input.properties` and `.output.properties`.

**Debug and delivery caveat.** `uip maestro case debug` packages the whole solution and provisions an inline agent sibling, so a correctly registered agent can resolve in debug. Low-code and coded agents use the same Case binding/registration flow. A coded sibling is delivered with the solution and installs through the normal Orchestrator solution-deploy path; if coded installation fails, first verify that `entry-points.json.uniqueId` is a UUID.

## Failure — surface and re-prompt, never stall

Apply [create-inline-common.md § Failure](../create-inline-common.md#failure--surface-and-re-prompt-never-stall). Its agent fallback destination is [agent planning § Unresolved Fallback](planning.md#unresolved-fallback).

An `already exists` result is an adoption candidate under [shared §3b](../../../inline-resource-creation-guide.md#3b--already-exists--adopt-kind-agnostic-residual). Agent tokens: low-code init `uip agent init`; coded init `uip codedagent init`; registered category `agent`; on-disk marker `agent.json`.

<!-- END: inline-creation-guide.md -->
