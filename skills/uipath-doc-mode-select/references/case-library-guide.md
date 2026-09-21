# Case Library

21 cases · 7 decision categories · 3 per category.

Match on **document shape and failure mechanism**, not on industry. Read the fast-routing table in
[../SKILL.md](../SKILL.md) first, then the nearest case here, then one boundary case only if the decisive
signals conflict. Do not read the whole library for a routing decision.

## Reading a case

Each case carries a positive fit, a negative route, and a boundary. Two labels distinguish how much
weight a case carries:

- **Observed** — this pattern or failure was seen in a real implementation. It is not a controlled
  measurement, and it does not prove the recommended route was the one used.
- **Illustrative** — a constructed example that teaches a real boundary. No field result behind it.

Where a case names a recommended route, that is this library's proposal, not a record of what shipped.
Numbers below are routing thresholds — document counts, page densities, volumes that change the design.
They are not performance results, and none should be quoted as a benchmark. Verify capabilities, limits,
and costs against the target environment before building.

---

## AH Advanced harness

Candidate workloads for the advanced harness. Each still requires the capability check in
[agent-harness-guide.md](agent-harness-guide.md) — none of these proves advanced was necessary.

### AH1 Amendment-aware contract audit

**Placement.** Autonomous agent, advanced harness only for a verified capability need; otherwise standard
with explicit Flow orchestration. Fixed document stages as nodes, exact comparisons in script, a durable
store plus polling for resumability.

**Match.** A base contract plus several amendments. Values depend on cross-section interpretation,
effective dates, and amendment scope. The output is an evidence-backed comparison against business-system
values, with lineage a reviewer can follow. Runs are long enough to need checkpoint and resume.

**Route.** Classify the documents; extract candidate values with evidence; determine which questions each
amendment changes; resolve precedence; perform the comparisons in code; present exceptions. Persist
completed stages so a retry does not redo them or duplicate outputs.

**Negative route — observed.** Sequential long-running processing inside a single serverless invocation
exceeded its execution window. Later runs produced blank downstream results and missing citations:
successful extraction had not established successful persistence or review readiness.

**Boundary.** If this settles into a stable field-only task, use EX3 or a plain Extract strategy. If the
deliverable is only a cited narrative, use SU2. Never release an audited comparison while evidence is
missing or amendment precedence is unresolved.

**Acceptance check.** A later amendment changes one fee and leaves another untouched: return both correct
effective values, their evidence, and the comparison result. Resume an interrupted run without
recomputing completed stages.

### AH2 Long mixed-format payment package review

**Placement.** Advanced harness is a candidate, subject to the capability check. Extract for fields,
script for reconciliation, Human review for the configured approval. Standard plus Flow orchestration
remains valid when it is sufficient.

**Match.** Thousand-page payment applications mixing typed, scanned, and handwritten content, arriving
roughly monthly. Review depends on a master agreement, party-specific contracts, and regularly added
amendments. The output is a set of potentially non-compliant charges plus the supporting contract chain —
not extracted invoice fields.

**Route.** Establish the document manifest and the governing contract hierarchy; extract charges;
reconcile amounts deterministically; apply document reasoning to applicability and exceptions; assemble
reviewable findings. Track coverage by segment and by obligation.

**Negative route — observed constraint.** The candidate policy engine handled one document at a time and
could not cleanly combine the governing agreement with its amendments. Concatenating the files was
proposed, but the resulting precedence ambiguity was never resolved — and a single-pass prompt would not
have fixed it.

**Boundary.** Length alone does not select AH: a long field-only document is EX3. Do not call a package
compliant while required documents, amendment applicability, or unprocessed segments remain open.

**Acceptance check.** Test a charge allowed by the original contract but disallowed by an applicable
amendment, alongside one unaffected charge. Preserve version-specific evidence and exact arithmetic for both.

### AH3 Control testing with exact calculations

**Placement.** Script and Data operations for the exact controls; an autonomous agent only for the
residual judgment. Advanced harness only on a demonstrated need. This case is mainly a boundary against
unnecessary agent use.

