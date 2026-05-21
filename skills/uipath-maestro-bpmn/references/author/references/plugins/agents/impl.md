# Agent Implementation

This document defines the implementation boundary for agent task recipes. Agents are implemented as `bpmn:serviceTask`; see [task-recipes/agent-job.md](../../task-recipes/agent-job.md) for the per-deployment-style shell decision table.

## Model-owned implementation

The model may edit:

- `bpmn:serviceTask` wrapper for agent invocation.
- `Orchestrator.StartAgentJob` activity shell for any folder-deployed agent (coded Python or low-code) with the required binding pair (`name` + `folderPath`, `resource="process"`, `resourceSubType="Agent"`, paired `propertyAttribute` values).
- `A2A.AgentExecution` activity shell for external A2A agents addressed by URL/skillId/authToken.
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
