# Publish and Debug Guide

How to test and publish UiPath Flow projects. Both CLI and JSON authoring modes converge here -- publishing and debugging always use the `uip` CLI.

---

## Debug (Cloud)

Debug uploads the flow to Studio Web, triggers a debug session in Orchestrator, and streams results back. It executes the flow **for real** -- sends emails, posts messages, calls APIs.

### Requirements

- `uip login` -- active authentication required.
- A valid project directory (the folder containing `project.uiproj`).
- The flow must pass `uip flow validate` before debugging.

### Command

```bash
UIPCLI_LOG_LEVEL=info uip flow debug <path-to-project-dir>
```

The argument is the **project directory path** (the folder containing `project.uiproj`). Use `<ProjectName>/` from the solution directory, or `.` if already inside the project directory.

### What It Does

1. Converts the `.flow` file to BPMN format.
2. Uploads the project to Studio Web.
3. Triggers a debug session in Orchestrator.
4. Streams execution results back to the terminal.

### Consent Requirement

> **Do NOT run `uip flow debug` without explicit user consent.** Debug executes the flow with real side effects. Always ask before running.

### Interpreting Results

Debug output follows the standard CLI output format (see below). A `"Result": "Success"` means the flow executed without errors. Check `Data` for node-level outputs. If a node fails, the error details appear in the node's error output (`$vars.<nodeId>.error`).

---

## Publish to Studio Web (Default)

This is the **default publish target**. When the user wants to publish, view, or share the flow, use this path.

### Command

```bash
# 1. Bundle the solution directory into a .uis file
uip solution bundle <SolutionDir> --output .

# 2. Upload the .uis to Studio Web
uip solution upload <SolutionName>.uis --output json
```

### When to Use

- User says "publish", "upload", or "share" without specifying Orchestrator.
- User wants to visualize or edit the flow in the browser.
- Default path for all publish requests.

### What It Does

1. `solution bundle` packages the solution directory (must contain a `.uipx` file) into a `.uis` archive.
2. `solution upload` pushes the archive to Studio Web.
3. The user can then visualize, inspect, edit, and publish from the browser.

Share the Studio Web URL with the user after uploading.

---

## Publish to Orchestrator (Only When Explicitly Requested)

This path puts the flow directly into Orchestrator as a process, **bypassing Studio Web**. The user cannot visualize or edit the flow in Studio Web after this.

> **Do NOT use this path unless the user explicitly asks to deploy to Orchestrator.** If the user says "publish" without specifying where, always default to the Studio Web path above.

### Command

```bash
uip flow pack <path-to-project-dir>
```

This creates a `.nupkg` package that can be published to Orchestrator using `uip solution publish` or uploaded manually. See the `uipath-platform` skill for Orchestrator deployment commands.

### When to Use

- User explicitly says "deploy to Orchestrator" or "publish to Orchestrator".
- User needs the flow available as an Orchestrator process (not just in Studio Web).

---

## `validate` vs `debug` Comparison

| | `uip flow validate` | `uip flow debug` |
|---|---|---|
| **What it does** | Local JSON schema + cross-reference check | Converts to BPMN, uploads to Studio Web, runs in Orchestrator, streams results |
| **Auth needed** | No | Yes (`uip login`) |
| **Side effects** | None | Real execution (sends emails, posts messages, calls APIs) |
| **Speed** | Instant | Cloud round-trip (seconds to minutes) |
| **What it catches** | Missing `targetPort`, missing definitions, invalid references, duplicate IDs | Runtime errors, connection failures, expression evaluation errors, resource unavailability |
| **When to use** | After every structural edit | Only when the user explicitly requests end-to-end testing |

Always `validate` locally before `debug`. Validation is instant; debug is a cloud round-trip.

---

## CLI Output Format

All `uip` commands return structured JSON when invoked with `--output json`:

**Success:**

```json
{ "Result": "Success", "Code": "FlowValidate", "Data": { } }
```

**Failure:**

```json
{ "Result": "Failure", "Message": "...", "Instructions": "Found N error(s): ..." }
```

Always use `--output json` for programmatic use. The `--localstorage-file` warning that appears in some environments is benign and can be ignored.
