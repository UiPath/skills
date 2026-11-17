# Interview Guide — fill the gaps before the SDD or genome is written

The interview asks the user what the source leaves open and writes each answer as content in the SDD or genome section that owns it. It runs inside three verbs and as a verb of its own:

| Where | When it is offered | Gaps it asks | Answers go |
|---|---|---|---|
| `design` Phase 1 Step 6 ([design-guide.md](../design/design-guide.md)) | after the Phase 1 summary, before scope confirmation | SDD entries (§ Coverage, column *Asked in*) | SDD sections Phases 2–3 write this turn |
| `author` Step 6 ([author-guide.md](../author/author-guide.md)), from an SDD too | after extraction, before Step 7 generates | genome entries, plus SDD entries when no SDD exists | genome sections Step 7 writes |
| `extract` Step 7 ([extract-guide.md](../extract/extract-guide.md)) | after the strict check, in place of naming the open rulings | migration entries | the written genome, as edits ([edit-guide.md](../edit/edit-guide.md)) |
| `interview <SDD_OR_GENOME>` | on request, any later session | every open marker of the document, plus coverage entries with no content | SDD: `design` revise; genome: `edit` |

Declined, each verb runs its own questions as it does without this guide.

## Read Plan

Inside `design`, `author` and `extract`, that verb's § Read Plan opens this guide and every other file. The `interview` verb reads:

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole; the document named, whole |
| start | an SDD | [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Gap Markers, Step 1.5 rule 5, Step 2 items 4, 8 and 9 and § Keeping the Genome Current; the SDD's template in `../../assets/templates/`, by the sections the answers touch |
| start | a genome | [edit-guide.md](../edit/edit-guide.md) whole; its § Read Plan names the rest |
| answers touch the SDD of a genome with a `Designed in:` line | — | the SDD that line links, and the SDD row above |

## Verb Rules

These add to the Critical Rules in [SKILL.md](../../SKILL.md).

1. **Offered once per run, never imposed.** The offer is one structured question (§ The Offer). Not offered — gaps take their markers and defaults as the verb writes them — when: `Execution autonomy` is `autonomous`; the run carries a `planner-design-request: v1` block; the run is unattended; the gap list holds no entry to ask. An autonomous run's closing summary names the counts and `interview <file>` in one line instead.
2. **Ask only what nothing else answers.** The source, the SDD, the tenant and the filesystem come first ([SKILL.md](../../SKILL.md) Anti-pattern 4). Every coverage entry is classified before anything is asked (§ The Gap List).
3. **An answer is content, never a record.** It is written as the fact in the section that owns it, with no marker and no attribution. Two exceptions: a source defect's ruling takes `User ruling ({date}): …` ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)); an SDD gets one Document History row per interview (§ Where Answers Go).
4. **Later steps never ask again.** An answered item has no marker, so no later step finds it. An item the interview put to the user and left open — skipped, defaulted, or held for an absent role — keeps its marker but is not asked again in the run: `design` Phase 3 Step 1.5 asks only the items Phases 2–3 marked after the interview, and `author` Step 8 and `extract`'s close name the open items without asking them.
5. **No round cap.** The user accepted the interview, so its rounds do not count against any verb's budget ([SKILL.md](../../SKILL.md) Critical Rule 9). It ends only on § Asking rule 6.
6. **Each entry is asked where its answer is written.** `design`'s interview asks SDD entries only: a genome entry asked before the genome turn has nowhere to live. The genome turn (`author` from the SDD) offers the interview again for the genome entries still open.

## The Gap List

Build it from § Coverage against the source after the verb's extraction step. Classify each entry that applies to the scope:

| State | Means | Asked |
|---|---|---|
| **known** | the source, the SDD or the tenant states it | never |
| **assumption** | a default from a guide or the template is safe | only at P2, after P0 and P1 are done and the user continues |
| **needs confirmation** | the planner has a reading, and it changes what is built or what a business outcome is | yes |
| **missing** | no reading and no safe default | yes, first within its priority |

Give each entry asked:

- **Priority.** P0 changes the product, the scope or the architecture. P1 changes what the automation does: a business outcome, a decision, what a run does on a failure. P2 is a value that has a default.
- **Answerer**, one of: `process owner` (business outcomes, rules, exceptions), `SME` (how a step is done today, a reading), `system owner` (access route, accounts, test instance), `environment owner` (hosts, mailboxes, folders, schedules per environment), `engineer` (build-side facts), `tenant admin` (folders, robots, connections), `CoE` (organisation standards).
- **Default**: what is written when nobody answers, from the guide or template that sets it.
- **Home**: the section § Coverage names.

## Coverage

SDD homes use the RPA template's numbers; another product's template holds the same subject under its own heading. *Asked in*: **SDD** — `design`'s interview, or `author`'s with no SDD; **genome** — `author`'s interview, the genome turn included; **migration** — `extract`'s interview.

| Area | Ask when | Priority | Answerer | SDD home | Genome home | Asked in |
|---|---|---|---|---|---|---|
| Trigger and schedule | the source names no start, or two | P0 | process owner | § 1 Process Overview | Workflow step 1; Deployment | SDD |
| Volume, peaks, run window | no volume, or one that sits near a product threshold | P0 | process owner | § 1 Process Overview | Transactional Shape evidence | SDD |
| Judgement steps | a step decides over free text or varied documents and the source gives no rule | P0 | process owner | § 4 Business Rules, Rules That Need Reasoning | Business Rules | SDD |
| Human steps | an approval, review or sign-off with no actor, no outcomes or no wait limit | P0 | process owner | § 3 Step Details; § 7 | Actors and Systems; Workflow | SDD |
| Access route per system | no API, UI or file interface is known for an in-scope system | P0 | system owner | § 9 Application Inventory | Target Applications | SDD |
| Scope boundaries | in-scope and out-of-scope statements conflict, or a step's side is unstated | P0 | process owner | § 1 In Scope / Out of Scope | Overview | SDD |
| Inputs | where items come from or their format is unstated | P1 | SME | § 3; § 5 Data Definitions | Interface; Workflow | SDD |
| Outputs and recipients | what is written, sent or reported, or to whom, is unstated | P1 | process owner | § 3; § 5 | Workflow; Interface | SDD |
| Decisions and outcomes | a decision has an outcome with no next step | P1 | process owner | § 3 Step Details; § 4 Decision Tables | Workflow; Business Rules | SDD |
| Business rules | a threshold, validation or calculation is named but not stated | P1 | process owner | § 4 Business Rules | Business Rules | SDD |
| Business exceptions | an exception has no handling, or no one to tell | P1 | process owner | § 7 Exception Handling | Error Handling; Transactional Shape outcomes | SDD |
| Failure on a critical step | what a run does when a write, a payment or a send fails is unstated | P1 | process owner | § 8 Error Handling | Error Handling | SDD |
| Sharing and recovery | items may be shared across robots or must survive a failed run, and the source does not say | P1 | process owner | § 12 Queue Architecture | Transactional Shape evidence | SDD |
| Compliance, audit, retention | the domain implies a regulation and the source names none | P1 | process owner | § 1 Assumptions; § 4 | Business Rules | SDD |
| Accounts | which persona signs in to a system, when several are implied | P1 | system owner | § 15 Credentials & Assets | Platform Dependencies | SDD |
| Environments | dev, UAT and prod hosts, mailboxes, folders or schedules are unstated | P2 | environment owner | § 15; § 16 Deployment Environment | Configuration Questions defaults | SDD |
| Step detail | a step's screens, fields or composite interaction are needed at replication grade and the source does not give them | P1 | SME | — | Workflow substeps | genome |
| Values with no SDD home | a path, threshold or name the build needs that no SDD section holds | P2 | environment owner | — | Configuration Questions defaults | genome |
| Defect rulings | a source defect whose evident intent only the step's purpose shows | P1 | process owner | — | the step's `User ruling`; the defect index | migration |
| Open intent details | an evident intent leaves options open ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)) | P1 | process owner | — | the step | migration |
| Not covered and unused objects | the Source Map has a `Not covered` or `Unused` row | P1 | engineer | — | partial re-extraction ([edit-guide.md](../edit/edit-guide.md)) | migration |
| Values not in the export | a Configuration Question's default is "not in the export" | P2 | environment owner | — | the question's default | migration |

