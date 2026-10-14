---
name: uipath-vertical-solutions
description: "UiPath Vertical Solutions via `uip vss deploy` — guided deploy of an industry solution package such as FINS (Financial Services) Loan Setup (`fins.loan-setup`) or Lending QA/QC (`fins.qaqc-uipath`): fresh install, upgrade/downgrade, deploy job status/resume/cancel, Data Fabric seeding (`uip vss deploy seed`), setting up a deployed solution (such as the FINS role groups), and checking the deploying user's tenant and folder access. Diagnoses refused or paused deploy jobs. For packing/deploying your own `.uipx` with `uip solution`→uipath-solution; Orchestrator folders/queues/roles or Data Fabric records outside a deploy→uipath-platform; other Identity users/groups/external apps→uipath-admin; faulted runtime jobs→uipath-troubleshoot."
when_to_use: "User says 'deploy a vertical solution', 'deploy FINS Loan Setup', 'deploy LoanQAQC', 'uip vss deploy', 'upgrade the vertical solution', 'deploy job paused', 'resume the deploy', 'cancel the deploy job', 'seed the deployed solution', 'help me set up QA/QC', 'set up Loan Setup roles', 'what access do I need to deploy FINS', or shows a deploy error such as 'User doesn't have permissions SolutionDeployments.Create granted' or 'Seems like you don't have access on Orchestrator'."
---

# UiPath Vertical Solutions Deploy

Guided `uip vss deploy` for a Vertical Solution: an industry solution package (such as FINS Loan Setup) that the Vertical Solutions service installs on a tenant. `uip vss deploy` submits a deploy job and watches it. The service runs the deploy in UiPath Cloud **as the identity that ran `uip login`**, with that identity's permissions.

Assume the user has never deployed a solution. You do the work: run the commands, read their output, and work out the options. The user only answers plain questions, one or two at a time, and says yes before anything changes. Explain terms the first time you use them: a *folder* is where Orchestrator keeps the solution's processes and apps; a *deployment* is one installed copy of a package.

> **Use the CLI. Don't hand-roll REST for deploy jobs.** `uip vss deploy` handles the deploy job's submit, polling, pauses, checkpoints and resume. A REST call to the Vertical Solutions service misses them, and a resubmit makes a second job (Critical Rule 2).

<!--skill-flavor:host-availability-extra:start-->

<!--skill-flavor:host-availability-extra:end-->

## When to Use This Skill

