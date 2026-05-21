# SDD Authoring — Worked Examples by Use Case

Companion to [`sdd-template.md`](sdd-template.md). Each section shows the SDD authoring snippets for a common pattern an author will encounter. Use as a reference when writing a new `sdd.md`.

Twelve v1-supported patterns. Two intentionally-dropped patterns documented at the end with workarounds.

## Quick lookup

| # | Pattern | Category | Where defined | Operator |
|---|---|---|---|---|
| 1 | Pure case state with default | `Variable` | Case Variables table | — |
| 2 | Trigger-sourced Variable (event payload → case var) | `Variable` | Case Variables + Triggers tables | — |
| 2b | Multi-trigger Variable (same slot from N triggers) | `Variable` | Case Variables + Triggers tables | — |
| 3 | Caller-supplied / Default-initialized input | `In` | Case Variables table | — |
| 4 | Returned output to caller | `Out` | Case Variables + producer task's Outputs | `->` |
| 5 | Task extracts response field → case var | (any) | Task's Outputs table | `->` |
| 6 | Task writes literal/computed value to existing var | (any) | Task's Outputs table | `=` |
| 7 | Sub-field consumer (read `=vars.X.subfield`) | `Variable` (jsonSchema) | Any expression field | — |
| 8 | Out-arg with Default fallback (no producer fires) | `Out` | Case Variables table | — |
| 9 | File In-argument (caller pre-uploads JobAttachment) | `In` (file) | Case Variables + Triggers tables | — |
| 10 | Download connector attachment → case file Variable | `Variable` (file) | Case Variables + Task Outputs | `->` |
| 11 | Send file attachment via multipart connector input | (any) | Task Inputs | — |

---

## Use Case 1 — Pure case state with default value

**Scenario:** Case tracks an internal counter or flag that's initialized at case start and may be updated by tasks during execution.

**SDD authoring** — single row in Case Variables:

```markdown
| Name        | Category | Type   | sourceTriggers | sourceFields | Default | Description                              |
|-------------|----------|--------|----------------|--------------|---------|------------------------------------------|
| caseStatus  | Variable | string |                |              | "Open"  | Current stage marker of the case          |
| reviewCount | Variable | integer |                |              | 0       | Number of review iterations completed     |
```

**Runtime behavior:** at case start, `vars.caseStatus = "Open"` and `vars.reviewCount = 0`. Downstream tasks, conditions, and SLA expressions can read them via `=vars.caseStatus` and `=vars.reviewCount`. To update them mid-case, see Use Case 6.

---

## Use Case 2 — Trigger-sourced Variable (event payload extraction)

**Scenario:** Event trigger fires from an external connector. A specific payload sub-field needs to populate a case variable so downstream tasks/conditions can use it.

**SDD authoring** — declare both the trigger AND the Case Variable that extracts from its payload:

In Case Triggers:
```markdown
| T# | Trigger Type        | Source  | Configuration                |
|----|---------------------|---------|------------------------------|
| T02 | Intsvc.EventTrigger | Outlook | Email received in Inbox      |
```

In Case Variables:
```markdown
| Name         | Category | Type   | sourceTriggers | sourceFields       | Default | Description                  |
|--------------|----------|--------|----------------|--------------------|---------|------------------------------|
| emailSubject | Variable | string | T02            | response.subject  |         | Subject line of incoming email|
| emailFrom    | Variable | string | T02            | response.from     |         | Sender address                |
```

**Runtime behavior:** when T02 fires, the engine evaluates `response.subject` against the trigger's payload and writes the value to `vars.emailSubject`. Same for `vars.emailFrom`. Both available at case-start time.

**Note:** dot-path nesting is supported (`response.user.email`, `response.attachments.first.filename`). Array indexing (`items[0]`) is NOT supported in v1.

---

## Use Case 2b — Multi-trigger Variable (same slot from multiple triggers)

**Scenario:** Case can start from multiple channels (e.g., email OR Slack), and the author wants ONE case variable holding "whoever / whatever initiated this case" regardless of channel. Whichever trigger fires populates the variable.

**SDD authoring** — single Variable row with CSV `sourceTriggers` and keyed `sourceFields`:

In Case Triggers (multiple trigger rows):
```markdown
| T# | Trigger Type        | Source  | Configuration                |
|----|---------------------|---------|------------------------------|
| T02 | Intsvc.EventTrigger | Outlook | Email received in Inbox      |
| T03 | Intsvc.EventTrigger | Slack   | Message posted in #intake     |
```