**Match.** A couple of hundred controls over evidence files, frequently spreadsheet exports. A control may
need a data transformation, exact arithmetic, and a judgment about whether the evidence satisfies a
policy. Inputs and procedures vary per control.

**Route.** Define the procedure and evidence requirements first. Run spreadsheet manipulation and
reconciliation in deterministic tools. Feed computed results plus evidence to the judgment step. Retain
an audit trail. Fixed controls need no agent at all.

**Negative route — observed failure.** A file-reading tool was used for everything, including
calculations and oversized evidence, with no deterministic tools built. A rerun changed the same
control's pass/fail result, and some evidence had never been evaluated at all.

**Boundary.** Arithmetic is code, not reasoning. A small qualitative file inspection is AF2. An
underspecified control or unread evidence produces "not evaluated", never "pass". Do not manufacture
calibrated confidence from a model's self-rating.

**Acceptance check.** Identical evidence yields identical computed totals across reruns. A missing input
blocks the corresponding conclusion rather than defaulting it. Test easy, medium, and complex procedures
— not only the easiest subset.

---

## AF Analyze files

### AF1 Detect an unfamiliar export layout

**Placement.** Autonomous agent, standard harness, Analyze files tool. Bind the detected structure to
deterministic row processing.

**Match.** Purchase-order exports arrive with unfamiliar, non-English column layouts and no fixed
template. The immediate output is the relevant sheet, the header row, and the column mapping. Repetitive
row processing happens afterwards.

**Route.** One bounded structure inspection. Supply an input representation the tool supports, inspect
once, validate the detected columns against the actual file, then process rows deterministically. If an
individual item later needs multi-source interpretation, that is PA1, separately.

**Negative route — counterexample.** Asking the agent to rediscover the structure and extract every row
multiplies calls and produces inconsistent row handling. An unfamiliar layout alone does not justify a
persistent index.

**Boundary.** Do not infer general spreadsheet support from one implementation — check the active input
path and budget. If deterministic parsing identifies headers reliably, skip the model. If the requirement
is production field extraction with per-field review, use EX2.

**Acceptance check.** Detect a shifted header row and reordered columns, confirm them in code, and
preserve every row without model arithmetic. Unknown or ambiguous headers are flagged, not guessed.

### AF2 Read invoice evidence for an asset review

**Placement.** Autonomous agent, standard harness, Analyze files tool. Add Context only for genuinely
reusable policy knowledge. Bind the analyst review to a Human node.

**Match.** An agent reviews invoice and backup attachments for fixed-asset addition requests, a few
hundred a month. It needs bounded file content as evidence before recommending approval, rejection, or
human review.

**Route.** Read the relevant content from supported, budget-fitting attachments, then apply policy in the
agent's reasoning. Perform amount calculations in code. Keep source identifiers and the analyst approval
step. Do not claim native calibrated field confidence.

**Negative route — counterexample.** Treating the reader as a complete extraction and approval engine
confuses content access with a validated decision. Forcing all policy reasoning and arithmetic into one
opaque tool prompt makes the intermediate evidence impossible to inspect.

**Boundary.** Attachment size is frequently unspecified — check it before choosing this route. Missing or
oversized evidence blocks a recommendation or routes to a document processor. Stable high-volume field
capture is EX1 or EX2; complex adaptive review may be AH3.

**Acceptance check.** Read the asset description and invoice amount; preserve unreadable fields as
unresolved; return a human-review outcome when required evidence is unavailable. The analyst remains the
final approver.

### AF3 Read three fields from a clean letter

**Placement.** Autonomous agent, standard harness, Analyze files tool. No Context and no Memory.

**Match.** Clean single-page letters, low daily volume. Three named fields are needed inside an agent
task. No field-level production SLA and no correction workflow has been requested.

**Route.** One bounded read with a small output contract. Return the requested values, explicitly mark
missing ones, and validate the schema. Stop after the answer — no index, no rereading.

