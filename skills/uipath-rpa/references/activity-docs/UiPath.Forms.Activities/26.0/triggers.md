# Form Triggers

## Overview

The **Form Trigger** activity monitors a running form and fires when a specific event occurs (e.g., a field value changes, a button is clicked, the window state changes). It can be used inside a **Trigger Scope** or as a standalone trigger.

## Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| FormId | String | No | The form to monitor (selected in the designer) |
| InstanceName | String | No | Instance tag filter |
| Event | String | Yes | The event to listen for (selected from a dropdown of available events) |
| MessageId | String | No | For message events only: filters by message ID |
| Enabled | Boolean | No | Whether the trigger is active |
| SchedulingMode | TriggerActionSchedulingMode | No | How trigger firings are scheduled (only visible outside Trigger Scope) |

## Event Types and Output

When you select a form in the designer, the available events are populated from the form definition. The trigger output varies based on the event type:

| Event Data Type | Output Properties |
|----------------|-------------------|
| Number | `Value` (Double?) |
| Boolean | `Value` (Boolean?) |
| Text | `Text` (String) |
| Password | `Password` (SecureString) |
| Window State | `State` (WindowState) |
| Message | `Data` (String), `Id` (String) |
| DataTable | `Value` (DataTable) |
| Dictionary | `Value` (Dictionary&lt;String, String&gt;) |
| *(generic)* | Base properties only |

### Base Properties (always available)

All trigger outputs include:

| Property | Type | Description |
|----------|------|-------------|
| FormSourceId | String | The form's design-time identifier |
| InstanceName | String | The form's instance tag |
| Index | Int32? | Event index within the form |

## Usage

1. Add a **Form Trigger** activity (typically inside a **Trigger Scope**)
2. Select the form to monitor
3. Select the event from the dropdown (populated from the form definition)
4. For **Message** events, set the `MessageId` to filter which messages trigger the action
5. Use the trigger output properties in the trigger body

## Message Events

Message events are for custom form-to-workflow communication via JavaScript `postMessage`. Set the `MessageId` property to filter by message type. The `Data` property contains the message payload as a string.
