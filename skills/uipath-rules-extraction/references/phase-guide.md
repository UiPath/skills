# Phase Guide

Each phase: do the work, show the result in the layout from [checkpoint-guide.md](checkpoint-guide.md), ask, wait (critical rule 1). A change to an earlier phase's result returns to that phase.

**After returning to an earlier phase,** redo only what depends on the change. Re-check the rows and results that use the changed input, outcome, section, scope, or date; leave the rest as approved, and do not re-ask a question the user already answered. Show what changed, as a diff against the state before the change (critical rule 8), then continue forward from the phase you returned to. A change at Finish returns to Extraction for the named sections only; then Finish repeats for those sections: resolve their citations, re-check clause coverage for them, check the changed rows against the whole table for overlaps, gaps, and conflicts (a changed row can collide with an unchanged one), then run `refresh` and `validate` and update the summary.

**Do not re-ask what the request already settled.** When the user's request or an earlier answer gave a fact a phase would confirm (scope, as-of date, decision question, outcomes, inputs), and what the agent finds matches it, the checkpoint shows the item as "matches your request" and does not ask about it. Ask only where the finding differs. The checkpoint itself still appears and shows its result. This does not apply to approving rows or the final table, to blocking and never-assume questions, or to anything critical rule 17 keeps.

**When a command cannot run.** When `uip` is not on the PATH, or `uip rules init`, `refresh`, or `validate` fails with an error that is not a diagnostic about the `.dmn`, stop and show the user the command and its error. Do not hand-write `project.uiproj`, `entry-points.json`, or `bindings_v2.json` to work around it. A diagnostic about the `.dmn` is repaired under critical rule 12.

## Phase 1: Framing

