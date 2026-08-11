# Final Resolution

Investigation complete. Here are the findings:

---

# Why your `Request_Failed` job faulted — Resolution

## Root Cause
The **Create Ticket** activity in your `Request_Failed` process called Freshdesk to create a ticket, and Freshdesk rejected the call with **HTTP 403 (`access_denied` — "You are not authorized to perform this action")**. The connection itself authenticated fine; the **Freshdesk account behind the connection lacks permission to create tickets**. This surfaced as UiPath error **DAP-RT-1101 (RequestFailed)**.

- Domain: Integration Service (root cause)
- Confidence: High — confirmed, no open cross-cause gaps

## What went wrong
- An unattended Orchestrator job for process **`Request_Failed`** (release "RPA Workflow") in folder **`Shared/uipath-rpa-isActivities/RequestFailed_DAPRuntime`** faulted on **2026-06-18T13:31:50Z**.
- It ran cleanly (Pending → Running → Faulted in ~9s) and then failed inside the workflow at the **Create Ticket** activity (`Main.xaml` → Sequence → Main).
- The activity uses the **uipath** (Freshdesk) connection to perform a ticket **Create** (`POST /tickets`). Freshdesk returned **403 Forbidden**.

## Why
The decisive evidence is the **provider's own status code**, not the UiPath code. `DAP-RT-1101` only says "the downstream API returned an error"; the **`ProviderErrorCode: 403` / `access_denied`** is what names the cause:
- **403 = authenticated but not permitted.** The connection resolved and authenticated (it pings as Enabled/active), and the call reached Freshdesk with a provider `RequestId`. Freshdesk accepted the credentials but refused the *operation*.
- This is **not** a token/credential problem (that would be 401), **not** a connection-resolution failure, and **not** a missing/invalid record (this is a create, so there is no record ID to be wrong).
- The Freshdesk API key inherits the permissions of its **agent account** (`original_email@test.com`). That account is currently **not authorized to create tickets** in Freshdesk — most likely it is a non-agent or a restricted-scope agent without ticket-create rights or without access to the target group/product.

## Evidence

**Integration Service (root cause domain)**

| Signal | Value | Source |
|---|---|---|
| UiPath error | `DAP-RT-1101` (RequestFailed) | `raw/triage-job-logs.json` |
| Provider error | `ProviderErrorCode: 403`, `code - access_denied`, "You are not authorized to perform this action", Message: Forbidden | `raw/triage-job-logs.json` |
| Provider RequestId | `6a33f346e4b089c6407a42a2` | `raw/triage-job-logs.json` |
| Faulted activity | **Create Ticket** (`Main.xaml` → Sequence → Main), runtime path `SendCUDRequestClientAsync` (create) | `raw/triage-job-logs.json`, evidence `H1-connection-permission-403.json` |
| Operation | Freshdesk **tickets / Create** → `POST /tickets`, `requiredFields []` | `raw/H1-resources-describe-create.json` |
| Connection | **uipath** (Freshdesk), id `29aae689-111d-459f-9a4a-d1ad1d9d2761`, owner `original_email@test.com` | `raw/H1-connections-list-folder.json` |
| Connection health | Status **Enabled** — "Connection is active and ready for operations." (authenticates → rules out 401/resolution failure) | `raw/H1-connections-ping.json` |
| Timeline | Connection Created 13:24:02Z, job Faulted 13:31:50Z (first observed run), connection Updated 14:26:54Z (after the fault → no prior-success regression) | `raw/H1-connections-list-folder.json` |
| Job | `Request_Failed`, job id 50205597, folder `Shared/uipath-rpa-isActivities/RequestFailed_DAPRuntime` | `state.json`, `raw/triage-job-get.json` |

## Immediate fix — Integration Service

**Grant the Freshdesk account ticket-create permission, then re-authenticate the connection.**