In Case Variables — one row with CSV + keyed format:
```markdown
| Name        | Category | Type   | sourceTriggers | sourceFields                                | Default | Description                  |
|-------------|----------|--------|----------------|---------------------------------------------|---------|------------------------------|
| caseStarter | Variable | string | T02, T03       | T02: response.user; T03: response.initiator |         | Whoever initiated the case   |
```

**Runtime behavior:**
- T02 (email) fires → engine extracts `response.user` → writes to `vars.caseStarter`
- T03 (Slack) fires → engine extracts `response.initiator` → writes to `vars.caseStarter`
- Only one trigger fires per case lifecycle in practice, so last-writer-wins is moot.

**Notation rules:**
- Each T-number in `sourceTriggers` MUST have a matching keyed entry in `sourceFields`. Mismatch → Phase 2 validation error.
- Order of T-numbers doesn't matter — the keyed format disambiguates per-trigger.
- Same Type and same Default apply across all listed triggers.

**When to use Use Case 2b vs declaring per-trigger Variables:**
- **Use Case 2b** when the value is *semantically the same thing* across triggers (e.g., "the initiator", "the customer ID"). One variable, one downstream reference.
- **Two separate Use Case 2 Variables** when the values are *different concepts* even if both come from triggers (e.g., `emailSubject` from email trigger and `slackChannelId` from Slack trigger are unrelated and don't share a slot).

---

## Use Case 3 — Caller-supplied input (In argument)

**Scenario:** Manual trigger; an API caller (or Studio Web "Run Case" dialog) supplies values at case start.

**SDD authoring:**

In Case Triggers:
```markdown
| T# | Trigger Type | Source | Configuration |
|----|--------------|--------|---------------|
| T02 | Manual       | API    | N/A           |
```

In Case Variables:
```markdown
| Name             | Category | Type   | sourceTriggers | sourceFields | Default | Description                       |
|------------------|----------|--------|----------------|--------------|---------|-----------------------------------|
| applicantId      | In       | string |                |              |         | Loan applicant ID (required)      |
| requestedAmount  | In       | double |                |              | 0       | Loan amount requested             |
```

**Runtime behavior:** caller submits `{applicantId: "ALC-123", requestedAmount: 50000}` via API. Engine routes these to `vars.applicantId` and `vars.requestedAmount` at case start. Downstream tasks read them via `=vars.applicantId` etc.

**Trigger type:** `In` works with any trigger type — manual, timer, or event. For event triggers, the In-arg's `Default` value propagates through to the case variable at trigger fire (no caller-override path, since events don't have an API caller). Use `In` when authoring a value that *could* be caller-supplied; use `Variable` + `sourceTriggers` + `sourceFields` (Use Case 2) when the value is *extracted from* the trigger's payload directly.

---

## Use Case 4 — Returned output to caller (Out argument)

**Scenario:** Case returns a decision and metadata to the API caller at case end. The producing task lives in some stage.

**SDD authoring** — Out-arg declared in Case Variables, producer task wires the value in its Outputs table:

In Case Variables:
```markdown
| Name          | Category | Type   | sourceTriggers | sourceFields | Default     | Description                                   |
|---------------|----------|--------|----------------|--------------|-------------|-----------------------------------------------|
| finalDecision | Out      | string |                |              | "Pending"  | Final decision returned to caller             |
| reviewComment | Out      | string |                |              |             | Reviewer's comment returned to caller         |
```

In the producing task (e.g., "Approve Decision" action task):

```markdown
**Output Schema:**

| Field   | Binding / Value      |
|---------|----------------------|
| Decision | -> finalDecision    |
| Comment  | -> reviewComment    |
```

**Runtime behavior:**
- Task fires → extracts `response.Decision` to `vars.finalDecision`; extracts `response.Comment` to `vars.reviewComment`.
- Case ends → API caller receives `{finalDecision: "Approved", reviewComment: "OK to proceed"}`.
- If the task never fires (case exits before reaching that stage), caller receives `{finalDecision: "Pending", reviewComment: ""}` — see Use Case 8 for the fallback mechanic.

---

## Use Case 5 — Task extracts response field into case variable

**Scenario:** Some task (any task type) produces a useful value in its response, and a downstream task needs to consume it.

**SDD authoring** — declare the case variable in Case Variables, then bind in the producing task's Outputs:

