# Case Library

24 cases · 8 decision categories · 3 per category.

Match on **document shape and failure mechanism**, not on industry. Read the fast-routing table in
[../SKILL.md](../SKILL.md) first, then the nearest case here, then one boundary case only if the decisive
signals conflict. Do not read the whole library for a routing decision.

## Reading a case

Each case is written to be read by a person as well as matched by an agent. The five sections are:

| Section | What it answers |
|---|---|
| **Problem description** | What the business is actually dealing with, and what "working" looks like |
| **Best-fit solution** | Which mode, which configuration, and which skill owns the build |
| **Decision reasoning** | The decisive signals that select that mode, and the order the work runs in |
| **Negative example** | The route that looks right and fails, with the mechanism — present only where one is real |
| **Boundary** | When a different mode or a deterministic node wins, and what blocks a conclusion |

Two labels distinguish how much weight a case carries:

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

**Problem description.** A base contract arrives with several amendments layered on top of it. The values
a reviewer needs are not stated in any one place — they depend on cross-section interpretation, on
effective dates, and on how far each amendment's scope reaches. What the business wants back is an
evidence-backed comparison against the values already held in a business system, with enough lineage that
a reviewer can follow any figure back to the clause that produced it. Runs are long enough that failing
partway through matters, so checkpoint and resume are part of the requirement rather than a nicety.
Working behaviour looks like this: a later amendment changes one fee and leaves another untouched, and
both effective values come back correct, each with its evidence and its comparison result; an interrupted
run resumes without recomputing the stages that already finished.

**Best-fit solution.** Autonomous agent, advanced harness only for a verified capability need; otherwise
standard with explicit Flow orchestration. Fixed document stages as nodes, exact comparisons in script, a
durable store plus polling for resumability.

**Decision reasoning.** The decisive signal is that values depend on cross-section interpretation,
effective dates, and amendment scope at once — no single extraction pass resolves them. Run it in this
order: classify the documents; extract candidate values with evidence; determine which questions each
amendment changes; resolve precedence; perform the comparisons in code; present exceptions. Persist
completed stages so a retry does not redo them or duplicate outputs.

**Negative example — observed.** Sequential long-running processing inside a single serverless invocation
exceeded its execution window. Later runs produced blank downstream results and missing citations:
successful extraction had not established successful persistence or review readiness.

**Boundary.** If this settles into a stable field-only task, use EX3 or a plain Extract strategy. If the
deliverable is only a cited narrative, use SU2. Never release an audited comparison while evidence is
missing or amendment precedence is unresolved.

### AH2 Long mixed-format payment package review

**Problem description.** Thousand-page payment applications arrive roughly monthly, mixing typed, scanned
and handwritten content in one package. Deciding whether the charges in them are allowable depends on a
master agreement, on party-specific contracts, and on amendments that keep being added. The deliverable
is not a set of extracted invoice fields — it is a list of potentially non-compliant charges together
with the contract chain that supports each call. Working behaviour: a charge allowed by the original
contract but disallowed by an applicable amendment is flagged, an unaffected charge alongside it is not,
and both carry version-specific evidence and exact arithmetic.

**Best-fit solution.** Advanced harness is a candidate, subject to the capability check. Extract for
fields, script for reconciliation, Human review for the configured approval. Standard plus Flow
orchestration remains valid when it is sufficient.

**Decision reasoning.** The decisive signal is that applicability depends on a contract hierarchy that
changes over time, so the governing text must be resolved before any charge can be judged. Establish the
document manifest and the governing contract hierarchy; extract charges; reconcile amounts
deterministically; apply document reasoning to applicability and exceptions; assemble reviewable
findings. Track coverage by segment and by obligation.

**Negative example — observed constraint.** The candidate policy engine handled one document at a time
and could not cleanly combine the governing agreement with its amendments. Concatenating the files was
proposed, but the resulting precedence ambiguity was never resolved — and a single-pass prompt would not
have fixed it.

**Boundary.** Length alone does not select AH: a long field-only document is EX3. Do not call a package
compliant while required documents, amendment applicability, or unprocessed segments remain open.

### AH3 Control testing with exact calculations

**Problem description.** A couple of hundred controls have to be tested against evidence files, often
spreadsheet exports. A single control may need a data transformation, some exact arithmetic, and a
judgment about whether the evidence actually satisfies a policy — and the inputs and procedures differ
from one control to the next. This case exists mainly as a boundary against reaching for an agent when
the work is arithmetic. Working behaviour: identical evidence yields identical computed totals across
reruns; a missing input blocks the corresponding conclusion rather than defaulting it; and easy, medium
and complex procedures are all exercised, not just the easiest subset.

**Best-fit solution.** Script and Data operations for the exact controls; an autonomous agent only for
the residual judgment. Advanced harness only on a demonstrated need.

