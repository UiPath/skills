# Final Resolution

---

**Root Cause:** The Workflow Analyzer rule **`ST-SEC-009` (SecureString
Misusage)** fires because `Main.xaml` converts a `SecureString` to a plain
`String` and holds it in an over-wide scope. `GetRobotCredential` outputs the
bearer token as a `SecureString` (`apiToken`); an Assign then builds the HTTP
`Authorization` header with `"Bearer " + new System.Net.NetworkCredential(
String.Empty, apiToken).Password` — a `SecureString`→`String` cast — and the
`apiToken` variable is declared at the whole "Create Support Ticket" sequence
scope. `ST-SEC-009` flags exactly this: casting `SecureString` to `String`,
and `SecureString` variables scoped beyond where they are needed. This is a
**design-time secure-coding finding, not a runtime fault or an activity bug**;
the process has never executed, so there are no Orchestrator jobs.

**The floated fix is wrong:** Upgrading `UiPath.WebAPI.Activities` to `2.3.0+`
does **NOT** clear `ST-SEC-009` and does not add "native SecureString-in-headers"
handling. The HTTP Request `Headers` dictionary is plain-`String` in every
version, so the conversion — and the finding — remain regardless of package
version. Do not recommend the package upgrade as the fix.

---

**Evidence:**

### Design-time (Root Cause)
- Symptom: Workflow Analyzer reports `ST-SEC-009 SecureString Misusage` at Error severity; validation fails and the project won't publish. No execution.
- `Main.xaml`: `GetRobotCredential` → `apiToken` (`SecureString`); Assign sets `authHeaderValue = "Bearer " + new System.Net.NetworkCredential(String.Empty, apiToken).Password` (SecureString→String cast); `HttpClient` `Authorization` header = `authHeaderValue`; `apiToken` declared at the sequence scope (wider than needed).
- The finding is a design-time analyzer result, not a job fault.

### Orchestrator (ruled out)
- No jobs exist (the process never ran); `or jobs list ... --state Faulted` returns empty. The diagnosis comes from `Main.xaml`, not job evidence.

### Package upgrade (ruled out)
- `UiPath.WebAPI.Activities 2.3.0+` does not resolve ST-SEC-009. The `Headers` dictionary remains plain-`String`, so the SecureString→String conversion still occurs and the rule still fires. The forum claim of "native secure handling" via package upgrade is false for this finding.

---

**Immediate fix:**

Address how the secret is handled in the workflow — not the package version.

1. **Keep the secret secure end-to-end.** Retrieve it with **Get Credential**
   from an **Orchestrator credential asset / credential store**; never
   hard-code it or persist the plaintext in a wider-scoped `String`.
2. **Minimise the SecureString scope.** Declare `apiToken` in the smallest
   container that builds and sends the request, so it is disposed as soon as
   that scope completes — not at the whole-sequence level.
3. **Convert only at the point of use.** Perform the
   `new System.Net.NetworkCredential(String.Empty, apiToken).Password`
   conversion inline where the header is set, inside that minimal scope; do
   not assign the plaintext to a longer-lived variable.
4. **If the activity genuinely cannot accept `SecureString`,** exclude it from
   the rule deliberately: Project Settings → **Workflow Analyzer** → add the
   activity namespace to `ST-SEC-009`'s **Excluded Activities** field (or lower
   the rule from Error to Warning if policy allows). A conscious, scoped
   exception — not a blanket disable.
- **Source:** `web-activities/playbooks/securestring-misuse-analyzer.md`.

> Do NOT "fix" this by upgrading `UiPath.WebAPI.Activities` — the package
> version does not change the plain-string header dictionary or clear
> ST-SEC-009.

---

**Preventive fix:**

1. **Retrieve and convert secrets at the point of use in a minimal scope** --
   standardise on Get Credential + Orchestrator credential assets; keep
   `SecureString` variables local.
   - **Why:** wide-scoped `SecureString` and eager `SecureString`→`String`
     conversion both trip ST-SEC-009 and leave secrets in memory longer.
   - **Who:** RPA developer.

2. **Record deliberate rule exclusions in project governance** -- when an
   activity cannot accept `SecureString`, document the ST-SEC-009 exclusion
   rather than disabling the rule globally.
   - **Who:** RPA developer / platform team.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | ST-SEC-009 fires because Main.xaml casts a SecureString token to String (NetworkCredential(...).Password) into the HTTP Authorization header and scopes the SecureString sequence-wide | Medium | Confirmed | Yes | Design-time ST-SEC-009 Error + Main.xaml SecureString→String conversion feeding header + wide variable scope + never ran (no jobs) | Get Credential + minimal scope + Orchestrator credential asset + convert at point of use; optionally exclude the activity namespace from the rule |
| H2 | Upgrading UiPath.WebAPI.Activities to 2.3.0+ adds native secure handling and clears ST-SEC-009 | Low | Rejected | No | Header dictionary is plain-String in all versions; package upgrade does not change the conversion or the finding | Not a fix — address secret handling instead |

---

Would you like a concrete before/after of the Get Credential + minimal-scope
pattern for this HTTP Request, or the exact Project Settings path to record an
ST-SEC-009 exclusion?