An Agent or Coded App gap stays the question of [scope-recommendation-guide.md](../design/scope-recommendation-guide.md) § Gap Handling for Agent / Coded App, asked in `design` Step 5; a Case design adds the entries [case-product-guide.md](../design/case-product-guide.md) sends to Step 6.

## The Offer

One structured question, with the counts from the gap list:

> The source leaves <N> points open: <P0> that change the design, <P1> that change what the automation does, <P2> values with defaults. Should I interview you on them before I write?
>
> 1. **Interview me** — I ask the open points by priority, a few at a time; you can stop or accept defaults at any point.
> 2. **Use defaults** — <the verb's own questions: `design` asks at most 5 clarifying questions; `author` its follow-up rounds; `extract` names the open rulings>.

Option 1 is Recommended when P0 is above zero or the source is thin (a sentence, a transcript with no step list); otherwise option 2.

## Asking

1. **Roles first.** One multi-select structured question: which of the gap list's answerer roles does the user answer for? Only those entries are asked. The question is skipped when every entry has one answerer.
2. **Order.** P0, then P1, then P2. Within a priority: missing before needs confirmation, then process order — trigger, steps, exceptions, environment.
3. **Batches.** At most 4 entries per structured question, at most 4 options each, the Recommended option first, the default named. Every batch offers "use defaults for the rest of this priority". A P0 batch is asked alone; the answers can change Step 4's product selection.
4. **New gaps.** An answer that opens a gap adds an entry to its priority's queue, asked in turn. An entry added after the last P1 batch takes its default.
5. **Unclear or partial answers.** Take the best reading, write it as the verb writes any gap (`[SME REVIEW]` in an SDD, `*[Inferred]*` in a genome) and move on; never ask the same entry twice.
6. **Stop** when the user says stop or accepts defaults for everything left, when the user's roles have no entry left, or when P0 and P1 are done and the user declines P2.
7. **What remains.** Close with one list of the entries still open, grouped by answerer, each with its default and home, so the user can forward each group. Their answers come back through `interview <file>`, or pasted into any later request, and go where § Where Answers Go says.