In Case Variables:
```markdown
| Name           | Category | Type   | sourceTriggers | sourceFields | Default | Description                                    |
|----------------|----------|--------|----------------|--------------|---------|------------------------------------------------|
| classification | Variable | string |                |              |         | Category assigned by classification agent       |
```

In the producing task's Outputs table (e.g., "Classify Email" agent task):
```markdown
| Field    | Binding / Value      |
|----------|----------------------|
| Category | -> classification    |
```

In a downstream task's Inputs (e.g., "Route to Reviewer" action task):
```markdown
| Field      | Type   | Binding                |
|------------|--------|------------------------|
| categoryIn | string | =vars.classification   |
```

**Runtime behavior:** Classify Email task completes → response `{Category: "Urgent"}` → engine extracts `"Urgent"` to `vars.classification` → Route to Reviewer task fires → reads `=vars.classification` → input `categoryIn` receives `"Urgent"`.

---

## Use Case 6 — Task writes literal/computed value to existing case variable

**Scenario:** A task needs to update a case variable's value with a literal or computed expression — NOT extracted from the task's response. Common for status flags, timestamps, counters.

**SDD authoring** — declare the target case variable in Case Variables (with initial Default), then use the `=` operator in any task's Outputs table:

In Case Variables (must be pre-declared):
```markdown
| Name        | Category | Type   | sourceTriggers | sourceFields | Default | Description                            |
|-------------|----------|--------|----------------|--------------|---------|----------------------------------------|
| caseStatus  | Variable | string |                |              | "Open"  | Stage progression marker               |
| reviewCount | Variable | integer |                |              | 0       | Count of review iterations             |
| enteredAt   | Variable | string |                |              |         | ISO timestamp when last stage entered  |
```

In a task's Outputs table (e.g., "Mark In Review" — any task type works):

```markdown
| Field | Binding / Value                            |
|-------|--------------------------------------------|
| —     | caseStatus = "InReview"                    |
| —     | reviewCount = =js:vars.reviewCount + 1     |
| —     | enteredAt = =js:new Date().toISOString()   |
```

**Runtime behavior:** task fires → engine evaluates each `=` row's right-hand side and writes to the named case variable's slot:
- `vars.caseStatus = "InReview"` (literal)
- `vars.reviewCount = previous + 1` (computed)
- `vars.enteredAt = "2026-05-17T15:30:00Z"` (computed)

**Notes:**
- `Field` column is `—` (empty / em-dash) for `=` rows.
- Target case variable MUST be pre-declared in Case Variables.
- Per task: each target case variable appears in at most one row (no double-binding). Mixing `->` and `=` for the same target in the same task is rejected.
- Same task can have both `->` rows (extract from response) AND `=` rows (literal/computed writes).

---

## Use Case 7 — Sub-field consumer (downstream input reads `=vars.X.subfield`)

**Scenario:** A trigger or upstream task produces a structured (jsonSchema) variable. Downstream consumers read a specific sub-field via dot-path navigation.

**SDD authoring** — declare ONE Variable holding the whole structured value, then consumers reference sub-fields directly:

In Case Variables:
```markdown
| Name     | Category | Type       | sourceTriggers | sourceFields | Default | Description              |
|----------|----------|------------|----------------|--------------|---------|--------------------------|
| eventData | Variable | jsonSchema | T02            | response    |         | Full event payload       |
```

In a downstream task's Inputs:
```markdown
| Field         | Type   | Binding                            |
|---------------|--------|------------------------------------|
| subject       | string | =vars.eventData.subject            |
| organizerName | string | =vars.eventData.organizer.name     |
| firstAttendee | string | =vars.eventData.attendees.first.email |
```

**Runtime behavior:** engine resolves `=vars.eventData` to the case variable, then walks the dot-path to retrieve the sub-field value. No additional Case Variables rows needed for each sub-field.