**Decision reasoning.** The decisive signal is that most of the work is deterministic and only a residue
is judgment — so the split, not the harness, is the design. Define the procedure and evidence
requirements first. Run spreadsheet manipulation and reconciliation in deterministic tools. Feed computed
results plus evidence to the judgment step. Retain an audit trail. Fixed controls need no agent at all.

**Negative example — observed failure.** A file-reading tool was used for everything, including
calculations and oversized evidence, with no deterministic tools built. A rerun changed the same
control's pass/fail result, and some evidence had never been evaluated at all.

**Boundary.** Arithmetic is code, not reasoning. A small qualitative file inspection is AF2. An
underspecified control or unread evidence produces "not evaluated", never "pass". Do not manufacture
calibrated confidence from a model's self-rating.

---

## AF Analyze files

### AF1 Detect an unfamiliar export layout

**Problem description.** Purchase-order exports arrive from many sources with no fixed template — column
layouts differ, headers sit on different rows, and the language is often not English. Before any row can
be processed, something has to work out which sheet holds the data, which row is the header, and which
columns matter. That structural question is asked once per file; the repetitive row work happens
afterwards. Working behaviour: a shifted header row and reordered columns are detected and then
confirmed in code, every row survives without model arithmetic, and headers that are unknown or
ambiguous are flagged rather than guessed.

**Best-fit solution.** Autonomous agent, standard harness, Analyze files tool. Bind the detected
structure to deterministic row processing.

**Decision reasoning.** The decisive signal is that the *structure* is unknown but the *processing* is
not — one bounded inspection unlocks ordinary code. Supply an input representation the tool supports,
inspect once, validate the detected columns against the actual file, then process rows deterministically.
If an individual item later needs multi-source interpretation, that is PA1, separately.

**Negative example — counterexample.** Asking the agent to rediscover the structure and extract every row
multiplies calls and produces inconsistent row handling. An unfamiliar layout alone does not justify a
persistent index.

**Boundary.** Do not infer general spreadsheet support from one implementation — check the active input
path and budget. If deterministic parsing identifies headers reliably, skip the model. If the requirement
is production field extraction with per-field review, use EX2. If the per-row work itself needs
natural-language reasoning once the layout is known, that is BT.

### AF2 Read invoice evidence for an asset review

**Problem description.** An agent reviews invoice and backup attachments attached to fixed-asset addition
requests — a few hundred a month. It does not need to capture a field set; it needs enough of the
document's content as evidence to recommend approval, rejection, or human review, with an analyst
remaining the final approver. Working behaviour: the asset description and invoice amount are read,
unreadable fields are preserved as unresolved rather than filled in, and when required evidence is simply
unavailable the outcome is a human-review route.

**Best-fit solution.** Autonomous agent, standard harness, Analyze files tool. Add Context only for
genuinely reusable policy knowledge. Bind the analyst review to a Human node.

**Decision reasoning.** The decisive signal is that content access, not field capture, is what the
decision needs — there is no schema to evaluate against. Read the relevant content from supported,
budget-fitting attachments, then apply policy in the agent's reasoning. Perform amount calculations in
code. Keep source identifiers and the analyst approval step. Do not claim native calibrated field
confidence.

**Negative example — counterexample.** Treating the reader as a complete extraction and approval engine
confuses content access with a validated decision. Forcing all policy reasoning and arithmetic into one
opaque tool prompt makes the intermediate evidence impossible to inspect.

**Boundary.** Attachment size is frequently unspecified — check it before choosing this route. Missing or
oversized evidence blocks a recommendation or routes to a document processor. Stable high-volume field
capture is EX1 or EX2; complex adaptive review may be AH3.

### AF3 Read three fields from a clean letter

**Problem description.** Clean single-page letters arrive at low daily volume, and three named values are
needed from them inside a wider agent task. Nobody has asked for a field-level production SLA, and no
correction workflow exists or is planned. The risk in this case is over-building in one direction and
under-building in the other. Working behaviour: a letter containing only two of the three fields returns
two values and one explicit missing value, and does not invent the third.

**Best-fit solution.** Autonomous agent, standard harness, Analyze files tool. No Context and no Memory.

**Decision reasoning.** The decisive signal is the absence of any review, accuracy or correction
requirement — that absence is what makes the lightweight route correct rather than lazy. One bounded read
with a small output contract. Return the requested values, explicitly mark missing ones, and validate the
schema. Stop after the answer — no index, no rereading.

**Negative example — illustrative counterexample.** Building an extraction project, a review workflow,
and evaluation infrastructure for an incidental read adds setup that satisfies no stated requirement. The
reverse error is just as real: keeping this design once production review requirements appear
under-engineers the task.

