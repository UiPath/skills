# Agent Implementation

This document defines the implementation boundary for agent tasks.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for agent invocation.
- Documented `Orchestrator.StartAgentJob` or `A2A.AgentExecution` `uipath:activity` shells.
- Input CDATA for public-safe invocation payloads.
- Output mappings for job ID, status, result, and structured fields.
- Timeout/error boundary events and validation gateways.

## CLI or operator-owned implementation

The CLI or operator must resolve:

- Real agent resource identity, version, folder, and binding metadata.
- Dynamic schemas for agent inputs and outputs.
- Deployment, creation, or modification of the agent itself.

## Validation expectations

- Agent binding resolves before upload/run.
- Input variables and output variables exist.
- Timeout and invalid-output paths are modeled when needed.
- High-impact outputs have review or validation gates when required by user intent.
