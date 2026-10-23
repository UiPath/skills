<!--skill-flavor:solution-commands-row:start-->
<!--skill-flavor:solution-commands-row:end-->

<!--skill-flavor:solution-init-section:start-->
## Solution

Studio Web works on one open solution, already scaffolded as the workspace root (`/solution`); never create another. The case project is created inside it with `uip maestro case init "<ProjectName>"` (see below).
<!--skill-flavor:solution-init-section:end-->

<!--skill-flavor:cd-mandatory-note:start-->
> **Run `case init` from the solution root (`/solution`).** Studio Web creates the project in the open solution at `/solution/<ProjectName>/`; there is no solution to create first and no second solution can be scaffolded by accident.
<!--skill-flavor:cd-mandatory-note:end-->

<!--skill-flavor:case-init-command:start-->
```bash
uip maestro case init <ProjectName>   # from the solution root, /solution
```
<!--skill-flavor:case-init-command:end-->

<!--skill-flavor:case-init-semantics:start-->
`case init` creates the project in the open Studio Web solution at `/solution/<ProjectName>/` and seeds its scaffold. There is no auto-scaffolded sibling solution, no `.uipx` on disk, and no registration step — Studio Web owns the solution manifest — so `--skip-solution-registration` and `uip solution projects add` have nothing to do here.
<!--skill-flavor:case-init-semantics:end-->

<!--skill-flavor:projects-add-section:start-->
## uip solution projects add

Not used in Studio Web: there is no `.uipx` on disk and Studio Web owns project registration — `uip maestro case init` already places the project in the open solution, and the verb is Node-CLI-only.
<!--skill-flavor:projects-add-section:end-->

<!--skill-flavor:phase-seven-row:start-->
| `solution publish` | Phase 7 Publish (consent-gated) — Studio Web packages and publishes the open solution; `maestro case pack` / `solution pack` are Node-CLI-only | Host-injected |
<!--skill-flavor:phase-seven-row:end-->

<!--skill-flavor:resources-row:start-->
| `solution resources list [--source local]`, `solution resources get <key>`, `solution resources add --source local\|remote`, `solution resources edit <key>` | Inventory read (`list`/`get`) + atomic single-resource mutations (local stub or remote import; patch spec via `--patch '<json>'`) — see [uipath-solution Step 9–11](/uipath:uipath-solution). `refresh` and `remove` are Node-CLI-only; the host keeps resources in sync | Host-injected |
<!--skill-flavor:resources-row:end-->

<!--skill-flavor:auth-column-note:start-->
> **Auth column — not applicable in Studio Web.** The host injects your session on every call. `uip login` / `logout` / `auth` / `config` are not in the Studio Web CLI — never run them, and never check login state.
<!--skill-flavor:auth-column-note:end-->

<!--skill-flavor:case-debug-command:start-->
## uip case debug

Debug a case in the open solution through the host. **Executes the case for real: sends emails, posts messages, calls APIs. Only run on explicit user consent.** In Studio Web the verb is `uip case debug`; `uip maestro case debug` is unavailable here.

```bash
uip case debug "<ProjectName>"
uip case debug "<ProjectName>" --inputs '{"claimId": "C-1"}'
```

| Flag | Description |
|------|-------------|
| `[project]` | Project name in the open solution, not a path. Defaults to the active project |
| `-i, --inputs <json>` | Inline JSON only; `@file` is not supported |
| `--entry-point <path>` | Entry point as `entry-points.json` spells it. Defaults to the project's default |
| `--timeout <seconds>` | Seconds to wait for a terminal state. Default `120`, clamped to `10`-`150` |

Output is plain text, not JSON: status, `Trace ID: <id>`, run logs, execution trace. Exit 1 means the run faulted. Run `uip case debug --help` for the host's exact surface.
<!--skill-flavor:case-debug-command:end-->