**Boundary.** Graduate to Extract when volume, measured field accuracy, difficult layout, or per-field
review justifies it. Use SU1 if a seemingly simple yes/no actually requires checking the whole document
for absence.

---

## CS Classify & Split

Read [classify-split-guide.md](classify-split-guide.md) before these cases — classifier models exist, but
their node configuration is not yet documented.

### CS1 Locate documents in a large packet

**Problem description.** Thousand-page, image-only bundles arrive at high monthly volume, and several
named document types are buried somewhere inside each one. The job is to find them and their page ranges,
apply a rule about which copy is authoritative when the same document appears more than once, and only
then extract fields from what survives. Working behaviour: original page ranges come back for every
target document, including one that straddles an input segment boundary, and the record shows which
duplicate was retained and why.

**Best-fit solution.** A published classifier model discovered from the registry, or a deterministic
script split for known page ranges. Bind the resulting segments to Extract.

**Decision reasoning.** The decisive signal is that document boundaries are unknown inside a single
physical file — extraction cannot start until they are established. Segment the input if the
digitization budget requires it, preserve original page numbering, and reconcile document boundaries
across segments. Apply the duplicate rule deterministically to the candidates, then extract fields per
retained document.

**Negative example — counterexample.** Extracting the whole packet as one document merges unrelated
headers and fields. Using top-k retrieval to locate document instances can miss additional copies and
cannot produce a verified boundary map.

**Boundary.** Repeated documents of one type still need boundary separation. Already-separated files may
need classification only. Locating a document does not establish its validity — do not discard competing
copies before the duplicate rule can be evaluated.

### CS2 Isolate a contract before checking its signature

**Problem description.** A bundle contains many documents and the first task is simply to find one
specific contract inside it. A later, separate task asks whether the buyer actually signed that contract.
Conflating the two is the trap: locating a document says nothing about its validity. Working behaviour:
given a bundle containing several signed forms and an unsigned target contract, the correct contract is
isolated and the unsigned result is returned — no signature is borrowed from a neighbouring form.

**Best-fit solution.** A published classifier plus splitting. The downstream signature check is a separate
specialist capability, not an agent tool. Preserve segment references through verification.

**Decision reasoning.** The decisive signal is that one specific document must be isolated from a mixed
bundle before any evidence question can be asked of it. Classify and split out the target contract, pass
that segment to the signature check and, where required, an independent visual verification. Preserve
segment-to-original-page mapping and any disagreement between the two checks.

**Negative example — counterexample.** Searching the whole packet for any signature can accept a
signature from the wrong form. A classifier's label is never proof that the right party signed the right
field.

**Boundary.** If the contract is already a separate file, skip splitting. Signature presence, identity,
and authenticity are downstream evidence analysis; unresolved disagreement goes to review. The classifier
must never infer "signed" from the document type.

### CS3 Classify correspondence with asymmetric error cost

**Problem description.** One logical correspondence document has to be routed among roughly seven
predefined classes — authorization, denial, clinical request, pending review and similar. The classes are
not equally costly to confuse: sending an authorization down the denial path does far more damage than an
ordinary mix-up, so overall accuracy is the wrong thing to optimise. Working behaviour: the confusing
class pairs are blind-tested and the critical-error confusion matrix is inspected alongside the review
load, rather than a high aggregate score being accepted as evidence the critical class is safe.

**Best-fit solution.** Classification only — a published classifier or an explicitly evaluated agent
implementation — then a Switch node. Bind planned review to Human nodes.

**Decision reasoning.** The decisive signal is the asymmetry: one confusion costs far more than the
others, which changes the architecture and not just the threshold. Define the classes and name the
confusing pairs. Evaluate critical errors separately from overall accuracy. Route uncertain cases to
review. Select an architecture that meets the measured critical-error bar rather than assuming one pass
will.

**Negative example — observed failure.** A single-model classifier's confidence score failed to separate
critical errors: driving critical errors to zero collapsed straight-through processing to a small
fraction of volume. A more complex consensus design raised throughput substantially but still produced a
critical error — better, but not the zero-error result the requirement demanded.

**Boundary.** If a label really means "no urgency claim appears anywhere", that is an absence question —
use SU1's complete-review pattern. A critical-error target overrides pressure for higher automation.

---

## SU Summarize

### SU1 Review a contract against standard terms

**Problem description.** A native contract of anywhere from a few dozen to a couple of hundred pages
arrives for a cited assessment: where does it conflict with standard terms, and which required
provisions are missing? The second half of that question is the hard one. "No issue found" is a claim
about the whole document, so it requires complete review of the defined input rather than a search for
clause language somebody already expected. Working behaviour: an unusually worded conflicting clause and
an absent required clause are both identified, and an unreadable page produces a coverage limitation —
never a clean "no conflicts".