**Negative route — illustrative counterexample.** Building an extraction project, a review workflow, and
evaluation infrastructure for an incidental read adds setup that satisfies no stated requirement. The
reverse error is just as real: keeping this design once production review requirements appear
under-engineers the task.

**Boundary.** Graduate to Extract when volume, measured field accuracy, difficult layout, or per-field
review justifies it. Use SU1 if a seemingly simple yes/no actually requires checking the whole document
for absence.

**Acceptance check.** A letter containing only two of the three fields returns two values and one
explicit missing value. It does not invent the third.

---

## CS Classify & Split

Read [classify-split-guide.md](classify-split-guide.md) before these cases — classifier models exist, but
their node configuration is not yet documented.

### CS1 Locate documents in a large packet

**Placement.** A published classifier model discovered from the registry, or a deterministic script split
for known page ranges. Bind the resulting segments to Extract.

**Match.** Thousand-page image-only bundles at high monthly volume. Locate several named document types
and their page ranges, then apply an authoritative-duplicate rule before extraction.

**Route.** Segment the input if the digitization budget requires it, preserve original page numbering, and
reconcile document boundaries across segments. Apply the duplicate rule deterministically to the
candidates, then extract fields per retained document.

**Negative route — counterexample.** Extracting the whole packet as one document merges unrelated headers
and fields. Using top-k retrieval to locate document instances can miss additional copies and cannot
produce a verified boundary map.

**Boundary.** Repeated documents of one type still need boundary separation. Already-separated files may
need classification only. Locating a document does not establish its validity — do not discard competing
copies before the duplicate rule can be evaluated.

**Acceptance check.** Return original page ranges for every target document, including one that crosses an
input segment boundary, and record which duplicate was retained and why.

### CS2 Isolate a contract before checking its signature

**Placement.** A published classifier plus splitting. The downstream signature check is a separate
specialist capability, not an agent tool. Preserve segment references through verification.

**Match.** A bundle contains many documents. The first task is to locate and isolate one specific
contract. A later task checks whether the buyer signed it.

**Route.** Classify and split out the target contract, pass that segment to the signature check and, where
required, an independent visual verification. Preserve segment-to-original-page mapping and any
disagreement between the two checks.

**Negative route — counterexample.** Searching the whole packet for any signature can accept a signature
from the wrong form. A classifier's label is never proof that the right party signed the right field.

**Boundary.** If the contract is already a separate file, skip splitting. Signature presence, identity,
and authenticity are downstream evidence analysis; unresolved disagreement goes to review. The classifier
must never infer "signed" from the document type.

**Acceptance check.** A bundle contains several signed forms but an unsigned target contract. Isolate the
correct contract and return the unsigned result rather than borrowing a signature from elsewhere.

### CS3 Classify correspondence with asymmetric error cost

**Placement.** Classification only — a published classifier or an explicitly evaluated agent
implementation — then a Switch node. Bind planned review to Human nodes.

**Match.** One logical correspondence document routed among roughly seven predefined classes, including
authorization, denial, clinical request, and pending review. Misclassifying an authorization as a denial
costs far more than an ordinary confusion.

**Route.** Define the classes and name the confusing pairs. Evaluate critical errors separately from
overall accuracy. Route uncertain cases to review. Select an architecture that meets the measured critical-error
bar rather than assuming one pass will.

**Negative route — observed failure.** A single-model classifier's confidence score failed to separate
critical errors: driving critical errors to zero collapsed straight-through processing to a small
fraction of volume. A more complex consensus design raised throughput substantially but still produced a
critical error — better, but not the zero-error result the requirement demanded.

**Boundary.** If a label really means "no urgency claim appears anywhere", that is an absence question —
use SU1's complete-review pattern. A critical-error target overrides pressure for higher automation.

**Acceptance check.** Blind-test the confusing class pairs and inspect the critical-error confusion matrix
alongside the review load. Do not accept high overall accuracy as evidence that the critical class is safe.

---

## SU Summarize

### SU1 Review a contract against standard terms

**Placement.** Summarize as a fixed review step. If an existing agent must decide when to run it, attach
it as an agent tool instead.

