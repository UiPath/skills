# SDD — LoanOrigination

> **⚠️ Generated lightweight; complexity exceeded thresholds.**
> Counts at generation time: 6 primary stages, 45 primary-stage tasks, 5 integrations,
> 5 personas, 0 child cases.
> Review carefully before approving. Consider splitting into smaller cases or trimming scope.

A case definition blueprint for the commercial term-loan origination lifecycle at
Accrual Capital. Each case represents one loan application from receipt through funding
(or adverse disposition), spanning Intake → Loan Setup → Underwriting → QA/QC →
Closing → Resolved, with four exception paths (Customer Comms, Escalation, Withdrawn,
Rejected).

---

## Table of Contents

1. [Case Definition](#section-1-case-definition) — Metadata, SLA, Triggers, Exit Conditions, Variables
2. [Stages & Tasks](#section-2-stages--tasks)
   - [Stage 1: Intake](#stage-1-intake) — 6 tasks
   - [Stage 2: Loan Setup](#stage-2-loan-setup) — 8 tasks
   - [Stage 3: Underwriting](#stage-3-underwriting) — 10 tasks
   - [Stage 4: QA/QC](#stage-4-qaqc) — 7 tasks
   - [Stage 5: Closing](#stage-5-closing) — 9 tasks
   - [Stage 6: Resolved](#stage-6-resolved) — 5 tasks
   - [Exception Stage: Customer Comms](#exception-stage-customer-comms) — 2 tasks
   - [Exception Stage: Escalation](#exception-stage-escalation) — 1 task
   - [Exception Stage: Withdrawn](#exception-stage-withdrawn) — 2 tasks
   - [Exception Stage: Rejected](#exception-stage-rejected) — 2 tasks
3. [Personas & App Views](#section-3-personas--app-views) — 5 Personas, Process App Views
4. [Integrations](#section-4-integrations) — External API Integrations

---

## Section 1: Case Definition

### Case Metadata

| Property | Value |
|----------|-------|
| Case Name | LoanOrigination |
| Case Description | Manages the end-to-end origination lifecycle for commercial term loans at Accrual Capital, from initial application receipt through funding or adverse disposition. Covers ~600 loans per month in the $1M–$25M range with a 30–45 day target lifecycle. |
| Case Identifier | Type: constant. Prefix: LO |
| Priority | Choiceset: Low, Medium, High, Critical — Default: Medium |
| Case-Level SLA | 45 d |
| SLA Type | time-based |

### Case-Level SLA Escalation Rules

| SLA Status | Threshold | Action |
|------------|-----------|--------|
| At-Risk | 80% of SLA duration (36 days) | Notify: UserGroup: LoanOperationsManagement _(source: inferred-default:no recipient stated — stage owner group applied)_ |
| Breached | 100% of SLA duration (45 days) | Notify: UserGroup: CreditCommittee _(source: inferred-default:no recipient stated — leadership tier applied)_ |

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete |
|------|-----|------|---------------------|
| `required-stages-completed` | — | Case exited | Yes |
| `selected-stage-completed("Withdrawn" (`stage-withdrawn`))` | — | Case exited | No |
| `selected-stage-completed("Rejected" (`stage-rejected`))` | — | Case exited | No |

### Case Variables

| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |
|------|----------|------|----------------|--------------|---------|-------------|
| loanApplicationId | In | string | | | | Unique loan application identifier supplied by the caller |
| borrowerName | In | string | | | | Borrower full legal name |
| borrowerEntity | In | string | | | | Borrowing entity or company name |
| loanAmount | In | float | | | | Requested loan amount in dollars |
| propertyAddress | In | string | | | | Subject property street address |
| propertyType | In | string | | | | Property type (e.g., commercial real estate, multi-family) |
| loanOfficerId | In | string | | | | Initiating Loan Officer user ID |
| borrowerEmail | In | string | | | | Borrower email address for communications |
| caseStatus | Variable | string | | | "Open" | Current case status (Open, Withdrawn, Declined, Funded) |
| communicationRequested | Variable | boolean | | | false | Flag set by Loan Officer when borrower communication is required |
| escalationRequired | Variable | boolean | | | false | Flag set when the loan requires management escalation |
| creditScore | Variable | integer | | | | Experian credit score retrieved in Intake |
| dAndBRating | Variable | string | | | | D&B business credit rating retrieved in Intake |
| uccLienResults | Variable | string | | | | UCC lien search summary from county portal |
| eligibilityResult | Variable | string | | | | Initial eligibility assessment outcome from AI screening |
| appraisalOrderId | Variable | string | | | | Property appraisal order reference number |
| appraiserValue | Variable | float | | | | Appraised property value in dollars entered by Loan Officer |
| titleSearchResult | Variable | string | | | | Title search result summary |
| floodZone | Variable | string | | | | FEMA flood zone designation |
| collateralData | Variable | jsonSchema | | | | Collateral assessment data retrieved from Databricks |
| assignedUnderwriterId | Variable | string | | | | Assigned underwriter user ID |
| financialAnalysisResult | Variable | jsonSchema | | | | AI financial statement analysis output |
| cashFlowResult | Variable | jsonSchema | | | | AI cash flow analysis output |
| riskScore | Variable | float | | | | Computed credit risk score from Databricks ML model |
| ltvRatio | Variable | float | | | | Loan-to-value ratio |
| dscr | Variable | float | | | | Debt service coverage ratio |
| underwriterDecision | Variable | string | | | | Underwriter decision: Approve, Conditional, Decline |
| conditionsToApproval | Variable | string | | | | Conditions attached to a conditional approval |
| qaDecision | Variable | string | | | | QA/QC officer decision: Approved, Rejected |
| disbursementAmount | Variable | float | | | | Actual loan disbursement amount |
| recordingConfirmation | Variable | string | | | | County deed of trust recording confirmation number |
| withdrawalReason | Variable | string | | | | Reason for loan withdrawal captured by Loan Officer |
| rejectionReason | Variable | string | | | | Reason for loan rejection captured in Adverse Action Notice |
| finalDecision | Out | string | | | "Pending" | Final loan decision returned at case close |
| caseOutcome | Out | string | | | "Pending" | Case outcome: Funded, Withdrawn, Rejected |

---

## Section 2: Stages & Tasks

### Stage 1: Intake (`stage-intake`)

**Type:** Stage
**Description:** Captures the initial loan application, collects required documents, pulls third-party credit and lien data, and performs an automated initial eligibility screen. Completed when all data has been gathered and the eligibility assessment is available.
**Required for Case Completion:** Yes

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
| 3 | d | 75% | Notify: UserGroup: LoanOperations | Notify: UserGroup: LoanOperationsManagement |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Receive Loan Application | action | Yes | Yes | Loan Officer | 1d |
| 2 | Document Collection | action | Yes | Yes | Loan Officer | — |
| 3 | Pull Experian Credit Report | api-workflow | Yes | Yes | — | — |
| 4 | Pull D&B Business Credit Report | api-workflow | Yes | Yes | — | — |
| 5 | UCC Lien Search | api-workflow | Yes | Yes | — | — |
| 6 | Initial Eligibility Assessment | agent | Yes | Yes | — | — |

---

##### Task 1.1: Receive Loan Application (`t01`)

**Type:** action
**Description:** Loan Officer reviews and confirms the loan application details, sets initial case metadata, and determines whether a borrower communication should be triggered.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| borrowerEntity | String | =vars.borrowerEntity | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |
| propertyType | String | =vars.propertyType | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Open" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm Application | communicationRequested = false | Confirms receipt; proceeds to document collection |
| Send Initial Communication | communicationRequested = true | Confirms receipt and flags that a borrower communication should be sent |
| Mark Withdrawn | caseStatus = "Withdrawn" | Marks loan as withdrawn at intake; triggers Withdrawn exception path |

---

##### Task 1.2: Document Collection (`t02`)

**Type:** action
**Description:** Loan Officer reviews the document submission checklist and confirms all required loan documents (financial statements, property docs, entity docs) have been received.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Receive Loan Application")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| borrowerName | String | =vars.borrowerName | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Documents Collected" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Documents Complete | caseStatus = "Documents Collected" | All required documents received; proceed to data pulls |
| Documents Incomplete | communicationRequested = true | Flag missing documents; request borrower communication |

---

##### Task 1.3: Pull Experian Credit Report (`t03`)

**Type:** api-workflow
**Description:** Calls the Experian credit bureau API to retrieve the borrower's credit report and score for use in underwriting.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Document Collection")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerName | string | =vars.borrowerName |
| borrowerEntity | string | =vars.borrowerEntity |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.creditScore | -> creditScore |
| — | eligibilityResult = "CreditPulled" |

---

##### Task 1.4: Pull D&B Business Credit Report (`t04`)

**Type:** api-workflow
**Description:** Calls the Dun & Bradstreet API to retrieve the borrower entity's commercial credit rating and business risk profile.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Document Collection")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerEntity | string | =vars.borrowerEntity |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.rating | -> dAndBRating |

---

##### Task 1.5: UCC Lien Search (`t05`)

**Type:** api-workflow
**Description:** Queries county UCC portal APIs to search for any existing Uniform Commercial Code liens on the borrower entity or subject property.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Document Collection")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerEntity | string | =vars.borrowerEntity |
| propertyAddress | string | =vars.propertyAddress |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.lienSummary | -> uccLienResults |

---

##### Task 1.6: Initial Eligibility Assessment (`t06`)

**Type:** agent
**Description:** AI agent evaluates the collected credit data, D&B rating, and lien results against Accrual Capital's initial eligibility criteria to produce a pass/refer/decline recommendation.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Pull Experian Credit Report", "Pull D&B Business Credit Report", "UCC Lien Search")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| creditScore | integer | =vars.creditScore |
| dAndBRating | string | =vars.dAndBRating |
| uccLienResults | string | =vars.uccLienResults |
| loanAmount | float | =vars.loanAmount |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.recommendation | -> eligibilityResult |

---

### Stage 2: Loan Setup (`stage-loan-setup`)

**Type:** Stage
**Description:** Establishes the full loan file by entering data into the LOS, ordering appraisal and title, completing flood and environmental reviews, verifying insurance, and confirming all setup is complete before underwriting begins.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Intake" (`stage-intake`))` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 7 | d | 70% | Notify: UserGroup: LoanOperations | Notify: UserGroup: LoanOperationsManagement |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Enter Loan Data | action | Yes | Yes | Loan Officer | — |
| 2 | Order Property Appraisal | action | Yes | Yes | Loan Officer | — |
| 3 | Title Search | api-workflow | Yes | Yes | — | — |
| 4 | Flood Zone Certification | api-workflow | Yes | Yes | — | — |
| 5 | Enter Appraisal Value | action | Yes | No | Loan Officer | — |
| 6 | Insurance Verification | action | Yes | Yes | Loan Officer | — |
| 7 | Collateral Data Retrieval | api-workflow | Yes | Yes | — | — |
| 8 | Confirm Loan Setup | action | Yes | Yes | Loan Officer | — |

---

##### Task 2.1: Enter Loan Data (`t07`)

**Type:** action
**Description:** Loan Officer enters all loan and borrower details into the LOS, confirming data accuracy against the intake application.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| borrowerEntity | String | =vars.borrowerEntity | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |
| propertyType | String | =vars.propertyType | Yes |
| eligibilityResult | String | =vars.eligibilityResult | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Loan Setup" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Data Entered | caseStatus = "Loan Setup" | LOS data entry complete; proceed to parallel setup tasks |
| Mark Withdrawn | caseStatus = "Withdrawn" | Borrower has withdrawn the application at setup stage |

---

##### Task 2.2: Order Property Appraisal (`t08`)

**Type:** action
**Description:** Loan Officer places the property appraisal order with an approved appraiser and records the order reference number.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Enter Loan Data")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| propertyAddress | String | =vars.propertyAddress | Yes |
| propertyType | String | =vars.propertyType | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> appraisalOrderId |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Appraisal Ordered | appraisalOrderId = =vars.appraisalOrderId | Appraisal placed; record order reference and proceed |

---

##### Task 2.3: Title Search (`t09`)

**Type:** api-workflow
**Description:** Calls the county records API to perform a title search on the subject property and return any encumbrances or title issues.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Enter Loan Data")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| propertyAddress | string | =vars.propertyAddress |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.titleSummary | -> titleSearchResult |

---

##### Task 2.4: Flood Zone Certification (`t10`)

**Type:** api-workflow
**Description:** Queries the FEMA flood map service to determine the flood zone designation for the subject property.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Enter Loan Data")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| propertyAddress | string | =vars.propertyAddress |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.floodZone | -> floodZone |

---

##### Task 2.5: Enter Appraisal Value (`t11`)

**Type:** action
**Description:** Loan Officer enters the appraised property value once the appraisal report is received from the appraiser. This task can be triggered when the report arrives.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `adhoc` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| appraisalOrderId | String | =vars.appraisalOrderId | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> appraiserValue |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Submit Appraisal Value | appraiserValue = =vars.appraiserValue | Record appraised value; enables LTV calculation in underwriting |

---

##### Task 2.6: Insurance Verification (`t12`)

**Type:** action
**Description:** Loan Officer verifies that the borrower has obtained adequate hazard insurance and records confirmation.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Enter Loan Data")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| borrowerName | String | =vars.borrowerName | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Insurance Verified" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Insurance Verified | caseStatus = "Insurance Verified" | Insurance confirmed; proceed to setup completion |
| Insurance Pending | communicationRequested = true | Insurance not yet obtained; flag for borrower communication |

---

##### Task 2.7: Collateral Data Retrieval (`t13`)

**Type:** api-workflow
**Description:** Calls the Databricks API to retrieve collateral assessment data including comparable sales, valuation models, and market data for the subject property.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Enter Loan Data")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| propertyAddress | string | =vars.propertyAddress |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.collateralData | -> collateralData |

---

##### Task 2.8: Confirm Loan Setup (`t14`)

**Type:** action
**Description:** Loan Officer confirms that all setup tasks are complete and the file is ready for underwriting.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Title Search", "Flood Zone Certification", "Enter Appraisal Value", "Insurance Verification", "Collateral Data Retrieval")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| titleSearchResult | String | =vars.titleSearchResult | Yes |
| floodZone | String | =vars.floodZone | Yes |
| appraiserValue | Number | =vars.appraiserValue | Yes |
| collateralData | Object | =vars.collateralData | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Ready for Underwriting" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Setup Complete | caseStatus = "Ready for Underwriting" | All setup elements confirmed; route to underwriting |
| Mark Withdrawn | caseStatus = "Withdrawn" | Borrower has withdrawn before underwriting begins |

---

### Stage 3: Underwriting (`stage-underwriting`)

**Type:** Stage
**Description:** Full credit and risk underwriting including AI-driven financial and cash flow analysis, risk scoring, LTV and DSCR calculations, and Underwriter review with a final credit decision. For loans ≤$5M, the Underwriter absorbs the Credit Analyst role.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Loan Setup" (`stage-loan-setup`))` | `vars.caseStatus != "Withdrawn"` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 15 | d | 70% | Notify: UserGroup: CreditTeamManagement | Notify: UserGroup: CreditCommittee |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Assign Underwriter | action | Yes | Yes | Loan Officer | — |
| 2 | Financial Statement Analysis | agent | Yes | Yes | — | — |
| 3 | Cash Flow Analysis | agent | Yes | Yes | — | — |
| 4 | Compute Risk Score | api-workflow | Yes | Yes | — | — |
| 5 | Calculate LTV Ratio | process | Yes | Yes | — | — |
| 6 | Calculate DSCR | process | Yes | Yes | — | — |
| 7 | Credit and Risk Review | action | Yes | Yes | Underwriter | 3d |
| 8 | Underwriting Decision | action | Yes | Yes | Underwriter | 2d |
| 9 | Document Conditions | action | No | No | Underwriter | — |
| 10 | Generate Underwriting Report | process | Yes | Yes | — | — |

---

##### Task 3.1: Assign Underwriter (`t15`)

**Type:** action
**Description:** Loan Officer assigns the appropriate underwriter to the file based on loan type and current workload. For loans ≤$5M the Underwriter absorbs credit analyst duties.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanAmount | Number | =vars.loanAmount | Yes |
| loanApplicationId | String | =vars.loanApplicationId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> assignedUnderwriterId |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Assign Underwriter | assignedUnderwriterId = =vars.assignedUnderwriterId | Underwriter assigned; triggers parallel analysis tasks |

---

##### Task 3.2: Financial Statement Analysis (`t16`)

**Type:** agent
**Description:** AI agent analyzes the borrower's financial statements (balance sheet, income statement, tax returns) against Accrual Capital's credit criteria using the Databricks analytical platform.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Assign Underwriter")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| collateralData | jsonSchema | =vars.collateralData |
| borrowerEntity | string | =vars.borrowerEntity |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.analysis | -> financialAnalysisResult |

---

##### Task 3.3: Cash Flow Analysis (`t17`)

**Type:** agent
**Description:** AI agent evaluates borrower cash flow projections and historical operating cash flows against DSCR thresholds using Snowflake data.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Assign Underwriter")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| financialAnalysisResult | jsonSchema | =vars.financialAnalysisResult |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.cashFlow | -> cashFlowResult |

---

##### Task 3.4: Compute Risk Score (`t18`)

**Type:** api-workflow
**Description:** Calls the Databricks ML model endpoint to compute a composite credit risk score from credit bureau data, financial analysis, and collateral metrics.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Financial Statement Analysis", "Cash Flow Analysis")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| creditScore | integer | =vars.creditScore |
| dAndBRating | string | =vars.dAndBRating |
| financialAnalysisResult | jsonSchema | =vars.financialAnalysisResult |
| cashFlowResult | jsonSchema | =vars.cashFlowResult |
| loanAmount | float | =vars.loanAmount |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.riskScore | -> riskScore |

---

##### Task 3.5: Calculate LTV Ratio (`t19`)

**Type:** process
**Description:** Calculates the loan-to-value ratio by dividing the requested loan amount by the appraised property value.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Assign Underwriter")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanAmount | float | =vars.loanAmount |
| appraiserValue | float | =vars.appraiserValue |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| ltvRatioResult | -> ltvRatio |

---

##### Task 3.6: Calculate DSCR (`t20`)

**Type:** process
**Description:** Calculates the debt service coverage ratio from the cash flow analysis results and the proposed loan payment schedule.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Cash Flow Analysis")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| cashFlowResult | jsonSchema | =vars.cashFlowResult |
| loanAmount | float | =vars.loanAmount |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| dscrResult | -> dscr |

---

##### Task 3.7: Credit and Risk Review (`t21`)

**Type:** action
**Description:** Underwriter (absorbing Credit Analyst role for loans ≤$5M) reviews all credit data, risk score, LTV, DSCR, and collateral analysis before forming a credit recommendation.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Compute Risk Score", "Calculate LTV Ratio", "Calculate DSCR")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| creditScore | Number | =vars.creditScore | Yes |
| dAndBRating | String | =vars.dAndBRating | Yes |
| uccLienResults | String | =vars.uccLienResults | Yes |
| riskScore | Number | =vars.riskScore | Yes |
| ltvRatio | Number | =vars.ltvRatio | Yes |
| dscr | Number | =vars.dscr | Yes |
| financialAnalysisResult | Object | =vars.financialAnalysisResult | Yes |
| cashFlowResult | Object | =vars.cashFlowResult | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Under Credit Review" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Review Complete | caseStatus = "Under Credit Review" | Credit review done; proceed to underwriting decision |
| Escalate | escalationRequired = true | Flag loan for management escalation |

---

##### Task 3.8: Underwriting Decision (`t22`)

**Type:** action
**Description:** Underwriter renders the formal credit decision (Approve, Conditional Approval, or Decline) after reviewing all analysis. This decision drives the downstream routing of the case.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Credit and Risk Review")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| riskScore | Number | =vars.riskScore | Yes |
| ltvRatio | Number | =vars.ltvRatio | Yes |
| dscr | Number | =vars.dscr | Yes |
| creditScore | Number | =vars.creditScore | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Decision Rendered" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | underwriterDecision = "Approve" | Loan approved; sets finalDecision and routes to QA/QC |
| Conditional Approval | underwriterDecision = "Conditional" | Approved with conditions; routes to document conditions task |
| Decline | underwriterDecision = "Decline" | Loan declined; routes to Rejected exception stage |
| Escalate | escalationRequired = true | Escalates to management; routes to Escalation exception stage |

---

##### Task 3.9: Document Conditions (`t23`)

**Type:** action
**Description:** Underwriter documents any conditions attached to a conditional approval, which the borrower must satisfy before closing.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Underwriting Decision")` | `vars.underwriterDecision == "Conditional"` |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| underwriterDecision | String | =vars.underwriterDecision | Yes |
| loanApplicationId | String | =vars.loanApplicationId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> conditionsToApproval |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Conditions Documented | conditionsToApproval = =vars.conditionsToApproval | Conditions recorded; proceed to QA/QC |

---

##### Task 3.10: Generate Underwriting Report (`t24`)

**Type:** process
**Description:** Generates the formal underwriting summary report from all analysis data, risk metrics, and the credit decision for the loan file.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Underwriting Decision")` | `vars.underwriterDecision != "Decline"` |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| underwriterDecision | string | =vars.underwriterDecision |
| riskScore | float | =vars.riskScore |
| ltvRatio | float | =vars.ltvRatio |
| dscr | float | =vars.dscr |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | finalDecision = =vars.underwriterDecision |

---

### Stage 4: QA/QC (`stage-qa-qc`)

**Type:** Stage
**Description:** Performs regulatory compliance checks (ECOA, HMDA), AI-assisted document completeness and data integrity validation, fair lending analysis, and final QA officer sign-off before closing.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Underwriting" (`stage-underwriting`))` | `vars.underwriterDecision == "Approve" \|\| vars.underwriterDecision == "Conditional"` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 5 | d | 75% | Notify: UserGroup: LoanOperations | Notify: UserGroup: LoanOperationsManagement |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | ECOA Compliance Check | action | Yes | Yes | Loan Officer | 1d |
| 2 | HMDA Data Validation | action | Yes | Yes | Loan Officer | — |
| 3 | Document Completeness Review | agent | Yes | Yes | — | — |
| 4 | Data Integrity Validation | process | Yes | Yes | — | — |
| 5 | Fair Lending Analysis | agent | Yes | Yes | — | — |
| 6 | QA Officer Review | action | Yes | Yes | Loan Officer | — |
| 7 | Final QA Approval | action | Yes | Yes | Loan Officer | 1d |

---

##### Task 4.1: ECOA Compliance Check (`t25`)

**Type:** action
**Description:** Loan Officer reviews the loan file for Equal Credit Opportunity Act compliance, confirming no discriminatory factors influenced the credit decision. ECOA requires a licensed officer sign-off on the adverse action determination.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| underwriterDecision | String | =vars.underwriterDecision | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "ECOA Review Complete" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| ECOA Compliant | caseStatus = "ECOA Review Complete" | No ECOA issues found; proceed to HMDA validation |
| ECOA Deficiency Found | escalationRequired = true | ECOA issue flagged; escalate for remediation |

---

##### Task 4.2: HMDA Data Validation (`t26`)

**Type:** action
**Description:** Loan Officer validates that all required Home Mortgage Disclosure Act data fields are accurately recorded in the loan file.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("ECOA Compliance Check")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "HMDA Validated" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| HMDA Data Valid | caseStatus = "HMDA Validated" | HMDA data confirmed accurate; proceed |
| HMDA Data Issue | communicationRequested = true | Flag HMDA data issue for correction |

---

##### Task 4.3: Document Completeness Review (`t27`)

**Type:** agent
**Description:** AI agent scans the loan file to verify all required documents are present, legible, and properly executed prior to QA officer review.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("HMDA Data Validation")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| conditionsToApproval | string | =vars.conditionsToApproval |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.completenessResult | -> eligibilityResult |

---

##### Task 4.4: Data Integrity Validation (`t28`)

**Type:** process
**Description:** Automated process cross-validates all data fields in the loan file against source system records to confirm data integrity.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("HMDA Data Validation")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| loanAmount | float | =vars.loanAmount |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Data Validated" |

---

##### Task 4.5: Fair Lending Analysis (`t29`)

**Type:** agent
**Description:** AI agent performs statistical fair lending analysis using Databricks to confirm the credit decision is consistent with comparable borrower profiles and free from disparate impact.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Document Completeness Review", "Data Integrity Validation")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| creditScore | integer | =vars.creditScore |
| loanAmount | float | =vars.loanAmount |
| underwriterDecision | string | =vars.underwriterDecision |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.fairLendingOutcome | -> eligibilityResult |

---

##### Task 4.6: QA Officer Review (`t30`)

**Type:** action
**Description:** QA Officer reviews the complete loan file, compliance results, and fair lending analysis to confirm the file meets quality standards before final approval.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Fair Lending Analysis")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| underwriterDecision | String | =vars.underwriterDecision | Yes |
| conditionsToApproval | String | =vars.conditionsToApproval | No |
| ltvRatio | Number | =vars.ltvRatio | Yes |
| dscr | Number | =vars.dscr | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "QA Review In Progress" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Review Complete | caseStatus = "QA Review In Progress" | QA review done; proceed to final QA approval |
| Escalate | escalationRequired = true | Issue found requiring management escalation |

---

##### Task 4.7: Final QA Approval (`t31`)

**Type:** action
**Description:** QA Officer renders the final QA/QC determination. Approval routes the case to Closing; rejection initiates the Rejected exception path.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("QA Officer Review")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| underwriterDecision | String | =vars.underwriterDecision | Yes |
| ltvRatio | Number | =vars.ltvRatio | Yes |
| dscr | Number | =vars.dscr | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "QA Complete" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| QA Approved | qaDecision = "Approved" | File cleared for closing |
| QA Rejected | qaDecision = "Rejected" | File rejected; triggers Rejected exception path |

---

### Stage 5: Closing (`stage-closing`)

**Type:** Stage
**Description:** Manages all pre-closing and closing activities including document preparation, closing disclosure review, borrower signing, title update, wire authorization, fund disbursement, deed recording, and borrower notification.
**Required for Case Completion:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("QA/QC" (`stage-qa-qc`))` | `vars.qaDecision == "Approved"` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 10 | d | 70% | Notify: UserGroup: ClosingTeam | Notify: UserGroup: LoanOperationsManagement |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Prepare Closing Package | process | Yes | Yes | — | — |
| 2 | Closing Disclosure Review | action | Yes | Yes | Closing Officer | 2d |
| 3 | Borrower Signing Acknowledgment | action | Yes | Yes | Borrower | — |
| 4 | Final Title Update | api-workflow | Yes | Yes | — | — |
| 5 | Hazard Insurance Binder Verification | action | Yes | Yes | Closing Officer | — |
| 6 | Wire Transfer Authorization | action | Yes | Yes | Closing Officer | 1d |
| 7 | Fund Disbursement | api-workflow | Yes | Yes | — | — |
| 8 | Record Deed of Trust | api-workflow | Yes | Yes | — | — |
| 9 | Notify Borrower of Funding | api-workflow | Yes | Yes | — | — |

---

##### Task 5.1: Prepare Closing Package (`t32`)

**Type:** process
**Description:** Automated process assembles the complete closing package including the note, deed of trust, closing disclosure, and all required compliance forms.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| loanAmount | float | =vars.loanAmount |
| borrowerName | string | =vars.borrowerName |
| borrowerEntity | string | =vars.borrowerEntity |
| propertyAddress | string | =vars.propertyAddress |
| conditionsToApproval | string | =vars.conditionsToApproval |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Closing Package Ready" |

---

##### Task 5.2: Closing Disclosure Review (`t33`)

**Type:** action
**Description:** Closing Officer reviews the Closing Disclosure for accuracy, confirms all fees and loan terms, and approves it for delivery to the borrower.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Prepare Closing Package")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |
| borrowerName | String | =vars.borrowerName | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Closing Disclosure Reviewed" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Closing Disclosure Approved | caseStatus = "Closing Disclosure Reviewed" | CD reviewed and approved; route to borrower signing |
| Closing Disclosure Issue | communicationRequested = true | Issue found; flag for correction and borrower communication |

---

##### Task 5.3: Borrower Signing Acknowledgment (`t34`)

**Type:** action
**Description:** Borrower reviews and acknowledges the closing disclosure and loan terms via the borrower portal. Confirms readiness to proceed to closing.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Closing Disclosure Review")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| borrowerName | String | =vars.borrowerName | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Borrower Acknowledged" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Acknowledge and Proceed | caseStatus = "Borrower Acknowledged" | Borrower acknowledges; proceed to final title and insurance verification |
| Request Changes | communicationRequested = true | Borrower has questions or requests changes |

---

##### Task 5.4: Final Title Update (`t35`)

**Type:** api-workflow
**Description:** Calls the county records API to confirm title is clear and perform the final title update prior to funding.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Borrower Signing Acknowledgment")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| propertyAddress | string | =vars.propertyAddress |
| titleSearchResult | string | =vars.titleSearchResult |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.titleStatus | -> titleSearchResult |

---

##### Task 5.5: Hazard Insurance Binder Verification (`t36`)

**Type:** action
**Description:** Closing Officer verifies the hazard insurance binder is in place, names Accrual Capital as mortgagee, and meets policy requirements.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Borrower Signing Acknowledgment")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| borrowerName | String | =vars.borrowerName | Yes |
| propertyAddress | String | =vars.propertyAddress | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Insurance Binder Verified" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Insurance Binder Verified | caseStatus = "Insurance Binder Verified" | Insurance confirmed; proceed to wire authorization |
| Insurance Binder Missing | communicationRequested = true | Binder not in place; flag for borrower follow-up |

---

##### Task 5.6: Wire Transfer Authorization (`t37`)

**Type:** action
**Description:** Closing Officer authorizes the wire transfer for loan funding, confirming the disbursement amount and destination wire instructions.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Final Title Update", "Hazard Insurance Binder Verification")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanAmount | Number | =vars.loanAmount | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| borrowerEntity | String | =vars.borrowerEntity | Yes |
| loanApplicationId | String | =vars.loanApplicationId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | disbursementAmount = =vars.loanAmount |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Authorize Wire | disbursementAmount = =vars.loanAmount | Wire authorized; initiate disbursement |
| Hold Wire | escalationRequired = true | Wire hold; escalate for review |

---

##### Task 5.7: Fund Disbursement (`t38`)

**Type:** api-workflow
**Description:** Executes the wire transfer via the bank's wire system API to disburse the loan proceeds to the borrower's designated account.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Wire Transfer Authorization")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| disbursementAmount | float | =vars.disbursementAmount |
| borrowerEntity | string | =vars.borrowerEntity |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.disbursedAmount | -> disbursementAmount |
| — | caseStatus = "Funded" |

---

##### Task 5.8: Record Deed of Trust (`t39`)

**Type:** api-workflow
**Description:** Submits the deed of trust to the county recorder's office via the county recording API and retrieves the recording confirmation number.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Fund Disbursement")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| propertyAddress | string | =vars.propertyAddress |
| borrowerEntity | string | =vars.borrowerEntity |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| response.confirmationNumber | -> recordingConfirmation |

---

##### Task 5.9: Notify Borrower of Funding (`t40`)

**Type:** api-workflow
**Description:** Sends an automated notification to the borrower confirming that the loan has been funded and providing disbursement and recording details.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Record Deed of Trust")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerEmail | string | =vars.borrowerEmail |
| borrowerName | string | =vars.borrowerName |
| disbursementAmount | float | =vars.disbursementAmount |
| recordingConfirmation | string | =vars.recordingConfirmation |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Borrower Notified" |

---

### Stage 6: Resolved (`stage-resolved`)

**Type:** Stage
**Description:** Post-closing activities including audit, loan file archival, investor and servicing reporting, and formal case closure. Marks the successful completion of the loan origination lifecycle.
**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Closing" (`stage-closing`))` | — | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Stage SLA

| SLA | Unit | At-Risk | At-Risk Action | Breach Action |
|-----|------|---------|----------------|---------------|
| 2 | d | 75% | Notify: UserGroup: LoanOperations | Notify: UserGroup: LoanOperationsManagement |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Post-Closing Audit | action | Yes | Yes | Loan Officer | — |
| 2 | Loan File Archival | process | Yes | Yes | — | — |
| 3 | Investor Reporting | api-workflow | Yes | Yes | — | — |
| 4 | Servicing Transfer Notification | api-workflow | Yes | Yes | — | — |
| 5 | Close Case | action | Yes | Yes | Loan Officer | — |

---

##### Task 6.1: Post-Closing Audit (`t41`)

**Type:** action
**Description:** Loan Officer performs a post-closing audit confirming all documents are executed, recorded, and the disbursement is accurate.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| disbursementAmount | Number | =vars.disbursementAmount | Yes |
| recordingConfirmation | String | =vars.recordingConfirmation | Yes |
| caseStatus | String | =vars.caseStatus | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Post-Closing Audit Complete" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Audit Passed | caseStatus = "Post-Closing Audit Complete" | Post-closing audit passed; proceed to archival |
| Audit Issue | escalationRequired = true | Audit issue found; escalate for remediation |

---

##### Task 6.2: Loan File Archival (`t42`)

**Type:** process
**Description:** Archives the complete loan file to the document management system with proper categorization and retention policies.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Post-Closing Audit")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| borrowerEntity | string | =vars.borrowerEntity |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "File Archived" |

---

##### Task 6.3: Investor Reporting (`t43`)

**Type:** api-workflow
**Description:** Submits the loan origination data to the investor reporting system via Snowflake for portfolio and regulatory reporting.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Loan File Archival")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| loanAmount | float | =vars.loanAmount |
| disbursementAmount | float | =vars.disbursementAmount |
| borrowerEntity | string | =vars.borrowerEntity |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Investor Reported" |

---

##### Task 6.4: Servicing Transfer Notification (`t44`)

**Type:** api-workflow
**Description:** Sends the loan servicing transfer notification to the designated loan servicer with all origination data.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Loan File Archival")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| disbursementAmount | float | =vars.disbursementAmount |
| borrowerEntity | string | =vars.borrowerEntity |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Servicing Transferred" |

---

##### Task 6.5: Close Case (`t45`)

**Type:** action
**Description:** Loan Officer formally closes the case, confirming all post-closing activities are complete and recording the final case outcome.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Investor Reporting", "Servicing Transfer Notification")` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| disbursementAmount | Number | =vars.disbursementAmount | Yes |
| caseStatus | String | =vars.caseStatus | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | caseOutcome = "Funded" |
| — | finalDecision = "Approved" |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Close Case | caseOutcome = "Funded" | Case formally closed as funded; all origination complete |

---

### Exception Stage: Customer Comms (`stage-customer-comms`)

**Type:** ExceptionStage
**Description:** Handles outbound communication to the borrower when the Loan Officer flags a communication need during the origination process.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Intake" (`stage-intake`))` | `vars.communicationRequested == true` | No |
| `selected-stage-completed("Loan Setup" (`stage-loan-setup`))` | `vars.communicationRequested == true` | No |
| `selected-stage-completed("Underwriting" (`stage-underwriting`))` | `vars.communicationRequested == true` | No |
| `selected-stage-completed("QA/QC" (`stage-qa-qc`))` | `vars.communicationRequested == true` | No |
| `selected-stage-completed("Closing" (`stage-closing`))` | `vars.communicationRequested == true` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Draft Borrower Communication | action | Yes | No | Loan Officer | — |
| 2 | Send Communication | api-workflow | Yes | No | — | — |

---

##### Task CC.1: Draft Borrower Communication (`t46`)

**Type:** action
**Description:** Loan Officer drafts and approves the communication to be sent to the borrower regarding the identified issue or information request.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| borrowerName | String | =vars.borrowerName | Yes |
| borrowerEmail | String | =vars.borrowerEmail | Yes |
| loanApplicationId | String | =vars.loanApplicationId | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | communicationRequested = false |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve Communication | communicationRequested = false | Communication approved; send to borrower |

---

##### Task CC.2: Send Communication (`t47`)

**Type:** api-workflow
**Description:** Sends the approved borrower communication via the configured notification channel (email or portal message).

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Draft Borrower Communication")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerEmail | string | =vars.borrowerEmail |
| borrowerName | string | =vars.borrowerName |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseStatus = "Communication Sent" |

---

### Exception Stage: Escalation (`stage-escalation`)

**Type:** ExceptionStage
**Description:** Handles management escalation when a loan requires senior review due to credit complexity, SLA risk, or compliance flags.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Underwriting" (`stage-underwriting`))` | `vars.escalationRequired == true` | No |
| `selected-stage-completed("QA/QC" (`stage-qa-qc`))` | `vars.escalationRequired == true` | No |
| `selected-stage-completed("Closing" (`stage-closing`))` | `vars.escalationRequired == true` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Escalation Review | action | Yes | No | Loan Officer | — |

---

##### Task ESC.1: Escalation Review (`t48`)

**Type:** action
**Description:** Senior Loan Officer or manager reviews the escalated loan and provides direction on how to proceed.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| loanAmount | Number | =vars.loanAmount | Yes |
| underwriterDecision | String | =vars.underwriterDecision | No |
| caseStatus | String | =vars.caseStatus | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| — | escalationRequired = false |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Resolved — Continue | escalationRequired = false | Escalation resolved; case continues through normal flow |
| Resolved — Decline | underwriterDecision = "Decline" | Management decision to decline after escalation review |

---

### Exception Stage: Withdrawn (`stage-withdrawn`)

**Type:** ExceptionStage
**Description:** Manages the loan withdrawal process when the borrower opts to withdraw the application at any point during origination.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Intake" (`stage-intake`))` | `vars.caseStatus == "Withdrawn"` | No |
| `selected-stage-completed("Loan Setup" (`stage-loan-setup`))` | `vars.caseStatus == "Withdrawn"` | No |
| `selected-stage-completed("Underwriting" (`stage-underwriting`))` | `vars.caseStatus == "Withdrawn"` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Process Withdrawal Request | action | Yes | Yes | Loan Officer | — |
| 2 | Generate Withdrawal Notice | process | Yes | Yes | — | — |

---

##### Task WD.1: Process Withdrawal Request (`t49`)

**Type:** action
**Description:** Loan Officer confirms the borrower's withdrawal request, captures the reason, and initiates the withdrawal documentation.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| caseStatus | String | =vars.caseStatus | Yes |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> withdrawalReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Confirm Withdrawal | withdrawalReason = =vars.withdrawalReason | Withdrawal confirmed; generate withdrawal notice |

---

##### Task WD.2: Generate Withdrawal Notice (`t50`)

**Type:** process
**Description:** Generates the formal loan withdrawal notice document and updates the case outcome to Withdrawn.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Process Withdrawal Request")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| loanApplicationId | string | =vars.loanApplicationId |
| borrowerName | string | =vars.borrowerName |
| withdrawalReason | string | =vars.withdrawalReason |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseOutcome = "Withdrawn" |
| — | finalDecision = "Withdrawn" |

---

### Exception Stage: Rejected (`stage-rejected`)

**Type:** ExceptionStage
**Description:** Manages the loan rejection process including the ECOA-mandated Adverse Action Notice when a loan is declined by the Underwriter or QA/QC officer.
**Required for Case Completion:** No
**Interrupting:** No

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|-----|-------------|
| `selected-stage-completed("Underwriting" (`stage-underwriting`))` | `vars.underwriterDecision == "Decline"` | No |
| `selected-stage-completed("QA/QC" (`stage-qa-qc`))` | `vars.qaDecision == "Rejected"` | No |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete |
|------|-----|-----------|---------------------|
| `required-tasks-completed` | — | exit-only | Yes |

#### Tasks

| # | Task Name | Type | Required | Run Only Once | Persona | SLA |
|---|-----------|------|----------|---------------|---------|-----|
| 1 | Issue Adverse Action Notice | action | Yes | Yes | Loan Officer | — |
| 2 | Send Adverse Action Notice | api-workflow | Yes | Yes | — | — |

---

##### Task REJ.1: Issue Adverse Action Notice (`t51`)

**Type:** action
**Description:** Loan Officer prepares and approves the ECOA-mandated Adverse Action Notice stating the specific reasons for the credit denial. ECOA requires a licensed officer to sign off on adverse action determinations.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `current-stage-entered` | — |

**HITL Implementation:** JSON Schema

**Input Schema:**

| Field | Type | Binding | Required |
|-------|------|---------|----------|
| loanApplicationId | String | =vars.loanApplicationId | Yes |
| borrowerName | String | =vars.borrowerName | Yes |
| underwriterDecision | String | =vars.underwriterDecision | No |
| qaDecision | String | =vars.qaDecision | No |

**Output Schema:**

| Field | Binding / Value |
|-------|------------------|
| Action | -> rejectionReason |

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve Adverse Action Notice | rejectionReason = =vars.rejectionReason | AAN approved by licensed officer; send to borrower |

---

##### Task REJ.2: Send Adverse Action Notice (`t52`)

**Type:** api-workflow
**Description:** Sends the ECOA-compliant Adverse Action Notice to the borrower via email and updates the case outcome to Rejected.

**Entry Condition:**

| WHEN | IF |
|------|-----|
| `selected-tasks-completed("Issue Adverse Action Notice")` | — |

**Inputs:**

| Field | Type | Binding |
|-------|------|---------|
| borrowerEmail | string | =vars.borrowerEmail |
| borrowerName | string | =vars.borrowerName |
| rejectionReason | string | =vars.rejectionReason |
| loanApplicationId | string | =vars.loanApplicationId |

**Outputs:**

| Field | Binding / Value |
|-------|------------------|
| — | caseOutcome = "Rejected" |
| — | finalDecision = "Declined" |

---

## Section 3: Personas & App Views

### Personas

| Persona | Stage Scope | Permissions | Description |
|---------|-------------|-------------|-------------|
| Loan Officer | Intake, Loan Setup, Underwriting (assign), QA/QC, Closing (oversight), Resolved | View, Act, Reassign | Owns intake through closing coordination; assigns underwriters; handles ECOA and HMDA compliance checks; performs post-closing audit |
| Credit Analyst | Underwriting (loans >$5M only) | View, Act | Reviews credit analysis for loans above $5M; for ≤$5M loans this role is absorbed by the Underwriter |
| Underwriter | Underwriting | View, Act | Performs full underwriting analysis and renders the formal credit decision; absorbs Credit Analyst role for loans ≤$5M |
| Closing Officer | Closing | View, Act, Reassign | Manages all closing activities including closing disclosure, wire authorization, and fund disbursement |
| Borrower | Closing (signing acknowledgment) | View, Act (own tasks only) | External party who acknowledges the closing disclosure and loan terms via the borrower portal |

### Process App Views

| App | View | Persona | Purpose | Key Components |
|-----|------|---------|---------|----------------|
| LoanOrigination App | Case List | Loan Officer | View and manage all active loan origination cases | Case ID, Borrower Name, Loan Amount, Stage, Days Open, SLA Status |
| LoanOrigination App | Case List | Underwriter | View cases assigned for underwriting | Case ID, Borrower Entity, Loan Amount, Risk Score, Assigned Date |
| LoanOrigination App | Case List | Closing Officer | View cases in Closing stage | Case ID, Borrower Name, Closing Date, Wire Status |
| LoanOrigination App | Case Detail | All Personas | Full case detail with stage progress, task list, and loan data | Stage timeline, Task status, Variable values, Document links |
| LoanOrigination App | Dashboard | Loan Officer | Portfolio-level view of origination pipeline | Volume by stage, SLA breach count, Average cycle time, Decision rates |

---

## Section 4: Integrations

### Integration Service Connectors

| Connector | System | Auth Method | Operations Used | Used By Tasks |
|-----------|--------|-------------|-----------------|---------------|
| Experian API | Experian Credit Bureau | API Key | Pull Credit Report | Pull Experian Credit Report (t03) |
| D&B API | Dun & Bradstreet | API Key | Pull Business Credit Report | Pull D&B Business Credit Report (t04) |
| County UCC Portal | County UCC Filing System | API Key | Search UCC Liens | UCC Lien Search (t05), Title Search (t09), Flood Zone Certification (t10), Final Title Update (t35), Record Deed of Trust (t39) |
| Databricks API | Databricks ML Platform | Service Account | Collateral Data Retrieval, Compute Risk Score, Financial Statement Analysis, Cash Flow Analysis, Fair Lending Analysis | t13, t16, t17, t18, t29 |
| Snowflake API | Snowflake Data Warehouse | Service Account | Investor Reporting, Servicing Transfer Notification | t43, t44 |

> All integrations are modeled as `api-workflow` tasks. No UiPath Integration Service connectors are provisioned for these systems. Connection IDs and activity type IDs are `tenant-default` pending connector provisioning.

#### Experian API

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Pull Credit Report | POST | borrowerName: string, borrowerEntity: string, loanApplicationId: string | creditScore: integer, creditReportData: jsonSchema |

#### D&B API

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Pull Business Credit Report | POST | borrowerEntity: string | rating: string, businessData: jsonSchema |

#### Databricks API

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Collateral Assessment | POST | propertyAddress: string, loanApplicationId: string | collateralData: jsonSchema |
| Compute Risk Score | POST | creditScore: integer, dAndBRating: string, financialAnalysisResult: jsonSchema, cashFlowResult: jsonSchema, loanAmount: float | riskScore: float |
| Financial Statement Analysis | POST | loanApplicationId: string, borrowerEntity: string | analysis: jsonSchema |
| Cash Flow Analysis | POST | loanApplicationId: string, financialAnalysisResult: jsonSchema | cashFlow: jsonSchema |

#### Snowflake API

**Operations:**

| Operation | Method | Input Fields | Output Fields |
|-----------|--------|-------------|---------------|
| Investor Reporting | POST | loanApplicationId: string, loanAmount: float, disbursementAmount: float | reportId: string |
| Servicing Transfer | POST | loanApplicationId: string, disbursementAmount: float | transferId: string |
