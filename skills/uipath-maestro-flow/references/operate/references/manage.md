# Manage — Instance Lifecycle

Intervene in a running or faulted Flow instance: pause, resume, cancel, retry. All commands require `uip login` and `--folder-key <FOLDER_KEY>` (`-f` shorthand).

> **Stub-with-content.** This guide ships with the canonical command list. Use-case framing (when to pause vs cancel, retry semantics, partial-flow recovery) is a TODO for a future expansion.

## Pre-flight

1. **Logged in.** `uip login status --output json` returns success.
2. **Folder key resolved.** Get it from `uip orchestrator folder list --output json` or from the job/process context. See [shared/cli-conventions.md — `--folder-key` requirement](../../shared/cli-conventions.md#5---folder-key-requirement).
3. **Instance ID known.** From a debug run (`Data.instanceId`), `flow job status` response, or `instance list`.

## Lifecycle commands

```bash
uip maestro flow instance pause <INSTANCE_ID> -f <FOLDER_KEY> --output json    # pause a running instance
uip maestro flow instance resume <INSTANCE_ID> -f <FOLDER_KEY> --output json   # resume a paused instance
uip maestro flow instance cancel <INSTANCE_ID> -f <FOLDER_KEY> --output json   # cancel an instance
uip maestro flow instance retry <INSTANCE_ID> -f <FOLDER_KEY> --output json    # retry a faulted instance
```

| Command | What it does |
| --- | --- |
| `pause` | Pause a running instance. |
| `resume` | Resume a paused instance. |
| `cancel` | Cancel an instance. |
| `retry` | Retry a faulted instance. Use after fixing the underlying issue. |

> **Runtime semantics** (when each takes effect, recoverability, partial-flow behavior) are not documented in this skill. Run `uip maestro flow instance <subcommand> --help` for any options the CLI exposes; consult Orchestrator docs for the underlying lifecycle model.

## What's next

- **Need to inspect why an instance faulted before deciding pause/cancel/retry?** Triage via [DIAGNOSE.md](../../diagnose/CAPABILITY.md) first — get incidents and runtime variables before intervening.
- **Need to look up the full `instance` CLI surface?** See [shared/cli-commands.md](../../shared/cli-commands.md) and [diagnose/troubleshooting-guide.md — CLI command reference](../../diagnose/references/troubleshooting-guide.md#cli-command-reference).

## Anti-patterns

- **Never `retry` a faulted instance without diagnosing the root cause first.** Triage via [DIAGNOSE.md](../../diagnose/CAPABILITY.md) — read incidents, runtime variables, and the deployed asset. Then decide whether to retry, cancel, or re-author.
- **Never skip the `--folder-key` flag.** Without it the command rejects before reaching the API.
