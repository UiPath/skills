# Troubleshooting Reference Router

Start here. Find the product or package that matches the user's issue, then follow the links to drill down into playbooks.

## Orchestrator

Manages automation resources, robots, processes, and execution. Handles job scheduling, queue management, asset storage, triggers, storage buckets, and folder-based access control. Issues here involve failed jobs, stuck jobs, queue item failures, trigger problems, robot connectivity, permissions, and platform availability.

CLI: `uip or --help`, `uip resource --help`

- [products/orchestrator/overview.md](./products/orchestrator/overview.md) — Product overview, features, and dependencies
- [products/orchestrator/summary.md](./products/orchestrator/summary.md) — All playbooks for Orchestrator issues

## Runtime Exceptions

General .NET runtime exceptions originating from the user's own workflow code — not from activity packages or platform internals. Covers null references, null arguments, and similar errors in workflow logic, variable handling, and data processing.

- [runtime-exceptions/overview.md](./runtime-exceptions/overview.md) — Scope boundary, investigation sources (local logs and Orchestrator jobs)
- [runtime-exceptions/summary.md](./runtime-exceptions/summary.md) — All playbooks for runtime exception issues

## Maestro

CLI: `uip maestro --help`

Agentic orchestration platform built on Orchestrator. BPMN-based process design with human-in-the-loop tasks, AI agent tasks, and service tasks. Processes are designed in Studio Web, deployed as solutions, and managed through Maestro Instance Management. Issues here involve deployment failures, debug-vs-deploy mismatches, expression/variable errors, file handling, boundary events, parallel markers, stuck instances, and service availability.

- [products/maestro/overview.md](./products/maestro/overview.md) — Product overview, dependencies, key concepts, and features
- [products/maestro/summary.md](./products/maestro/summary.md) — All playbooks for Maestro issues

## Integration Service

Connector platform for third-party integrations (Salesforce, Outlook, SAP, Slack, etc.). Manages OAuth connections, exposes activities for automations and BPMN processes, and provides event-based triggers. Issues here involve connection failures, expired authentication, triggers not firing, and operation errors. Connection errors from Integration Service often surface through Maestro or Orchestrator as the calling product.

CLI: `uip is --help`

- [products/integration-service/overview.md](./products/integration-service/overview.md) — Product overview, connectors, connections, and CLI commands
- [products/integration-service/summary.md](./products/integration-service/summary.md) — All playbooks for Integration Service issues

## UI Automation

Activities for interacting with desktop and web application UIs. Robots use selectors (XML descriptors) to find and interact with UI elements. Issues here involve selector failures, element not found exceptions, timeout issues, Healing Agent problems, and data validation errors during UI interactions.

Namespaces: `UiPath.UIAutomationNext.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.Core.Activities`

- [activity-packages/ui-automation/overview.md](./activity-packages/ui-automation/overview.md) — Package overview, selector mechanics, exception types, and dependencies
- [activity-packages/ui-automation/summary.md](./activity-packages/ui-automation/summary.md) — All playbooks for UI Automation issues

## System Activities

Core workflow activities from `UiPath.System.Activities` that interact with Orchestrator resources at runtime — asset retrieval, credential lookup, queue operations, and storage buckets. Issues here involve asset-not-found errors, permission denied, folder scope mismatches, external vault failures, and package version bugs.

Namespaces: `UiPath.Core.Activities`

- [activity-packages/system-activities/overview.md](./activity-packages/system-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/system-activities/summary.md](./activity-packages/system-activities/summary.md) — All playbooks for System Activities issues

## Google Workspace Activities

Activities for interacting with Google Workspace including Google Calendar, Google Drive, Google Sheets, Gmail, Google Docs, Google Tasks, and Google Forms. Issues here involve files not found, sheet name conflicts, multiple items name conflicts, emails not found, sheet cell limit exceeded, sheets invalid ranges, upload storage quota exceeded.

Namespaces: `UiPath.GSuite.Activities`

- [activity-packages/gsuite-activities/overview.md](./activity-packages/gsuite-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/gsuite-activities/summary.md](./activity-packages/gsuite-activities/summary.md) — All playbooks for Google Workspace Activities issues

## Microsoft Office 365 Activities

Activities for interacting with Microsoft Office 365 through Graph API. Issues here involve multiple items name conflicts, drive items not found, mail folders not found, emails not matching the filters, already existing item names.

Namespaces: `UiPath.MicrosoftOffice365.Activities`

- [activity-packages/o365-activities/overview.md](./activity-packages/o365-activities/overview.md) — Package overview, activity types, and common failure patterns
- [activity-packages/o365-activities/summary.md](./activity-packages/o365-activities/summary.md) — All playbooks for Microsoft Office 365 Activities issues

## Excel Activities

Activities for automating Microsoft Excel on Windows via COM interop (modern `Excel Process Scope` activities) and OpenXML file access (legacy workbook activities). Issues here involve `Invoke VBA` failures — Trust Center security blocks, malformed external code files, entry method name mismatches, parameter marshaling errors, and COM interop instability (`0x80010100 RPC_E_SYS_CALL_FAILED` and related HRESULTs).

Namespaces: `UiPath.Excel.Activities`

- [activity-packages/excel-activities/overview.md](./activity-packages/excel-activities/overview.md) — Package overview, `Invoke VBA` execution model, and common failure patterns
- [activity-packages/excel-activities/summary.md](./activity-packages/excel-activities/summary.md) — All playbooks for Excel Activities issues


## Playbooks

All playbooks use the same headers: `## Context`, `## Investigation` (optional), `## Resolution` (optional). They vary by confidence level:

| Confidence | What you know | Investigation | Example |
|---|---|---|---|
| **High** | Exact error → exact cause | Quick verification | "GetAsset" error → asset missing |
| **Medium** | Specific error → known troubleshooting path | Concrete steps | SSL cert invalid → check cert, chain, trust |
| **Low** | General symptoms → multiple causes | General guidance or absent | Robot unresponsive → could be heartbeat, network, or machine issue |

Template and full guide: [templates/playbook-template.md](./templates/playbook-template.md) | [knowledge-base-guide.md](./knowledge-base-guide.md)
