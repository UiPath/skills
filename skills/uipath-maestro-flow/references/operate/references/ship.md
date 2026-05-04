# Ship — Publish a Flow

Publish journey for a Flow project. Two paths: **Studio Web upload** (default) and **Orchestrator deploy** (only when explicitly requested). Both require `uip login`.

> **When to use which path:** if the user says "publish" without specifying where, default to Studio Web. Only use Orchestrator deploy when the user explicitly asks to deploy to Orchestrator. Studio Web upload lets the user visualize, inspect, edit, and publish from the browser; Orchestrator deploy puts the flow directly into a process, bypassing Studio Web — the user cannot visualize or edit it there.

## Suggested initial todos

Pre-populate these via `TodoWrite` when entering this journey. Drop the Orchestrator rows when the user is doing Studio Web upload (the default). See [shared/ux-narration-and-todos.md](../../shared/ux-narration-and-todos.md) for granularity, narration cadence, and pivot rules.

- [ ] Confirm authoring complete (`flow validate` + `flow tidy` ran)
- [ ] Confirm logged in (`uip login status`)
- [ ] Refresh solution resources (`solution resource refresh`)
- [ ] Choose path (Studio Web upload — default — or Orchestrator deploy)
- [ ] Run `solution upload` (Studio Web path) **OR** `flow pack` + `solution publish` (Orchestrator path)
- [ ] Verify Studio Web URL or Orchestrator package returned
- [ ] Report URL / package details to user

## Pre-flight

Before either publish path, ensure:

1. **Authoring is complete.** `uip maestro flow validate` passes and `uip maestro flow tidy` was run. If not, send the user back to [author/CAPABILITY.md](../../author/CAPABILITY.md).
2. **Logged in.** `uip login status --output json` returns success. See [shared/cli-conventions.md — Login state](../../shared/cli-conventions.md#4-login-state).
3. **Solution resources are refreshed.** Always run this before `solution upload` or `solution publish` so that connection and process resource declarations are in sync with the project bindings:

   ```bash
   uip solution resource refresh <SolutionDir> --output json
   ```

   The argument is the solution directory (containing the `.uipx` file). Defaults to the current directory if omitted.

## Path 1 — Studio Web upload (default)

After `solution resource refresh`, upload the solution to Studio Web:

```bash
uip solution upload <SolutionDir> --output json
```

`uip solution upload` accepts the solution directory directly — no intermediate bundling step required. If the project was created with `uip maestro flow init`, it already lives inside a solution directory. The command pushes it to Studio Web where the user can visualize, inspect, edit, and publish from the browser.

**Share the Studio Web URL with the user** when the upload succeeds.

## Path 2 — Orchestrator deploy (explicit only)

Use this path **only when the user explicitly asks to deploy to Orchestrator.** Otherwise, default to Studio Web.

Pack the flow project into a `.nupkg` then publish via the platform skill:

```bash
# 1. Refresh solution resources
uip solution resource refresh <SolutionDir> --output json

# 2. Pack
uip maestro flow pack <ProjectDir> <OutputDir>
```

For `uip solution publish` and the rest of the deployment workflow, see [/uipath:uipath-platform](/uipath:uipath-platform). See [shared/cli-commands.md — uip maestro flow pack](../../shared/cli-commands.md#uip-maestro-flow-pack) for `pack` flags.

## Anti-patterns

- **Never run `solution upload` without `solution resource refresh` first.** Stale resource declarations cause runtime binding failures (the deployed flow can't find its connections).
- **Never default to Orchestrator deploy when the user said "publish".** "Publish" without specifier means Studio Web. When the target is ambiguous, confirm via `AskUserQuestion` with **Studio Web upload** / **Orchestrator deploy** / **Something else** as options before running `flow pack` + `solution publish`. See the AskUserQuestion dropdown rule in [SKILL.md](../../../SKILL.md).
- **Never publish a flow that hasn't been validated and tidied.** `flow validate` catches schema errors; `flow tidy` ensures Studio Web renders nodes correctly. Both are author-side gates — see [author/CAPABILITY.md](../../author/CAPABILITY.md).

## What's next

After Studio Web upload, the user typically wants to **debug** the flow end-to-end against real systems. See [run.md](run.md). After Orchestrator deploy, the user typically wants to **trigger and monitor** the deployed process — also [run.md](run.md).
