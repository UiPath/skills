# Checkpoint Formats

Keep each checkpoint short. Start each one with its phase name in bold (Framing, Intake, Understanding, Inputs and structure, Extraction, Finish), never a number. Tables are Markdown; every question is one AskUserQuestion with the options listed. The first option of every question is your proposed answer, labelled with `(Recommended)` at the end, with a short description of why; the labels below show where it goes. Names, outcomes, and values below are illustrations; take phase 1 framing from the request and phase 3 outcomes from the policy.

## Phase 1: Framing

```markdown
**Decision question:** Is this employee device reimbursement claim approved?
**Requested scope:** Device reimbursement policy (pages to confirm after intake)
```

**Review level for extraction** (one question): `Ask me only when unclear (Recommended)` | `Every section` | `Quick draft (IXP)` (only when the phase guide offers it; one document, no amendments)

The Framing question asks the decision question when the request gave none (generic options; the user types their own wording in Other) together with the review level, and nothing else.

### One-shot profile

One question set (outcomes, score bands when scored, folder); its answers start the run. The query is stated in the question text, not asked.

```markdown
**Quick draft (IXP)**
**Document:** <FILE_NAME>
**Query:** Is this device reimbursement approved?
```

Outcomes options: `<LABEL>:positive, <LABEL>:negative, <LABEL>:neutral (Recommended)` | a variant. Folder options: `Personal workspace (Recommended)` | a `Standard` folder by path.

## Phase 2: Intake

```markdown
**Readable source:** document.md (temporary copy), pages 1-3 (tables on p.2 readable)
**Position data:** dom.json available
**Proposed scope:** Pages 1-2 (matches your request, or <DIFFERENCE> and asked below)
**As-of date:** <DATE_OR_TODAY> (matches your request, asked below, or `today (base document only)` when there is nothing to apply)

| Document | Role | Version | Effective | Authority | Supersedes |
|---|---|---|---|---|---|
| <BASE_TITLE> | Base policy | <N> | <DATE> | <ISSUER> (<AUTHORITY>) | - |
| <AMENDMENT_TITLE> | Amendment | <N> | <DATE> | <ISSUER> | base section 3 |
| <FAQ_TITLE> | Guidance | - | - | <ISSUER> | - |

**Conformed copy needed:** <AMENDMENT_TITLE> arrived as a redline | none
```

Options: `Confirm source, register, and as-of date (Recommended)` | `Change scope` | `Add or correct a document`.

## Phase 3: Understanding

```markdown
**Summary:** <SUMMARY>
**Decision question:** unchanged from Framing (or, when the policy decides something different: <NEW_QUESTION>, with the question asked below)
**Outcomes:** Approved, Denied, Referred (categorical; from policy wording; Referred also covers insufficient information); matches your request, or <OUTCOME> added by the policy and asked below
**Definitions:** <TERM> = <MEANING> (p.<N>)
**Overrides:** Section 3 overrides section 1 for contractors (p.2)

**Reconciliation** (only with supporting documents)

| Topic | Base | Supporting | Verdict |
|---|---|---|---|
| Laptop limit | p.2 "up to $1,000" | Amendment 1 p.1 "up to $1,200" | Replaced (effective <DATE>) |
| Phone eligibility | p.1 | FAQ p.3 | Clarified |
| Tablet limit | - | Amendment 2 p.1 | Not yet effective |

**Sections with rules**

| # | Section | Pages | Kind | Est. rows | Extract? |
|---|---|---|---|---|---|
| 1 | Eligibility | 1 | Normative | 6 | Yes |
| 2 | Limits | 1-2 | Normative | 9 | Yes |
| 3 | Examples | 2 | Informative | 4 | No (restates section 2) |
| 4 | Appendix: history | 3 | No rules found | 0 | No |


**Needs your input** (blocking only; asked as questions whose first option is the proposed answer, marked `(Recommended)`)
1. "Eligible employee" is not defined in the policy. Proposed: all full-time employees. Which employees count?
2. Page 2 says "recent purchase" with no time limit. What limit applies?
3. Page 1 "up to $1,000" and page 2 "must not exceed $1,000" both cap laptops. Proposed: treat as one rule. Same requirement?

**Assumed, not asked** (recorded as qualityWarning)
- "More than 500" read as exclusive of 500
```

Options: `Confirm profile and sections (Recommended)` | `Change profile or sections`. Each question under **Needs your input** is its own AskUserQuestion question whose options are `<PROPOSED_ANSWER> (Recommended)` | `<ALTERNATIVE>` | `<ALTERNATIVE>`.

## Phase 4: Inputs and structure

```markdown
**Hit policy:** FIRST

| Input | Type | Source | Allowed values | Your request |
|---|---|---|---|---|
| employmentMonths | number | document | - | matches |
| deviceCategory | string | document | Laptop, Phone, Tablet | not given |

| Output | Type | Values |
|---|---|---|
| decision | string | Approved, Denied, Referred |
```

For several decisions, repeat this block per decision, each with its own hit policy, and add a line saying which decisions feed it:

```markdown
**Decision: <DECISION_NAME>** (feeds <DECISION_NAME>, or: final decision)
**Hit policy:** <HIT_POLICY>

| Input | Type | Source | Allowed values | Your request |
|---|---|---|---|---|

| Output | Type | Values |
|---|---|---|
```

Options: `Approve (Recommended)` | `Rename or change`.

### Inputs, more than 8 (phase 4)

```markdown
**Inputs:** 14, in 3 groups. Judgments shown in full; the rest by name and type.

| Input | Type | Source | Why shown |
|---|---|---|---|
| clinicalNeedAssessed | boolean | document, assessed | judgment criterion |
| dosesPerCourseCap | number | system | customer-defined |

**Eligibility:** age (number), residencyConfirmed (boolean), employmentMonths (number)
**History:** priorClaims (number), bankruptcyLast7Years (boolean)
```

Options: `Approve all (Recommended)` | `Change some`.

## Phase 5: Extraction

Show only the section's rows, then the diff line.

```markdown
**Section: Eligibility (p.1)**

| # | employmentMonths | deviceCategory | decision | Annotation | Cited |
|---|---|---|---|---|---|
| 1 | < 6 | - | "Denied" | Under six months | p.1 "less than six months of service" |

**Earlier rows:** unchanged
```

With several decisions, add the decision to the heading (`**Section: Eligibility (p.1), decision: <DECISION_NAME>**`) and show one table per decision the section touches.

A row with many citations shows its count instead of every quote (`p.1 - 13 quotes, see cites.json`); list the quotes under the table on request.

Options: `Approve section (Recommended)` | `Change rows`. Blocking questions are listed under the table and asked as their own questions. Whether a section asks at all follows the review level (phase guide, phase 5).

## Phase 6: Finish

```markdown
**Citations:** 14 resolved, 1 unresolved (row 7), 0 ambiguous
**Overlaps:** rows 3 and 5 both match deviceCost 500 with Laptop
**Gaps:** none
**Duplicates:** none
**Uncovered clauses:** p.2 "Managers may approve exceptions" - not a rule (permission)
**Review level:** Ask me only when unclear
**validate:** passed   **Sampled runs:** 6 of 6 evaluated; the omitted-input set returned Referred, or none was made (<REASON>)
**Documents:** base and 1 amendment applied as of <DATE>; FAQ read, not used; 1 amendment not yet effective
**Limits:** supporting-document citations carry no box; 2 assumptions recorded; 1 user-stated rule awaiting written confirmation
```

Options: `Approve the table (Recommended)` | `Change rows in a section`.
