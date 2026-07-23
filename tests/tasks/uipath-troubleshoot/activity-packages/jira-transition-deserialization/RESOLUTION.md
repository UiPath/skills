# Final Resolution

---

**Root Cause:** A known JSON metadata-deserialization bug in an **older**
`UiPath.Jira.Activities` release. The project pins `UiPath.Jira.Activities`
`[1.5.0]`; when `Get Transitions` parses the transition field metadata for an
issue that has a complex custom field (here `customfield_10044`, which carries an
`operations` array), the old pack cannot map the value to its
`Atlassian.Jira.IssueFieldEditMetadataOperation` type and throws
`Newtonsoft.Json.JsonSerializationException: Error converting value "add" to type
'Atlassian.Jira.IssueFieldEditMetadataOperation'`.

**What went wrong:** The `JiraEscalation` job (started 2026-06-16T17:22:02Z)
authenticated and opened the session (Trace log: "session opened"), then faulted
inside `Get Transitions` (Trace: "fetching transitions with field metadata for
issue OPS-2087") with the `Error converting value "add" to type
'...IssueFieldEditMetadataOperation'` at `Path
'fields.customfield_10044.operations[0]'`. The workflow logic is correct — it
resolves transitions dynamically and the auth/URL are valid — so the failure is
not in how the workflow is built; it is the package deserializing the field
metadata.

**Why:** This is sub-case **T4** of the transition-issue playbook. Older
`UiPath.Jira.Activities` versions mis-handle complex transition-screen field
metadata (attachments, radio/option lists, fields with an `operations` array)
when deserializing the Jira REST response into the pack's
`Atlassian.Jira.IssueFieldEditMetadataOperation` type. The error is a
`Newtonsoft.Json.JsonSerializationException` raised during the metadata
round-trip, before the transition is even attempted — a version-bound parsing
defect, not a configuration or data problem. This is not a missing required
field (no `Field '<name>' is required`), not an invalid transition ID (no
`Transition '<id>' is not valid`), and not a permission/validator denial.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: JiraEscalation -- Faulted at 2026-06-16T17:22:04.010Z (ran ~2 seconds)
- Job type: Unattended, triggered manually by user "user1" on machine MOCK-ROBOT
- Folder: Escalations (key `5a06a2b3-d4e5-4f60-8a06-000000000006`)
- Final error: `Get Transitions: Error converting value "add" to type 'Atlassian.Jira.IssueFieldEditMetadataOperation'. Path 'fields.customfield_10044.operations[0]'` -> `Main.xaml` -> `JiraApplicationScope "Jira Scope"` -> `GetTransitions "Get Transitions"`

### Jira Activities (Root Cause)
- The scope authenticated and opened (Trace: "session opened ... Api Token"); the fault is inside `Get Transitions` parsing field metadata — auth, URL, and transition-config causes are ruled out.
- `project.json` pins `UiPath.Jira.Activities` `[1.5.0]` — an old release.
- The exception is `Newtonsoft.Json.JsonSerializationException` converting to `Atlassian.Jira.IssueFieldEditMetadataOperation` at a custom field's `operations` array — the documented **T4** metadata-parsing bug on complex fields.

---

**Immediate fix:**

### Fix path A -- upgrade the package (preferred, in-place)
In Studio, open **Manage Packages** and upgrade `UiPath.Jira.Activities` from
`1.5.0` to the latest stable release; the `IssueFieldEditMetadataOperation`
deserialization bug on complex field metadata is fixed in newer versions.
Restore, re-validate, and re-run.

### Fix path B -- migrate to the Integration Service Jira connector
If the project is cloud-targeted, move the Jira calls to the **Integration
Service** Jira connector activities, which use standard REST structures and do
not go through the legacy pack's metadata deserialization path.

### Verification (hand to the user - off-host / in Studio)
- Check the pinned `UiPath.Jira.Activities` version in `project.json` (`1.5.0`)
  against the latest available in Manage Packages; upgrade and confirm
  `Get Transitions` succeeds on `OPS-2087`.

- **Source:** `jira-activities/playbooks/jira-transition-issue-failures.md` (T4)

---

**Preventive fix:**

1. **Keep the Jira pack current** -- complex-field metadata handling improved
   across releases; do not run transition/metadata workflows on long-stale pack
   versions.
   - **Why:** the deserialization of complex transition-screen fields is
     version-bound; old packs throw on field shapes newer packs handle.
   - **Who:** RPA developer.

2. **Prefer the Integration Service Jira connector for new work** -- it avoids
   the legacy deserialization path entirely.
   - **Who:** RPA developer / solution architect.

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | Old UiPath.Jira.Activities (1.5.0) metadata-deserialization bug on a complex field (T4) | High | Confirmed | Yes | `Newtonsoft.Json.JsonSerializationException: Error converting value "add" to type 'Atlassian.Jira.IssueFieldEditMetadataOperation'` at `fields.customfield_10044.operations[0]` in Get Transitions; `UiPath.Jira.Activities [1.5.0]` in project.json; workflow logic and auth valid | Upgrade UiPath.Jira.Activities, or migrate to the Integration Service Jira connector |
| H2 | Missing required field (T1) | Low | Rejected | No | Error is a JSON type-conversion exception, not `Field '<name>' is required`; fails before the transition is attempted | -- |
| H3 | Invalid transition ID (T2) | Low | Rejected | No | Workflow resolves transitions dynamically via Get Transitions; no `Transition '<id>' is not valid` | -- |

---

Would you like the exact package version to upgrade to, the steps to swap in the
Integration Service Jira connector, or help cleaning up the
`.local/investigations/` folder?
