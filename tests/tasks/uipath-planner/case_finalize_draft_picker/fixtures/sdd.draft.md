# SDD — VendorOnboarding

A Case Definition Blueprint for onboarding a new supplier at Northwind: collect the vendor's documents, approve the vendor, and let a Compliance Officer pull the case aside for a compliance hold whenever they spot a red flag.

---

## Requirements (authoritative — settled with the business owner)

- Document Collection runs first, then Vendor Approval.
- **Compliance Hold is launched by a person, not by an event.** A Compliance Officer watching the queue can pull any active case into the Compliance Hold lane at any moment from the stage picker. Nothing triggers it automatically — there is no connector event, no SLA breach, and no decision button that routes there. When the hold clears, the case returns to the stage it came from.
- The Approve Vendor decision itself only advances or rejects the vendor; it never sends anything to Compliance Hold.

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | VendorOnboarding |
| Case Description | Onboards a new supplier at Northwind from document collection through vendor approval, with a manually-launched compliance hold lane. |
| Case Identifier | Type: constant. Prefix: VO |
| Case-Level SLA | — |
| SLA Type | — |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T01 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| `required-stages-completed` | — | Vendor onboarded | Yes |

### Case Variables

| Variable | Type | Default | Producer | Consumed By |
|----------|------|---------|----------|-------------|
| vendorName | String | — | Case trigger input | Collect Vendor Documents, Approve Vendor |
| documentsComplete | Boolean | false | Collect Vendor Documents | Approve Vendor entry gate |
| vendorDecision | String | — | Approve Vendor | Case exit reporting |
| complianceFindings | String | — | Compliance Review | Approve Vendor |

---

## Section 2: Stages & Tasks

### Stage 1: Document Collection (`stage-document-collection`)

**Type:** Stage
**Description:** Collects and files the vendor's registration, tax, and insurance documents before any approval work starts.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `case-entered` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Collect Vendor Documents | api-workflow | Yes | No | system | — |

---

##### Task 1.1: Collect Vendor Documents (`t01`)

**Type:** api-workflow
**Description:** Pulls the vendor's submitted registration, tax, and insurance documents from the supplier portal and records whether the set is complete.
**Design Rationale:** A system integration with no human judgment, so an api-workflow rather than an action task.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Resource Identity:** `<UNRESOLVED: api-workflow "Collect Vendor Documents">`
**Folder Path:** `<UNRESOLVED>`

**Inputs:**

| Field | Binding / Value |
|-------|-----------------|
| vendorName | =vars.vendorName |

**Outputs:**

| Field | Binding / Value |
|-------|-----------------|
| complete | -> documentsComplete |

---

### Stage 2: Vendor Approval (`stage-vendor-approval`)

**Type:** Stage
**Description:** A Procurement Manager reviews the collected documents and approves or rejects the vendor.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Document Collection")` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Approve Vendor | action | Yes | No | Procurement Manager | — |

---

##### Task 2.1: Approve Vendor (`t02`)

**Type:** action
**Description:** The Procurement Manager reviews the document set and any compliance findings, then approves or rejects the vendor.
**Design Rationale:** A human judgment call on the vendor record, so an action task with an explicit decision.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| vendorName | String | =vars.vendorName | Yes |
| complianceFindings | String | =vars.complianceFindings | No |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | vendorDecision = "Approve" | Vendor approved; case completes |
| Reject | vendorDecision = "Reject" | Vendor rejected; case completes |

---

### Secondary Stage: Compliance Hold (`stage-compliance-hold`)

**Type:** Secondary Stage
**Interrupting:** Yes
**Description:** A Compliance Officer pulls the case into this lane to run an ad-hoc compliance review, then returns it to the stage it came from.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `user-selected-stage` | — | Yes |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | return-to-origin | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Compliance Review | action | Yes | No | Compliance Officer | — |

---

##### Task 3.1: Compliance Review (`t03`)

**Type:** action
**Description:** The Compliance Officer records the compliance findings for the vendor and releases the hold.
**Design Rationale:** A human review with a written finding, so an action task.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| vendorName | String | =vars.vendorName | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|-----------------|
| findings | -> complianceFindings |

---

## Section 3: Personas & App Views

| Persona | Description |
|---------|-------------|
| Procurement Manager | Approves or rejects the vendor. |
| Compliance Officer | Watches the active queue and pulls cases into Compliance Hold. |

---

## Section 4: Integrations

| Integration | Connector | Usage |
|-------------|-----------|-------|
| Supplier portal | — | Document retrieval via the Collect Vendor Documents api-workflow. |
