# Beep

`UiPath.Core.Activities.Beep`

Generates a simple tone on the speaker.

**Package:** `UiPath.System.Activities`
**Category:** System.Environment

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|

_This activity has no configurable properties._

## XAML Example

```xml
<ui:Beep />
```

## Notes

- Plays the system `Beep` sound using `System.Media.SystemSounds.Beep.Play()`.
- The tone is determined by the operating system's default beep sound; frequency and duration cannot be customised through this activity.
- If the system has no audio output device or the beep sound is muted, the activity completes silently without error.
