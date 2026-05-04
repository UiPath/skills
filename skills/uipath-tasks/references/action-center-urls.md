# Action Center URL patterns

Reference guidance for constructing Action Center / Orchestrator task URLs.
**The tenant slug is mandatory in every form.** Omitting it triggers
[MST-9322](https://uipath.atlassian.net/browse/MST-9322) — the portal-UI
misclassifies a tenant-less URL as "Orchestrator is not enabled for this
tenant" even when the service is fully enabled, sending the user down a
wrong support path (admin/license escalation instead of "fix your URL").

## The two canonical patterns

There are two URL forms in active use. Always use the one that matches your
target surface; both require all four segments below.

### 1. Action Center inbox deep-link

```
https://{host}/{org}/{tenant}/orchestrator_/actions/inbox/{taskKey}
```

* **When to use:** linking to a *task in the inbox* — the form a user sees
  in Action Center's task-list landing.
* **Example:**
  `https://cloud.uipath.com/popoc/DefaultTenant/orchestrator_/actions/inbox/abc-123-def-456`

### 2. Action Center standalone task URL

```
https://{host}/{org}/{tenant}/actions_/current-task/tasks/{taskId}
```

* **When to use:** linking *directly to a single task* (typically from
  Coded Action Apps, notification emails, or the standalone task page).
  This is the form documented in `uipath-coded-apps/references/patterns.md`.
* **Example:**
  `https://cloud.uipath.com/popoc/DefaultTenant/actions_/current-task/tasks/42`
* **Embed variant:** prefix `embed_/` for iframe rendering:
  `https://cloud.uipath.com/embed_/popoc/DefaultTenant/actions_/current-task/tasks/42`

## Mandatory segments

Every URL above MUST include:

| Segment    | Source                                                | Notes |
|------------|-------------------------------------------------------|-------|
| `{host}`   | UI host (NOT the API host — see "Environment mapping" below) | `cloud.uipath.com`, `staging.uipath.com`, `alpha.uipath.com` |
| `{org}`    | Organization name or ID                               | URL-encode if it contains spaces/unicode. |
| `{tenant}` | Tenant **name** (e.g. `DefaultTenant`)                | **Mandatory.** Never substitute a path keyword like `actions` here. |
| `{taskKey}` or `{taskId}` | From `uip tasks get` / `uip tasks list` JSON | Use `Key` (string GUID) for inbox; numeric `Id` for standalone. |

## MST-9322: what NOT to produce

```
❌ https://alpha.uipath.com/popoc/orchestrator_/actions/inbox/<taskKey>
                          ^^^^^^^
                          tenant slug missing
```

The portal-UI parser interprets `actions` (the next segment) as the tenant
name, then redirects to:

```
/portal_/unregistered?serviceType=orchestrator&organizationName=popoc&tenantName=actions
```

…rendering "Orchestrator is not enabled for this tenant." This is wrong:
the service is enabled; only the URL is malformed. **Always include the
tenant.** If you don't know it, run `uip login status --output json` and
read `tenantName` from the response before constructing the URL.

## Environment mapping (API host ≠ UI host)

The Action Center URLs above use the **UI host**, which differs from the
API host that backs `uip` CLI calls. Never paste an API host into one of
these URLs.

| API host                   | UI host                    |
|----------------------------|----------------------------|
| `api.uipath.com`           | `cloud.uipath.com`         |
| `staging.api.uipath.com`   | `staging.uipath.com`       |
| `alpha.api.uipath.com`     | `alpha.uipath.com`         |
| `gov.api.uipath.com`       | `gov.uipath.com`           |

If `uip login status` reports a base URL of `https://alpha.api.uipath.com`,
strip the `api.` prefix before building an Action Center URL.

## Agent guidance: when surfacing a task URL to the user

If your skill needs to print or hand off an Action Center URL:

1. **Resolve `{org}` and `{tenant}` from the live login session**, not from
   memory or the conversation. Run `uip login status --output json` and
   read `organizationName` (or `organizationId` as fallback) and
   `tenantName`. Treat any `null`/missing tenant as a hard error — do not
   construct the URL.
2. **URL-encode** any segment that may contain spaces or unicode (org
   names, tenant names, taskKey strings).
3. **Map API host → UI host** if the login's base URL is the API host.
4. **Choose the form** based on the destination: inbox-with-list-context
   (`/orchestrator_/actions/inbox/{taskKey}`) vs. direct-task-view
   (`/actions_/current-task/tasks/{taskId}`).
5. **Verify before sharing** — paste the constructed URL into a browser
   on the same tenant and confirm it lands on the task, not on the
   `/portal_/unregistered` page. The "Orchestrator is not enabled" page
   is the exact MST-9322 symptom — if you see it, your URL is malformed.

## CLI-side helpers (for tool authors)

The `uip` CLI ships canonical builders in `@uipath/common`. If you're
extending the CLI rather than constructing URLs by hand from a skill,
import these:

```typescript
import {
    buildActionCenterInboxUrl,
    buildActionCenterTaskUrl,
    buildOrchestratorUrl,
} from "@uipath/common";

const inboxUrl = buildActionCenterInboxUrl(uiHost, org, tenant, taskKey);
//   → https://cloud.uipath.com/popoc/DefaultTenant/orchestrator_/actions/inbox/<taskKey>

const taskUrl = buildActionCenterTaskUrl(uiHost, org, tenant, taskId);
//   → https://cloud.uipath.com/popoc/DefaultTenant/actions_/current-task/tasks/42
```

All three helpers throw if `tenant` (or `org` / `baseUrl`) is empty —
this is the runtime backstop for the MST-9322 contract. See
`packages/common/src/orchestrator-urls.ts` in the [CLI repo](https://github.com/UiPath/cli).

## Related

* MST-9322 — primary ticket for this URL hygiene work.
* MST-9188 — adjacent issue ("Hide Flow project option when Maestro
  unlicensed") on the same `/portal_/unregistered` page surface.
* `uipath-coded-apps/references/patterns.md` — already documents the
  standalone form for Coded Action App developers (React/TypeScript).
