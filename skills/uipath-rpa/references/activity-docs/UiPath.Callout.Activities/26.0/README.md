# UiPath.Callout.Activities

> NuGet Package ID: `UiPath.Callout.Activities`

## Overview

The Callout Activities package provides the **Show Callout** activity, which displays a form-based callout anchored to a UI element on screen. Unlike regular forms, callouts automatically track and follow their target element, providing contextual guidance overlays for attended automations.

## Activity

| Activity | Description |
|----------|-------------|
| [Show Callout](activities.md) | Displays a callout anchored to a UI element |

## How Callouts Differ from Forms

| Aspect | Forms | Callouts |
|--------|-------|----------|
| Positioning | Manual (Left/Top) or unset | Anchored to a UI element, auto-positioned |
| Pointer | No | Yes (visual arrow toward target) |
| Window chrome | Configurable | Off by default |
| Taskbar | Configurable | Hidden by default |
| Execution mode | Async or Sync | Always Async |
| ContinueOnError | Not available | Available (defaults to true) |
| Auto-close timer | Not available | Available |
| Requires UI target | No | Yes |

## Dependencies

This package depends on `UiPath.Form.Activities` (for the forms infrastructure) and uses UI Automation for element targeting.

## Platform Support

Windows only (requires native UI element tracking).