## Where Answers Go

- **Conflicts.** An answer outranks the source documents and the defaults ([design-guide.md](../design/design-guide.md) Verb Rule 11), never a platform or compliance constraint: an answer that breaks one is written as the constraint allows and named in the closing summary. In an extracted genome the source is the ground truth: an answer that changes a source behaviour is a ruling, written as one.
- **`design`.** Each answer is the fact the section in the Home column is written from in Phases 2–3, with no `[SME REVIEW]` for it. An answer that changes a product signal (a P0) reruns Phase 1 Step 4 before scope confirmation. Step 2 of [sdd-writing-guide.md](../design/sdd-writing-guide.md) adds one Document History row: `Interview: <n> points answered by <roles>; <n> left open`.
- **`author`.** Each answer is the fact Step 7 writes in its genome section. On a genome from an SDD, an answer to a point the SDD holds goes to the SDD instead (`design` revise), and the genome follows it ([sdd-writing-guide.md](../design/sdd-writing-guide.md) § Keeping the Genome Current).
- **`extract`.** Each answer is an edit of the written genome by its [edit-guide.md](../edit/edit-guide.md) row: a ruling, a step change, a partial re-extraction for a `Not covered` or `Unused` object, a question's default. The strict check runs after the last edit.
- **`interview <SDD>`.** The gap list is every `[SME REVIEW]` item of the SDD plus § Coverage's SDD entries with no content. Answers are a `design` revise: only the sections they touch change, the answered rows leave the Action Required table, the Document History row is added, Step 2 items 8 and 9 rerun, and a blocking item answered can flip `Status` to `ready`. A genome the `Genome` row names follows through § Keeping the Genome Current.
- **`interview <GENOME>`.** The gap list is every `*[Inferred]*` line, every source defect with no `User ruling`, every option an evident intent leaves open, every `Not covered` and `Unused` row and every Configuration Question whose default is "not in the export", plus § Coverage's genome entries with no content. On a genome with a `Designed in:` line, a point marked `(SDD [SME REVIEW]: …)` is answered in the SDD, as for `author`. Answers are edits ([edit-guide.md](../edit/edit-guide.md)), each removing its marker, then the strict check.
- **Unanswered entries** keep the marker and default the verb writes for any gap.
