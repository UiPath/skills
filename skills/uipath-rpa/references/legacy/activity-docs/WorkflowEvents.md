# UiPath WorkflowEvents Activities - Legacy Reference

## Overview
App-triggered workflow invocation and two-way communication via SignalR. Package: `UiPath.WorkflowEvents.Activities`.

---

## Key Activities

| Activity | Purpose | Key Arguments |
|----------|---------|---------------|
| `AppRequestTrigger` | Listen for app workflow requests | ConnectionMode (RobotJS/Cloud), Arguments (output) |
| `HandleAppRequest` | Execute and respond to request | Arguments (from trigger), Timeout |
| `SendInterimResult` | Push intermediate status | (mid-execution update to app) |

### Supporting Activities
- `OpenAppsPage` / `OpenAppsUrl` - Navigation
- `CloseAppsPopOver` / `ResetAppsValues` - UI state
- `ShowAppsToast` / `ShowHideAppsSpinner` - Notifications
- `SubmitAction` - Form submission
- `DetectChangesActivity` - Change detection

---

## Critical Gotchas

1. **Heartbeat required every 30 seconds** or connection drops
2. **SignalR idle timeout: 90 seconds** - connection terminated if no activity
3. **Workflow context must serialize/deserialize cleanly** for data transfer
4. **Remote execution requires IPC bridge** setup
5. **Apps UI state must sync with workflow state** - race conditions possible
6. **Serialization failures break request handling** silently
7. **ConnectionMode**: RobotJS (local) vs Cloud (Orchestrator-mediated)
8. **SignalR timeout configurable**: SignalRTimeoutMS = 90,000ms default