**Match.** A native contract of a few dozen to a couple of hundred pages arrives for a cited assessment of
conflicts or missing required provisions. "No issue found" requires complete review of the defined input,
not a search for familiar clauses.

**Route.** Supply the standard terms, the conflict precedence rules, and the distinction between missing,
ambiguous, and contradictory provisions. Track review coverage and cite findings. A clean result requires
complete processing plus a validation process — not merely choosing this mode.

**Negative route — illustrative misroute.** Searching only for the expected clause language misses
unusually phrased clauses and absent ones entirely. A plausible retrieved passage cannot prove that no
exception appears elsewhere.

**Boundary.** One named effective date belongs in Extract or a bounded read. Positive lookups against a
persistent corpus can use PS2, but an absence claim needs full coverage. Missing pages or uncertain OCR
must qualify the conclusion or block clearance.

**Acceptance check.** Include one unusually worded conflicting clause and one absent required clause.
Identify both. An unreadable page produces a coverage limitation, never "no conflicts".

### SU2 Produce a cross-document assessment

**Placement.** Summarize for the synthesis stages, script for formatting, Control nodes for any required
partitioning and convergence.

**Match.** A defined set of a few dozen documents holds the evidence for one written risk assessment.
Cross-document synthesis, contradictions, and traceable claims matter more than response latency.

**Route.** Process the complete manifest within supported budgets. Where necessary use coverage-tracked
thematic passes followed by a synthesis pass that retains the original evidence links. Apply report
formatting deterministically afterwards.

**Negative route — illustrative misroute.** Querying a persistent index produces selected evidence, not
verified coverage of the supplied set. Pasting a full output template into every reasoning pass adds
tokens without adding evidence.

**Boundary.** Researching an unknown set of sources is a gathering and orchestration task first. Fixed
fields go to Extract. Use AH2 when the task needs contract-version resolution and numerical compliance
checks rather than a written assessment. Unprocessed documents remain explicit gaps.

**Acceptance check.** Two documents disagree about a risk. Explain the conflict, cite both sources and the
handling rule applied, and preserve the full document manifest through partitioning.

### SU3 Build a cited briefing from collected evidence

**Placement.** Summarize after source collection, or an agent tool when the agent chooses the moment.
Human review handles the configured approval.

**Match.** Evidence has already been gathered for a profile and discussion guide. The deliverable is a
coherent, cited briefing for human approval, refreshed periodically or on demand.

**Route.** Synthesize over the collected evidence snapshot. Separate source-supported facts from suggested
discussion topics, retain freshness dates and citations, and send the output for review. The surrounding
workflow owns gathering, storage, access, refresh, and approval.

**Negative route — counterexample.** A few retrieved snippets cannot produce a complete profile. Calling
the whole research-and-approval workflow "Summarize" hides responsibilities that belong to other steps.

**Boundary.** If the user wants one established fact from the knowledge pool, use PS1. If evidence is
missing or sources conflict, gather more or flag it — never invent biographical detail. Formatting comes
after synthesis.

**Acceptance check.** An older profile and a newer source list different affiliations. Report the dated
evidence and either resolve or flag the conflict, and distinguish a proposed discussion topic from an
established fact.

---

## PS Persistent index — semantic search

Shared configuration: a persistent corpus in the agent's context, `retrievalMode: "semantic"`. Search
returns evidence; the agent forms the answer. Retrieval proves neither absence nor exhaustive coverage.
See [search-mode-guide.md](search-mode-guide.md).

### PS1 Answer support questions from a shared knowledge base

**Placement.** Autonomous agent, Context with a persistent index, semantic search, standard harness.
Fixed live-system lookups are a Flow-owned request; agent-selected ones are an agent tool.

**Match.** Staff repeatedly ask policy and system-support questions over a standing document collection.
A typical question is answered by one procedure or a few passages.

**Route.** Use the existing access-scoped corpus. Retrieve once for a bounded question, inspect relevance,
and answer with source references. Use a deterministic system-of-record tool for live transaction status.