**Best-fit solution.** Summarize as a fixed review step. If an existing agent must decide when to run it,
attach it as an agent tool instead.

**Decision reasoning.** The decisive signal is that the deliverable makes an absence claim, and absence
cannot be established by retrieval. Supply the standard terms, the conflict precedence rules, and the
distinction between missing, ambiguous, and contradictory provisions. Track review coverage and cite
findings. A clean result requires complete processing plus a validation process — not merely choosing
this mode.

**Negative example — illustrative misroute.** Searching only for the expected clause language misses
unusually phrased clauses and absent ones entirely. A plausible retrieved passage cannot prove that no
exception appears elsewhere.

**Boundary.** One named effective date belongs in Extract or a bounded read. Positive lookups against a
persistent corpus can use PS2, but an absence claim needs full coverage. Missing pages or uncertain OCR
must qualify the conclusion or block clearance.

### SU2 Produce a cross-document assessment

**Problem description.** A defined set of a few dozen documents holds the evidence for one written risk
assessment. The value is in the synthesis across them — contradictions between sources, claims traceable
back to the document that supports them — and the business is willing to trade response latency for
that. Working behaviour: when two documents disagree about a risk, the conflict is explained, both
sources and the handling rule applied are cited, and the full document manifest survives whatever
partitioning the processing required.

**Best-fit solution.** Summarize for the synthesis stages, script for formatting, Control nodes for any
required partitioning and convergence.

**Decision reasoning.** The decisive signal is cross-document synthesis over a *defined* set — the
manifest is known, so coverage is verifiable and worth verifying. Process the complete manifest within
supported budgets. Where necessary use coverage-tracked thematic passes followed by a synthesis pass that
retains the original evidence links. Apply report formatting deterministically afterwards.

**Negative example — illustrative misroute.** Querying a persistent index produces selected evidence, not
verified coverage of the supplied set. Pasting a full output template into every reasoning pass adds
tokens without adding evidence.

**Boundary.** Researching an unknown set of sources is a gathering and orchestration task first. Fixed
fields go to Extract. Use AH2 when the task needs contract-version resolution and numerical compliance
checks rather than a written assessment. Unprocessed documents remain explicit gaps.

### SU3 Build a cited briefing from collected evidence

**Problem description.** Evidence has already been gathered for a profile and a discussion guide; the
remaining job is to turn it into a coherent, cited briefing that a human approves, refreshed on a
schedule or on demand. The surrounding workflow — gathering, storage, access, refresh, approval — is
somebody else's responsibility, and calling the whole thing "Summarize" hides that. Working behaviour: an
older profile and a newer source list different affiliations, the dated evidence is reported and the
conflict either resolved or flagged, and a proposed discussion topic is never presented as an established
fact.

**Best-fit solution.** Summarize after source collection, or an agent tool when the agent chooses the
moment. Human review handles the configured approval.

**Decision reasoning.** The decisive signal is that collection is already done — what remains is
synthesis over a fixed snapshot. Synthesize over the collected evidence snapshot. Separate
source-supported facts from suggested discussion topics, retain freshness dates and citations, and send
the output for review.

**Negative example — counterexample.** A few retrieved snippets cannot produce a complete profile.
Calling the whole research-and-approval workflow "Summarize" hides responsibilities that belong to other
steps.

**Boundary.** If the user wants one established fact from the knowledge pool, use PS1. If evidence is
missing or sources conflict, gather more or flag it — never invent biographical detail. Formatting comes
after synthesis.

---

## PS Persistent index — semantic search

Shared configuration: a persistent corpus in the agent's context, `retrievalMode: "semantic"`. Search
returns evidence; the agent forms the answer. Retrieval proves neither absence nor exhaustive coverage.
See [search-mode-guide.md](search-mode-guide.md).

### PS1 Answer support questions from a shared knowledge base

**Problem description.** Staff repeatedly ask policy and system-support questions against a standing
document collection. A typical question is satisfied by one procedure or a handful of passages, and the
corpus is genuinely reused rather than assembled per request. The failure mode that matters here is not
retrieval quality — it is ingestion. Working behaviour: a supported procedure question is answered with
its source, and for a file that was skipped at ingestion the answer reports unavailable evidence rather
than claiming the policy does not exist.

**Best-fit solution.** Autonomous agent, Context with a persistent index, semantic search, standard
harness. Fixed live-system lookups are a Flow-owned request; agent-selected ones are an agent tool.

**Decision reasoning.** The decisive signal is a reusable corpus plus bounded questions — one retrieval
answers most of them. Use the existing access-scoped corpus. Retrieve once for a bounded question,
inspect relevance, and answer with source references. Use a deterministic system-of-record tool for live
transaction status.

