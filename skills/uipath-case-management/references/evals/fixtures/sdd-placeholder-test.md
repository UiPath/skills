# Chrysanthemum Claims Triage — UiPath Case Management Specification

**Case Description:** Fictitious claims-intake case used as a test fixture for the placeholder path. Every task references a process/agent/connector whose name has been deliberately fabricated so no registry match exists — the skill should emit each task as a placeholder rather than aborting.

## Solution Overview

Two stages, six tasks, one connector trigger, one connector activity, one action, one agent, one RPA, one API workflow. Designed to exercise every placeholder branch (RPA / API / agent / action with `taskTitle` / connector activity / connector trigger) in a single run.

**Case Metadata:**

| Property | Value |
|----------|-------|
| Case Name | Chrysanthemum Claims Triage (TEST) |
| Case Description | Fictitious claim triage for placeholder-path testing |
| Case Key | Prefix: TST (e.g., TST-2026-00001) |
| Priority | Choiceset: Urgent, High, Medium, Low — Default: Medium |
| Case-Level SLA | 1 hour |
| SLA Type | Static |

**Components Used:**

| Component | Role in This Solution |
|-----------|----------------------|
| Maestro Case Management | 2 stages, connector-triggered |
| Integration Service | Fictional connector for intake (Quantum Pager) |
| Agentic Processes | 1 fictional agent for classification |
| API Workflows | 1 fictional API workflow for inbox polling |
| RPA (Studio) | 1 fictional RPA for backoffice registration |
| HITL (Action Center) | 1 fictional action app for triage review |

---

## Case Plan Design

### Case Triggers

| Trigger Type | Source | Configuration | Initial Data Mapping | Notes |
|-------------|--------|---------------|---------------------|-------|
| Wait for Connector | Chrysanthemum Inbox (fictional) | IS Connector: fictional "Chrysanthemum Mailbox" connector monitors a fabricated claim mailbox | sender_email, subject, attachment_url -> case entity fields | Deliberately no registry entry — should produce a placeholder trigger |

### Stages

| # | Stage Name | Interrupting | Required for Case Completion |
|---|-----------|-------------|------------------------------|
| 1 | Intake | No | Yes |
| 2 | Triage | No | Yes |

### Task Definitions

#### Stage 1: Intake

**Stage Description:** Receive, register, and classify the incoming fictional claim.

| Task Name | Task Description | Component Type | Required | Persona | SLA | Run on Re-entry |
|-----------|-----------------|----------------|----------|---------|-----|-----------------|
| Chrysanthemum Claim Fetcher | Polls the fictional Chrysanthemum inbox and pulls claim PDFs | API_WORKFLOW | Yes | — | 2 min | No |
| Obsidian Claim Registrar | Fictional RPA that registers the claim in a fabricated backoffice system | RPA | Yes | — | 3 min | No |
| Claim Classifier Agent | Fictional agent that classifies claims by fabricated taxonomy | AGENT | Yes | — | 2 min | No |

#### Stage 2: Triage

**Stage Description:** Human triage of the classified claim, followed by a fictional pager notification.

| Task Name | Task Description | Component Type | Required | Persona | SLA | Run on Re-entry |
|-----------|-----------------|----------------|----------|---------|-----|-----------------|
| Triage Review Action App | Human reviews the classified claim in a fictional action-center app | HITL | No | Claims Specialist | 30 min | No |
| Send Quantum Pager Notification | Sends a notification via a fictional "Quantum Pager" connector activity | CONNECTOR_ACTIVITY | Yes | — | 1 min | No |

### Edges

| Source | Target | Condition |
|--------|--------|-----------|
| Trigger → Intake | — | default |
| Intake → Triage | — | Intake completed |

### Process References

| Task Name | Process Name in UiPath | Folder Path |
|-----------|------------------------|-------------|
| Chrysanthemum Claim Fetcher | Chrysanthemum Claim Fetcher | /Shared/Claims/Fictional |
| Obsidian Claim Registrar | Obsidian Claim Registrar | /Shared/Claims/Fictional |
| Claim Classifier Agent | Claim Classifier Agent | /Shared/Claims/Fictional |
| Triage Review Action App | Triage Review Action App | /Shared/Claims/Fictional |
| Send Quantum Pager Notification | Quantum Pager (connector activity) | n/a |

---

## Notes for Test Reviewers

Every name above is deliberately fabricated. The expected behavior on a real tenant:

1. Planning **should not abort**. All registry lookups will fail after `uip case registry pull --force`.
2. Every task in the resulting `tasks.md` should have `placeholder: true` with a distinct `placeholderReason`.
3. `tasks/registry-resolved.json` should record `status: "REGISTRY LOOKUP FAILED: ..."` for each task.
4. Step 5 should surface the six placeholders (1 trigger + 5 tasks) before asking for approval.
5. Step 9 should route the connector-activity placeholder through `uip case tasks add --type execute-connector-activity`, NOT `tasks add-connector`.
6. Step 9 should emit `--task-title "Triage Review Action App"` for the action placeholder.
7. `uip case validate` should return `Status: Valid` with exactly one `[warning]` per placeholder: `Stage "<name>" has a task with no configuration`.
8. No `uip case var bind` commands should be emitted for any task in this fixture.