**When to use this vs Use Case 2:**
- **Use Case 7** when many sub-fields are needed sporadically (you'd otherwise need 5+ Case Variables rows that just re-extract from the same parent).
- **Use Case 2** when one or two specific sub-fields are heavily used and deserve their own first-class case variable name.

Trade-off: Use Case 7 keeps Case Variables table compact but readers have to navigate `=vars.X.Y.Z` paths. Use Case 2 is more verbose at declaration time but clearer at consumption.

---

## Use Case 8 — Out-arg with Default fallback (no producer task fires)

**Scenario:** An Out-arg might or might not be populated by a task (e.g., case can exit through multiple paths). The Default value ensures the caller always receives something sensible.

**SDD authoring** — Default value in the Out-arg's Case Variables row; producer task is optional:

In Case Variables:
```markdown
| Name    | Category | Type   | sourceTriggers | sourceFields | Default     | Description                              |
|---------|----------|--------|----------------|--------------|-------------|------------------------------------------|
| outcome | Out      | string |                |              | "Cancelled" | Final outcome returned to caller          |
```

Optional producer (if a task DOES produce the value):
```markdown
| Field    | Binding / Value |
|----------|-----------------|
| Decision | -> outcome      |
```

**Runtime behavior:**
- If the producer task fires → caller receives whatever the task produced (e.g., `"Approved"` or `"Rejected"`).
- If no task fires that targets `outcome` → caller receives `"Cancelled"` (the Default).
- The `Default` value is honored automatically by the runtime when the slot is unwritten.

**When to use:**
- Always declare a `Default` on Out-args that aren't guaranteed to be produced by every case path.
- Skip `Default` only when the producer is on the case's mandatory path (e.g., a required-stage task on the only completion path).

---

## Use Case 9 — File In-argument (caller pre-uploads JobAttachment)

**Scenario:** Case starts manually; the API caller pre-uploads a file to Orchestrator JobAttachments and passes the resulting record as an In-argument. First task in Stage 1 can immediately reference `=vars.evidenceDoc`.

**SDD authoring:**

In Case Triggers:
```markdown
| T# | Trigger Type | Source | Configuration |
|----|--------------|--------|---------------|
| T02 | Manual       | API    | N/A           |
```

In Case Variables:
```markdown
| Name        | Category | Type | sourceTriggers | sourceFields | Default | Description                                              |
|-------------|----------|------|----------------|--------------|---------|----------------------------------------------------------|
| evidenceDoc | In       | file |                |              |         | JobAttachment record supplied by caller at case start    |
```

**Runtime caller obligation** (programmatic starts only — Studio Web "Start case" picker handles this automatically):

1. `POST /odata/Attachments` with `{"Name": "claim.pdf"}` → returns `{id, blobFileAccess: {uri, verb}}`.
2. `PUT <uri>` with the file bytes → blob upload.
3. `POST .../StartJobs` with:
   - `startInfo.InputArguments.evidenceDoc = {ID, FullName, MimeType, Metadata}` (the JobAttachment record)
   - `startInfo.Attachments = [{attachmentId: <id>}]` (associates the attachment with the new job)

**Runtime behavior:** as soon as the case starts, `vars.evidenceDoc` resolves to the JobAttachment record. Downstream tasks can wire `=vars.evidenceDoc` (whole record) or `=vars.evidenceDoc.FullName` (sub-field).

**Notes:**
- `Default` MUST stay empty — the FE rejects any other value for file Variables (`InputOutputArgumentsDialog.tsx:148`).
- For event/timer triggers (no caller), use Use Case 10 instead — a Stage 1 task produces the file from an external source.

---

## Use Case 10 — Download connector attachment → case file Variable

**Scenario:** First stage downloads a file from an external system (Outlook attachment, Drive file, S3 object, …) and parks it in a case file Variable for downstream stages.

**SDD authoring:**

In Case Variables:
```markdown
| Name        | Category | Type   | sourceTriggers | sourceFields | Default | Description                                                |
|-------------|----------|--------|----------------|--------------|---------|------------------------------------------------------------|
| emailId     | In       | string |                |              |         | Outlook message id to download from (supplied by caller)   |
| evidenceDoc | Variable | file   |                |              |         | Downloaded attachment, available to all downstream stages  |
```

In Stage 1 task (Outlook 365 → Download Email Attachment, activity type `6c474b91-affe-3869-9a49-f55e464b6b77`):

```markdown
**Inputs:**

| Field                | Binding              |
|----------------------|----------------------|
| queryParameters.id   | `=vars.emailId`      |

**Outputs:**

| Field    | Binding / Value   |
|----------|-------------------|
| response | -> evidenceDoc    |
```

**Runtime behavior:**
- Activity runs, fetches the email attachment bytes, uploads to JobAttachments, writes `{ID, FullName, MimeType, Metadata}` to `vars.evidenceDoc`.
- The activity output is `type: "file"` with `target: "=orchestrator.JobAttachments"` — emitted directly by `case spec`, no skill post-processing needed.
- Downstream stages reference `=vars.evidenceDoc` or sub-fields like `=vars.evidenceDoc.FullName`.

**Notes:**
- The `response` output name is the connector spec's curated file response (knowledge file §4.1). The `->` operator on the right side names it `evidenceDoc`, which becomes the case-Variable id.
- This pattern generalizes to any connector activity whose spec returns `type: "file"` / `"octet-stream"` (CLI normalizes both to `"file"`).

---

## Use Case 11 — Send file attachment via multipart connector input

**Scenario:** A case file Variable holds an attachment (populated by an earlier trigger or download task — Use Case 10 / 9); a later stage sends it out via a connector activity that accepts a multipart file input (Outlook Send Email, Drive Upload, Slack File Upload, …).

**SDD authoring:**

In Case Variables (file already populated by an earlier task):
```markdown
| Name        | Category | Type | sourceTriggers | sourceFields | Default | Description                                |
|-------------|----------|------|----------------|--------------|---------|--------------------------------------------|
| evidenceDoc | Variable | file |                |              |         | File to attach (set by Stage 1)            |
```

In the sending task (Outlook 365 → Send Email, activity type `c7ce0a96-2091-3d94-b16f-706ebb1eb351`):

```markdown
**Inputs:**

| Field                              | Binding                |
|------------------------------------|------------------------|
| body.message.toRecipients          | `"reviewer@vip.com"`   |
| body.message.subject               | `"Evidence for review"` |
| body.message.body.contentType      | `"Text"`               |
| body.message.body.content          | `"See attached."`      |
| file                               | `=vars.evidenceDoc`    |
```

**Runtime behavior:**
- The `file` input is the multipart sink — `case spec` emits it with `target: "file"` (literal string, NOT an expression). Skill preserves verbatim.
- `=vars.evidenceDoc` resolves to the JobAttachment record; the runtime adapter fetches bytes from JobAttachments and streams them into the multipart `file` part of the outbound HTTP request.

**Anti-patterns:**
- ❌ `=vars.evidenceDoc.ID` — sub-field references are rejected by file inputs. The picker is `selectionOnly` (`IntsvcActivityPropertiesUtils.tsx:272-279`); only whole-record binding is valid.
- ❌ Hardcoded file path or URL in `value` — file variables don't hold paths; the multipart adapter expects a JobAttachment record reference.

---

## Patterns INTENTIONALLY excluded from v1 (with workarounds)

### NOT supported — InOut argument

Caller supplies a value AND receives the (possibly modified) value back at case end.

**Workaround:** declare separate `In` and `Out` arguments with different names. The first task on the case path can copy the In value to the Out target via Use Case 6 (`outId = =vars.inId`) or via a literal extraction.

Example: caller passes `inputClaimId`, case enriches, returns `enrichedClaimId`:

```markdown
| inputClaimId    | In  | string |   |   |   | Raw claim ID from caller |
| enrichedClaimId | Out | string |   |   |   | Enriched ID returned     |
```

Plus a task with:
```markdown
| — | enrichedClaimId = =vars.inputClaimId |
```

(Or use a task that calls an enrichment service via `->` extraction.)

### NOT supported — Task-local-only variables (variables not declared in Case Variables)

In v1, **every variable accessible via `=vars.X` must appear in the Case Variables table** OR be an auto-emitted field of a task's response schema (which the skill exposes by the field's natural name, e.g., `=vars.score` for a task returning `{score: number}`).

