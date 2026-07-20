# Operating & Diagnosing a Published API Workflow

After `uip solution publish` + deploy, the workflow lives in Orchestrator as an **API process**. The local authoring verbs (`uip api-workflow init/validate/run/pack`) no longer apply to the deployed copy — operate and diagnose it through the platform surfaces below.

**These commands belong to sibling skills** — `uip or` / `uip is` to `uipath-platform`, root-cause to `uipath-troubleshoot`. They are the correct owners for depth (flags, folder scoping, auth). Listed here so the operate + diagnose loop is discoverable and actionable from this skill; if a sibling skill is unavailable, the commands below still run standalone. All require `uip login`.

## Invoke a published workflow (the three trigger types)

A published API workflow is started three ways — the same three trigger types the product exposes:

| Trigger | When it fires | Drive it with |
|---------|---------------|---------------|
| **HTTP** | A caller (app, agent, external system) POSTs a JSON payload matching the workflow's `input.schema`; runs synchronously, returns the `Response` output | Start a run as an Orchestrator job: `uip or jobs start <process-key> --output json` |
| **Schedule** | Cron cadence managed in Orchestrator | `uip or triggers create` / `list` / `get` / `update` / `delete` |
| **Integration Service event** | An upstream connector event/webhook (Salesforce opportunity closed, new Snowflake row, Slack message) starts it and passes the event payload as input | Configure the event subscription in Integration Service; inspect with `uip or triggers list --folder-path <path>` |

All three deliver the payload as the workflow's input variables — the same body runs under any trigger if the input shape matches.

> **`uip or` commands are folder-scoped — but the accepted selectors differ per command:**
> - `jobs list` requires `--folder-path <path>`, `--folder-key <key>`, **or** `--all-folders` (searches every folder).
> - `triggers list`/`create`/`get`/`update`/`delete` require `--folder-path <path>` or `--folder-key <key>` — they do **not** accept `--all-folders`.
> - `jobs start <process-key>` takes the process key as a required positional; the folder is **optional** (inferred from the process if omitted).
> - `jobs get`/`logs`/`stop` take a `<jobId>` directly — no folder selector.

## Manage the Integration Service connections it consumes

API workflows don't own connections — they bind named Integration Service connections at author time and reuse them at runtime.

```bash
uip is connections list --all-folders --output json   # enumerate (folder-scoped; --all-folders searches every folder)
uip is connections ping <connection-uuid> --output json # health — Code: "ConnectionPing" = usable
uip is connections edit <connection-uuid>               # re-authenticate (opens OAuth browser flow)
```

A workflow authored against a connection that does not `ping` 401s in cloud regardless of how correct the JSON is. See [connector-activity-discovery.md](connector-activity-discovery.md) for the author-time discovery+verify flow and [troubleshooting.md](troubleshooting.md) for the stale-listing / `ConnectionNotEnabled` failure modes.

## Run / manage the deployed process

```bash
uip or processes list --output json                     # confirm the API process deployed
uip or jobs start <process-key> --output json           # invoke a run (folder optional — inferred from the process)
uip or jobs list --all-folders --output json            # runs + their states (needs a folder selector)
uip or jobs get <jobId> --output json                   # one run's status / fault detail
uip or jobs stop <jobId> --output json                  # cancel a running job
```

## Diagnose a failed cloud run

The local diagnose loop catches structure/expression faults **before** publish — always run it first:

```bash
uip api-workflow validate ./Workflow.json --output json   # static: schema + semantic
uip api-workflow run ./Workflow.json --no-auth --output json  # runtime: expression / logic
```

Faults that only surface in cloud (auth, connection state, real vendor responses, trigger wiring) are diagnosed from the deployed job:

```bash
uip or jobs get <jobId> --output json                  # status + fault summary
uip or jobs logs <jobId> --output json                 # execution logs for the run
uip traces spans get --job-key <jobKey> --output json  # span-level execution trace (also accepts a <trace-id> positional)
```

> `uip or jobs traces` is documented Agent-type-process-only — for an API-workflow job use `uip traces spans get --job-key <jobKey>` instead.

Map the surfaced error back to a fix using the category catalog in [troubleshooting.md](troubleshooting.md) (Structure > Expression > Activity Config > Logic). For deep, multi-signal root-cause investigations (what changed, cross-run comparison, incident correlation), hand off to **uipath-troubleshoot**.

## Mode cheat-sheet

| Mode | Local (this skill's CLI) | Post-publish (delegate) |
|------|--------------------------|-------------------------|
| **Build** | `init`, edit, `validate`, `registry resolve`/`stub`, `pack` | — |
| **Operate** | `run` (local execution) | `uip or jobs start <process-key>`/`list`/`stop`, `uip or triggers` (need `--folder-path`/`--folder-key`), `uip is connections` |
| **Diagnose** | `validate` → `run --no-auth` loop, `uip is connections ping` | `uip or jobs logs`/`get`, `uip traces spans get --job-key`, uipath-troubleshoot |
