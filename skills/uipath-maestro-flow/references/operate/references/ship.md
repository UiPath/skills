# Ship — Publish a Flow

Publish journey for a Flow project. Two paths: **Studio Web upload** (default) and **Orchestrator deploy** (only when explicitly requested). Both require `uip login`.

> **When to use which path:** if the user says "publish" without specifying where, default to Studio Web. Only use Orchestrator deploy when the user explicitly asks to deploy to Orchestrator. Studio Web upload lets the user visualize, inspect, edit, and publish from the browser; Orchestrator deploy puts the flow directly into a process, bypassing Studio Web — the user cannot visualize or edit it there.

## Pre-flight

Before either publish path, ensure:

1. **Authoring is complete.** `uip maestro flow validate` passes and `uip maestro flow format` was run. If not, send the user back to [author/CAPABILITY.md](../../author/CAPABILITY.md).
2. **Logged in.** `uip login status --output json` returns success. See [shared/cli-conventions.md — Login state](../../shared/cli-conventions.md#5-login-state).
3. **Solution resources are refreshed.** Always run this before `solution upload` or `solution publish` so that connection and process resource declarations are in sync with the project bindings:

   ```bash
   uip solution resources refresh --solution-folder <SolutionDir> --output json
   ```

   `<SolutionDir>` is the solution directory (containing the `.uipx` file). The command has no positional solution argument; omit `--solution-folder` only when the current directory is already the solution root.

## Path 1 — Studio Web upload (default)

After `solution resources refresh`, upload the solution to Studio Web:

```bash
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory directly — no intermediate bundling step required. Use the exact solution root path (or `.` from inside the solution root). If your shell is inside the nested flow project folder, pass the absolute solution root path or `..`; do not pass the solution name again, because that resolves to a child path that does not exist. If the project was created with `uip maestro flow init`, it already lives inside a solution directory. The command pushes it to Studio Web where the user can visualize, inspect, edit, and publish from the browser.

**Share the Studio Web URL with the user** when the upload succeeds.

## Path 2 — Orchestrator deploy (explicit only)

Use this path **only when the user explicitly asks to deploy to Orchestrator.** Otherwise, default to Studio Web.

Pack the flow project into a `.nupkg` then publish via the platform skill:

```bash
# 1. Refresh solution resources
uip solution resources refresh --solution-folder <SolutionDir> --output json

# 2. Pack
uip maestro flow pack <project-path> <OutputDir>
```

For `uip solution publish` and the rest of the deployment workflow, see [/uipath:uipath-solution](/uipath:uipath-solution). See [shared/cli-commands.md — uip maestro flow pack](../../shared/cli-commands.md#uip-maestro-flow-pack) for `pack` flags.

## Anti-patterns

- **Never run `solution upload` without `solution resources refresh` first.** Stale resource declarations cause runtime binding failures (the deployed flow can't find its connections).
- **Never default to Orchestrator deploy when the user said "publish".** "Publish" without specifier means Studio Web. When the target is ambiguous, ask the user with **Studio Web upload** / **Orchestrator deploy** / **Something else** as options before running `flow pack` + `solution publish`. See the dropdown question rule in [SKILL.md](../../../SKILL.md).
- **Never publish a flow that hasn't been validated and formatted.** `flow validate` catches schema errors; `flow format` ensures Studio Web renders nodes correctly. Both are author-side gates — see [author/CAPABILITY.md](../../author/CAPABILITY.md).

## What's next

After Studio Web upload, the user typically wants to **debug** the flow end-to-end against real systems. See [run.md](run.md). After Orchestrator deploy, the user typically wants to **trigger and monitor** the deployed process — also [run.md](run.md).
