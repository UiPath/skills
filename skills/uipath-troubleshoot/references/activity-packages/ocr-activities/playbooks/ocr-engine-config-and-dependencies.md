---
confidence: medium
---

# OCR Engine Configuration & Dependency Errors

## Context

A UiPath OCR activity failed before or during engine initialization — a missing dependency package, an incompatible companion-package version, an unsupported engine, or a missing required setting. These fail deterministically on the robot host regardless of the image. Route on the message text.

What this looks like:
- `Please make sure you have the UiPath.ComputerVision.LocalServer package version <n> or higher installed in order to use local server mode.` (`NotSupportedException`) — Screen OCR in local mode without the CV LocalServer package.
- `Please make sure you have the UiPath.DocumentUnderstanding.OCR.LocalServer package installed in order to use local server mode.` (`NotSupportedException`) — Document OCR in local mode without the DU OCR LocalServer package.
- `In order to use this activity in this Studio version, please install the UiPath.CoreIPC package, version 2.0.1 or higher. For more information please check the documentation.` — missing CoreIPC on the host-process path.
- `This version of the OCR.Activities package is incompatible with UiPath.IntelligentOCR.Activities older than v6.20.0, UiPath.PDF.Activities older than v3.20.0, UiPath.DocumentUnderstanding.ML.Activities older than v1.29.0, UiPath.OmniPage.Activities older than v1.20.0` — mismatched companion package versions.
- `Value for a required activity argument 'ApiKey' was not supplied.` / `Value for a required activity argument <name> was not supplied in activity designer nor in project settings.` — a required setting is missing.
- `Unsupported engine: <engine>` — an invalid engine selection reached the engine factory.
- `Timeout must be a number greater than 0.` (`ArgumentOutOfRangeException`) — a non-positive timeout value.

What can cause it:
- Local server mode is on but the matching LocalServer package (CV or DU) is not installed in the project.
- Companion packages (IntelligentOCR, PDF, DU.ML, OmniPage) are older than the versions this OCR.Activities release requires.
- The required `ApiKey` / `Endpoint` is not set in project settings or bound on the activity.
- An out-of-range engine or timeout value.

What to look for:
- The message plus the OCR activity and its `UseLocalServer` setting.
- The installed package set and versions in `project.json` vs the compatibility message.
- Whether `ApiKey` / `Endpoint` are set (project settings or bindings) and `Timeout` is positive.

## Investigation

1. Capture the message and the faulted OCR activity, and read its `UseLocalServer` setting.
2. Compare installed package versions in `project.json` against any compatibility message.
3. Confirm the required `ApiKey` / `Endpoint` are supplied and `Timeout` is greater than 0.

## Resolution

### Missing local-server package
Install the named LocalServer package (`UiPath.ComputerVision.LocalServer` for Screen, `UiPath.DocumentUnderstanding.OCR.LocalServer` for Document) at the required version, or turn off local server mode to use the cloud endpoint.

### Missing CoreIPC
Install `UiPath.CoreIPC` version 2.0.1 or higher.

### Incompatible companion versions
Upgrade the named companion packages (IntelligentOCR, PDF, DU.ML, OmniPage) to at least the stated minimums.

### Required `ApiKey` / `Endpoint` not supplied
Set them in Project Settings for the OCR engine, or bind them on the activity.

### `Unsupported engine`
Select a supported engine (Screen / Document / CJK) for the activity.

### `Timeout must be a number greater than 0.`
Set a positive `Timeout` value.
