# Coded IS e2e — Setup & Run

Prerequisites and procedure to run the coded Integration Service **e2e** tasks
(`coded/is_jira_create_issue`, `coded/is_outlook_send_mail`) locally or in CI.
The tenant-free `coded/is_smoke` needs none of this — it runs in the smoke lane
with no tenant.

These e2e tasks **mutate a live tenant**: they create a real Jira issue and send
a real email. Do not run them casually.

> **Both e2e tasks ship `skip: true`** so the nightly (which runs `e2e`-tagged
> tasks, unlike the `--tags smoke` PR gate) does not fail on an unprovisioned
> tenant. Once the folder + connections below exist on the run tenant, flip
> `skip: false` in `is_jira_create_issue.yaml` / `is_outlook_send_mail.yaml` to
> activate them.

## What the e2e needs

| Dependency | Provided by | Notes |
|---|---|---|
| `uip` auth | local `uip auth` / CI ROPC bot | tempdir agent inherits `~/.uipath/.auth` |
| Anthropic creds | `ANTHROPIC_API_KEY` (or Bedrock) | the in-sandbox agent |
| Folder `Shared/uipath-agents` | one-time tenant setup | connections live here |
| Connection `jira-coded-eval` | one-time OAuth, `uipath-atlassian-jira` | in `Shared/uipath-agents` |
| Connection `outlook-coded-eval` | one-time OAuth, `uipath-microsoft-outlook365` | in `Shared/uipath-agents`; mailbox can self-send |
| `JIRA_PROJECT_KEY` | env / CI secret | e.g. `ENGCE` |
| `JIRA_ISSUETYPE_ID` | env / CI secret | numeric, e.g. `10001` (Task) |
| `OUTLOOK_TEST_TO` | env / CI secret | a mailbox the connection can send to |

The seed scripts **hard-FAIL** when the env vars are placeholders/missing
(`seed_jira.py`, `seed_outlook.py`) — by design, so a misconfigured run fails
loudly instead of silently passing.

## Which tenant / org

- Environment: `https://alpha.uipath.com`.
- Org/tenant: **confirm against the repo's GitHub Actions secrets**
  `UIPATH_ORG_NAME` and `UIPATH_TENANT_NAME` (used by `run-coder-eval.yml`).
  As of 2026-05, the intended org was `codereval` but config had drifted to
  `autopilot_demo_data` and was unresolved — do NOT assume. Verify with the
  test-infra DRIs (Bai Li, Tomasz Religa, Gurpreet Chahal, Ganesh Borle).
- The connections must be created in **that** org/tenant, in folder
  `Shared/uipath-agents`, and reachable by the user the run authenticates as
  (the ROPC bot user in CI; your own user locally).

## One-time tenant provisioning

Connection creation is browser-OAuth — it cannot be scripted headlessly. Do it
once; Integration Service refreshes the token server-side afterward.

```bash
# 1. Create the folder (if absent) on the target tenant.
uip or folders create "uipath-agents" --parent "Shared" --output json

# 2. Create the connections (interactive OAuth — opens a browser).
uip is connections create uipath-atlassian-jira
uip is connections create uipath-microsoft-outlook365
```

Then in the cloud UI: name them `jira-coded-eval` / `outlook-coded-eval`, place
both in `Shared/uipath-agents`, and confirm the Jira project accepts new `Task`
issues and the Outlook mailbox can self-send. In CI, the **bot user** must have
access to this folder and these connections.

## Run locally

`default.yaml` uses the `tempdir` driver, so the agent runs on-host and inherits
your `~/.uipath/.auth`.

```bash
# from tests/
SKILLS_REPO_PATH="$(cd .. && pwd)" \
ANTHROPIC_API_KEY=<key> \
JIRA_PROJECT_KEY=ENGCE JIRA_ISSUETYPE_ID=10001 \
  .venv/bin/coder-eval run \
  tasks/uipath-agents/coded/is_jira_create_issue/is_jira_create_issue.yaml \
  -e experiments/default.yaml -v

OUTLOOK_TEST_TO=<mailbox> \
  .venv/bin/coder-eval run \
  tasks/uipath-agents/coded/is_outlook_send_mail/is_outlook_send_mail.yaml \
  -e experiments/default.yaml -v
```

`make e2e` runs all `e2e`-tagged tasks.

## Daily / CI runs

The nightly suite authenticates as the **ROPC bot user** (`run-coder-eval.yml`:
`UIPATH_ROPC_CLIENT_ID/SECRET` + `UIPATH_BOT_USERNAME/PASSWORD` →
`alpha.uipath.com`) — non-interactive, no browser.

The seed runs automatically as each task's `pre_run` (`seed_jira.py` /
`seed_outlook.py`), reading the env vars and writing `seed.json`. For daily runs
to seed correctly, two things must be wired (gap as of 2026-05):

1. **CI env vars** — add `JIRA_PROJECT_KEY`, `JIRA_ISSUETYPE_ID`,
   `OUTLOOK_TEST_TO` as repo secrets and into the workflow `env:` (and the VM
   cron env). They are not present today, so daily e2e hits the seed's hard-FAIL.
   For a Docker e2e lane, also add them to `env_passthrough_extra`.
2. **Pre-provisioned connections** — the seed does NOT create connections; the
   `jira-coded-eval` / `outlook-coded-eval` connections must already exist in the
   bot tenant's `Shared/uipath-agents`. If their OAuth ever lapses, e2e fails
   until re-authed.

## How the checks verify tenant state

After the agent runs the project, the check scripts query the live tenant via
`uip is connections list` / `uip is resources run` to confirm the issue/email was
actually created (`check_is_jira_create_issue.py`,
`check_is_outlook_send_mail.py`) — not the agent's self-report.
