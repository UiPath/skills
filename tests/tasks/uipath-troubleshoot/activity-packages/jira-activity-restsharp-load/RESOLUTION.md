# Final Resolution

---

**Root Cause:** A transitive **RestSharp** version conflict. The project depends
on both `UiPath.Jira.Activities` (built against `RestSharp 106.x`) and
`UiPath.WebAPI.Activities` (which pulls a newer RestSharp). At runtime only one
RestSharp assembly loads; because it is not the `106.15.0.0` the Jira pack was
built against, the Jira activity's reference no longer resolves and the scope
faults at load with `System.IO.FileLoadException: Could not load file or assembly
'RestSharp, Version=106.15.0.0 ...' ... The located assembly's manifest
definition does not match the assembly reference. (HRESULT: 0x80131040)`.

**What went wrong:** The `JiraTicketCreator` job (started 2026-06-15T11:30:01Z)
faulted ~1.5 seconds after launch at `Jira Scope`, before any Jira REST call.
The job error and Error-level logs show the `FileLoadException` on
`RestSharp, Version=106.15.0.0` at `JiraApplicationScope "Jira Scope"`. The
project worked until another activity package was added — the classic
manifest-mismatch signature of a shared-dependency version collision.

**Why:** This is the activity-load family. The legacy `UiPath.Jira.Activities`
pack carries pinned transitive dependencies — notably **RestSharp**. When a
second package in the same project (`UiPath.WebAPI.Activities` here) pins a
different RestSharp, NuGet/runtime resolution keeps one version. The version that
wins does not match the Jira pack's reference (`106.15.0.0`), so the loader
cannot bind the Jira activity assembly and raises `FileLoadException` with
`HRESULT 0x80131040` (manifest definition does not match the reference). This is
not a credential problem (no `Authentication information is invalid`) and not a
response/URL problem (no REST call ran) — the activity never loaded.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraTicketCreator -- Faulted at 2026-06-15T11:30:02.640Z (ran ~1.5 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Integrations (key `5a03a2b3-d4e5-4f60-8a03-000000000003`)
- Final error: `System.IO.FileLoadException: Could not load file or assembly 'RestSharp, Version=106.15.0.0 ...' ... manifest definition does not match the assembly reference. (HRESULT: 0x80131040)` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"`

### Jira Activities (Root Cause)
- The fault is an assembly **load** failure at `Jira Scope`, before authentication or any REST call — so the auth and response/URL families are ruled out.
- `project.json` depends on `UiPath.Jira.Activities` `[1.9.4]` **and** `UiPath.WebAPI.Activities` `[1.20.2]`. Both packages rely on **RestSharp**; the Jira pack was built against `RestSharp 106.15.0.0`, which is the version the loader reports as missing/mismatched.
- The failure began after the second package was added (per the user) — the dependency graph changed and the RestSharp the Jira pack needs is no longer the one that loads.

---

**Immediate fix:**

Two paths — prefer the migration for a durable fix.

### Fix path A -- resolve the version conflict (keep the classic pack)
Align the project so the RestSharp version the Jira pack needs is the one that
loads: remove or replace `UiPath.WebAPI.Activities` (e.g. use the modern
`UiPath.Web.Activities` HTTP activities, or a version that does not force a newer
RestSharp), or pin the dependency so `RestSharp 106.x` wins. Restore, re-open in
Studio (the Jira activity should load), and re-run.

### Fix path B -- migrate off the legacy scope (preferred)
Move the Jira logic from the classic `UiPath.Jira.Activities` Jira Scope to the
**Integration Service** Jira connector activities. The connector uses a managed
OAuth connection instead of an in-workflow scope and does not carry the legacy
in-project RestSharp dependency, so it is not subject to this class of conflict.
This is the recommended path for new work and when the version conflict cannot be
resolved cleanly in-project.

### Verification (hand to the user - off-host / in Studio)
- In Studio, open *Manage Packages* and check the resolved **RestSharp** version
  against what `UiPath.Jira.Activities` requires; the mismatch is the cause.
- After applying either fix, confirm the Jira activity loads (no red error in the
  designer) and the job runs past the scope.

- **Source:** `jira-activities/playbooks/jira-activity-missing-or-not-loaded.md`

---

**Preventive fix:**

1. **Watch shared transitive dependencies** -- before adding a package to a
   project that uses the classic Jira pack, check whether it pulls a different
   **RestSharp** (or other shared assembly) version.
   - **Why:** the legacy Jira pack pins specific transitive versions; a sibling
     package that forces a newer one breaks the assembly binding at load.
   - **Who:** RPA developer.

2. **Prefer the Integration Service Jira connector for new work** -- it avoids
   in-project legacy dependencies entirely.
   - **Who:** RPA developer / solution architect.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Transitive RestSharp version conflict between UiPath.Jira.Activities and UiPath.WebAPI.Activities; Jira activity fails to load | High | Confirmed | Yes | `FileLoadException` on `RestSharp 106.15.0.0` (manifest mismatch, HRESULT 0x80131040) at Jira Scope; both packages in project.json; failure began after adding the second package | Resolve the RestSharp pin or migrate to the Integration Service Jira connector |
| H2 | Authentication failure | Low | Rejected | No | No `Authentication information is invalid`; fault is an assembly load error before any REST call | -- |
| H3 | Server URL / response problem | Low | Rejected | No | No REST call ran; the activity never loaded | -- |

---

Would you like the exact `project.json` dependency edit, the steps to swap the
Jira Scope for the Integration Service connector, or help cleaning up the
`.local/investigations/` folder?
