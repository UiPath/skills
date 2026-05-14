---
confidence: high
---

# No Message Events Found (400)

## Context

What this looks like:
- HTTP 400 at Message Start Event or Message Receive Event
- Error message: `No Message events found. Generate a trigger event that matches the expected format and try again.`
- Variants name a specific source — `No File events found` for OneDrive/SharePoint file triggers

What can cause it:
- The trigger event was never generated at the source (e.g., no new file in SharePoint)
- The event was generated but does not match the configured connector/action/object filter
- Integration Service connection backing the trigger is misconfigured or expired
- Debug mode does not always exercise triggers — known design-time limitation for SharePoint and similar triggers

What to look for:
- Message Start Event's Implementation: connector, action ("Wait for connector event"), event type
- Whether the user is debugging vs running the deployed workflow
- Whether the inbound event matches the configured filter (folder, file extension, mailbox, etc.)

## Investigation

1. Get the incident: `uip maestro instance incidents <instance-id> -f <folder-key> --output json`
2. Inspect the BPMN to confirm the Message Start Event configuration: `uip maestro instance asset <instance-id> -f <folder-key> --output json`
3. Check the Integration Service connection's health in Orchestrator UI → **Integration Service > Connections**
4. Trigger a test event from the external system that meets the configured filter; confirm via the connector's event log
5. If user is in debug, ask whether the same trigger works in the published flow

## Resolution

- **If trigger config wrong:** set the Implementation to "Wait for connector event"; pick the right connector and event type
- **If connection expired:** re-authenticate the IS connection
- **If filter mismatch:** generate an event that satisfies the filter (correct folder, file type, channel)
- **If debug-only limitation:** publish the workflow and run it deployed; design-time debug has known limitations for some triggers
- **If using a custom webhook:** regenerate the webhook URL on the connector and re-register it in the external system

## Notes

- This error is **Not Troubleshootable** from PIMS API alone — incident lacks the trigger configuration details and the inbound event format. Expect to ask the user for the failing element name and to share the trigger config

## References

- [Docs: Events in BPMN](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/events-in-bpmn-modeling-perspective)
- [Docs: Events](https://docs.uipath.com/maestro/automation-cloud/latest/user-guide/events)