**Workaround:** if you want a "task-local" variable that doesn't pollute Case Variables, rely on the task's auto-emitted schema fields directly via their natural names. The skill auto-emits all of a task's response fields; you only need a Case Variables row when you want to RENAME the variable or expose it as case-level state with custom Default / Type / Description.

---

## Authoring checklist

When writing a new SDD, run through this list:

- [ ] Every variable referenced via `=vars.X` somewhere (input bindings, conditions, SLA expressions) — declared in Case Variables OR is a task's auto-emitted schema field
- [ ] Every `Out` Category row has either a `Default` value OR a producer task with a matching binding row
- [ ] Every `In` Category row has `sourceTriggers` empty (trigger ownership is implicit — case is assumed to have one start-path trigger that owns all `In` args)
- [ ] Every `Variable` with `sourceTriggers` set has matching entries in `sourceFields` — single path for one trigger; keyed `T<N>: <path>` format for CSV multi-trigger
- [ ] Every `sourceFields` is a valid dot-path (no `[0]` indexing)
- [ ] In each task's Outputs table: each target case variable appears in ≤1 row
- [ ] In each task's Outputs table: `->` rows have a non-empty Field column; `=` rows have `Field` as `—`
- [ ] No skill-internal vocabulary in narrative cells (per Output Rules)
