# Diagnostics Reference Router

Start here. Find the product or package that matches the user's issue, then follow the links to drill down into playbooks.

## Orchestrator

Manages automation resources, robots, processes, and execution. Handles job scheduling, queue management, asset storage, triggers, storage buckets, and folder-based access control. Issues here involve failed jobs, stuck jobs, queue item failures, trigger problems, robot connectivity, permissions, and platform availability.

CLI: `uip or --help`, `uip resources --help`

- [products/orchestrator/overview.md](./products/orchestrator/overview.md) — Product overview, features, and dependencies
- [products/orchestrator/summary.md](./products/orchestrator/summary.md) — All playbooks for Orchestrator issues

## UI Automation

Activities for interacting with desktop and web application UIs. Robots use selectors (XML descriptors) to find and interact with UI elements. Issues here involve selector failures, element not found exceptions, timeout issues, Healing Agent problems, and data validation errors during UI interactions.

Namespaces: `UiPath.UIAutomationNext.Activities`, `UiPath.UIAutomation.Activities`, `UiPath.Core.Activities`

- [activity-packages/ui-automation/overview.md](./activity-packages/ui-automation/overview.md) — Package overview, selector mechanics, exception types, and dependencies
- [activity-packages/ui-automation/summary.md](./activity-packages/ui-automation/summary.md) — All playbooks for UI Automation issues

## Playbooks

All playbooks use the same headers: `## Context`, `## Investigation` (optional), `## Resolution` (optional). They vary by confidence level:

| Confidence | What you know | Investigation | Example |
|---|---|---|---|
| **High** | Exact error → exact cause | Quick verification | "GetAsset" error → asset missing |
| **Medium** | Specific error → known diagnostic path | Concrete steps | SSL cert invalid → check cert, chain, trust |
| **Low** | General symptoms → multiple causes | General guidance or absent | Robot unresponsive → could be heartbeat, network, or machine issue |

Template and full guide: [templates/playbook.md](./templates/playbook.md) | [GUIDE.md](./GUIDE.md)
