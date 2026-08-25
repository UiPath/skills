---
confidence: medium
---

# HTTP Activity — Workflow Analyzer ST-SEC-009 (SecureString Misusage, design-time)

## Context

What this looks like:
- A **design-time** Workflow Analyzer finding — **`ST-SEC-009` SecureString Misusage** — raised against an `HttpClient` / `NetHttpRequest` (or its surrounding Assign). At **Error** severity it blocks validate/publish; at Warning it flags the file. No runtime job is involved.
- Typical trigger: a credential/API token held as a **`SecureString`** (e.g. from **Get Credential** / an Orchestrator credential asset) is **converted to a plain `String`** to build an `Authorization` / API-key **header** — e.g. `new System.Net.NetworkCredential(String.Empty, secureToken).Password`, `.ToString()`, or `Marshal.PtrToStringBSTR(...)` — and/or the `SecureString` variable is **scoped wider** than the activity that needs it.

What causes it (per the rule):
- **ST-SEC-009 flags casting `SecureString` to `String`** and `SecureString` variables whose scope extends beyond where they are created. The Web activities' `Headers` dictionary takes plain strings, so putting a secret in a header requires a `SecureString→String` conversion — which is exactly what the rule catches. This is a **secure-coding lint, not an activity bug**.

What to look for:
- The **conversion expression** feeding the header (`NetworkCredential(...).Password`, `.ToString()`, `Marshal.*`).
- The **scope** of the `SecureString` variable — is it declared at the whole workflow/`Sequence` level rather than the minimal container?
- The **rule severity** in Project Settings → Workflow Analyzer (Error blocks build; Warning does not).

## Do NOT recommend a package upgrade as the fix

Upgrading `UiPath.WebAPI.Activities` (e.g. to `2.3.0+`) does **NOT** resolve ST-SEC-009 and does **not** add "native SecureString-in-headers" handling — the header dictionary is still plain-string, so the conversion (and the finding) remain. This is a common but **false** fix. The finding is about how the secret is handled in the workflow, addressed by scoping + secure storage + (optionally) excluding the activity from the rule — see below.

## Do NOT invent a SecureString header property

`HttpClient` has **no** `AuthenticationType` property and its `OAuth2Token` is a **plain `String`**, not a `SecureString` — routing a bearer token through `OAuth2Token` still requires a `SecureString`→`String` conversion and does not clear ST-SEC-009. The only SecureString-typed auth input is **`SecurePassword`**, and it applies to **Basic (Username/Password) authentication only** — not to a bearer/API-key header. For a header-borne token there is no SecureString escape hatch on the activity; the fix is scoping + secure storage + point-of-use conversion + (optionally) rule exclusion, below.

## Investigation

1. **Confirm it is design-time** (Workflow Analyzer, not a job fault) and read the exact rule id/severity.
2. **Find the SecureString→String conversion** in the workflow source that feeds the HTTP header, and note the `SecureString` variable's scope.
3. **Confirm the secret's source** — Get Credential / Orchestrator asset (good) vs a hard-coded or broadly-scoped value (worse).

## Resolution

- **Minimise scope.** Retrieve the secret with **Get Credential** and keep the `SecureString` variable scoped to the smallest container (the `Sequence` that builds and sends the request), so it is disposed as soon as that scope completes.
- **Store the secret securely.** Use an **Orchestrator Credential asset / credential store** — never a hard-coded key or a plain-`String` variable that lingers.
- **Convert at the point of use only**, inside that minimal scope, with `new System.Net.NetworkCredential(String.Empty, secureToken).Password` — do not persist the plaintext to a wider-scoped `String` variable.
- **If the activity genuinely cannot accept `SecureString`**, exclude it from the rule deliberately: Project Settings → **Workflow Analyzer** → add the activity namespace to the rule's **Excluded Activities** field (or lower ST-SEC-009 from Error to Warning if policy allows). This is a conscious, scoped exception — not a blanket disable.
- Re-run the analyzer to confirm the finding clears.