**Negative route — observed ingestion failure.** Legacy document formats were silently skipped during
ingestion, producing "missing source" complaints. Repeated queries cannot recover content that never
entered the index, and rebuilding the corpus per request wastes the ingestion work.

**Boundary.** Verify ingestion and freshness before interpreting an empty result. If a question requires
dependent searches, that is PA. Live system data is not necessarily current in indexed documents.

**Acceptance check.** Answer a supported procedure question with its source. For a file skipped at
ingestion, report unavailable evidence — do not claim the policy does not exist.

### PS2 Look up a provision in plan documents

**Placement.** Autonomous agent, Context with a persistent index, semantic search, scoped to the
applicable plan and version. Harness chosen independently.

**Match.** Analysts need bounded, source-backed plan-language lookups. Use this route when the applicable
plan is known, its indexed version is current, and the provision is locally answerable.

**Route.** Scope to the plan and version, return the relevant provisions with citations, and reserve the
decision for the analyst or a downstream reasoning step. Confirm the corpus is genuinely reused; transient
documents belong in a bounded read instead.

**Negative route — observed comparison.** A heavier just-in-time retrieval path was presumed more
accurate, but was measured slower while agreeing with the validated regular-index answers on the large
majority of questions. Output agreement is not accuracy. A later report also found semantic-search
timeouts and tool-call limits — neither route is universally reliable.

**Boundary.** If exclusions and related provisions require dependent searches, use PA2. If the conclusion
requires proving no contrary provision exists, use SU1. Do not select a heavier path merely because the
surrounding business process is complex.

**Acceptance check.** Retrieve the applicable clause and its version. A missing hit is unresolved, not "no
such right". Compare routes on adjudicated answers and latency, not on identical free-text wording.

### PS3 Answer a domain-scoped knowledge question

**Placement.** Autonomous agent, Context with a persistent index, semantic search with domain scoping,
standard harness.

**Match.** A shared body of knowledge is partitioned by office or bureau. A question asks for a
definition, a required artifact, or a documented procedure answerable within one known domain.

**Route.** Apply domain scoping before retrieval. Attach canonical term definitions and document
provenance, then return the bounded cited answer. Reuse the same knowledge service other consumers use.

**Negative route — counterexample.** Searching all domains together can return a plausible but wrong
office's terminology or requirement. Starting a multi-step loop for one well-defined term adds latency
with no demonstrated benefit.

**Boundary.** An unknown domain is a routing ambiguity to resolve first. Enrichment that needs related
terms and supporting obligations is PA2. Without an evaluation set, do not describe the design as having
validated accuracy.

**Acceptance check.** The same term appears in two domains with different expectations. Answer from the
selected domain and cite its source; do not blend the definitions.

---

## PA Persistent index — agentic search

Shared configuration: the same persistent index in the agent's context, read through a bounded search
loop. Define scope, an evidence checklist, a numeric budget, and stop conditions before invoking it —
[search-mode-guide.md](search-mode-guide.md), and
`/uipath:uipath-agents — references/agentic-search/planning.md`
for the build.

### PA1 Resolve codes across several reference sources

**Placement.** Autonomous agent, Context with a persistent index, bounded search loop. Harness chosen
independently — the loop is not a harness feature.

**Match.** A line item must be interpreted against an item master and two further attribute sources.
Noisy aliases, placeholder substitution, and seasonal variation affect which evidence is needed next. One
semantic hit identifies only part of the answer.

**Route.** Scope to the relevant source and version. Resolve the base item, then use the returned
identifiers to search the dependent attribute sources, then validate the seasonal and substitution
evidence. Keep deterministic substitutions and row iteration in code. Return values with source lineage
and an explicit list of unresolved components.

**Negative route — observed boundary.** A single likely item match did not validate both dependent
attributes. Sheet-origin information was missing, so a constant-looking attribute could not be confirmed
valid for the current season. More searches and majority voting cannot restore provenance that was never
captured.