**Negative example — observed ingestion failure.** Legacy document formats were silently skipped during
ingestion, producing "missing source" complaints. Repeated queries cannot recover content that never
entered the index, and rebuilding the corpus per request wastes the ingestion work.

**Boundary.** Verify ingestion and freshness before interpreting an empty result. If a question requires
dependent searches, that is PA. Live system data is not necessarily current in indexed documents.

### PS2 Look up a provision in plan documents

**Problem description.** Analysts need bounded, source-backed lookups of plan language: the applicable
plan is known, its indexed version is current, and the provision they want is answerable locally without
chasing cross-references. The decision itself stays with the analyst. Working behaviour: the applicable
clause and its version are retrieved; a missing hit is reported as unresolved rather than as "no such
right"; and competing retrieval routes are compared on adjudicated answers and latency, not on whether
their free-text wording happens to match.

**Best-fit solution.** Autonomous agent, Context with a persistent index, semantic search, scoped to the
applicable plan and version. Harness chosen independently.

**Decision reasoning.** The decisive signal is a known plan and a locally answerable provision — scoping
does more work here than search strategy. Scope to the plan and version, return the relevant provisions
with citations, and reserve the decision for the analyst or a downstream reasoning step. Confirm the
corpus is genuinely reused; transient documents belong in a bounded read instead.

**Negative example — observed comparison.** A heavier just-in-time retrieval path was presumed more
accurate, but was measured slower while agreeing with the validated regular-index answers on the large
majority of questions. Output agreement is not accuracy. A later report also found semantic-search
timeouts and tool-call limits — neither route is universally reliable.

**Boundary.** If exclusions and related provisions require dependent searches, use PA2. If the conclusion
requires proving no contrary provision exists, use SU1. Do not select a heavier path merely because the
surrounding business process is complex.

### PS3 Answer a domain-scoped knowledge question

**Problem description.** A shared body of knowledge is partitioned by office or bureau, and the same term
can mean different things in different partitions. A question asks for a definition, a required artifact,
or a documented procedure that is answerable within one known domain. Getting the domain right matters
more than getting the retrieval clever. Working behaviour: where the same term appears in two domains
with different expectations, the answer comes from the selected domain and cites its source, without
blending the two definitions.

**Best-fit solution.** Autonomous agent, Context with a persistent index, semantic search with domain
scoping, standard harness.

**Decision reasoning.** The decisive signal is that the corpus is partitioned and the partition is known
— scoping before retrieval is what prevents the wrong office's answer. Apply domain scoping before
retrieval. Attach canonical term definitions and document provenance, then return the bounded cited
answer. Reuse the same knowledge service other consumers use.

**Negative example — counterexample.** Searching all domains together can return a plausible but wrong
office's terminology or requirement. Starting a multi-step loop for one well-defined term adds latency
with no demonstrated benefit.

**Boundary.** An unknown domain is a routing ambiguity to resolve first. Enrichment that needs related
terms and supporting obligations is PA2. Without an evaluation set, do not describe the design as having
validated accuracy.

---

## PA Persistent index — agentic search

Shared configuration: the same persistent index in the agent's context, read through a bounded search
loop. Define scope, an evidence checklist, a numeric budget, and stop conditions before invoking it —
[search-mode-guide.md](search-mode-guide.md), and
`/uipath:uipath-agents — references/agentic-search/planning.md`
for the build.

### PA1 Resolve codes across several reference sources

**Problem description.** A line item has to be interpreted against an item master and two further
attribute sources before it means anything. The identifiers are noisy: aliases, placeholder substitution,
and seasonal variation all change which evidence is needed next, so one lookup identifies only part of
the answer. Working behaviour: an aliased base code and a placeholder are resolved using all the required
sources; where a match lacks the seasonal evidence to confirm it, the result comes back unresolved rather
than as a guessed final code.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop. Harness
chosen independently — the loop is not a harness feature.

**Decision reasoning.** The decisive signal is dependent retrieval: the identifier returned by the first
lookup is the input to the second. Scope to the relevant source and version. Resolve the base item, then
use the returned identifiers to search the dependent attribute sources, then validate the seasonal and
substitution evidence. Keep deterministic substitutions and row iteration in code. Return values with
source lineage and an explicit list of unresolved components.

**Negative example — observed boundary.** A single likely item match did not validate both dependent
attributes. Sheet-origin information was missing, so a constant-looking attribute could not be confirmed
valid for the current season. More searches and majority voting cannot restore provenance that was never
captured.

**Boundary.** An exact, complete keyed mapping belongs in a deterministic lookup, not a search loop. A
single-source question stays PS. If the reference data is small enough to travel with each row, that is
BT2, not a search loop. If the seasonal evidence is absent or contradictory, return needs-review; repair
the metadata or the source access rather than continuing to loop. Structure detection for the same file
is AF1, a separate step.