- **What:** In the **Freshdesk admin console**, give the agent account behind the **uipath** (Freshdesk) connection — `original_email@test.com` — a role that can **create tickets** (typically a full **Agent** with access to the relevant group/product, or **Admin**). A quick check: if that account cannot manually create a ticket in the Freshdesk UI, the API call will also 403 — fix it there first.
- **Why:** Freshdesk returned 403 `access_denied` on `POST /tickets`. The API key inherits the agent account's permissions; the account currently lacks ticket-create rights. The playbook's 403 branch resolution is: *"widen the connection's scope or grant the external account the permission the operation requires, then re-authenticate."*
- **Where:** Freshdesk admin console (agent roles / group / product access) for `original_email@test.com`; then the UiPath connection **uipath** (`29aae689-111d-459f-9a4a-d1ad1d9d2761`) in folder `uipath-rpa-isActivities`.
- **Who:** A **Freshdesk administrator** (to change the agent's role/access) plus the **connection owner** (`original_email@test.com`) to re-authenticate the UiPath connection.
- **Source:**
  - Playbook `references/products/integration-service/playbooks/request-failed.md` — ## Resolution, 403 branch
  - https://docs-staging.uipath.com/integration-service/automation-cloud/latest/user-guide/uipath-freshworks-freshdesk-authentication
  - https://docs-staging.uipath.com/integration-service/automation-cloud/latest/user-guide/connections-troubleshooting

After fixing the Freshdesk role, re-authenticate the connection so it picks up the corrected permissions, then re-run the `Request_Failed` job and confirm `POST /tickets` returns **201 Created**.

> **Known open gap (must be confirmed manually):** The exact Freshdesk permission/role name could **not** be enumerated via the `uip` CLI — the CLI does not expose Freshdesk's granted-vs-required per-operation permissions. You must confirm in the **Freshdesk admin console** which role `original_email@test.com` holds and grant it ticket-create rights. This refinement does **not** change the resolution above; the 403 authorization cause is confirmed regardless. [Partly Unverified — provider-side role name only]

## Preventive fix
- **Provision the connection's service account with create/write scope up front.** When creating Integration Service connections for write operations, verify the underlying provider account can perform the target operation (here: create tickets) *before* deploying, e.g. by doing the action manually in the provider UI with that account.
- **Smoke-test new connections.** After deploying a solution, run a one-off create against a non-production target to surface 403s before the first real job.
- **Treat provider status codes as the classifier.** For any `DAP-RT-1101`, read `ProviderErrorCode`/`ProviderErrorMessage` first — 401 = credentials, 403 = permissions/scope, 404 = bad record, 429/5xx = throttle/outage. Source: `references/products/integration-service/playbooks/request-failed.md`.

---

## Investigation summary

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|---|---|---|---|---|---|
| H1 | The **uipath** (Freshdesk) connection authenticated, but the underlying Freshdesk account lacks permission to create tickets, so `POST /tickets` was rejected with 403 `access_denied` → DAP-RT-1101. | High | Confirmed (depth-check: verified, no gaps) | **Yes** | `ProviderErrorCode 403` `access_denied` "You are not authorized to perform this action" (RequestId `6a33f346e4b089c6407a42a2`); connection pings **Enabled**; operation = Freshdesk tickets **Create** (`POST /tickets`); single Create Ticket activity bound to `29aae689…` owned by `original_email@test.com` | Grant the Freshdesk account ticket-create permission in the Freshdesk admin console, then re-authenticate the **uipath** connection (`uip is connections edit 29aae689-111d-459f-9a4a-d1ad1d9d2761`) and re-run the job. |

---

Now let me walk through the one interactive follow-up action from the resolution.

**Connection id:**
```
29aae689-111d-459f-9a4a-d1ad1d9d2761
```

**Command to re-authenticate the connection:**
```
uip is connections edit 29aae689-111d-459f-9a4a-d1ad1d9d2761
```

**⚠️ Warning:** Re-authentication only takes effect after the Freshdesk admin has granted the account `original_email@test.com` ticket-create permission. If you re-authenticate before fixing the Freshdesk role, the connection will still return 403 on the next run. Re-authenticate as the connection owner.
