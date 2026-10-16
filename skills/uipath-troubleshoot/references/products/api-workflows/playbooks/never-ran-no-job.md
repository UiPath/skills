---
confidence: medium
---

# Published API Workflow Never Ran — No Job Was Created

## Context

What this looks like:
- The user says the integration "didn't run", or "ran yesterday but not today", and there is nothing to look at — **no job record exists** for that window
- The workflow itself is fine: `run --no-auth` succeeds, and the last cloud job, if there is one, was `Successful`

**Check this first.** This playbook is for when no job record exists. If a job does exist, go elsewhere:

| What you found | Go to |
|---|---|
| A job that faulted, or `Result: "Failure"` | [run-not-successful.md](./run-not-successful.md) |
| A job stuck on `Pending` | Orchestrator — `job-pending-no-host.md` / `job-pending-stale-dispatch.md` |
| A job that ran ~15 min and stopped | [platform-limits.md](./platform-limits.md) |
| A job rejected before it started, near-zero runtime | Orchestrator — `serverless-license-quota.md` |

A published API workflow can be started three ways. Find out which one the user is expecting before you investigate — they fail for different reasons and leave different evidence behind:

| How it starts | Set up as | Why it stops starting | Where the record is |
|---|---|---|---|
| **On a schedule** | A cron trigger in Orchestrator (`--type time`) | Someone turned it off, the cron or time zone is wrong, or it still points at an old deployment | `or triggers history` |
| **On demand** | Nothing to set up — **Automations > Processes > Start a job**, an Agent using it as a tool, Maestro's "Start and wait for API workflow", or a `Run Job` activity elsewhere. Optionally an API trigger (`--type api`), which publishes it at a URL slug | Whatever was meant to call it never did. The problem is in the caller, not here | `or triggers history` if there is an API trigger — otherwise only the caller's own run |
| **On an event** | An Integration Service connector event | The connection behind the event is broken or switched off. No connection, no events | Nothing in the CLI. `--type` only covers time, queue and api |

A published workflow can always be started on demand, so "no trigger" never means "no way to run it". What it can be missing is a *schedule* or an *event* trigger — those only exist if someone created them. If the user expects the workflow to run by itself and no such trigger exists, it was never set up to.

## Investigation

1. Make sure the job really doesn't exist, rather than you not having found it yet:

   ```bash
   uip or jobs list --folder-path "<FOLDER_PATH>" --process-name "<PROCESS_NAME>" --created-after <FROM_TIMESTAMP> --output json
   ```

   You must pass one of `--folder-path`, `--folder-key` or `--all-folders`. An empty result from the wrong folder proves nothing — check the folder is right before you conclude anything.
2. Find the release a trigger would point at: `uip or processes list --folder-path "<FOLDER_PATH>" --name "<PROCESS_NAME>" --output json`. Note `Key` (that is the release key — `ProcessKey` is the package, which is not what a trigger binds to), `ProcessVersion` and `IsLatestVersion`.
3. Work out how the workflow is meant to start. Ask the user if it isn't obvious — don't assume it's on a schedule.
4. **Scheduled or on-demand trigger** — list the folder's triggers, find the one whose `ReleaseKey` matches step 2, then read its history:

   ```bash
   uip or triggers list --type time --folder-path "<FOLDER_PATH>" --output json
   uip or triggers history <TRIGGER_KEY> --folder-path "<FOLDER_PATH>" --output json
   ```

   Use `--type api` for an on-demand trigger. The listing gives you `Enabled`, `ReleaseKey`, `ReleaseName`, `StartProcessCron` and `TimeZoneId`. The history gives you `TimeStamp`, `EventType`, `Level`, `Message` and `TriggerKey`, and reads like this:
   - nothing in the window → the trigger never fired
   - `EventType: "Failed"` → the `Message` tells you why it couldn't fire
   - `EventType: "Fired"` → a job did start, so you are looking in the wrong place. Go back to step 1 and re-check the folder and time window
5. **Event trigger** — ping the connection the event comes from: `uip is connections ping <CONNECTION_UUID> --output json`. `Result: "Failure"` or `not enabled` means the event source is dead and the workflow is not at fault; [connection-auth-failure.md](./connection-auth-failure.md) covers the connection's own states. The CLI has no log of event deliveries, so you are inferring from the connection's state — say so, rather than implying you read a record that doesn't exist.
6. **On demand, no trigger** — investigate the caller instead. Follow the chain one step to the caller's own run (the Agent run, the Maestro instance, the parent job) and diagnose there. Per SKILL.md §4, more than one step → escalate.

## Resolution

These fixes all change Orchestrator, not a file on disk, so recommend them rather than applying them: print the command and let the user run it (SKILL.md invariant 10).

- **No schedule or event trigger exists:** create the one the user is expecting. If the workflow is meant to run on demand instead, nothing is broken here — the real question is why the caller didn't call.
- **Trigger switched off:** `uip or triggers update <TRIGGER_KEY> --enabled --folder-path "<FOLDER_PATH>"`. Find out who turned it off and when before you close — a disabled trigger is usually a symptom, not the cause.
- **Trigger points at an old release:** `uip or triggers update <TRIGGER_KEY> --release-key <RELEASE_KEY> --folder-path "<FOLDER_PATH>"`. This is the usual outcome when a republish created a new deployment instead of updating the existing one.
- **Wrong cron or time zone:** `uip or triggers update <TRIGGER_KEY> --cron "<CRON_EXPRESSION>" --time-zone "<IANA_TIME_ZONE>" --folder-path "<FOLDER_PATH>"`, then check the next run actually lands where you expect in `or triggers history` instead of assuming it will.
- **Event connection broken:** fix the connection first — `uip is connections edit <CONNECTION_UUID>` re-runs the OAuth flow — then confirm events start arriving again. The workflow needs no change.
- **Caller never called:** the cause is in the caller. Say so, and name the path from the caller to this workflow. Never report the API workflow as healthy without saying what failed to start it.