### PA2 Enrich a request with domain-specific evidence

**Problem description.** An incoming request must be normalized before the receiving office can act on
it. The terminology it should use, the artifacts it should carry, and the obligations that apply are
scattered across the domain corpus, and the mappings are not all predefined — so what to look up next
depends on what the last lookup returned. Working behaviour: a request whose canonical name and evidence
requirement live in different sources is resolved with both cited; an unresolved domain or obligation
becomes a reviewer question rather than a guess.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop after
domain selection. Human review where required.

**Decision reasoning.** The decisive signal is scattered evidence plus undefined mappings — reformulation
is doing real work, not padding recall. Select the domain first. Retrieve candidate obligations, inspect
canonical terms and document context, reformulate for whatever evidence is still missing, and return a
normalized request with citations and open questions. Preserve the retrieval trail and route the proposed
wording for review.

**Negative example — counterexample.** One global semantic hit can normalize the terminology while
missing a separate obligation entirely. Keyword rules alone cannot resolve contextual differences between
offices. Conversely, a simple definition request does not justify a loop at all.

**Boundary.** Bounded knowledge questions are PS3. If the requirement is *every* applicable obligation,
search cannot establish completeness — require a defined source manifest and a full review. Stop when each
required element has evidence or a recorded gap. Do not infer calibrated certainty from an
agent-generated confidence number.

### PA3 Investigate impacted documents, with an exhaustiveness boundary

**Problem description.** Several thousand controlled documents may be affected by a terminology or policy
change, and somebody has asked which ones. Iterative discovery genuinely helps — it finds candidates,
separates current text from revision history, and chases ambiguous references. What it cannot do is
prove it found them all, which matters because the deliverable is phrased as a complete list. Working
behaviour: a current-text hit, a history-only hit, an alias, a duplicate and an inaccessible document are
each handled correctly, and processed IDs are reconciled against the inventory before the list is allowed
to claim completeness; otherwise it is labelled partial.

**Best-fit solution.** Autonomous agent, Context with a persistent index, bounded search loop for
candidate discovery — **plus** a separate deterministic enumeration and coverage reconciliation whenever
the deliverable claims completeness.

**Decision reasoning.** The decisive signal is a collision: dependent discovery argues for the loop,
while an enumerative deliverable argues that the loop can never finish the job. Expand justified terms,
inspect current-content matches, deduplicate by stable document ID, and record scope and version
evidence. If the deliverable says "all impacted documents", add a deterministic corpus enumeration and
reconcile the processed IDs against the inventory.

**Negative example — observed workaround, unresolved guarantee.** A proof of concept raised the retrieval
result limit and added a review pass because relevance-only retrieval did not meet the enumeration
objective. That design is evidence of a completeness problem, not proof that every impacted document was
found. Reducing the per-run batch size did not help either — the ceiling was being consumed by a single
unbounded investigation, not by the number of items in a batch.

**Boundary.** A search loop is appropriate for investigation and **insufficient on its own for a
guaranteed exhaustive list**. A literal, well-defined keyword scan may be entirely deterministic —
prefer it. Reaching the result cap, lacking an inventory, or hitting unreadable files all prevent an
exhaustive claim.

---

## EX Extract

### EX1 Extract fields from short, consistent forms

**Problem description.** Short, consistent forms of a few pages each carry the same fixed fields every
time, and classification has usually already happened upstream. What makes this a production problem
rather than a reading problem is the cost of releasing an incorrect value: review gates, correction
workflow and field-level evaluation are central requirements, not extras. Working behaviour: missing
fields, incorrect values and exception load are evaluated separately from one another, and a deliberately
difficult or ambiguous field follows the defined review path rather than being released.

**Best-fit solution.** Extract with verified settings. Decision and Human review only with configured
field-review data and continuation bindings.

**Decision reasoning.** The decisive signal is a fixed schema plus a real review requirement — that
combination is what rules out a bounded read. Start at the lowest supported strategy and evaluate it
against the actual forms; consider a specialized trained model where appropriate. Define the schema,
evaluate field errors, set review gates using validated confidence behavior, and preserve the correction
workflow. Skip duplicate classification when inputs are already reliably separated.

**Negative example — counterexample.** An agent-only file prompt can return correct-looking JSON without
the field-level evaluation and correction process the requirement actually names. Raising a confidence
threshold without validating it creates review load and still misses errors.

**Boundary.** A low-volume incidental three-field read is AF3. Packets need CS1 first. Zero observed
errors in a small sample is not a guarantee of zero production errors — release decisions need ongoing
validation.

### EX2 Extract handwritten forms and results

