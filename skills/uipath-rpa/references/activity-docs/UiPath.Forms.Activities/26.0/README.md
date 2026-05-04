# UiPath.Form.Activities

> NuGet Package ID: `UiPath.Form.Activities`

## Overview

The Forms Activities package provides workflow activities for displaying and interacting with Form.io-based forms in UiPath automations. Forms are designed in UiPath Studio's Form Designer and displayed at runtime as standalone windows.

The package supports both **synchronous** (blocking) and **asynchronous** (non-blocking) form display, bi-directional data binding with workflow variables (including Global Variables), event-driven triggers, and programmatic manipulation of running forms.

## Activities

| Activity | Description |
|----------|-------------|
| [Show Form](activities.md#show-form) | Displays a form designed in Studio |
| [Close Form](activities.md#close-form) | Closes a running form |
| [Get Form Fields](activities.md#get-form-fields) | Reads field values from a running form |
| [Set Form Fields](activities.md#set-form-fields) | Sets field values on a running form |
| [Change Form Properties](activities.md#change-form-properties) | Modifies window properties (size, position, title, state) |
| [Hide Form](activities.md#hide-form) | Hides a running form window |
| [Bring Form To Front](activities.md#bring-form-to-front) | Brings a hidden form back to the foreground |
| [Execute Script](activities.md#execute-script) | Executes JavaScript within a running form |
| [Form Trigger](triggers.md) | Reacts to form events (value changes, button clicks, etc.) |

## Documentation

- **[activities.md](activities.md)** - Activity reference: properties, usage, and errors
- **[triggers.md](triggers.md)** - Form event triggers and supported event types

## Key Concepts

### Form Identification

Every form has a **FormId** (the design-time source identifier, set automatically when you pick a form in the designer) and an optional **InstanceName** that distinguishes multiple instances of the same form. All form-action activities (Close, Get/Set Fields, etc.) use these two properties to address a specific running form.

### Execution Modes

- **Async** (`IsAsync = true`, default): Show Form completes immediately. The workflow continues while the form stays open. Use triggers and Get/Set Form Fields to interact with it.
- **Sync** (`IsAsync = false`): Show Form blocks until the form is closed. Out-argument values are applied when the form closes.

### Data Binding

Form field values can be bound to workflow variables via the `Arguments` dictionary:
- **InArgument**: Provides initial values when the form is shown
- **OutArgument**: Receives values when the form closes (sync) or in real time (async)
- **InOutArgument**: Both directions

### Global Variables

When form arguments reference Global Variables, changes propagate bidirectionally in real time: modifying the Global Variable updates the form field, and modifying the form field updates the Global Variable.

## Common Errors

| Error | Cause |
|-------|-------|
| Form not found | No running form matches the FormId/InstanceName, or no form has been shown yet |
| Form already displayed | Trying to show a form with the same FormId and InstanceName as one already open |
| No form selected | FormId is not set (pick a form in the designer) |
| No event selected | Form Trigger used without selecting an event |