**Boundary.** An exact, complete keyed mapping belongs in a deterministic lookup, not a search loop. A
single-source question stays PS. If the seasonal evidence is absent or contradictory, return
needs-review; repair the metadata or the source access rather than continuing to loop. Structure
detection for the same file is AF1, a separate step.

**Acceptance check.** Resolve an aliased base code and a placeholder using all required sources. For a
match lacking seasonal evidence, return unresolved rather than a guessed final code.

### PA2 Enrich a request with domain-specific evidence

**Placement.** Autonomous agent, Context with a persistent index, bounded search loop after domain
selection. Human review where required.

**Match.** An incoming request must be normalized for the receiving office. Relevant terminology, expected
artifacts, and supporting passages are distributed across the domain corpus, and the mappings are not all
predefined.

**Route.** Select the domain first. Retrieve candidate obligations, inspect canonical terms and document
context, reformulate for whatever evidence is still missing, and return a normalized request with
citations and open questions. Preserve the retrieval trail and route the proposed wording for review.

**Negative route — counterexample.** One global semantic hit can normalize the terminology while missing a
separate obligation entirely. Keyword rules alone cannot resolve contextual differences between offices.
Conversely, a simple definition request does not justify a loop at all.

**Boundary.** Bounded knowledge questions are PS3. If the requirement is *every* applicable obligation,
search cannot establish completeness — require a defined source manifest and a full review. Stop when each
required element has evidence or a recorded gap. Do not infer calibrated certainty from an
agent-generated confidence number.

**Acceptance check.** Resolve a request whose canonical name and evidence requirement live in different
sources, citing both. An unresolved domain or obligation becomes a reviewer question, not a guess.

### PA3 Investigate impacted documents, with an exhaustiveness boundary

**Placement.** Autonomous agent, Context with a persistent index, bounded search loop for candidate
discovery — **plus** a separate deterministic enumeration and coverage reconciliation whenever the
deliverable claims completeness.

**Match.** Several thousand controlled documents may be affected by a terminology or policy change.
Iterative discovery helps find candidate impacts, separate current text from revision history, and
investigate ambiguous references.

**Route.** Expand justified terms, inspect current-content matches, deduplicate by stable document ID, and
record scope and version evidence. If the deliverable says "all impacted documents", add a deterministic
corpus enumeration and reconcile the processed IDs against the inventory.

**Negative route — observed workaround, unresolved guarantee.** A proof of concept raised the retrieval
result limit and added a review pass because relevance-only retrieval did not meet the enumeration
objective. That design is evidence of a completeness problem, not proof that every impacted document was
found.

**Boundary.** A search loop is appropriate for investigation and **insufficient on its own for a
guaranteed exhaustive list**. A literal, well-defined keyword scan may be entirely deterministic —
prefer it. Reaching the result cap, lacking an inventory, or hitting unreadable files all prevent an
exhaustive claim.

**Acceptance check.** Test a current-text hit, a history-only hit, an alias, a duplicate, and an
inaccessible document. Reconcile processed IDs against the inventory before claiming completeness;
otherwise label the list partial.

---

## EX Extract

### EX1 Extract fields from short, consistent forms

**Placement.** Extract with verified settings. Decision and Human review only with configured field-review
data and continuation bindings.

**Match.** Short, consistent forms of a few pages each with repeated fixed fields. Production review and
the cost of releasing an incorrect value are central requirements. Classification may already have
happened upstream.

**Route.** Start at the lowest supported strategy and evaluate it against the actual forms; consider a
specialized trained model where appropriate. Define the schema, evaluate field errors, set review gates
using validated confidence behavior, and preserve the correction workflow. Skip duplicate classification
when inputs are already reliably separated.

**Negative route — counterexample.** An agent-only file prompt can return correct-looking JSON without the
field-level evaluation and correction process the requirement actually names. Raising a confidence
threshold without validating it creates review load and still misses errors.

**Boundary.** A low-volume incidental three-field read is AF3. Packets need CS1 first. Zero observed errors
in a small sample is not a guarantee of zero production errors — release decisions need ongoing validation.

