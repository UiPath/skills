# Final Resolution

---

**Root Cause:** The `Get Outlook Mail Messages` activity in `Main.xaml`
carries a malformed DASL/Jet `Filter`. The expression is
`[Subject] = VarSubject` -- the right-hand value is **unquoted**, so it is
not a valid DASL literal. When Outlook applies the restriction it cannot
parse the condition and raises
`Cannot parse condition. Error at "VarSubject".`, surfaced through COM as
`System.Runtime.InteropServices.COMException ... (Exception from HRESULT:
0x80020009 (DISP_E_EXCEPTION))`. The folder resolved and the COM session is
fine -- the only fault is the filter syntax.

This maps to
`references/activity-packages/mail-activities/playbooks/get-outlook-mail-failures.md`,
**Branch 4 (Malformed `Filter` -- DASL/Jet)**.

**What went wrong:** The `SupportTriageReader` job (started
2026-06-03T09:25:00Z) faulted ~2 seconds after launch, immediately after the
activity applied its `Filter`. The job logs show Outlook attached over COM
and the `Inbox` folder resolved cleanly, then the activity echoed the applied
restriction `[Get Outlook Mail Messages] applying Filter: [Subject] = VarSubject`
on the line **immediately before** the parse error -- the unquoted value is
visible in that log line.

**Why:** DASL/Jet requires the value on the right of a comparison to be a
quoted string literal. `[Subject] = VarSubject` makes Outlook treat
`VarSubject` as a token it cannot resolve, so it rejects the whole condition.
The value must be single-quoted: `[Subject] = 'Text'`. When the value comes
from a workflow variable it must be concatenated INSIDE the quotes:
`"[Subject] = '" + mySubjectVariable + "'"`.

**This is NOT the other branches, and NOT a null variable:**

- **NOT Branch 1 (folder not resolved).** The log line
  `Resolved mail folder 'Inbox' on the default profile` confirms the
  `MailFolder` resolved; there is no "specified folder does not exist" error.
- **NOT Branch 2 (timeout on a large folder).** The job faulted in ~2 s with a
  parse error, not "The operation has timed out" after `TimeoutMS`.
- **NOT Branch 3 (Outlook not running / COM cast / privilege).** Outlook
  attached over COM (`Attached to running Outlook application via COM`); there
  is no "Outlook is not running" message, no cast failure, and no hang.
- **NOT Branch 5 (Cached Exchange Mode desync).** That branch produces NO
  error and silently missing mail; here the job faulted with an explicit parse
  error.
- **NOT an empty / uninitialized subject variable.** The fault is the
  **missing quotes** (invalid DASL syntax), not a null value. A null value
  would still be a syntactically valid `[Subject] = ''` once quoted; the parse
  error fires before any value lookup because the literal is unquoted.

---

**Evidence:**

### Orchestrator (Propagation)
- Job: SupportTriageReader -- Faulted at 2026-06-03T09:25:02.330Z (ran ~2.2 seconds)
- Job type: Unattended, triggered by a scheduled trigger on machine MOCK-HOST
- Folder: RPA Production (key `c1d2e3f4-5a6b-4c7d-8e9f-0a1b2c3d4e5f`)
- Final error: `Get Outlook Mail Messages: Cannot parse condition. Error at "VarSubject".` -> `Main.xaml` -> `GetOutlookMailMessages "Get Outlook Mail Messages"` -> `Sequence "Main Sequence"` -> `Main "Main"`, wrapping `COMException ... 0x80020009 (DISP_E_EXCEPTION)`

### Mail Activities (Root Cause)
- Activity: `GetOutlookMailMessages` (DisplayName: "Get Outlook Mail Messages"), package `UiPath.Mail.Outlook.Activities`
- `MailFolder` (from `Main.xaml`): `Inbox` -- valid, and confirmed resolved in the logs
- `Account` (from `Main.xaml`): empty (default profile) -- not implicated
- `Top` (from `Main.xaml`): `50` -- not implicated
- `Filter` (from `Main.xaml`): **`[Subject] = VarSubject`** -- the unquoted
  right-hand value is the bug
- Job-log smoking gun: `[Get Outlook Mail Messages] applying Filter: [Subject] = VarSubject`
  immediately precedes `Cannot parse condition. Error at "VarSubject".`

---

**Immediate fix:**

Single-quote the value in the `Filter` so it is a valid DASL/Jet literal.

- Incorrect (current): `[Subject] = VarSubject`
- Correct (literal): `[Subject] = 'Text to find'`
- Correct (variable): `"[Subject] = '" + mySubjectVariable + "'"`

Save, rebuild, and re-run. The activity will apply the restriction and return
the matching `MailMessage` list instead of faulting.

---

**Preventive fix:**

1. **Studio** -- always single-quote DASL/Jet values in any `Filter`, and
   parameterize them with the quotes baked into the concatenation
   (`"[Subject] = '" + var + "'"`). Never concatenate a bare variable into a
   DASL expression.
   - **Why:** An unquoted value is the most common Get Outlook Mail filter
     fault and fails at parse time on every run.
   - **Who:** RPA developer
2. **Studio** -- validate a new `Filter` against a small known-matching set
   before running at scale, so a syntax error is caught at design time rather
   than as a production fault.
   - **Why:** Confirms the restriction parses and returns the expected mail.
   - **Who:** RPA developer

---

**Investigation Summary:**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | The `Filter` is malformed DASL/Jet -- the value `VarSubject` is unquoted, so Outlook cannot parse the condition | High | Confirmed | Yes | `Filter="[Subject] = VarSubject"` in `Main.xaml` + job-log `applying Filter: [Subject] = VarSubject` + `Cannot parse condition. Error at "VarSubject".` (HRESULT 0x80020009) | Single-quote the value: `[Subject] = 'Text'` / `"[Subject] = '" + var + "'"` |
| H2 | Folder not resolved (Branch 1) | Low | Eliminated | No | Log: `Resolved mail folder 'Inbox' on the default profile`; no "specified folder does not exist" | n/a |
| H3 | Outlook not running / COM session broken (Branch 3) | Low | Eliminated | No | Log: `Attached to running Outlook application via COM`; no cast failure, no hang | n/a |

---

Would you like me to draft the one-line `Filter` fix as a patch note you can
hand to the RPA developer, or clean up the `.local/investigations/` folder?