**Problem description.** Forms arrive containing handwriting and low-contrast scans, carrying a unified
schema of a couple of dozen fields across several groups — demographics, result details and more. Ordered
items have to be told apart from reported values and ranges, and human field validation is required. The
lesson this case carries is that taxonomy and field definitions moved quality more than model effort did.
Working behaviour: an ordered item is distinguished from an actual result, an unreadable value is
preserved as unresolved, weak fields route to review, and retained evidence is still available when a
delayed review resumes.

**Best-fit solution.** Extract with verified schema and digitization settings. Bind exceptions and
corrected fields through a supported human review workflow.

**Decision reasoning.** The decisive signal is a fixed multi-group schema under difficult digitization —
which makes settings and taxonomy the levers, not reasoning effort. Validate digitization settings on
representative scans. Unify field semantics and taxonomy, define missing-value behavior, evaluate by
field and by group, and preserve document references for review. Escalate the extraction strategy only
when measured density or cross-page assembly requires it.

**Negative example — observed correction.** The engagement began with poor handwriting performance and
fragmented pipelines. Taxonomy and field-type corrections were what moved quality; increasing reasoning
effort or replacing the workflow with a generic file prompt would not have established a reliable field
contract. Even after the correction, overall accuracy being high did not mean every individual field was
— at least one lagged well behind the aggregate, which is why per-field evaluation is the requirement.

**Boundary.** A narrative history belongs in SU2's synthesis pattern, not a repeated extraction field.
Split mixed logical documents first. Do not infer a digitization option from the presence of handwriting
— test it on the actual scans.

### EX3 Extract repeated entity groups without truncation

**Problem description.** Documents describe fifteen to twenty or more repeated entities, each with fields
spread across the document, and a single file can yield hundreds of output rows across a dozen columns.
The difficulty is not page count — it is output volume and entity density, plus assembling each group
completely. A truncated result is the dangerous failure here because it looks clean. Working behaviour: a
document listing twenty entities returns all twenty groups with values correctly associated, and a
deliberately truncated result is detected before release rather than shipped as complete.

**Best-fit solution.** Extract, escalating strategy only where supported and validated. Extraction
strategy names are not harness settings. Use explicit partition and collection stages where required.

**Decision reasoning.** The decisive signal is output and entity density rather than input length — so
the fix is schema decomposition, not a bigger window. Use schema decomposition and evidence-preserving
assembly. Partition by field group or entity when that matches the density. Consider an adaptive strategy
for sparse or irregular targets. Retain a tested split-taxonomy fallback and cost it explicitly.

**Negative example — observed failure.** The existing extraction path hit a field and output ceiling. The
documented mitigation split the taxonomy, at several times the per-document cost for the affected
documents. Page-windowing alone does not help when every window still requires a large repeated-entity
output.

**Boundary.** Short, clean field sets are EX1. Amendment precedence plus business-system comparison needs
AH1 around the extraction. Never read an empty or missing entity group as true absence without a
completeness check — validate expected entities and schema coverage.

---

## BT Batch transform

Per-row LLM work over a tabular file, appending generated columns to each row. The node sees one row at
a time plus the prompt — never another row, never an external document, and it cannot perform side
effects. Those three limits are what most BT routing decisions turn on.

### BT1 Parse a free-text operational note into charge intent

**Problem description.** Every shipment record in a freight-invoicing system carries an operational notes
field written by whoever handled the job. It has no format at all — terse fragments, inline rates,
status shorthand — and most of it is written in a mix of two languages. Operators read those notes
alongside a per-customer rate table and key the resulting charges into a billing system, tens of
thousands of records a month. The goal is to produce the charge lines automatically. Two properties
shape the design: the rate table is per-customer and changes without notice, and a single note can
imply several separate charges. Working behaviour: a note stating an inline rate yields a charge intent
carrying that rate and marked as an override; a note that is pure status shorthand yields no charge at
all rather than a speculative one; and a note implying three charges is not silently reduced to one.

**Best-fit solution.** `Data → Batch transform` over an exported record table, emitting charge intent
columns. Rate resolution and arithmetic are deterministic downstream nodes, never part of the prompt.

**Decision reasoning.** The decisive signal is that the per-row work is genuine natural-language
interpretation of a short field against a closed intent vocabulary, and nothing about one row depends on
another. Export the records, run one batch pass to append the intent columns, then explode any multi-
charge result into separate rows in a Script, then join to the rate table and compute amounts
deterministically. Keep the rate table out of the node entirely: it is reference data the row cannot
see, and treating rate lookup as part of the same reasoning step is what makes the result unauditable.