**Do.** Frame the decision question (it names what is decided and what it is decided on) and the user's requested scope from the request alone. Ask only for the decision question when the request leaves it open; never ask about scope here. Note a page range or sections only when the request names them, and Intake confirms them. The as-of date and other governing documents are asked in Intake. When the request gives no decision question, ask for it in the Framing AskUserQuestion with generic options such as `Approve / Reject / Refer a request` and `Classify or route a case`; the user types their own wording in Other. Do not infer it from the file name or the document, and do not ask it as prose. Treat any requested outcomes or page range as provisional until the policy is readable; do not pre-scan or interpret the document yet. Note any amendments or supporting documents the request mentions, and the as-of date if one is implied (a historical case, a future effective date).
**Ask.** Always call AskUserQuestion here; never write the Framing questions as a prose message. Ask the decision question when the request gave none; ask nothing else about the framing. Do not ask about other documents here: Intake asks (Build the document register). In the same AskUserQuestion, ask the review level for the extraction phase (critical rule 1): `Ask me only when unclear (Recommended)` (show each section's rows, stop only when the section has a blocking question) | `Every section` (stop and approve each section). Say that blocking and never-assume questions are asked at every level. A typed (Other) answer maps to the closest listed level, which you confirm in one sentence in your next message; a request for more review than `Every section` gives is `Every section`.
<!--skill-flavor:one-shot-offer:start-->
**Typed answer and one-shot.** A typed answer that names amendments, supporting documents, several documents, or a page range never selects `Quick draft (IXP)`: use the guided flow and say why in one sentence.
**One-shot level.** Offer `Quick draft (IXP)` as a third review level only when all of these hold: the request names exactly one document, no amendments or supporting documents, and no page range or sections (the pipeline reads the whole document); `uip` and `node` are on the PATH; `uip login status --output json` reports `Data.Status` `Logged in`. Otherwise do not list it, and do not mention it. When offering it, describe it in one short sentence: IXP drafts the whole rule from the document in one run, for one document. Do not mention timing, billing, the upload, or amendments in the level description. When the user picks one-shot, follow [one-shot-guide.md](one-shot-guide.md) instead of phases 2-5.
<!--skill-flavor:one-shot-offer:end-->
**Write.** Nothing yet; keep the framing in the conversation.
**Done when.** The decision question is clear enough to obtain the source and check the scope.

## Phase 2: Intake

**Do.** Obtain `document.md` with readable, page-marked text using the digitizer outputs or the open-source PDF path below. Locate `dom.json` when available. Confirm the page count and the provisional scope from phase 1 against the readable pages. A scanned page without text goes back to digitization, or to an OCR tool only when one is installed, or is reported as unreadable.
**Open-source PDF path.** In this order: `pdftotext -layout -f <PAGE> -l <PAGE> <PDF> -` for each page when `pdftotext` is installed; otherwise a Python PDF library already present in the environment (for example `pypdf` or `PyMuPDF`); otherwise report the pages as unreadable. Write `document.md` (and each supporting document's text the same way) into `<TEMP_DIR>`, with a `<!-- page: N -->` marker before each page's text. Delete `<TEMP_DIR>` after Finish; if a later return to an earlier phase finds it gone, extract the pages again. Never install a tool without asking. Do not proceed to interpretation while a scoped page is unreadable. Spot-check each scoped page that holds a table (rate tables, code lists, limits): rows and columns must survive as separable text, because garbled table text yields wrong thresholds. A page whose tables do not survive is reported as unreadable.
**Build the document register.** For the base document and every supporting document, capture title, version, effective date, issuer and its authority (law, regulator guidance, organization policy, internal guidance), what it supersedes or amends, and jurisdiction or line of business when stated. Ask whether other documents govern the same decision. Classify each by role:

| Role | Used for |
|---|---|
| Base policy | Source of rows (one per run) |
| Amendment or addendum | Replaces, adds, or deletes base clauses from its effective date |
| Higher authority (law, regulation, contract) | Wins over organization policy on conflict |
| Guidance, FAQ, SOP | Definitions and intent only; never overrides policy text |
| Reference data (code list, rate table, fee schedule) | Values for inputs or lookups; not rules |
| Example cases | Listed in the summary for the evals step; not used for extraction |

Digitize each supporting document the same way as the base (critical rule 4); a supporting document without `dom.json` is fine, because its citations carry no box. For an amendment that arrives as a redline or tracked changes, extracted text cannot show what was struck or inserted: ask for the conformed (clean) copy, or ask the user to confirm the in-force wording clause by clause. Documents beyond about 5 supporting ones: ask the user which to scope out (critical rule 2).
**As-of date.** The as-of date decides which amendments apply, so ask it only when it can change the result: a supporting document or amendment carries an effective date, the base policy's own effective date is in the future, or the request mentions a past or future date. Ask which date the rule should reflect: today, a stated future effective date, or a past date for historical cases. Amendments effective after that date are recorded and not applied. With only the base document and no such date in the request, the as-of date is today; do not ask, and show `As-of date: today (base document only)` for the user to correct.
**Ask.** Confirm the readable source and scope; for a long document, confirm the page range to process; confirm the register (roles, effective dates, precedence) and, when the as-of date rule above applies, the as-of date. Skip the scope, page range, or as-of date the request already gave when the readable pages match it. Record the base policy's effective date as the document states it; when it states none, write `not stated` in the register and do not ask.
**Write.** `document.md` in `<TEMP_DIR>` on the open-source PDF path; use existing digitizer output unchanged when available, and a page-marked `.md` the user supplied where it is, read-only. Hold the register for phase 4, which writes the base document's title, version, effective date, and the amendments applied into the decision's `description`.
**Done when.** The scoped pages have readable text and tables, the register is confirmed, and the scope and as-of date are fixed.

## Phase 3: Understanding

**Do.** Read the scoped pages. Produce a short summary, the policy's decision wording, the outcomes it defines and their type (categorical, score, boolean), its definitions (term -> meaning), and the sections that contain rules, each with its page range. Take outcomes from the policy's own disposition wording (for example "routed to manual review" gives `ManualReview`); never carry over the example outcomes in [checkpoint-guide.md](checkpoint-guide.md). Note cross-references between sections, and list every override clause ("except", "unless", "notwithstanding", "subject to section N") with the section it overrides; phase 5 orders those rows ahead of the rows they override.
**Outcomes.** Always include an outcome for insufficient information (critical rule 14). When the policy defines ordered outcomes (a severity scale, tiers) or says the most severe finding decides, record the order and the precedence rule, and include "Not applicable" when the policy defines it.
**Reconcile the documents.** When the register holds more than the base, read each supporting document's scoped pages and build a ledger with one line per topic or clause: the base clause, each supporting clause that touches it, and a verdict.

| Verdict | Meaning | Effect on extraction |
|---|---|---|
| Replaced | An amendment effective on the as-of date supersedes the base clause | Extract the amendment's wording; do not extract the base clause |
| Added | A clause with no base counterpart | Extract it as a new rule |
| Deleted | An amendment removes the base clause | No row; record the deletion in the ledger |
| Clarified | Guidance or a definition narrows a base term | Use it as the term's definition; cite it in the annotation |
| Not yet effective | Effective after the as-of date | Record only; no row |
| Conflict | Two clauses disagree and the precedence order does not settle it | Blocking question |

Apply the precedence order in critical rule 16 to settle conflicts before asking. Reference data is matched to inputs here: values that answer a "which codes" or "what rate" question are taken from it and not asked, and a table that is long or changes often (about 20 values or more, or revised on its own schedule) becomes a `system` input or lookup, not inline entries. Example cases found in supporting documents are listed in the summary for the evals step.
**Classify each section as normative or informative.** Normative text states requirements, thresholds, and dispositions ("must", "shall", numeric limits). Informative text is guidance, examples, rationale, and annexes. Extract normative sections; extract informative ones only when the user asks, and say so when they restate a normative rule (they produce near-duplicate rows).
**Find clauses with the same intent.** Within the sections to extract, and across the base and supporting documents, list pairs or groups of normative clauses that state the same requirement, such as the same limit or the same eligibility test worded twice. Settle them with the question triage below: they are a blocking question, never merged silently. Informative text that restates a rule stays out of this list (see above).
**Estimate size.** Count the rows the confirmed sections would produce. When the estimate is above about 100 rows, or one decision would span several services, codes, or entities, propose scoping to one of them before extraction. A table nobody can review is not a deliverable.
**Triage the questions.** Sort every unclear term, conflicting clause, vague threshold, and reference to a document not provided with the question triage below. Only blocking questions go to the user.
**Ask.** Apply "Do not re-ask what the request already settled" (top of this guide) to the decision question and the outcomes; for outcomes, the policy must also have an insufficient-information outcome. Confirm the reconciliation ledger when there is one; answer the blocking questions or leave them open; confirm, skip, or re-order sections. Skipped sections are never extracted.
**Write.** Nothing.
**Done when.** The decision question, outcomes, and section list to extract are confirmed.

### Question triage

| Class | Examples | Action |
|---|---|---|
| **Blocking: ask** | A threshold the policy leaves vague ("recent", "significant") that changes the outcome; conflicting clauses; who counts as eligible; what happens when a criterion is not met (deny or refer); which document wins on a conflict the precedence order does not settle; the as-of date and whether an amendment is retroactive; whether a tolerance is one-sided or two-sided and whether it applies to price, quantity, or both | Ask (critical rule 9). |
| **Same intent in several clauses** | Section 2 and section 5 both cap laptops at one amount; an amendment and the FAQ both require a manager's approval | Ask once per group, with `Treat as one rule (Recommended)` as option 1. Show the clauses side by side with page and quote. On "same", the group becomes one converged row or condition. On "different", keep separate rows and note the difference in each annotation. When the clauses carry a threshold or limit and the question is unanswered, keep separate rows and write a `uipdm:qualityWarning`. |
| **Assume and warn** | Inclusive vs exclusive when the wording is clear ("at least", "more than"); calendar vs business days when the text says "days"; currency and units; rounding | Apply the common reading, write a `uipdm:qualityWarning` stating it, and list it in the checkpoint. Do not ask. |
| **Never assume** | Age limits, exclusions, clinical or safety thresholds, diagnosis, procedure, or account code lists, approval authority limits, segregation of duties, any term with a legal or regulatory effect | Ask. If unanswered, extract no row for it, write a `uipdm:qualityWarning`, and let the default row refer to a person. |
| **Customer-defined** | A threshold the policy says the organization sets (by segment, entity, or country) | Make it a `system` input named for the parameter; never invent a value (see phase 4). |
| **Answered by a supporting document** | A term defined in a glossary or FAQ; a code list or rate in reference data; a threshold stated in an amendment | Do not ask. Use the answer and cite it in the annotation. |
| **Skip** | Definitions without a decision effect, filing and contact procedures, response-time targets, KPIs, rationale, purely informational supporting documents (training decks) | Do not extract; do not ask. Record an unused document as read, not used. |

A rule that comes from a user answer or a call, not from the document, has no quote to cite. Record it with a `uipdm:qualityWarning` that says it is user-stated and names the answer (citation guide).

## Phase 4: Inputs and structure

**Do.** Propose every input (name, type, source `document` or `system`, allowed values the policy names), the outputs, and the hit policy. When the policy has distinct steps whose results feed later steps, propose several decisions in one file instead of one flat table, each with its own hit policy, inputs, and outputs, and say which decisions feed it. Use the designer's types: `string`, `number`, `boolean`, `Any`, `date`, `time`, `date and time`, `dayTimeDuration`, `yearMonthDuration`.
**Input source.** `document`: the value is read from the case evidence (the claim or application the policy decides). `system`: the value is read from a system of record, such as a database, CRM, or application screen, for example a customer-defined threshold, an aggregate over history, or a long code list.
**Express criteria.**
- A test that compares two inputs, or needs a function (`contains`, `string length`), is a boolean column: the `inputExpression` holds the FEEL expression and the entries are `true` or `-`.
- Guard every function that errors on null or empty text (`string length`, `substring`) with `if <FIELD> = null then false else if <FIELD> = "" then false else ...`; a missing input must not raise a FEEL error. Use `if ... then ... else`, not `or` or `and`: they do not skip a failing operand, so `x = null or string length(x) > 0` still errors on null.
- Avoid `replace()`; it errored in this engine even on non-empty text, so whitespace-only text cannot be detected. Record that as a `uipdm:qualityWarning`.
- For a policy that approves when ALL criteria hold, write one approving row first and a default row last (hit policy FIRST). A row per failing criterion placed first would fall through to the approving outcome on a null input.

**Input kinds.**
- **Judgment criteria** ("medically necessary", "reasonable", "material"): do not invent a threshold. Declare a boolean or categorical `document` input whose `sourceMapping` states the criterion in the policy's words; a person or an extraction step assesses it. Say in the checkpoint that these inputs are assessed, not read.
- **Customer-defined parameters** (a threshold the policy says the organization sets): a `system` input named for the parameter.
- **Aggregates and windows** ("more than N transactions in 30 days", year-to-date totals): a `system` input computed before the rule runs; a row sees one case.
- **Lists** (diagnoses, invoice lines): an input typed as a list, tested with FEEL `some`/`every`. Decide per rule whether it applies to the header or to each line, and say which.
- **Presence vs value:** "X is documented" and "X equals Y" are separate tests; use one input for each when the policy asks for both.
- **Illustrative lists:** "including", "such as", and "not all inclusive" mark a list as illustrative. Never turn it into a closed allow-list; only a list the policy states as exhaustive becomes one.

**Checklist policies.** When the policy is a list of criteria each checked on its own, write one decision per criterion with outcomes `Met`, `NotMet`, `NotApplicable`, and `CantTell`, and a final decision that aggregates them. A conditional requirement ("applies when telehealth") is a guard that returns `NotApplicable`. A single flat FIRST table hides which check failed.

**Ordered outcomes.** When the policy takes the most severe finding as the result, score each finding on an ordered numeric scale whose steps are far enough apart that the band equals the most severe finding, and take the maximum with a COLLECT hit policy and a max aggregator when `validate` and a sampled run accept it. Otherwise use a decision per finding feeding a final decision that takes the worst. Confirm the choice with a sampled run in phase 6; when that step is skipped, record the choice as unconfirmed in the summary.

**Reason output.** Add a `reason` output to any decision that denies, rejects, refers, or raises an exception. Use one reason per distinct cause the policy names, taken from its wording; do not collapse several causes into one code. Add a `severity` output (blocking or non-blocking) when the policy distinguishes them.

**Ask.** Apply "Do not re-ask what the request already settled" to supplied input names, types, and outcomes. With up to 8 inputs, approve or rename inputs and outputs. With more than 8, group the inputs by section and show in full only those where you made a judgment (judgment criteria, `system` inputs, an assumed type or meaning, a name that departs from the policy's wording); list the rest by name and type, one line per group. Options: `Approve all (Recommended)` | `Change some`. The outputs are always shown in full.
<!--skill-flavor:scaffold:start-->
**Write.** Scaffold the project when it is new (`uip rules init <RULE_NAME> --output json`; the project folder is the one that holds `project.uiproj`, inside `<RULE_NAME>Solution/`, and is `<PROJECT_DIR>` below), then write the `.dmn` skeleton: DMN 1.5 namespaces, declared inputs with `uipdm:inputVariable`, outputs, an empty table per decision. Keep the scaffolded `.dmn` file name and the decision `id`; set the decision's `name` and `label`, and put the document title, version, effective date, and amendments applied from phase 2 in the decision's `description`. Then `uip rules refresh <PROJECT_DIR> --output json`.
<!--skill-flavor:scaffold:end-->
**Done when.** `uip rules validate <PROJECT_DIR> --output json` returns `Valid` on the skeleton and the user approved the names. The `DMN_NO_RULES` warning on the empty tables is expected; fix any other diagnostic.

## Phase 5: Extraction, section by section

Repeat for each confirmed section, in document order.

**Do.** Add rows that use only declared inputs (critical rule 5). Each row gets an annotation name and one or more citations: page plus a verbatim quote from `document.md`. Record citations in the working `cites.json` (see [citation-guide.md](citation-guide.md)); a row built from an amendment or other supporting document is cited as the citation guide says. A row whose base clause was Replaced cites the amendment's wording and notes the base clause it replaced. With several decisions, put each row in the decision it belongs to, and name the decision in the section heading and the diff line. Read each clause's modal verb before writing the row (critical rule 13). Order a row for an override clause ahead of the rows it overrides, then diff against the table before this section (critical rule 8). When the table grows past what the user can review in one pass (about 30 rows in a section), split the section.
**Same intent.** Before writing a row, check whether an earlier row or a clause in the confirmed list already states the same intent. If the Understanding phase did not flag the pair, ask the user to confirm before converging, using the same blocking question. A converged row cites every source clause, with one `cites.json` entry per clause, and the diff line says the row was merged from clauses X and Y. If the user says the clauses differ, write separate rows.
**Ask.** Follows the review level from phase 1. `Every section`: approve the section's rows, or answer the blocking questions (critical rule 9); apply the answers, show the table again, repeat until approved. `Ask me only when unclear`: show the rows and the diff, then continue unless the section has a blocking question; ask those questions, apply the answers, and show the table again. At every level a never-assume item is asked, not assumed (question triage).
**Write.** The rows in the `.dmn` and each new citation in `cites.json`. Explain a row only in its annotation column, never in an XML comment (critical rule 7). Do not write `uipdm:sourceRefs` yet; phase 6 writes them once the boxes are resolved. A clause that states the outcome for the whole policy (a disposition or fallback clause) is cited on the default row it decides, or on the approving row when there is no default row.
**Done when.** The section is approved (`Every section`) or its blocking questions are answered, and the diff shows no change to earlier rows or only changes shown to the user.

## Phase 6: Finish

1. **Resolve citations.** Run `node "<SKILL_DIR>/scripts/resolve-refs.mjs" --dom <DOM_JSON> --cites <TEMP_DIR>/cites.json`. Write each resolved box as a `uipdm:sourceRef` (this is the only phase that writes `sourceRefs`); each unresolved or ambiguous citation becomes a `uipdm:qualityWarning`, or a longer quote when the quote was only too short (citation guide).
2. **Check the table.** Look for overlapping rows (two rows can fire for the same input under a UNIQUE hit policy), gaps (an input combination no row covers), duplicate rows, and conflicting rows (same inputs, different outcome). Show each finding. Check each input for a missing value: a case with that input missing must reach the insufficient-information outcome, never an approving row. Then check clause coverage: list each scoped normative clause that no row cites, and mark it as not a rule, deliberately skipped, or missed. A missed clause returns to phase 5 for its section. With supporting documents, also check each ledger line: every Replaced, Added, and Clarified clause maps to a row or definition, no row still carries the wording of a Replaced or Deleted base clause, and every Not yet effective clause is listed. Report each registered document as used or not used.
3. **Refresh and validate.** `uip rules refresh <PROJECT_DIR> --output json`, then `uip rules validate <PROJECT_DIR> --output json`; fix every `Data.Diagnostics` entry.
4. **Check the uipdm elements** with the uipath-rules skill when it is installed and documents a uipdm check (critical rule 10); otherwise skip the check and say so in the summary.
<!--skill-flavor:verify:start-->
5. **Debug.** `uip rules debug` uploads the solution to the user's tenant on every run.
   - Ask once with AskUserQuestion before the first run. Skip the step when the user declines, when the run is headless and the request did not ask for it, or when `debug` fails with an authentication error; the summary then says `debug` was not run and why.
   - Sample instead of covering every combination: one input set for the first-listed row, one for the default row, and for each threshold one just inside and one just outside. `--inputs` takes one JSON object, so each set is one run.
   - Run the all-criteria-pass set first, then a set with an optional input omitted: FEEL errors on null inputs surface in those two runs, before the budget is spent.
   - Save each set as `<TEMP_DIR>/inputs-<N>.json` and run `uip rules debug <PROJECT_DIR> --inputs @<TEMP_DIR>/inputs-<N>.json --output json`. Read `Data.result.decisions[].outputs` for evaluation errors, and check that the omitted-input set returns the insufficient-information outcome.
   - The runs show that the rule evaluates and that a missing input does not raise a FEEL error; they do not judge correctness (critical rule 15). Stop after 3 fix rounds on one failure (critical rule 12).
<!--skill-flavor:verify:end-->

**State the limits.** The final summary lists: the review level chosen, that the rule has not been evaluated against cases (the evals step is next), documents applied and their as-of date, amendments recorded but not yet effective, supporting-document citations that carry no box, assumptions recorded as `qualityWarning`, and clauses left uncovered.
Write the same list to `<PROJECT_DIR>/../review-notes.md` for the reviewer.
**Ask.** Approve the final table, or name rows to change (return to phase 5 for that section).
**Done when.** `validate` passes, the sampled runs evaluate without error (or the summary says why none was made), and the user approved.
