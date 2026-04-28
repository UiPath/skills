# Compliance · Assistant — product quirks

Product-specific CLI value conventions and error patterns for `productIdentifier: "Assistant"`. Follow the shared CREATE recipe in [../../../policy-crud.md](../../../policy-crud.md). This file lists only what's Assistant-specific.

## Product identifiers

| Field | Value |
|---|---|
| `--product-name` | `Assistant` (exact case) |
| Default license | `Attended` (Assistant is a per-user attended product) |

## CLI value quirks — will cause 400 if wrong

### ⚠ `"yes"` / `"no"` strings (NOT booleans)

Assistant uses string toggles for almost every "allow users to X" setting. This is the same quirk as AITL's `allow-llm-model-auto-routing`, but Assistant has **14 such fields**. If your pack passes `true` or `false`, the API will reject.

| Property | Accepted values |
|---|---|
| `allowCustomWidgets` | `"yes"` \| `"no"` |
| `allowTaskCapture` | `"yes"` \| `"no"` |
| `allowTaskMining` | `"yes"` \| `"no"` |
| `enableGroupByFolder` | `"yes"` \| `"no"` |
| `minimizeWhileRunning` | `"yes"` \| `"no"` |
| `launchAtStartup` | `"yes"` \| `"no"` |
| `assistantAllowLoggingChanges` | `"yes"` \| `"no"` |
| `allowAutomationsOutsidePw` | `"yes"` \| `"no"` |
| `allowActionCenter` | `"yes"` \| `"no"` |
| `assistantAllowCopyAutomationLink` | `"yes"` \| `"no"` |
| `displayEdrMessage` | `"yes"` \| `"no"` |
| `switchToRunningTab` | `"yes"` \| `"no"` |
| `allowStudioWeb` | `"yes"` \| `"no"` |
| `showPip` | `"yes"` \| `"no"` |

### Widget array — requires identifier field

`widgets-edit-grid[]` items must include an `identifier` field (concatenation of name + version) to survive update round-trips. The generate-data default has the full shape — follow it exactly when extending.

```jsonc
{
  "is-enabled": true,
  "name": "UiPath.Autopilot.Assistant.Widget",
  "version": "1.2.3",
  "identifier": "UiPath.Autopilot.Assistant.Widget1.2.3"
}
```

## Error triage

| Error message fragment | Likely cause | Action |
|---|---|---|
| `allowCustomWidgets` (or any other yes/no field) type mismatch | Passed as boolean `true`/`false` | Halt. Bug in pack or upstream synthesis — coerce to `"yes"`/`"no"`. |
| Widget `identifier` missing / mismatch | Array item constructed without concatenating name+version | Halt. Rebuild the item following the generate-data shape. |
