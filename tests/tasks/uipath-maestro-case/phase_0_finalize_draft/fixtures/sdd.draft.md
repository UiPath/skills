# SDD — CandidateInterview

> **⚠️ Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: 7 primary stages (within), 31 tasks (exceeds 14), 4 integrations (exceeds 3),
> 5 personas (exceeds 3), 0 child cases.
> Review carefully before approving. Consider splitting into smaller cases or trimming scope.

A Case Definition Blueprint for the Helix end-to-end candidate hiring process — from initial application receipt through recruiter screen, technical evaluation, onsite loop, debrief, offer, and final HRIS handoff to Workday.

---

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Application Received](#stage-1-application-received-stage-application-received) — 3 tasks
   - [Stage 2: Recruiter Screen](#stage-2-recruiter-screen-stage-recruiter-screen) — 3 tasks
   - [Stage 3: Technical Screen](#stage-3-technical-screen-stage-technical-screen) — 4 tasks
   - [Stage 4: Onsite Loop](#stage-4-onsite-loop-stage-onsite-loop) — 4 tasks
   - [Stage 5: Debrief](#stage-5-debrief-stage-debrief) — 3 tasks
   - [Stage 6: Offer](#stage-6-offer-stage-offer) — 5 tasks
   - [Stage 7: Hired](#stage-7-hired-stage-hired) — 3 tasks
   - [Exception Stage: Rejected](#exception-stage-rejected-stage-rejected) — 2 tasks
   - [Exception Stage: Withdrawn](#exception-stage-withdrawn-stage-withdrawn) — 2 tasks
   - [Exception Stage: On Hold](#exception-stage-on-hold-stage-on-hold) — 2 tasks
3. [Personas & App Views](#section-3-personas--app-views) — 5 Personas, Process App Views
4. [Integrations](#section-4-integrations) — Integration Service Connectors

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | CandidateInterview |
| Case Description | Manages the end-to-end hiring lifecycle for a candidate at Helix, from application receipt through recruiter screening, technical evaluation, optional onsite interview loop, compensation debrief, offer issuance via DocuSign, and final employee record creation in Workday. |
| Case Identifier | Type: constant. Prefix: CI |
| Priority | Choiceset: Low, Medium, High, Critical — Default: Medium |
| Case-Level SLA | 42 d |
| SLA Type | time-based |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 80% of SLA duration (~34 days) | Notify: UserGroup: Recruiting Leadership |
| Breached | 100% of SLA duration (42 days) | Notify: UserGroup: HR Leadership |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| `required-stages-completed` | — | Case exited as Hired | Yes |
| `selected-stage-completed("Rejected")` | — | Case exited as Rejected | No |
| `selected-stage-completed("Withdrawn")` | — | Case exited as Withdrawn | No |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| candidateName | In | string | | | | Full name of the candidate |
| candidateEmail | In | string | | | | Candidate email address |
| roleTitle | In | string | | | | Job title being applied for |
| roleDepartment | In | string | | | | Department (Engineering, Product, Design) |
| roleLevel | In | string | | | | Seniority level (L1–L7) |
| greenhouseApplicationId | In | string | | | | Greenhouse application ID |
| applicationStatus | Variable | string | | | "Active" | Current lifecycle status of the application |
| resumeScreeningResult | Variable | string | | | "" | AI resume screening outcome (Pass / Review / Fail) |
| resumeScreeningNotes | Variable | string | | | "" | Detailed AI screening commentary |
| linkedInProfileUrl | Variable | string | | | "" | LinkedIn profile URL retrieved during recruiter lookup |
| recruiterScreenNotes | Variable | string | | | "" | Notes captured during recruiter phone screen |
| coderPadSessionUrl | Variable | string | | | "" | URL of the CoderPad coding session |
| technicalInterviewerEmail | Variable | string | | | "" | Email of the assigned technical interviewer |
| technicalScreenScore | Variable | integer | | | 0 | Numeric score from technical screen (0–100) |
| technicalScreenNotes | Variable | string | | | "" | Interviewer notes from technical screen |
| onsiteRequired | Variable | boolean | | | false | Whether an onsite interview loop is required |
| onsiteScheduleDetails | Variable | string | | | "" | Schedule details for the onsite interview panel |
| scorecard1Rating | Variable | string | | | "" | Onsite interview 1 scorecard rating |
| scorecard2Rating | Variable | string | | | "" | Onsite interview 2 scorecard rating |
| scorecard3Rating | Variable | string | | | "" | Onsite interview 3 scorecard rating |
| debriefNotes | Variable | string | | | "" | Summary notes from the debrief meeting |
| offerBaseSalary | Variable | string | | | "" | Proposed base salary for the offer |
| offerTotalComp | Variable | string | | | "" | Total compensation package value |
| offerDocuSignEnvelopeId | Variable | string | | | "" | DocuSign envelope ID for the signed offer letter |
| offerAccepted | Variable | boolean | | | false | Whether the candidate accepted and signed the offer |
| workdayEmployeeId | Variable | string | | | "" | Employee ID assigned in Workday upon hiring |
| rejectionReason | Variable | string | | | "" | Reason for rejecting the candidate |
| withdrawalReason | Variable | string | | | "" | Reason the candidate withdrew from the process |
| holdReason | Variable | string | | | "" | Reason the case was placed on hold |
| holdReviewDate | Variable | datetime | | | | Date to review and potentially resume the on-hold case |
| finalDisposition | Out | string | | | "Pending" | Final outcome: Hired, Rejected, or Withdrawn |

---

## Section 2: Stages & Tasks

---

### Stage 1: Application Received (`stage-application-received`)

**Type:** Stage
**Description:** Validates and triages the incoming application by syncing data from Greenhouse, running an AI resume screen, and having the Recruiter confirm whether to advance the candidate to the next stage.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `case-entered` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: Recruiting Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Sync Application from Greenhouse | execute-connector-activity | Yes | Yes | system | — |
| 2 | Screen Resume | agent | Yes | Yes | system | — |
| 3 | Recruiter Initial Review | action | Yes | Yes | Recruiter | — |

---

##### Task 1.1: Sync Application from Greenhouse (`t01`)

**Type:** execute-connector-activity
**Description:** Retrieves the full candidate application record from Greenhouse using the application ID supplied at case start, populating any supplementary application data for downstream use.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 5e7a1087-0368-3b64-bf48-6e1470218afb
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Get Candidate

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | applicationStatus = "Active" |

---

##### Task 1.2: Screen Resume (`t02`)

**Type:** agent
**Description:** Applies AI-based screening to evaluate the candidate's resume and experience against the role requirements, producing a structured screening result and commentary for Recruiter review.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Sync Application from Greenhouse")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| candidateName | string | =vars.candidateName |
| roleTitle | string | =vars.roleTitle |
| roleDepartment | string | =vars.roleDepartment |
| roleLevel | string | =vars.roleLevel |
| applicationId | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| screeningResult | -> resumeScreeningResult |
| screeningNotes | -> resumeScreeningNotes |

---

##### Task 1.3: Recruiter Initial Review (`t03`)

**Type:** action
**Description:** The Recruiter reviews the AI screening result alongside the application data and makes the initial triage decision to advance, reject, or place the candidate on hold.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Screen Resume")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| roleDepartment | String | =vars.roleDepartment | Yes |
| roleLevel | String | =vars.roleLevel | Yes |
| resumeScreeningResult | String | =vars.resumeScreeningResult | Yes |
| resumeScreeningNotes | String | =vars.resumeScreeningNotes | No |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| rejectionNotes | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Advance | applicationStatus = "Advance" | Mark application as advancing to Recruiter Screen |
| Reject | applicationStatus = "Reject" | Mark application as rejected; rejection reason captured in rejectionNotes field |
| On Hold | applicationStatus = "OnHold" | Place application on hold pending further review |

---

### Stage 2: Recruiter Screen (`stage-recruiter-screen`)

**Type:** Stage
**Description:** The Recruiter conducts a phone screen with the candidate to assess cultural fit and role alignment. Includes a LinkedIn profile lookup for background context and a final advance/reject/withdrawn decision.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Application Received")` | =vars.applicationStatus == "Advance" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: Recruiting Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Look Up Candidate Profile | execute-connector-activity | Yes | Yes | system | — |
| 2 | Conduct and Evaluate Recruiter Screen | action | Yes | Yes | Recruiter | — |
| 3 | Update Greenhouse Stage | execute-connector-activity | Yes | Yes | system | — |

---

##### Task 2.1: Look Up Candidate Profile (`t04`)

**Type:** execute-connector-activity
**Description:** Queries LinkedIn to retrieve the candidate's public profile URL, providing Recruiter context before the phone screen.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Connector:** uipath-microsoft-linkedin
**Connection:** LinkedIn (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 1cf9777f-d12b-3b39-b4e8-284d7f957744
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Get Person By Email

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| email | string | =vars.candidateEmail |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| profileUrl | -> linkedInProfileUrl |

---

##### Task 2.2: Conduct and Evaluate Recruiter Screen (`t05`)

**Type:** action
**Description:** The Recruiter conducts the phone screen, records observations and notes, and submits the screening decision to advance, reject, or note a candidate withdrawal.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Look Up Candidate Profile")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| linkedInProfileUrl | String | =vars.linkedInProfileUrl | No |
| resumeScreeningResult | String | =vars.resumeScreeningResult | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| screenNotes | -> recruiterScreenNotes |
| rejectionNotes | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Advance | applicationStatus = "Advance" | Candidate passes recruiter screen; advance to Technical Screen |
| Reject | applicationStatus = "Reject" | Candidate does not meet bar; rejection reason captured |
| Candidate Withdrew | applicationStatus = "Withdrawn" | Candidate withdrew from process during or after phone screen |
| On Hold | applicationStatus = "OnHold" | Place process on hold at recruiter screen stage |

---

##### Task 2.3: Update Greenhouse Stage (`t06`)

**Type:** execute-connector-activity
**Description:** Advances or rejects the application in Greenhouse to keep the ATS status synchronized with the case outcome.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Conduct and Evaluate Recruiter Screen")` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 0dcc93ac-4389-30bc-82bb-7ad89980089e
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Advance Application

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | applicationStatus = =vars.applicationStatus |

---

### Stage 3: Technical Screen (`stage-technical-screen`)

**Type:** Stage
**Description:** A structured technical evaluation including a CoderPad coding session assigned to a Technical Interviewer, followed by a Hiring Manager review and final decision on whether to advance without onsite, advance to the full Onsite Loop, or reject.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Recruiter Screen")` | =vars.applicationStatus == "Advance" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 7 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: Hiring Managers |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Create CoderPad Session | execute-connector-activity | Yes | Yes | system | — |
| 2 | Assign Technical Interviewer | action | Yes | Yes | Recruiter | — |
| 3 | Conduct Technical Screen | action | Yes | Yes | Technical Interviewer | — |
| 4 | Technical Screen Decision | action | Yes | Yes | Hiring Manager | — |

---

##### Task 3.1: Create CoderPad Session (`t07`)

**Type:** execute-connector-activity
**Description:** Creates a new CoderPad coding session for the candidate and records the session URL for use during the technical interview.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Connector:** coderpad
**Connection:** CoderPad (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 00000000-0000-0000-0000-000000000000
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** API Key
**Account / Endpoint:** —
**Operation:** Create Session

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| candidateName | string | =vars.candidateName |
| jobTitle | string | =vars.roleTitle |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| sessionUrl | -> coderPadSessionUrl |

---

##### Task 3.2: Assign Technical Interviewer (`t08`)

**Type:** action
**Description:** The Recruiter selects and assigns the Technical Interviewer who will conduct the coding screen, recording the interviewer's email for coordination.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Create CoderPad Session")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| coderPadSessionUrl | String | =vars.coderPadSessionUrl | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| interviewerEmail | -> technicalInterviewerEmail |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm Assignment | applicationStatus = "Advance" | Interviewer assigned; proceed to technical screen |

---

##### Task 3.3: Conduct Technical Screen (`t09`)

**Type:** action
**Description:** The Technical Interviewer conducts the coding interview via CoderPad, scores the candidate's performance, and records detailed evaluation notes.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Assign Technical Interviewer")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| coderPadSessionUrl | String | =vars.coderPadSessionUrl | Yes |
| technicalInterviewerEmail | String | =vars.technicalInterviewerEmail | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| score | -> technicalScreenScore |
| notes | -> technicalScreenNotes |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Scorecard | applicationStatus = "Advance" | Scorecard submitted; advance to Hiring Manager review |

---

##### Task 3.4: Technical Screen Decision (`t10`)

**Type:** action
**Description:** The Hiring Manager reviews the technical scorecard and decides whether to advance the candidate without an onsite loop, advance to a full Onsite Loop (required for Engineering L4+), or reject.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Conduct Technical Screen")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| roleDepartment | String | =vars.roleDepartment | Yes |
| roleLevel | String | =vars.roleLevel | Yes |
| technicalScreenScore | Number | =vars.technicalScreenScore | Yes |
| technicalScreenNotes | String | =vars.technicalScreenNotes | Yes |
| onsiteRecommended | Boolean | =js:(vars.roleDepartment === "Engineering" && parseInt(vars.roleLevel.replace("L","")) >= 4) | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| onsiteRecommended | -> onsiteRequired |
| rejectionNotes | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Advance | applicationStatus = "Advance" | Advance; onsiteRequired captured from form checkbox |
| Reject | applicationStatus = "Reject" | Candidate does not meet technical bar |
| On Hold | applicationStatus = "OnHold" | Place process on hold after technical screen |

---

### Stage 4: Onsite Loop (`stage-onsite-loop`)

**Type:** Stage
**Description:** A panel of three Technical Interviewers conduct individual onsite interviews and submit scorecards. The Debrief stage cannot begin until all three scorecards are submitted, which is enforced by the stage completion condition.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Technical Screen")` | =js:(vars.applicationStatus === "Advance" && vars.onsiteRequired === true) | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 7 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: Hiring Managers |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Schedule Onsite Interviews | action | Yes | Yes | Recruiter | — |
| 2 | Submit Scorecard — Interviewer 1 | action | Yes | Yes | Technical Interviewer | — |
| 3 | Submit Scorecard — Interviewer 2 | action | Yes | Yes | Technical Interviewer | — |
| 4 | Submit Scorecard — Interviewer 3 | action | Yes | Yes | Technical Interviewer | — |

---

##### Task 4.1: Schedule Onsite Interviews (`t11`)

**Type:** action
**Description:** The Recruiter coordinates the onsite interview panel by scheduling three separate interview slots and records the schedule details.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| candidateEmail | String | =vars.candidateEmail | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| scheduleDetails | -> onsiteScheduleDetails |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm Schedule | applicationStatus = "Advance" | Onsite loop scheduled; interviews may proceed |

---

##### Task 4.2: Submit Scorecard — Interviewer 1 (`t12`)

**Type:** action
**Description:** Technical Interviewer 1 conducts their onsite session and submits a structured scorecard with rating and detailed observations.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Schedule Onsite Interviews")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| onsiteScheduleDetails | String | =vars.onsiteScheduleDetails | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| rating | -> scorecard1Rating |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Scorecard | applicationStatus = "Advance" | Scorecard 1 submitted |

---

##### Task 4.3: Submit Scorecard — Interviewer 2 (`t13`)

**Type:** action
**Description:** Technical Interviewer 2 conducts their onsite session and submits a structured scorecard with rating and observations.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Schedule Onsite Interviews")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| onsiteScheduleDetails | String | =vars.onsiteScheduleDetails | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| rating | -> scorecard2Rating |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Scorecard | applicationStatus = "Advance" | Scorecard 2 submitted |

---

##### Task 4.4: Submit Scorecard — Interviewer 3 (`t14`)

**Type:** action
**Description:** Technical Interviewer 3 conducts their onsite session and submits a structured scorecard with rating and observations.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Schedule Onsite Interviews")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| onsiteScheduleDetails | String | =vars.onsiteScheduleDetails | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| rating | -> scorecard3Rating |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Scorecard | applicationStatus = "Advance" | Scorecard 3 submitted |

---

### Stage 5: Debrief (`stage-debrief`)

**Type:** Stage
**Description:** The Hiring Manager facilitates a structured debrief meeting to review all evaluation data (resume screening, technical screen, and onsite scorecards). Produces a final hire/no-hire decision.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Technical Screen")` | =js:(vars.applicationStatus === "Advance" && vars.onsiteRequired === false) | No |
| `selected-stage-completed("Onsite Loop")` | =vars.applicationStatus == "Advance" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 3 | d | 75% | Notify: UserGroup: Hiring Managers | Notify: UserGroup: Recruiting Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Prepare Debrief Summary | agent | Yes | Yes | system | — |
| 2 | Conduct Debrief Meeting | action | Yes | Yes | Hiring Manager | — |
| 3 | Record Debrief Decision | action | Yes | Yes | Hiring Manager | — |

---

##### Task 5.1: Prepare Debrief Summary (`t15`)

**Type:** agent
**Description:** An AI agent compiles and synthesizes all evaluation data — resume screening notes, technical screen score and notes, and all onsite scorecards — into a structured debrief summary to facilitate the meeting.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| candidateName | string | =vars.candidateName |
| roleTitle | string | =vars.roleTitle |
| resumeScreeningResult | string | =vars.resumeScreeningResult |
| technicalScreenScore | integer | =vars.technicalScreenScore |
| technicalScreenNotes | string | =vars.technicalScreenNotes |
| scorecard1Rating | string | =vars.scorecard1Rating |
| scorecard2Rating | string | =vars.scorecard2Rating |
| scorecard3Rating | string | =vars.scorecard3Rating |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| debriefSummary | -> debriefNotes |

---

##### Task 5.2: Conduct Debrief Meeting (`t16`)

**Type:** action
**Description:** The Hiring Manager reviews the AI-prepared debrief summary with the full hiring panel and records key discussion points and consensus signal.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Prepare Debrief Summary")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| debriefNotes | String | =vars.debriefNotes | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| meetingNotes | -> debriefNotes |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Debrief Complete | applicationStatus = "Advance" | Debrief meeting conducted; proceed to decision task |

---

##### Task 5.3: Record Debrief Decision (`t17`)

**Type:** action
**Description:** The Hiring Manager submits the final hire/no-hire decision following the debrief discussion, which routes the case to either the Offer stage or the Rejected exception stage.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Conduct Debrief Meeting")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| debriefNotes | String | =vars.debriefNotes | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| rejectionNotes | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Advance to Offer | applicationStatus = "Advance" | Hire decision made; route to Offer stage |
| Reject | applicationStatus = "Reject" | No-hire decision made; route to Rejected exception |

---

### Stage 6: Offer (`stage-offer`)

**Type:** Stage
**Description:** The Compensation Analyst prepares the compensation package, the Hiring Manager approves, and the offer letter is sent to the candidate via DocuSign. The case waits for the signed envelope before advancing to the Hired stage.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Debrief")` | =vars.applicationStatus == "Advance" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 7 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: Compensation Analysts |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Prepare Offer Package | action | Yes | Yes | Compensation Analyst | — |
| 2 | Approve Offer | action | Yes | Yes | Hiring Manager | — |
| 3 | Send Offer Letter | execute-connector-activity | Yes | Yes | system | — |
| 4 | Await Offer Signature | wait-for-connector | Yes | Yes | system | — |
| 5 | Update Greenhouse Offer Status | execute-connector-activity | Yes | Yes | system | — |

---

##### Task 6.1: Prepare Offer Package (`t18`)

**Type:** action
**Description:** The Compensation Analyst reviews compensation benchmarks and prepares the offer package including base salary and total compensation for the Hiring Manager's approval.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| roleDepartment | String | =vars.roleDepartment | Yes |
| roleLevel | String | =vars.roleLevel | Yes |
| debriefNotes | String | =vars.debriefNotes | No |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| baseSalary | -> offerBaseSalary |
| totalComp | -> offerTotalComp |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Offer Package | applicationStatus = "Advance" | Compensation package prepared; route to HM approval |

---

##### Task 6.2: Approve Offer (`t19`)

**Type:** action
**Description:** The Hiring Manager reviews the proposed compensation package and either approves it for sending or requests revisions from the Compensation Analyst.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Prepare Offer Package")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| offerBaseSalary | String | =vars.offerBaseSalary | Yes |
| offerTotalComp | String | =vars.offerTotalComp | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| — | offerAccepted = false |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve Offer | applicationStatus = "Advance" | Compensation approved; proceed to send offer via DocuSign |
| Request Revision | applicationStatus = "Active" | Revisions requested; return to Compensation Analyst |

---

##### Task 6.3: Send Offer Letter (`t20`)

**Type:** execute-connector-activity
**Description:** Sends the signed offer letter to the candidate via DocuSign, creating an envelope and recording the envelope ID for tracking.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Approve Offer")` | =vars.applicationStatus == "Advance" |

**Connector:** uipath-docusign-docusign
**Connection:** DocuSign (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 4f48f8d0-d55e-3f3c-ae4b-ee7ce234dc7e
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Send Envelope

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| recipientEmail | string | =vars.candidateEmail |
| recipientName | string | =vars.candidateName |
| subject | string | =js:("Offer Letter - " + vars.roleTitle + " at Helix") |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| envelopeId | -> offerDocuSignEnvelopeId |

---

##### Task 6.4: Await Offer Signature (`t21`)

**Type:** wait-for-connector
**Description:** Pauses the case and waits for the DocuSign event confirming that the candidate has signed all documents in the offer envelope.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |
| `selected-tasks-completed("Send Offer Letter")` | — |

**Connector:** uipath-docusign-docusign
**Connection:** DocuSign (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** b697fea8-0f23-586c-ac00-26798f0b6cbc
**Service Type:** Intsvc.ConnectorTrigger
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Trigger / Event:** Envelope Signed by All Recipients

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| envelopeId | string | =vars.offerDocuSignEnvelopeId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | offerAccepted = true |
| — | applicationStatus = "Advance" |

---

##### Task 6.5: Update Greenhouse Offer Status (`t22`)

**Type:** execute-connector-activity
**Description:** Updates the Greenhouse application record to reflect the offer letter was sent and accepted, keeping the ATS in sync.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Await Offer Signature")` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** d106f103-2990-3db0-a703-061e8c7a19a1
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Update Candidate

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | applicationStatus = "Advance" |

---

### Stage 7: Hired (`stage-hired`)

**Type:** Stage
**Description:** Completes the hiring process by creating the employee record in Workday, notifying the hiring team, and closing the application in Greenhouse as hired.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Offer")` | =vars.offerAccepted == true | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | d | 75% | Notify: UserGroup: Recruiters | Notify: UserGroup: HR Leadership |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Create Employee Record in Workday | execute-connector-activity | Yes | Yes | system | — |
| 2 | Notify Hiring Team | action | Yes | Yes | Recruiter | — |
| 3 | Close Application in Greenhouse | execute-connector-activity | Yes | Yes | system | — |

---

##### Task 7.1: Create Employee Record in Workday (`t23`)

**Type:** execute-connector-activity
**Description:** Creates the new hire record in Workday (HRIS) using the candidate information and role details, completing the HRIS handoff.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Connector:** uipath-workday-workday
**Connection:** Workday (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 4ca3f6fb-cd19-395c-8d96-0825aef04777
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Hire Employee

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| firstName | string | =vars.candidateName |
| email | string | =vars.candidateEmail |
| jobTitle | string | =vars.roleTitle |
| department | string | =vars.roleDepartment |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| employeeId | -> workdayEmployeeId |

---

##### Task 7.2: Notify Hiring Team (`t24`)

**Type:** action
**Description:** The Recruiter confirms the hire and sends onboarding notifications to the hiring team, HR, and the new employee using the Workday employee ID.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Create Employee Record in Workday")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| workdayEmployeeId | String | =vars.workdayEmployeeId | Yes |
| candidateEmail | String | =vars.candidateEmail | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| — | finalDisposition = "Hired" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm and Notify | applicationStatus = "Hired" | Hiring team notified; proceed to close in Greenhouse |

---

##### Task 7.3: Close Application in Greenhouse (`t25`)

**Type:** execute-connector-activity
**Description:** Marks the Greenhouse application as hired and closes it, ensuring the ATS reflects the final successful hiring outcome.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Notify Hiring Team")` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 0dcc93ac-4389-30bc-82bb-7ad89980089e
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Advance Application

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | finalDisposition = "Hired" |

---

### Exception Stage: Rejected (`stage-rejected`)

**Type:** ExceptionStage
**Description:** Handles the rejection path for candidates eliminated at any stage of the hiring process. Sends a rejection notification and updates Greenhouse.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Application Received")` | =vars.applicationStatus == "Reject" | No |
| `selected-stage-completed("Recruiter Screen")` | =vars.applicationStatus == "Reject" | No |
| `selected-stage-completed("Technical Screen")` | =vars.applicationStatus == "Reject" | No |
| `selected-stage-completed("Debrief")` | =vars.applicationStatus == "Reject" | No |
| `selected-stage-completed("Offer")` | =vars.applicationStatus == "Reject" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Send Rejection Notification | execute-connector-activity | Yes | Yes | system | — |
| 2 | Update Greenhouse — Rejected | execute-connector-activity | Yes | Yes | system | — |

---

##### Task R.1: Send Rejection Notification (`t26`)

**Type:** execute-connector-activity
**Description:** Sends a rejection email notification to the candidate via the Greenhouse connector, communicating the hiring decision.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** f7d2791d-1c9a-3304-8316-9ca2a589448c
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Reject Application

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |
| rejectionReason | string | =vars.rejectionReason |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | finalDisposition = "Rejected" |

---

##### Task R.2: Update Greenhouse — Rejected (`t27`)

**Type:** execute-connector-activity
**Description:** Updates the Greenhouse application record status to reflect the final rejected disposition.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Send Rejection Notification")` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** 99e1499a-0000-0000-0000-000000000000
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Update Record

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | finalDisposition = "Rejected" |

---

### Exception Stage: Withdrawn (`stage-withdrawn`)

**Type:** ExceptionStage
**Description:** Handles cases where the candidate voluntarily withdraws from the interview process at any stage. Records the withdrawal reason and updates Greenhouse.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Recruiter Screen")` | =vars.applicationStatus == "Withdrawn" | No |
| `selected-stage-completed("Technical Screen")` | =vars.applicationStatus == "Withdrawn" | No |
| `selected-stage-completed("Onsite Loop")` | =vars.applicationStatus == "Withdrawn" | No |
| `selected-stage-completed("Debrief")` | =vars.applicationStatus == "Withdrawn" | No |
| `selected-stage-completed("Offer")` | =vars.applicationStatus == "Withdrawn" | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Record Withdrawal | action | Yes | Yes | Recruiter | — |
| 2 | Update Greenhouse — Withdrawn | execute-connector-activity | Yes | Yes | system | — |

---

##### Task W.1: Record Withdrawal (`t28`)

**Type:** action
**Description:** The Recruiter documents the candidate's withdrawal including the reason, date, and any relevant context for future reference.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |
| candidateEmail | String | =vars.candidateEmail | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| withdrawalReason | -> withdrawalReason |
| — | finalDisposition = "Withdrawn" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm Withdrawal | applicationStatus = "Withdrawn" | Withdrawal recorded; update ATS |

---

##### Task W.2: Update Greenhouse — Withdrawn (`t29`)

**Type:** execute-connector-activity
**Description:** Updates the Greenhouse application record to reflect the candidate's withdrawal from the process.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Record Withdrawal")` | — |

**Connector:** uipath-greenhouse-greenhouse
**Connection:** Greenhouse (tenant default)
**Connection ID:** tenant-default
**Activity Type ID:** f7d2791d-1c9a-3304-8316-9ca2a589448c
**Service Type:** Intsvc.ConnectorActivity
**Auth Method:** OAuth2
**Account / Endpoint:** —
**Operation:** Reject Application

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| id | string | =vars.greenhouseApplicationId |
| rejectionReason | string | =vars.withdrawalReason |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| — | finalDisposition = "Withdrawn" |

---

### Exception Stage: On Hold (`stage-on-hold`)

**Type:** ExceptionStage
**Description:** Temporarily pauses the hiring process when the Recruiter determines the case should be held (e.g., budget freeze, role re-scoping). Resumes to the origin stage after the hold review date passes.
**Required for Case Completion:** No
**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Application Received")` | =vars.applicationStatus == "OnHold" | Yes |
| `selected-stage-completed("Recruiter Screen")` | =vars.applicationStatus == "OnHold" | Yes |
| `selected-stage-completed("Technical Screen")` | =vars.applicationStatus == "OnHold" | Yes |
| `selected-stage-completed("Debrief")` | =vars.applicationStatus == "OnHold" | Yes |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | return-to-origin | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Document Hold Details | action | Yes | Yes | Recruiter | — |
| 2 | Schedule Hold Review | wait-for-timer | Yes | Yes | system | — |

---

##### Task OH.1: Document Hold Details (`t30`)

**Type:** action
**Description:** The Recruiter documents the reason for placing the case on hold and sets a review date, after which the process will be automatically resumed.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| candidateName | String | =vars.candidateName | Yes |
| roleTitle | String | =vars.roleTitle | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| reason | -> holdReason |
| reviewDate | -> holdReviewDate |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Place on Hold | applicationStatus = "OnHold" | Hold details recorded; set hold timer |

---

##### Task OH.2: Schedule Hold Review (`t31`)

**Type:** wait-for-timer
**Description:** Pauses the case until the hold review date arrives, at which point the On Hold stage completes and the case returns to the stage that was interrupted.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Document Hold Details")` | — |

**Timer:** dateTime
**Value:** =vars.holdReviewDate

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Recruiter | All | View, Act, Reassign | Primary coordinator of the hiring lifecycle; manages scheduling, ATS updates, and exception handling |
| Hiring Manager | Technical Screen, Onsite Loop, Debrief, Offer, Hired | View, Act | Reviews technical evaluations and makes advance/reject and offer decisions |
| Technical Interviewer | Technical Screen, Onsite Loop | View, Act | Conducts technical evaluations and submits scorecards |
| Compensation Analyst | Offer | View, Act | Prepares and structures the compensation package for the offer |
| Candidate | All | View | The individual being evaluated through the hiring process (external portal access) |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| CandidateInterview App | Case List | Recruiter, Hiring Manager | View all active candidate cases with stage and status filters | Candidate name, Role, Stage, Status, SLA indicator, Assigned Recruiter |
| CandidateInterview App | Case Detail | All personas | Full case view with stage history, task actions, and data fields | Stage timeline, Task panel, Variable values, Activity log |
| CandidateInterview App | Scorecard Dashboard | Hiring Manager, Technical Interviewer | View submitted scorecards and evaluation summaries per candidate | Scorecard ratings per interviewer, AI debrief summary, Decision recommendation |

---

## Section 4: Integrations

### Integration Service Connectors

| Connector | System | Auth Method | Operations Used | Used By Tasks |
|-----------|--------|-------------|-----------------|---------------|
| uipath-greenhouse-greenhouse | Greenhouse ATS | OAuth2 | Get Candidate, Advance Application, Reject Application, Update Candidate, Update Record | t01, t06, t22, t25, t26, t27, t29 |
| uipath-microsoft-linkedin | LinkedIn | OAuth2 | Get Person By Email | t04 |
| uipath-docusign-docusign | DocuSign | OAuth2 | Send Envelope, Envelope Signed by All Recipients (trigger) | t20, t21 |
| uipath-workday-workday | Workday HRIS | OAuth2 | Hire Employee | t23 |

#### uipath-greenhouse-greenhouse

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Get Candidate | GET | id | candidate.name, candidate.emails, jobs.name |
| Advance Application | POST | id | status |
| Reject Application | POST | id, rejectionReason | status |
| Update Candidate | PUT | id | status |

#### uipath-docusign-docusign

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Send Envelope | POST | recipientEmail, recipientName, subject | envelopeId |
| Envelope Signed by All Recipients | EVENT | envelopeId (filter) | status, completedDateTime |

#### uipath-workday-workday

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Hire Employee | POST | firstName, email, jobTitle, department | employeeId |