- User wants to deploy a Vertical Solution package (FINS Loan Setup, Lending QA/QC, or another vertical's package), or says "uip vss deploy"
- User wants to upgrade or downgrade an installed Vertical Solution
- User asks for the status of a deploy job, or wants to resume or cancel one ("deploy job paused", "resume the deploy")
- User wants to seed a deployed solution's Data Fabric data with `uip vss deploy seed`
- User wants to set up a deployed solution, such as who may use its app ("help me set up QA/QC", "set up Loan Setup roles")
- User asks what access a deploy needs, or whether a user can deploy a package into a folder
- User shows a deploy refusal, such as `User doesn't have permissions SolutionDeployments.Create granted` or `Seems like you don't have access on Orchestrator`

## Critical Rules

1. **Check the login first.** A deploy goes to the tenant of the current login, as that identity. `uip login` with a different account replaces the saved session, so check `uip login status` again after any login.
2. **Never run `uip vss deploy --yes` again to retry.** A second submit makes a separate job. Once a job exists, continue it with `uip vss deploy resume <JOB_ID>`. It restarts from the last checkpoint, and completed steps are not re-run.
3. **Fix access, then resume.** When a step is refused for a missing permission, have it granted (see rule 6), then resume the same job. A role change applies without a new login. An external application that was missing a scope must run `uip login` again before the resume.
4. **`cancel` does not roll back.** `uip vss deploy cancel <JOB_ID> --yes` stops the job. Steps already applied stay applied.
5. **Copy filled-in seed CSVs out first.** Every watched deploy or resume that succeeds writes the seed templates again, also with `--no-seed`, and replaces the CSVs in `./seeding/<PACKAGE_NAME>`.
6. **Do not change access without being asked.** Reading roles and permissions is fine. Assigning roles or editing a role or user changes the tenant: say what you would change and wait for the user to agree.
7. **Find answers with commands, not by digging.** Do not read the CLI source, call the service's API by hand, or search the disk for solution zips. The service deploys from its own feed. The vertical files and the dry run (step 5) give you everything else.
8. **Never pass `--yes` before the user says yes.** Run the deploy without `--yes` first: it checks everything and stops before it sends anything. Show the summary from step 6 and pass `--yes` only after the user agrees. The same holds for `seed --yes`.
9. **Pass `--no-interactive` and `--output json` to every `uip vss deploy` command you run.** `--no-interactive` keeps it from waiting on a prompt you cannot answer. Read `Result`, `Code`, `Data` and, on a failure, `Message` and `Instructions`.

## The Guided Deploy

Work through these steps in order. Keep a short list of the answers so far, and show it again before the final yes.

### 1. Get ready

```bash
uip --version
uip vss deploy --help
uip login status --output json
```

<!--skill-flavor:cli-ready:start-->
- `command not found` / `uip: not found` / `'uip' is not recognized` → CLI not installed. Tell the user to run the official installer (`curl -fsSL https://download.uipath.com/uipath-cli/install.sh | bash` on macOS/Linux; `irm https://download.uipath.com/uipath-cli/install.ps1 | iex` in Windows PowerShell), then `uip login`, and stop until those succeed.
- `uip vss deploy --help` fails or does not list `cancel`, `resume`, `seed` and `status` → the CLI is too old. Tell the user to run the installer again to update it, and stop.
- `Status` is not logged in, or has expired → ask the user to run `uip login` in their terminal. It opens a browser. They log in as the person who should own the deployment, and pick the organization and tenant.
<!--skill-flavor:cli-ready:end-->
- Tell the user, in one line, who they are logged in as and which tenant the deploy will go to, and that they can say so if it is wrong (`uip login tenant set <TENANT_NAME>` switches tenant). Do not stop to wait for a yes: in the same message, go on to step 2 and ask the first question there.

### 2. Pick the vertical, then the solution

Ask one question at a time, and skip any the user already answered.

1. **Which vertical.** A *vertical* is the industry the solution is built for, such as FINS (Financial Services). When the user has not named one, list the verticals in [verticals-guide.md](references/verticals/verticals-guide.md) by their full name and ask which. Offer "another vertical" too: the service can have verticals this skill has no file for yet.
2. **Which solution.** Open the vertical's file, list its packages by their display name, and ask which. Use the exact `--package-name` from the file.

When the user names something the files do not list (another vertical, or a package not in the file), ask them for the package name, or have them run `uip vss deploy` in their own terminal: it lists the verticals and their packages to pick from, and they can stop once they have the name.

### 3. New install or upgrade

Run the dry run with only the package name:

```bash
uip vss deploy --package-name <PACKAGE_NAME> --no-seed --no-interactive --output json
```

- It says **"This package is already deployed"** and names the deployment, version, folder and folder key: tell the user what is installed and where, and ask: upgrade that one, or install a second copy next to it? For an upgrade, follow [upgrade-guide.md](references/upgrade-guide.md). A second copy needs `--action install` and its own `--deployment-name` on every command from here on, because the default name is taken.
- It says **"A target folder is required"**: nothing is installed yet, so this is a new install. Go on.
- Any other failure, such as "Could not list current deployments": explain it as in step 5, and fix it before you go on.

### 4. Where and what name (new install)

- **Folder.** List the folders and offer the likely ones:

  ```bash
  uip or folders list --output json
  ```

  Read `Data[].Path`. Skip folders whose `Type` is `Solution` (the deploy refuses them) and personal workspaces. Page with `--offset` when there are many. The folder must already exist. The deploy creates the solution's own folder inside it. When the user has no preference, suggest `Shared`.
- **Deployment name.** It defaults to the solution's name from the package (not the package name) and must be unique on the tenant. Ask only if the user wants a second copy or a different name.

Then check the access for that folder, as in [Check the Access](#check-the-access). Report the result before you go on.

### 5. Values the package needs, and the dry run

The vertical's file lists the values each package asks for, with what they mean. Ask the user for each one in plain words. Then run the deploy **without `--yes`**:

```bash
uip vss deploy --package-name <PACKAGE_NAME> --folder-path "<FOLDER_PATH>" \
  --config <KEY>=<VALUE> --no-seed --no-interactive --output json
```

- `Configuration for <KEY>, ... is required`: it can name several keys. Ask the user for each, add `--config <KEY>=<VALUE>` for each, and run it again. Use `--config <KEY>=env.<ENV_VAR>` for a secret, so it never sits on the command line.
- A warning that `<RESOURCE>.<PROPERTY>` is required: a per-resource value, such as a web app's `routingName`. Ask the user for it and write it to `./deploy-config.json` under that resource's name:

  ```json
  { "version": 1, "resources": [
      { "name": "<RESOURCE>", "configuration": { "<PROPERTY>": "<VALUE>" } } ] }
  ```

  Or tell the user the deploy will pause on a portal page that asks for it. A property whose name looks like a secret is never sent this way: it is set on that portal page.
- `Confirmation is required before a deploy runs`: every check passed. Nothing has been sent. Go to step 6.
- Any other failure: explain the `Message` and `Instructions` in plain words and fix that first. A taken name, a missing folder or an unknown version all show up here, before any job exists.

### 6. Confirm and deploy

Show the user a short summary: the solution, the version (the one they asked for, or "the newest one allowed"), the tenant, the folder, the deployment name (or "the solution's default name"), and which values were set. Ask for a yes. Then run the same command with `--yes`:

```bash
uip vss deploy <SAME_FLAGS> --yes --output json
```

A deploy takes many minutes, longer than a shell command is usually allowed to run. Run it in the background, or with a long timeout, and tell the user it is running. Note the job id from the `Deploy job <JOB_ID> accepted and running.` line at once. If your command is stopped before the job ends, the job keeps running: follow it with `uip vss deploy status <JOB_ID>`, and re-attach with `uip vss deploy resume <JOB_ID>`. Never submit again (rule 2).

### 7. Follow it to the end

Tell the user what happened in plain words, and what to do next:

| Outcome | Exit | What to tell the user |
|---------|------|-----------------------|
| `Status: succeeded` | `0` | It is installed. Offer step 8 |
| `Deployment succeeded — with warnings:` | `0` | Installed. One optional step failed: the output names it and why |
| Paused for a setup page (activation, connection authorization, configuration wizard) | `1` | The deploy needs them to finish one thing in the browser, on the page the CLI prints. For an activation pause, the pause text also lists the setup to do there (after "Setup listed:"): tell them each item. When they are done, you run `uip vss deploy resume <JOB_ID>` |
| Paused because the login expired | `1`, `ErrorCode: authentication_required` | They run `uip login` again in their terminal, then you resume the job |
| A step failed (`Code: job-failed`) | `1` | Explain the step's message. Fix the cause (for a permission, see [When a Deploy Is Refused](#when-a-deploy-is-refused)), then resume |
| The service refuses the name as taken | `1` | Pick another name: `uip vss deploy resume <JOB_ID> --deployment-name <OTHER_NAME>` |
| `Code: lost-contact` (Ctrl-C while submitting, or an answer the CLI could not read) | `1` | It is not known whether a job was made. Check `uip solution deploy list` or the portal's deployments page before anything else. Never submit again without that check |
| `--timeout` elapsed | `4` | The job is still going. Check `uip vss deploy status <JOB_ID>` |

`uip vss deploy status <JOB_ID>` is read-only and safe to run at any time.

### 8. After the deploy

- **Seed data.** The deploy wrote CSV templates to `./seeding/<PACKAGE_NAME>`. Explain that these are the solution's starting data (its records in Data Fabric). The user fills in the CSVs. Seeding writes records, so ask for a yes, then run:

  ```bash
  uip vss deploy seed --yes --no-interactive --output json
  ```

  A seed is safe to run again: rows it already inserted are matched, not inserted twice. `--refresh` downloads fresh templates and replaces the CSVs.

On `succeeded` (with or without warnings), report the result (the solution folder, and that it is active) and the seed step above, nothing else. When the vertical's file has a "Set up a deployed solution" section, add one sentence: they can ask later to set up who may use the solution. When that file says the app turns everyone away until then, say so in the same sentence. Do not start it, and do not list its steps: it is a separate task ([Set Up a Deployed Solution](#set-up-a-deployed-solution)). The job log prints a "Setup the platform lists for this deployment" block before it activates: it is the platform's generic checklist (activate apps, add accounts and roles, add machines, account-machine mappings, per-robot asset values). Do not pass it on: the deploy activated, so it no longer applies. Do not add setup steps of your own either: nothing the vertical's file does not list (no activation checks, redirect URLs, folder accounts, robots, machines or asset values). When the job needs something more, it pauses and names it (step 7).

## Set Up a Deployed Solution

A separate task from the deploy: the user asks for it later ("help me set up QA/QC", "set up who can use Loan Setup"). It needs no deploy job, and a deploy does not need it.

1. Run `uip login status --output json` and check it is a user logged in to the right tenant. The `uip vss deploy --help` check is not needed here.
2. Pick the vertical and the solution (step 2), skipping what the user already said.
3. Open the vertical's file and follow its "Set up a deployed solution" section. When it has none, say the skill has no setup steps for that vertical, and stop. Do not make some up.
4. Read before you change: show what exists and what is missing. Each change (a group, a member, a row) changes the tenant, so ask for a yes first (rule 6).

## Check the Access

Do this before every deploy, and tell the user the result before you submit. In `uip login status`, note `IdentityType`. For an external application, the commands below do not apply: check its scopes and its folder assignments in the portal. For a user:

```bash
uip or users current --output json
uip or roles user-permissions list <USER_NAME> --output json
uip or roles user-permissions list <USER_NAME> --folder-path "<TARGET_FOLDER>" --output json
```

`Data.UserName` from the first command is the name to check. The second reads the tenant level, the third the folder level. Compare the output with the vertical's file, as [verticals-guide.md](references/verticals/verticals-guide.md) describes:

- Compare the tenant table with the tenant output, and the target-folder and seed tables with the target-folder output. The solution folder does not exist yet, and it inherits the target folder's roles. On an upgrade, the target folder is the one that holds the solution folder.
- A role on a parent folder also applies. Before you call a folder line missing, run the folder-level command for each parent folder too.
- An empty list (`Data: []`) means no roles at that level. It is not a refusal.

Then report one of these:

- **All present.** Say so, and go on.
- **Some missing.** List each missing line by level (tenant, target folder) with its **Source**. A missing *Inferred* line may not be needed: say so, and let the deploy confirm it. Give the instructions an administrator needs: which permissions, at which level, on which tenant or folder, and the command or portal page that grants them (see section 5 of [access-troubleshooting-guide.md](references/access-troubleshooting-guide.md)). Do not grant them yourself (rule 6). Ask whether to wait for the fix or to deploy anyway. A step that is refused fails with the permission's name, and the job resumes after the fix.
- **The check itself is refused (`403`).** Reading roles needs the Roles and Users view permissions, which a deploying user often does not have. That says nothing about the deploy. Say so, and give the user the vertical's full list as a checklist for an administrator. The administrator runs the check in their own session, with the user name you noted. Do not switch this session to the administrator's login: the deploy would then run as the administrator. If the user does log in as someone else, they must log in again as the deploying user and you must check `uip login status` before you submit.
- **The folder cannot be found** ("Error resolving folder"). The folder does not exist or this login cannot see it. That is not missing access. Ask for the right folder.
- **No list for the package.** Say that no access list exists for it yet, and use the per-step table in [access-troubleshooting-guide.md](references/access-troubleshooting-guide.md).

Data Fabric roles (Data Reader, Data Writer) are not in this output. Report them as unconfirmed, and ask the user to check them in the Data Fabric admin page.

## When a Deploy Is Refused

Read the failing step and the message. A refusal names the permission it needed, for example:

```text
Deployment failed at step SOLUTION: Automation Solutions rejected the deployment
of '<DEPLOYMENT_NAME>': User doesn't have permissions SolutionDeployments.Create granted
```

Follow [access-troubleshooting-guide.md](references/access-troubleshooting-guide.md), and compare with the vertical's file under [verticals-guide.md](references/verticals/verticals-guide.md). Once the access is fixed, resume the same job.

## Other Commands

- `uip vss deploy` with no flags, in the user's own terminal, asks every question itself. Offer it to a user who would rather click through.
- `--no-wait` submits and prints the job id without watching. Follow it with `uip vss deploy status <JOB_ID>`.
- From a pipeline, pass every input as a flag with `--yes`. The full list is in `uip vss deploy --help`.

## Reference Navigation

| File | Read when |
|------|-----------|
| [references/verticals/verticals-guide.md](references/verticals/verticals-guide.md) | Picking a vertical, checking a user against a vertical's access list, or adding a vertical |
| [references/verticals/fins-guide.md](references/verticals/fins-guide.md) | FINS packages, the values they ask for, what must exist before the first deploy, how to set up a deployed solution, and their access lists |
| [references/upgrade-guide.md](references/upgrade-guide.md) | Upgrading or downgrading an installed deployment |
| [references/access-troubleshooting-guide.md](references/access-troubleshooting-guide.md) | A deploy step is refused, a role read returns `403`, or granting access after the user agrees |

## What NOT to Do

1. **Do not resubmit to retry.** A second `uip vss deploy --yes` makes a second job next to the first. Use `uip vss deploy resume <JOB_ID>`.
2. **Do not pass `--yes` on the first run.** The dry run is how you learn which values are missing, and the user has not agreed to anything yet.
3. **Do not guess a package or start a dry run before the user picks the vertical and the solution.**
4. **Do not switch the session to an administrator's login to read roles.** The deploy would then run as the administrator.
5. **Do not grant roles or edit users to make a deploy pass.** Name the exact change and wait for the user to agree.
6. **Do not treat `cancel` as an undo.** Steps already applied stay applied.
7. **Do not read the CLI source, call the service's REST API, or search the disk for solution zips.** The service deploys from its own feed.
8. **Do not redeploy, upgrade, resume or run `seed --refresh` before the user copies filled-in CSVs out of `./seeding/<PACKAGE_NAME>`.** A successful deploy or resume, and `--refresh`, replace them. A plain `seed` reads them and leaves them in place.
9. **Do not add setup to the deploy.** After a successful deploy, report the job result and offer seeding. Setting up the solution is a separate task the user asks for (see [Set Up a Deployed Solution](#set-up-a-deployed-solution)). List nothing else: no activation checks, redirect URLs, folder accounts, robots, machines or asset values, whether you made them up or read them in the job log's "Setup the platform lists" block of a deploy that succeeded. When the job pauses because activation failed, the pause names the setup still needed: pass that on (step 7).