**Negative example — illustrative counterexample.** Asking the node to read the note *and* apply the
customer's rate card in one prompt fails twice over: the rate table is not visible to a row, and folding
a keyed lookup into a language judgement removes the deterministic step that made the charge defensible.
Expecting one input row to emit several charge lines fails too — the node appends columns to the row it
was given. Emit a structured multi-charge value in one column and expand it downstream.

**Boundary.** If the note field is absent and the charge is derivable from structured columns alone, this
is a Transform, not BT. If a single record needs evidence gathered from several reference sources before
it can be interpreted, that is PA1. If the notes arrive as document images rather than a table column,
classification and extraction come first.

### BT2 Classify a line item against a condensed reference matrix

**Problem description.** Invoice line items have to be assigned a tax category drawn from a set of a few
hundred. Today only items above a value threshold get reviewed by a specialist team; everything below it
is processed without review, so the business wants coverage extended downward and the reviewed path
sped up. The reference material is a taxability matrix, and the pivotal question turned out to be not
which model to use but where that matrix lives: condensed to a couple of hundred rows it is small enough
to travel with every row, while the full category set is not. Working behaviour: a line item whose
wording matches no matrix row returns an explicit no-category result routed to review, rather than the
nearest-looking category.

**Best-fit solution.** `Data → Batch transform` appending a single category column, with the condensed
matrix carried in the prompt. Review routing is a downstream Decision plus Human node.

**Decision reasoning.** The decisive signal is a per-row classification into a closed label set where the
entire reference table can be condensed small enough to fit alongside the row — that is what keeps it in
BT rather than pushing it into a grounded search loop. Condense the matrix first and treat that
condensation as a design artifact to be reviewed, not a preprocessing detail. Then one batch pass per
file. Do not let the node call out for reference data; if the matrix stops fitting, the route changes.

**Negative example — observed.** No labeled evaluation set existed on the business side — correct
categories were hand-researched during review, so there was no answer key to score the classifier
against. Category and reference-data quality gated the outcome harder than model quality did, and no
amount of prompt work substitutes for a matrix whose ownership and correctness are unsettled.

**Boundary.** If the reference table cannot be condensed to fit a row, this becomes a grounded lookup —
PA1 when resolution is dependent, PS2 when one scoped retrieval answers it. If the label is a routing
decision over documents rather than a column on a row, that is CS. If categories must be assigned by
exact keyed mapping, use a deterministic lookup and skip the model.

### BT3 Independent per-row judgements feeding a case-level decision

**Problem description.** A claim case carries several documents, a couple of dozen extracted fields per
document, and multiple line items. Each line item is then put through five separate judgements —
diagnosis matching, beneficiary exclusion, policy exclusion, treatment validation, benefit
classification — and the business wants a high no-touch straight-through rate with essentially no false
positives. The structural problem is arithmetic: a case is safe to auto-process only if every field and
every one of the five judgements on every line item is right, so per-row accuracy multiplies rather than
averages. Working behaviour: the release gate is evaluated at case level, not per judgement, and a case
containing one low-confidence line item routes to review as a whole.

**Best-fit solution.** `Data → Batch transform` for the five per-line-item judgements as appended
columns; a deterministic Script to roll line-item results up to a case-level verdict; a consolidated
review surface showing documents, citations, line items and every judgement together.

**Decision reasoning.** The decisive signal is that each judgement is independent per row and none of
them needs another row — which is exactly BT's shape — while the *decision* they feed is case-level and
therefore cannot be made inside the node. Run the judgements as appended columns, then aggregate
deterministically, then gate. Size the review surface to the case, not the row: a reviewer asked to
approve a case cannot do it from five disconnected per-row outputs.

**Negative example — observed.** Extraction confidence was treated as the release gate, and a high
confidence threshold still admitted a substantial share of incorrect fields. Because one wrong
high-confidence field or one wrong judgement makes the whole case unsafe, a per-field gate that looks
strong in isolation did not produce a safe case-level result. Model confidence alone was not a usable
release control.

**Boundary.** If the five judgements are actually dependent — if one determines whether another applies —
they are not five BT columns but a sequence, and the dependency belongs in a Flow. If a judgement needs
evidence from outside the row, it leaves BT. Never read a high aggregate per-field score as evidence that
the case-level outcome is safe.

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
| Per-row work needs a reference table the row cannot see | BT2 | PA1 when the table cannot be condensed to fit |
| One input row must produce several output rows | BT1 | The node appends columns; expand downstream in a Script |
| Per-row scores look strong but the case-level result is unsafe | BT3 | Errors multiply across rows; gate at the decision level |
| An appended column is a formula, regex, or date reformat | Transform or Script | BT only when the row needs language reasoning |

## Maintaining the library

Keep exactly three cases per category. Replace a weaker case rather than adding a twenty-fifth — see
[case-template.md](case-template.md).
