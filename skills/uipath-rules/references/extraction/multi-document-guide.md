# More Than One Document

Read before Intake when the request gives an amendment or any supporting document. It adds to the guided path ([guided-guide.md](guided-guide.md)); everything else there stays as written. Rows still come from one base document (extraction rule 14); the other documents change what its in-force text is.

## Precedence

An amendment replaces the text it names only when it is effective on the as-of date the user confirmed; higher authority (law, regulation, contract) beats organization policy; guidance, FAQs, and examples never override policy text. A conflict this order does not settle is a blocking question with the later-dated or higher-authority clause proposed first. Ask for the as-of date under the conditions below and never assume it when they hold; never assume whether an amendment is retroactive or the jurisdiction either. When none of those conditions holds, the as-of date is today and the Intake result says so.

## Intake: register the documents

**Build the document register.** For the base document and every supporting document, capture title, version, effective date, issuer and its authority (law, regulator guidance, organization policy, internal guidance), what it supersedes or amends, and jurisdiction or line of business when stated. Do not ask whether other documents exist. When the base document depends on one that was not supplied (an amendment, a schedule, a delegation of authority) and a rule needs it, that is a blocking question (question triage). Classify each by role:

| Role | Used for |
|---|---|
| Base policy | Source of rows (one per run) |
| Amendment or addendum | Replaces, adds, or deletes base clauses from its effective date |
| Higher authority (law, regulation, contract) | Wins over organization policy on conflict |
| Guidance, FAQ, SOP | Definitions and intent only; never overrides policy text |
| Reference data (code list, rate table, fee schedule) | Values for inputs or lookups; not rules |
| Example cases | Listed in the summary for the evals step; not used for extraction |

Digitize each supporting document the same way as the base (extraction rule 3); a supporting document without `dom.json` is fine, because its citations carry no box. For an amendment that arrives as a redline or tracked changes, extracted text cannot show what was struck or inserted: ask for the conformed (clean) copy, or ask the user to confirm the in-force wording clause by clause. Documents beyond about 5 supporting ones: ask the user which to scope out.

**As-of date.** The as-of date decides which amendments apply, so ask it only when it can change the result: a supporting document or amendment carries an effective date, the base policy's own effective date is in the future, or the request mentions a past or future date. Ask which date the rule should reflect: today, a stated future effective date, or a past date for historical cases. Amendments effective after that date are recorded and not applied. With only the base document and no such date in the request, the as-of date is today; do not ask, and show `As-of date: today (base document only)` for the user to correct.

Queue for the one call for blocking questions: the as-of date when the rule above applies, and a conformed copy for a redlined amendment. The Intake result adds the register:

```markdown
| Document | Role | Version | Effective | Authority | Supersedes |
|---|---|---|---|---|---|
| <BASE_TITLE> | Base policy | <N> | <DATE> | <ISSUER> (<AUTHORITY>) | - |
| <AMENDMENT_TITLE> | Amendment | <N> | <DATE> | <ISSUER> | base section 3 |
| <FAQ_TITLE> | Guidance | - | - | <ISSUER> | - |

**Conformed copy needed:** <AMENDMENT_TITLE> arrived as a redline | none
```

## Understanding: reconcile

**Reconcile the documents.** When the register holds more than the base, read each supporting document's scoped pages and build a ledger with one line per topic or clause: the base clause, each supporting clause that touches it, and a verdict.

| Verdict | Meaning | Effect on extraction |
|---|---|---|
| Replaced | An amendment effective on the as-of date supersedes the base clause | Extract the amendment's wording; do not extract the base clause |
| Added | A clause with no base counterpart | Extract it as a new rule |
| Deleted | An amendment removes the base clause | No row; record the deletion in the ledger |
| Clarified | Guidance or a definition narrows a base term | Use it as the term's definition; cite it in the annotation |
| Not yet effective | Effective after the as-of date | Record only; no row |
| Conflict | Two clauses disagree and the precedence order does not settle it | Blocking question |

Apply the precedence order above to settle conflicts before asking. Reference data is matched to inputs here: values that answer a "which codes" or "what rate" question are taken from it and not asked, and a table that is long or changes often (about 20 values or more, or revised on its own schedule) becomes a `system` input or lookup, not inline entries. Example cases found in supporting documents are listed in the summary for the evals step.

Each Conflict the precedence order does not settle is a blocking question. The Understanding result adds the ledger:

```markdown
**Reconciliation** (only with supporting documents)

| Topic | Base | Supporting | Verdict |
|---|---|---|---|
| Laptop limit | p.2 "up to $1,000" | Amendment 1 p.1 "up to $1,200" | Replaced (effective <DATE>) |
| Phone eligibility | p.1 | FAQ p.3 | Clarified |
| Tablet limit | - | Amendment 2 p.1 | Not yet effective |
```

## Inputs and structure: record the documents

In the decision's `description`, after the base document's facts, list every other registered document with its status: applied, not yet effective, or read and not used. It is the record a later reviewer reads.

## Extraction: cite supporting documents

A row whose base clause was Replaced cites the amendment's wording and notes the base clause it replaced.

Only the base document has a `dom.json` and `cites.json` entries. A row built from an amendment, higher-authority source, guidance, or reference data names the source in its annotation as `<DOCUMENT_NAME> p.<N> "<verbatim quote>"`, copied from that document's text. Add no `cites.json` entry and no `uipdm:sourceRef`: `resolve-refs.mjs` reads one `dom.json`, and a page number from another document would resolve to the wrong box. List these citations in the Finish summary as carrying no box. A row that combines a base clause and a supporting clause cites the base clause normally and the supporting one in the annotation.

## Finish: check the ledger

In step 2 (Check the table), also check each ledger line: every Replaced, Added, and Clarified clause maps to a row or definition, no row still carries the wording of a Replaced or Deleted base clause, and every Not yet effective clause is listed. Report each registered document as used or not used, and correct its status in the decision's `description` when it changed. The Finish result adds a line: `**Documents:** base and 1 amendment applied as of <DATE>; FAQ read, not used; 1 amendment not yet effective`.
