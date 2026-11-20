# End-to-End Readiness: Publish, Schedule, Run

Check what the tenant can do **before** offering to take an automation from a built package to a scheduled, running process. Publishing, creating a trigger and running a job have different prerequisites. A tenant often supports the first two and not the third, and the user should hear that before anything is published.

## When to Use

- Before offering or agreeing to "publish it and schedule it", "run it every day", "deploy and run it", or any plan that ends in a job running in Orchestrator
- Before creating a time, queue or API trigger
- Before reporting that a published automation is scheduled or running

## Rules

1. **Check, then offer.** Run the read-only checks below before proposing the end-to-end plan, not after publishing. Never promise a stage you have not checked.
2. **Name each stage's status separately.** Publish, trigger creation and execution are three outcomes. One missing prerequisite blocks only the stages that need it.
3. **Explain a gap before acting, with the fix.** Say what is missing, why it matters and what the user (or an admin) has to do, then ask whether to go ahead with the stages that can proceed.
4. **Report a stage as done only after confirming it** with the read-back command in [§ Confirm Each Stage](#confirm-each-stage). A created trigger is not a successful run.

## Prerequisites per Stage

| Stage | Needs | How to check |
|---|---|---|
| Publish | Signed in; a feed that accepts the package type; permission to upload to it | `uip login status --output json`; `uip or folders list --output json` (pick the destination folder) |
| Process in a folder | The package published; the folder exists | `uip or processes list --folder-path "<folder>" --output json` |
| Trigger creation | The process exists in the folder | Same as above. A trigger does **not** need a robot to be created. |
| Execution (trigger firing or `jobs start`) | A runtime of the type the job will use, assigned to the folder and connected | `uip or folders runtimes "<folder>" --output json`; `uip or sessions unattended list --folder-path "<folder>" --output json` |
| Execution: package resources | Assets, queues and buckets the package declares exist in the folder | After the process exists: `uip or processes resources <process-key> --output json` (see [run-jobs.md](run-jobs.md)) |

## Check Execution Readiness

```bash
uip or folders runtimes "<folder>" --output json
```

Each row of `Data` has `Type`, `Total`, `Connected` and `Available`. Read the row for the runtime type the trigger or job will use (`--runtime-type`; `Unattended` unless the user chose otherwise):

| Row | Execution status | Tell the user |
|---|---|---|
| `Total` is `0` | **Blocked** | The folder has no runtime of that type, so nothing will run (`jobs start` fails with error 2818 "no runtimes configured"). An admin has to assign a machine (template) with that runtime type to the folder ([setup-environment.md](setup-environment.md)), or the user picks another folder or runtime type that has one. |
| `Total` > `0`, `Connected` is `0` | **Blocked until a robot connects** | Runtimes are assigned but no machine is connected. Someone has to bring the machine online (sign in its robot / start the service). Jobs wait in `Pending` until then. |
| `Connected` > `0`, `Available` is `0` | **Will queue** | Robots are connected but busy. Jobs start when one frees up. |
| `Available` > `0` | **Ready** | — |

`uip or sessions unattended list --folder-path "<folder>" --runtime-type <type> --output json` names the machines behind those numbers when the user asks which robot will run it. For a job that stays `Pending`, `uip or jobs get <job-key> --output json` includes the reasons (robot availability, capacity).

## Offer the Plan

State each stage with its status before acting. For example, when the folder has no Unattended runtime:

> I can publish the package and create the daily 9:00 trigger in **Finance**. It won't run yet: Finance has no Unattended runtime, so there is no robot to run it. An admin needs to assign a machine with Unattended runtimes to the Finance folder in Orchestrator. Should I publish and create the trigger now — disabled, so it doesn't fire until a robot is assigned — or wait?

Create a trigger with `--disabled` when execution is blocked and the user wants the trigger anyway. Turn it on later with `uip or triggers update <key> --type time --enabled`.

## Confirm Each Stage

| Stage | Done when | Command |
|---|---|---|
| Publish | The package version is in the feed (and, for a folder process, the process exists) | `uip or packages list --output json`; `uip or processes list --folder-path "<folder>" --output json` |
| Trigger | The trigger exists with the expected schedule and enabled state | `uip or triggers get <trigger-key> --type time --folder-path "<folder>" --output json` (read `StartProcessCronSummary` and `Enabled`) |
| Execution | A job of the process reached `Running` or `Successful` | `uip or jobs list --folder-path "<folder>" --output json`, then `uip or jobs get <job-key> --output json` |

Until a job has run, report execution as "scheduled, next run at …, not yet run" — or as "blocked: <reason>" — never as done. If the user wants proof now, offer a one-off `uip or jobs start` and report its final state.

## Related

- [triggers-and-webhooks.md](triggers-and-webhooks.md) — trigger creation and options
- [run-jobs.md](run-jobs.md) — processes, `processes resources`, starting and monitoring jobs
- [manage-sessions.md](manage-sessions.md) — runtimes and robot sessions
- [setup-environment.md](setup-environment.md) — assigning machines and users to folders
