---
confidence: medium
---

# O365 — Application Scope / connection misconfiguration (before any Graph call)

## Context

What this looks like — the failure happens **before any Microsoft Graph call**, from the Microsoft 365 Application Scope's own configuration (no HTTP status / Graph error code). **Where** it shows up depends on the fault:

**As a faulted Orchestrator job (runtime):**
- `Could not retrieve the selected asset: '<asset>'` — the scope reads its connection from an Orchestrator asset that can't be retrieved (the inner cause can be a missing / forbidden asset, or an empty asset id).
- A bare `ArgumentNullException` naming a credential field (e.g. `ApplicationId`) — a required credential resolved to null at runtime. (The friendly "You must provide a value …" wording below is design-time only.)

**As Studio design-time validation / test-connection errors (not a job fault):**
- `You must provide a literal value for <field> in order to use design time services` — a required field is bound to an expression the design-time service can't read (Classic design experience).
- `The authentication parameters could not be read` — the connection object is null/empty.
- `You must provide a value for <field>` or `You must provide a value for at least one of the following properties: <Application Secret, Secure Application Secret>` / `<Password, Secure Password>` — a required credential field for the chosen authentication type is missing.
- `Please select an account.` — Interactive Token auth with no account chosen.
- `Activity is only valid inside an Office 365 Scope` (Mail / Excel / SharePoint) **or** `Cannot be used outside of a MicrosoftOffice365 Application Scope or outside of a Use OneDrive/SharePoint activity` (Files/OneDrive) — the activity was placed outside any Application Scope.

What activities can produce this:
- The **Microsoft 365 Application Scope** (`Office365ApplicationScope`) itself, and every Mail / Files / Excel activity placed under it (the fault propagates to the child that runs first, or surfaces as a design-time validation error on the misplaced activity).

What can cause it:
- **Orchestrator asset can't be retrieved** — the configured connection asset has the wrong name/path, isn't present in the folder the robot runs in, the robot lacks permission to read it, or it isn't a valid connection asset.
- **Non-literal value on a design-time field** — a required scope field is bound to a variable/expression that can't be read at design time.
- **Null / incomplete credentials** — no connection is configured, or the credential fields required by the chosen authentication type (App ID + Tenant + Secret/Certificate; Username + Password) are missing. At design time this is the `You must provide a value …` / `The authentication parameters could not be read` validation; at runtime a missing Application ID surfaces instead as a bare `ArgumentNullException` naming the field.
- **No account selected** — Interactive Token auth without a chosen account.
- **Activity placed outside the scope** — a Mail/Files/Excel activity dropped on the canvas with no Microsoft 365 Application Scope (or, for OneDrive/SharePoint, no Use OneDrive/SharePoint activity) as a parent.

> **Different cause, do not apply this playbook:**
> - Any message carrying a Microsoft Graph result — `The caller doesn't have permission ...` (403), `The resource could not be found.` (404), `Too many requests.` (429), `The server is unable to process the current request.` (503), or a token/`AADSTS` authentication error. Those happen **after** the scope successfully authenticates and makes a Graph call — use **insufficient-graph-scope**, the not-found playbooks, **request-throttled**, **transient-service-error**, or **authentication-token-invalid** respectively.

## Investigation

1. Read the message to identify which configuration family it is (asset / non-literal field / null or incomplete credentials / no account / placement).
2. **Asset (`Could not retrieve the selected asset`):** confirm the asset exists in the folder the robot runs against and that the robot account can read it; check the asset name/path is correct.
3. **Credentials (`You must provide a value for ...` / `The authentication parameters could not be read`):** confirm every field required by the scope's authentication type is set with a literal value.
4. **Placement (`Activity is only valid inside an Office 365 Scope` / `Cannot be used outside ...`):** confirm the activity sits inside a Microsoft 365 Application Scope (or a Use OneDrive/SharePoint activity for OneDrive/SharePoint).

## Resolution

- **Asset:** correct the selected Orchestrator asset (right name/path), ensure it lives in the robot's folder, and grant the robot read access — or switch the scope to configure credentials directly.
- **Non-literal field:** provide a literal value for the field the message names, or configure the scope so the design-time service can read it.
- **Incomplete credentials:** supply the fields required for the chosen authentication type — Application ID + Tenant + (Secret or Certificate) for app-only, Username + Password for ROPC, or select an account for Interactive Token.
- **Placement:** move the activity inside a Microsoft 365 Application Scope (or a Use OneDrive/SharePoint activity).

This class is resolved entirely in Studio / Orchestrator configuration — there is no Graph response to handle. If the configuration is correct (asset resolves, credentials complete, activity correctly nested) and the scope still fails to build, escalate.