**Acceptance check.** Evaluate missing fields, incorrect values, and exception load separately. Include one
difficult or ambiguous field and confirm it follows the defined review path.

### EX2 Extract handwritten forms and results

**Placement.** Extract with verified schema and digitization settings. Bind exceptions and corrected
fields through a supported human review workflow.

**Match.** Forms containing handwriting and low-contrast scans. A unified schema of a couple of dozen
fields across several groups, including demographics and result details. Ordered items must be
distinguished from reported values and ranges. Human field validation is required.

**Route.** Validate digitization settings on representative scans. Unify field semantics and taxonomy,
define missing-value behavior, evaluate by field and by group, and preserve document references for
review. Escalate the extraction strategy only when measured density or cross-page assembly requires it.

**Negative route — observed correction.** The engagement began with poor handwriting performance and
fragmented pipelines. Taxonomy and field-type corrections were what moved quality; increasing reasoning
effort or replacing the workflow with a generic file prompt would not have established a reliable field
contract. Even after the correction, overall accuracy being high did not mean every individual field was
— at least one lagged well behind the aggregate, which is why per-field evaluation is the requirement.

**Boundary.** A narrative history belongs in SU2's synthesis pattern, not a repeated extraction field.
Split mixed logical documents first. Do not infer a digitization option from the presence of handwriting
— test it on the actual scans.

**Acceptance check.** Distinguish an ordered item from an actual result, preserve an unreadable value as
unresolved, and route weak fields to review. Verify retained evidence is still available when delayed
review resumes.

### EX3 Extract repeated entity groups without truncation

**Placement.** Extract, escalating strategy only where supported and validated. Extraction strategy names
are not harness settings. Use explicit partition and collection stages where required.

**Match.** Documents describing 15–20 or more repeated entities, each with fields spread across the
document. The difficulty is output and entity density plus complete group assembly — not page count.

**Route.** Use schema decomposition and evidence-preserving assembly. Partition by field group or entity
when that matches the density. Consider an adaptive strategy for sparse or irregular targets. Retain a
tested split-taxonomy fallback and cost it explicitly.

**Negative route — observed failure.** The existing extraction path hit a field and output ceiling. The
documented mitigation split the taxonomy, at several times the per-document cost for the affected
documents. Page-windowing alone does not help when every window still requires a large repeated-entity
output.

**Boundary.** Short, clean field sets are EX1. Amendment precedence plus business-system comparison needs
AH1 around the extraction. Never read an empty or missing entity group as true absence without a
completeness check — validate expected entities and schema coverage.

**Acceptance check.** A document lists 20 entities across several sections. Return all 20 groups, associate
the values correctly, and detect a deliberately truncated result before release. Preserve explicit
unresolved fields.

---

## Boundary Lookup

Direct jumps when the symptom is already known. Do not scan the library.

| Symptom | Read first | Counter-boundary |
|---|---|---|
| A simple lookup sent through a heavy reasoning path | PS2 | SU1 when the claim is complete review |
| One semantic hit misses related rules or identifiers | PA1 or PA2 | PS3 for a one-passage question |
| "All impacted documents" or "nothing contradicts" | PA3 or SU1 | A result limit is not a coverage test |
| A long task times out or cannot resume | AH1 | EX3 when only extraction is needed |
| The same control produces different computed results | AH3 | Deterministic tools before judgment |
| A file read has grown into bulk spreadsheet processing | AF1 | EX2 when field review is required |
| Confidence-based approval misses critical errors | CS3 | EX1 for calibrated field-review design |
| Header groups or signatures come from the wrong document | CS1 or CS2 | Extract only after boundaries are established |
| Partial results or missing repeated entities | EX3 | AH1 when precedence is also required |
| Search misses files or source metadata | PS1 or PA1 | Repair ingestion and metadata; do not loop blindly |
| A "summary" task also requires research and external actions | SU3 | Separate collection and orchestration from synthesis |

## Maintaining the library

Keep exactly three cases per category. Replace a weaker case rather than adding a twenty-second — see
[case-template.md](case-template.md).
