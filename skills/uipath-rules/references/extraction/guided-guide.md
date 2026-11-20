# Guided Path

The guided path after Framing ([start-guide.md](start-guide.md)): Intake, Understanding, Inputs and structure, Extraction, Finish. Each phase: do the work, show its result ([Results](#results)), and continue. The only stop is the one call for blocking questions in Inputs and structure, and only when there is something to ask. A change to an earlier phase's result returns to that phase.

**After returning to an earlier phase,** redo only what depends on the change. Re-check the rows and results that use the changed input, outcome, section, scope, or date; leave the rest as approved, and do not re-ask a question the user already answered. Show what changed, as a diff against the state before the change (extraction rule 7), then continue forward from the phase you returned to. A change at Finish returns to Extraction for the named sections only; then Finish repeats for those sections: resolve their citations, re-check clause coverage for them, check the changed rows against the whole table for overlaps, gaps, and conflicts (a changed row can collide with an unchanged one), then run `refresh` and `validate` and update the summary.

**Do not re-ask what the request already settled.** When the user's request or an earlier answer gave a fact a phase would confirm (scope, as-of date, decision question, outcomes, inputs), and what the agent finds matches it, the result shows the item as "matches your request" and does not ask about it. Ask only where the finding differs. The result itself still appears. This does not apply to approving rows or the final table, to blocking and never-assume questions, or to anything extraction rule 12 keeps.

**When a command cannot run.** When `uip` is not on the PATH, or `uip rules init`, `refresh`, or `validate` fails with an error that is not a diagnostic about the `.dmn`, stop and show the user the command and its error. Do not hand-write `project.uiproj`, `entry-points.json`, or `bindings_v2.json` to work around it. A diagnostic about the `.dmn` is repaired under uipath-rules critical rule 7.

## Intake

**Do.** Obtain `document.md` with readable, page-marked text using the digitizer outputs or the open-source PDF path below. Locate `dom.json` when available. Confirm the page count and the provisional scope from Framing against the readable pages. A scanned page without text goes back to digitization, or to an OCR tool only when one is installed, or is reported as unreadable.

**Open-source PDF path.** In this order: `pdftotext -layout -f <PAGE> -l <PAGE> <PDF> -` for each page when `pdftotext` is installed; otherwise a Python PDF library already present in the environment (for example `pypdf` or `PyMuPDF`); otherwise, when the host's file reader returns the document's text, use that text as it is and cite from it, taking page numbers from its page boundaries; otherwise report the pages as unreadable. Only a tool writes `document.md`: never type the document's text into a file yourself, because a retyped copy can differ from the source and a quote must be verbatim. With a tool, write `document.md` (and each supporting document's text the same way) into `<TEMP_DIR>`, with a `<!-- page: N -->` marker before each page's text. Delete `<TEMP_DIR>` after Finish; if a later return to an earlier phase finds it gone, extract the pages again. Never install a tool without asking. Do not proceed to interpretation while a scoped page is unreadable. Spot-check each scoped page that holds a table (rate tables, code lists, limits): rows and columns must survive as separable text, because garbled table text yields wrong thresholds. A page whose tables do not survive is reported as unreadable.

**Document facts.** Record the base document's title, version, effective date, and issuer for the decision's `description`. Record the effective date as the document states it; when it states none, write `not stated` and do not ask. Do not ask whether other documents exist. When the base document depends on one that was not supplied (an amendment, a schedule, a delegation of authority) and a rule needs it, that is a blocking question (question triage).

**As-of date.** With one document the as-of date is today: show `As-of date: today (base document only)` for the user to correct. When the request names a past or future date, or the policy's own effective date is in the future, which date the rule should reflect is a blocking question.

**More than one document.** When the request gives an amendment or any supporting document, read [multi-document-guide.md](multi-document-guide.md) now; it replaces the two paragraphs above and adds steps to Understanding, Extraction, and Finish.

**Ask.** Nothing here. Show the Intake result and continue. Without `dom.json`, the result says that citations carry page numbers and no boxes; that is a statement, not a question. Items that need the user join the blocking questions asked after Inputs and structure (extraction rule 1): the as-of date when the rule above makes it a question, the page range of a long document the request did not scope, and a scoped page that is unreadable.

**Write.** `document.md` in `<TEMP_DIR>` on the open-source PDF path; use existing digitizer output unchanged when available, and a page-marked `.md` the user supplied where it is, read-only. Hold the document facts for Inputs and structure, which writes them into the decision's `description`.

**Done when.** The scoped pages have readable text and tables, the document facts are recorded, and the scope and as-of date are fixed or queued as blocking questions.

## Understanding

**Do.** Read the scoped pages. Produce a short summary, the decision question in the policy's own decision wording (or the one the request stated), the outcomes it defines and their type (categorical, score, boolean), its definitions (term -> meaning), and the sections that contain rules, each with its page range. Take outcomes from the policy's own disposition wording (for example "routed to manual review" gives `ManualReview`); never carry over an example outcome from these guides. Note cross-references between sections, and list every override clause ("except", "unless", "notwithstanding", "subject to section N") with the section it overrides; Extraction orders those rows ahead of the rows they override.

**Outcomes.** Always include an outcome for insufficient information (extraction rule 10). When the policy defines ordered outcomes (a severity scale, tiers) or says the most severe finding decides, record the order and the precedence rule, and include "Not applicable" when the policy defines it.

**Classify each section as normative or informative.** Normative text states requirements, thresholds, and dispositions ("must", "shall", numeric limits). Informative text is guidance, examples, rationale, and annexes. Extract normative sections; extract informative ones only when the user asks, and say so when they restate a normative rule (they produce near-duplicate rows).

**Find clauses with the same intent.** Within the sections to extract, and across the base and supporting documents, list pairs or groups of normative clauses that state the same requirement, such as the same limit or the same eligibility test worded twice. Settle them with the question triage below: they are a blocking question, never merged silently. Informative text that restates a rule stays out of this list (see above).

**Estimate size.** Count the rows the confirmed sections would produce. When the estimate is above about 100 rows, or one decision would span several services, codes, or entities, propose scoping to one of them before extraction. A table nobody can review is not a deliverable.

**Triage the questions.** Sort every unclear term, conflicting clause, vague threshold, and reference to a document not provided with the question triage below. Only blocking questions go to the user.

**Ask.** Nothing here. Show the Understanding result and continue. Queue for the one blocking-question call (extraction rule 1): each blocking and never-assume question from the triage below, each Conflict in the reconciliation ledger, and, only when the policy does not state them, what it decides or which outcomes it has. Do not ask the user to confirm the decision question, the outcomes, the ledger, or the section list when the documents state them; the Finish review shows them for correction. Skipped sections are never extracted.

**Write.** Nothing.

**Done when.** The decision question, outcomes, and section list are fixed, or queued as blocking questions.

### Question triage

| Class | Examples | Action |
|---|---|---|
| **Blocking: ask** | A threshold the policy leaves vague ("recent", "significant") that changes the outcome; conflicting clauses; who counts as eligible; what happens when a criterion is not met (deny or refer); which document wins on a conflict the precedence order does not settle; the as-of date and whether an amendment is retroactive; whether a tolerance is one-sided or two-sided and whether it applies to price, quantity, or both | Ask (extraction rule 8). |
| **Same intent in several clauses** | Section 2 and section 5 both cap laptops at one amount; an amendment and the FAQ both require a manager's approval | Ask once per group, with `Treat as one rule (Recommended)` as option 1. Show the clauses side by side with page and quote. On "same", the group becomes one converged row or condition. On "different", keep separate rows and note the difference in each annotation. When the clauses carry a threshold or limit and the question is unanswered, keep separate rows and write a `uipdm:qualityWarning`. |
| **Assume and warn** | Inclusive vs exclusive when the wording is clear ("at least", "more than"); calendar vs business days when the text says "days"; currency and units; rounding | Apply the common reading, write a `uipdm:qualityWarning` stating it, and list it in the result. Do not ask. |
| **Never assume** | Age limits, exclusions, clinical or safety thresholds, diagnosis, procedure, or account code lists, approval authority limits, segregation of duties, any term with a legal or regulatory effect | Ask. If unanswered, extract no row for it, write a `uipdm:qualityWarning`, and let the default row refer to a person. |
| **Customer-defined** | A threshold the policy says the organization sets (by segment, entity, or country) | Make it a `system` input named for the parameter; never invent a value (see Inputs and structure). |
| **Answered by a supporting document** | A term defined in a glossary or FAQ; a code list or rate in reference data; a threshold stated in an amendment | Do not ask. Use the answer and cite it in the annotation. |
| **Skip** | Definitions without a decision effect, filing and contact procedures, response-time targets, KPIs, rationale, purely informational supporting documents (training decks) | Do not extract; do not ask. Record an unused document as read, not used. |

A rule that comes from a user answer or a call, not from the document, has no quote to cite. Record it with a `uipdm:qualityWarning` that says it is user-stated and names the answer (citation guide).

## Inputs and structure

**Do.** Propose every input (name, type, source `document` or `system`, allowed values the policy names), the outputs, and the hit policy. When the policy has distinct steps whose results feed later steps, and the structure allowed in one file (extraction rule 6) includes several chained decisions, propose them instead of one flat table, each with its own hit policy, inputs, and outputs, and say which decisions feed it. Use the designer's types: `string`, `number`, `boolean`, `Any`, `date`, `time`, `date and time`, `days and time duration`, `years and months duration`.

**Input source.** `document`: the value is read from the case evidence (the claim or application the policy decides). `system`: the value is read from a system of record, such as a database, CRM, or application screen, for example a customer-defined threshold, an aggregate over history, or a long code list.

**Express criteria.**
- A test that compares two inputs, or needs a function (`contains`, `string length`), is a boolean column: the `inputExpression` holds the FEEL expression and the entries are `true` or `-`.
- Guard every function that errors on null or empty text (`string length`, `substring`) with `if <FIELD> = null then false else if <FIELD> = "" then false else ...`; a missing input must not raise a FEEL error. Use `if ... then ... else`, not `or` or `and`: they do not skip a failing operand, so `x = null or string length(x) > 0` still errors on null.
- Avoid `replace()`; it errored in this engine even on non-empty text, so whitespace-only text cannot be detected. Record that as a `uipdm:qualityWarning`.
- For a policy that approves when ALL criteria hold, write one approving row first and a default row last (hit policy FIRST). A row per failing criterion placed first would fall through to the approving outcome on a null input.

**Input kinds.**
- **Judgment criteria** ("medically necessary", "reasonable", "material"): do not invent a threshold. Declare a boolean or categorical `document` input whose `sourceMapping` states the criterion in the policy's words; a person or an extraction step assesses it. Say in the result that these inputs are assessed, not read.
- **Customer-defined parameters** (a threshold the policy says the organization sets): a `system` input named for the parameter.
- **Aggregates and windows** ("more than N transactions in 30 days", year-to-date totals): a `system` input computed before the rule runs; a row sees one case.
- **Lists** (diagnoses, invoice lines): an input typed as a list, tested with FEEL `some`/`every`. Decide per rule whether it applies to the header or to each line, and say which.
- **Presence vs value:** "X is documented" and "X equals Y" are separate tests; use one input for each when the policy asks for both.
- **Illustrative lists:** "including", "such as", and "not all inclusive" mark a list as illustrative. Never turn it into a closed allow-list; only a list the policy states as exhaustive becomes one.

**Checklist policies.** When the policy is a list of criteria each checked on its own, and several decisions are allowed (extraction rule 6), write one decision per criterion with outcomes `Met`, `NotMet`, `NotApplicable`, and `CantTell`, and a final decision that aggregates them. A conditional requirement ("applies when telehealth") is a guard that returns `NotApplicable`. A single flat FIRST table hides which check failed.

**Ordered outcomes.** When the policy takes the most severe finding as the result, score each finding on an ordered numeric scale whose steps are far enough apart that the band equals the most severe finding, and take the maximum with a COLLECT hit policy and a max aggregator when `validate` and a sampled run accept it. Otherwise, when several decisions are allowed (extraction rule 6), use a decision per finding feeding a final decision that takes the worst; with one table only, order the rows most severe first under a FIRST hit policy. Confirm the choice with a sampled run in Finish; when that step is skipped, record the choice as unconfirmed in the summary.

**Reason output.** Add a `reason` output to any decision that denies, rejects, refers, or raises an exception. Use one reason per distinct cause the policy names, taken from its wording; do not collapse several causes into one code. Add a `severity` output (blocking or non-blocking) when the policy distinguishes them.

**Ask.** This is the one call for blocking questions (extraction rule 1). In one AskUserQuestion, ask every queued blocking and never-assume question, at most four per call (extraction rule 8), with the Intake, Understanding, and Inputs and structure results in its intro. The answers are context for every later phase: apply them to the inputs, the rows, and the summary, and do not ask them again. With nothing queued, do not stop. With more than 8 inputs, group them by section in the result and show in full only those where you made a judgment (judgment criteria, `system` inputs, an assumed type or meaning, a name that departs from the policy's wording); list the rest by name and type, one line per group. The outputs are always shown in full. Apply "Do not re-ask what the request already settled" to supplied input names, types, and outcomes.
<!--skill-flavor:scaffold:start-->
**Write.** Find or create the project as uipath-rules Quick Start step 1 says: an existing project that still holds the placeholder is used, and one with rules of its own needs the user's choice, which joins the call for blocking questions above. The project folder is the one that holds `project.uiproj` and is `<PROJECT_DIR>` below. Then write the `.dmn` skeleton: DMN 1.5 namespaces, declared inputs with `uipdm:inputVariable`, outputs, an empty table per decision. Keep the scaffolded `.dmn` file name and the decision `id`; set the decision's `name` and `label`, and put the base document's title, version, and effective date, and the as-of date, in the decision's `description` (with more documents, the multi-document guide adds each one and its status): it is the record a later reviewer reads. Do not validate the skeleton on its own; the first section's check covers it.
<!--skill-flavor:scaffold:end-->

**Done when.** The skeleton is written, and the blocking questions are answered or recorded as `uipdm:qualityWarning`.

## Extraction, section by section

Work through the confirmed sections in document order. Write the first section alone, then all the remaining sections together; nobody reviews between sections on this path, so there is no reason to stop or validate after each one.

**Do.** Add rows that use only declared inputs (extraction rule 4). Each row gets an annotation name and one or more citations: page plus a verbatim quote from `document.md`. Record each citation in the working `<TEMP_DIR>/cites.json`, one entry per place a row was read: `{ "id": "<ANNOTATION>-1", "page": <N>, "quote": "<4 to 12 words copied from the clause>" }`. A threshold alone appears many times; include its neighbouring words. A row built from several clauses gets one entry per clause. With several decisions, put each row in the decision it belongs to, and name the decision in the section heading and the diff line. Read each clause's modal verb before writing the row (extraction rule 9). Order a row for an override clause ahead of the rows it overrides, then diff against the table before this section (extraction rule 7). When the table grows past what the user can review in one pass (about 30 rows in a section), split the section.

**Same intent.** Before writing a row, check whether an earlier row or a clause in the confirmed list already states the same intent. If the Understanding phase did not flag the pair, ask the user to confirm before converging, using the same blocking question. A converged row cites every source clause, with one `cites.json` entry per clause, and the diff line says the row was merged from clauses X and Y. If the user says the clauses differ, write separate rows.

<!--skill-flavor:section-rows:start-->
**Show.** After each batch of sections, show each section's rows and the diff.
<!--skill-flavor:section-rows:end-->

**Ask.** Continue to the next section without stopping. Stop only for a blocking or never-assume question that the section raises and the earlier call did not cover: ask it once, apply the answer, and show the table again. A never-assume item is asked, not assumed (question triage).

**Write.** The rows in the `.dmn` and each new citation in `cites.json`. Explain a row only in its annotation column, never in an XML comment (extraction rule 6). Write a range in one cell as an interval, never as a comma list (uipath-rules critical rule 10). Do not write `uipdm:sourceRefs` yet; Finish writes them once the boxes are resolved. A clause that states the outcome for the whole policy (a disposition or fallback clause) is cited on the default row it decides, or on the approving row when there is no default row. Run `refresh` and `validate` as one command (uipath-rules Quick Start, step 4) once here: after the skeleton and the first section are written, so that a mistake in the skeleton or the row pattern is caught before it repeats. The remaining sections are checked in Finish (step 3), together with the source references. The whole run validates twice; do not run it after the skeleton alone or after each section. A diagnostic is fixed and checked again.

**Done when.** The section's blocking questions are answered, and the diff shows no change to earlier rows or only changes shown to the user.

**Rules with no quote.** A rule that comes from a user's answer or a call, not from the document, has no clause to quote. Do not invent a quote and do not add a `cites.json` entry. Write a `uipdm:qualityWarning` on the row (`conditionId` or `field` set when known) with text starting `User-stated, not in document:` followed by the rule and who stated it. Ask the user to get it confirmed in writing, and list it in the Finish summary.

## Finish

1. **Resolve citations.** With no `dom.json`, skip `resolve-refs.mjs` and write each row's cited pages as page-only `uipdm:sourceRef` elements from `cites.json` ([uipdm guide](../uipdm-guide.md)). Otherwise follow [citation-guide.md](citation-guide.md): run `node "<SKILL_DIR>/scripts/extraction/resolve-refs.mjs" --dom <DOM_JSON> --cites <TEMP_DIR>/cites.json`. Write each resolved box as a `uipdm:sourceRef` (this is the only phase that writes `sourceRefs`); each unresolved or ambiguous citation becomes a `uipdm:qualityWarning`, or a longer quote when the quote was only too short.
2. **Check the table.** Do this check yourself, in this conversation; do not start another agent or a separate review for it, and do not wait on one. Look for overlapping rows (two rows can fire for the same input under a UNIQUE hit policy), gaps (an input combination no row covers), duplicate rows, and conflicting rows (same inputs, different outcome). Show each finding. Check each input for a missing value: a case with that input missing must reach the insufficient-information outcome, never an approving row. Then check clause coverage: list each scoped normative clause that no row cites, and mark it as not a rule, deliberately skipped, or missed. A missed clause returns to Extraction for its section. With supporting documents, also run the Finish checks in the multi-document guide.
3. **Refresh and validate** as in the uipath-rules Quick Start (step 4); fix every `Data.Diagnostics` entry.
4. **Check the uipdm elements.** Run `node "<SKILL_DIR>/scripts/check-uipdm.mjs" <DMN_FILE>` ([uipdm guide](../uipdm-guide.md)); `validate` does not read them. Fix every element it reports.
<!--skill-flavor:verify:start-->
5. **Debug, only when asked.** `uip rules debug` uploads the solution to the user's tenant on every run.
   - Run it only when the request asked for sampled runs, or when the user asks for them after the Finish result; do not ask whether to run. Otherwise skip the step, and also when `debug` fails with an authentication error; the summary then says the rule was not run and why.
   - Sample instead of covering every combination: one input set for the first-listed row, one for the default row, and for each threshold one just inside and one just outside. `--inputs` takes one JSON object, so each set is one run.
   - Run the all-criteria-pass set first, then a set with an optional input omitted: FEEL errors on null inputs surface in those two runs, before the budget is spent.
   - Save each set as `<TEMP_DIR>/inputs-<N>.json` and run `uip rules debug <PROJECT_DIR> --inputs @<TEMP_DIR>/inputs-<N>.json --output json`. Read `Data.result.decisions[].outputs` for evaluation errors, and check that the omitted-input set returns the insufficient-information outcome.
   - The runs show that the rule evaluates and that a missing input does not raise a FEEL error; they do not judge correctness (extraction rule 11). Stop after 3 fix rounds on one failure (uipath-rules critical rule 7).
<!--skill-flavor:verify:end-->

**Result.** After steps 1 to 4, show the Finish result and end; do not ask a question. This is the first time the user sees the whole draft; what the result holds is in the next paragraph. Close with one line that says what the user can ask for next: the sampled runs, or a change to named rows or inputs. A change returns to Extraction for the named sections, or to Inputs and structure for a named input, and Finish repeats for what changed. Renaming an input is one edit across the file; it does not need the rows rewritten.

<!--skill-flavor:finish-result:start-->
**What the result holds.** The decision question, the outcomes, the inputs and outputs (the Inputs and structure layout), the full table by section, every assumption recorded as `qualityWarning`, the findings of the table check, and the limits below. The conversation is where the user reads the rule.
<!--skill-flavor:finish-result:end-->

**State the limits.** The Finish result lists: the review level chosen, that the rule has not been run or evaluated against cases (the evals step is next), documents applied and their as-of date, amendments recorded but not yet effective, supporting-document citations that carry no box, assumptions recorded as `qualityWarning`, and clauses left uncovered. The result is the reviewer's record; write no separate notes file. After sampled runs, say what they returned.

**Done when.** `validate` passes, the uipdm check passes, and the Finish result is shown.

## Results

Show each phase's result in the conversation, short, starting with the phase name in bold (never a number). Tables are Markdown. Names and values come from the request and the policy.

| Phase | The result shows |
|---|---|
| Intake | Readable source and pages; position data (`dom.json available`, or `none; citations carry page numbers and no boxes`); scope; as-of date; the document's title, version, effective date, and issuer; anything queued for the user |
| Understanding | A short summary; the decision question; the outcomes and where each comes from; definitions with their page; override clauses; a table of sections (pages, normative or informative, estimated rows, extract or not); **Needs your input** (the blocking questions, queued); **Assumed, not asked** (each recorded as `qualityWarning`) |
| Inputs and structure | Hit policy; a table of inputs (name, type, source, allowed values); a table of outputs (name, type, values) |
| Extraction | As Extraction, Show says: per section, its rows as a table with the annotation and the citation (`p.1 "less than six months of service"`), then one line saying whether earlier rows changed. A row with many citations shows their count |
| Finish | What Finish, What the result holds says, then the limits. Last line: `Next: ask me to run the sampled checks, or name rows or inputs to change.` |
