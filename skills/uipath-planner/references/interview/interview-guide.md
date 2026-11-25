# Interview Guide — ask what is open, before and after the SDD or genome is written

The interview asks the user what the source leaves open. Before a document is written it asks only what changes the design, and writes each answer as content in the section that owns it; once it is written it asks the document's open items, and applies each answer as `edit` applies answers. It runs inside three verbs and as a verb of its own:

| Where | When it is offered | Gaps it asks | Answers go |
|---|---|---|---|
| `design` Phase 1 Step 6 ([design-guide.md](../design/design-guide.md)) | after the Phase 1 summary, before scope confirmation | the P0 SDD entries (§ Coverage, column *Asked in*) | SDD sections Phases 2–3 write this turn |
| `author` Step 6 ([author-guide.md](../author/author-guide.md)), with no agreed SDD | after extraction, before Step 7 generates | the P0 entries (§ Coverage) | genome sections Step 7 writes |
| `extract` Step 7 ([extract-guide.md](../extract/extract-guide.md)) | after the strict check | the written genome's open items (§ After Writing) | the written genome, as "Apply the answers" applies them ([edit-guide.md](../edit/edit-guide.md)) |
| `interview <SDD_OR_GENOME>` | on request, any later session | the document's open items (§ After Writing) | the same |

Declined, each verb runs its own questions. Every point not asked before writing is written as the verb writes any gap: an Open Decisions entry in the genome ([genome-format-guide.md § Open Decisions](../shared/genome-format-guide.md)), and an item of the SDD's Action Required where an SDD exists ([open-questions-guide.md](../shared/open-questions-guide.md)), with who answers it, what a blank costs and the step it rests on. The build's own questions — the split, the libraries, the technology for each capability, scaffolding, the build environment — are `uipath-genome`'s, asked at build or written by its `prepare` into the readiness file; the interview never writes them into the genome.

## Read Plan

Inside `design`, `author` and `extract`, that verb's § Read Plan opens this guide and every other file. The `interview` verb reads:

| Phase | Condition | Read |
|---|---|---|
| start | — | this guide whole; the document named and its companion, whole (the SDD beside a genome, the genome an SDD's `Genome` row names); [open-questions-guide.md](../shared/open-questions-guide.md) whole; [edit-guide.md](../edit/edit-guide.md) whole, whose § Read Plan names the rest |
| start | an SDD | [sdd-writing-guide.md](../design/sdd-writing-guide.md) § Gap Markers and § Keeping the Genome Current; where an answer revises it (a designed genome's SDD, or one with no genome on disk), also its Step 2 items 4, 8 and 9, and with no genome its Step 1.5 and Step 3 |
| start | a readiness file beside the genome | that file, whole |

## Verb Rules

These add to the Critical Rules in [SKILL.md](../../SKILL.md).

1. **Offered once per run, never imposed.** The offer is one structured question: before writing in `design` and `author` (§ The Offer), after the strict check in `extract` (§ After Writing). `author`'s closing names `interview <genome>` for what is still open and asks nothing. Not offered — gaps take their markers and defaults as the verb writes them — when: `Execution autonomy` is `autonomous`; the run carries a `planner-design-request: v1` block; the run is unattended; the gap list holds no entry to ask.
2. **Ask only what nothing else answers.** The source, the SDD, the tenant and the filesystem come first ([SKILL.md](../../SKILL.md) Anti-pattern 4). Every coverage entry is classified before anything is asked (§ The Gap List).
3. **Before writing, an answer is content, never a record.** It is written as the fact in the section that owns it, with no marker and no attribution. One exception: an SDD gets one Document History row per interview (§ Where Answers Go). After writing, an answer is to an item that has an id: its entry reads decided, so the genome keeps what was decided and when ([genome-format-guide.md § Open Decisions](../shared/genome-format-guide.md)).
4. **Later steps never ask again.** An answered point has no marker, so no later step finds it. A point the interview left open — put to the user and skipped or defaulted, or held for an absent role — is written as an item and not asked again in the run: `design` Phase 3 Step 1.5 asks only the other items of the user's roles ([sdd-writing-guide.md](../design/sdd-writing-guide.md)), and `author` Step 8 and `extract`'s close name the open items without asking them.
5. **No round cap.** The user accepted the interview, so its rounds do not count against any verb's budget ([SKILL.md](../../SKILL.md) Critical Rule 9). It ends only on § Asking rule 6.
6. **Only what changes the design is asked before writing.** The P0 entries: the product, the scope and the architecture follow from them, so a later answer would mean writing again. A P1 or P2 point is asked once its step is written, where its item can point at that step and go to whoever answers it, even when it concerns the same step as a P0 point. Each entry is asked where its answer is written: `design`'s interview asks SDD entries only, since a genome entry asked before the genome turn has nowhere to live.

## The Gap List

Before writing, build it from § Coverage against the source after the verb's extraction step. Classify each entry that applies to the scope:

| State | Means | Asked before writing |
|---|---|---|
| **known** | the source, the SDD or the tenant states it | never |
| **assumption** | a default from a guide or the template is safe, and no P0 row of § Coverage holds | never: written with its default |
| **needs confirmation** | the planner has a reading, and it changes what is built or what a business outcome is | when it is P0 |
| **missing** | no reading and no safe default | when it is P0, first |

Give each entry:

- **Priority.** P0 changes the product, the scope or the architecture. P1 changes what the automation does: a business outcome, a decision, what a run does on a failure. P2 is a value that has a default.
- **Answerer**, one of the roles an entry names ([genome-format-guide.md § Open Decisions](../shared/genome-format-guide.md)): `the process owner` (business outcomes, rules, exceptions, scope), `whoever knows the process` (how a step is done today, a reading), `whoever holds the source` (an object or file the build needs), `the system's owner` (access route, accounts, test instance), `the environment's owners` (hosts, mailboxes, folders, schedules per environment), `the delivery lead or the centre of excellence` (organisation standards).
- **Default**: what is written when nobody answers, from the guide or template that sets it.
- **Home**: the section § Coverage names.

## Coverage

SDD homes use the RPA template's numbers; another product's template holds the same subject under its own heading. *Asked in*: **SDD** — before writing when P0, by `design`'s interview or `author`'s with no SDD; **genome** and **migration** — after writing, as an item of an authored or an extracted genome.

| Area | Ask when | Priority | Answerer | SDD home | Genome home | Asked in |
|---|---|---|---|---|---|---|
| Trigger and schedule | the source names no start, or two | P0 | the process owner | § 1 Process Overview | Workflow step 1; Deployment | SDD |
| Volume, peaks, run window | no volume, or one that sits near a product threshold | P0 | the process owner | § 1 Process Overview | Transactional Shape evidence | SDD |
| Judgement steps | a step decides over free text or varied documents and the source gives no rule | P0 | the process owner | § 4 Business Rules, Rules That Need Reasoning | Business Rules | SDD |
| Human steps | an approval, review or sign-off with no actor, no outcomes or no wait limit | P0 | the process owner | § 3 Step Details; § 7 | Actors and Systems; Workflow | SDD |
| Access route per system | no API, UI or file interface is known for an in-scope system | P0 | the system's owner | § 9 Application Inventory | Target Applications | SDD |
| Scope boundaries | in-scope and out-of-scope statements conflict, or a step's side is unstated | P0 | the process owner | § 1 In Scope / Out of Scope | Overview | SDD |
| Inputs | where items come from or their format is unstated | P1 | whoever knows the process | § 3; § 5 Data Definitions | Interface; Workflow | SDD |
| Outputs and recipients | what is written, sent or reported, or to whom, is unstated | P1 | the process owner | § 3; § 5 | Workflow; Interface | SDD |
| Decisions and outcomes | a decision has an outcome with no next step | P1 | the process owner | § 3 Step Details; § 4 Decision Tables | Workflow; Business Rules | SDD |
| Business rules | a threshold, validation or calculation is named but not stated | P1 | the process owner | § 4 Business Rules | Business Rules | SDD |
| Business exceptions | an exception has no handling, or no one to tell | P1 | the process owner | § 7 Exception Handling | Error Handling; Transactional Shape outcomes | SDD |
| Failure on a critical step | what a run does when a write, a payment or a send fails is unstated | P1 | the process owner | § 8 Error Handling | Error Handling | SDD |
| Sharing and recovery | items may be shared across robots or must survive a failed run, and the source does not say | P1 | the process owner | § 12 Queue Architecture | Transactional Shape evidence | SDD |
| Compliance, audit, retention | the domain implies a regulation and the source names none | P1 | the process owner | § 1 Assumptions; § 4 | Business Rules | SDD |
| Accounts | which persona signs in to a system, when several are implied | P1 | the system's owner | § 15 Credentials & Assets | Platform Dependencies | SDD |
| Environments | dev, UAT and prod hosts, mailboxes, folders or schedules are unstated | P2 | the environment's owners | § 15; § 16 Deployment Environment | Configuration Questions defaults | SDD |
| Step detail | a step's screens, fields or composite interaction are needed at replication grade and the source does not give them | P1 | whoever knows the process | — | Workflow substeps | genome |
| Values with no SDD home | a path, threshold or name the build needs that no SDD section holds | P2 | the environment's owners | — | Configuration Questions defaults | genome |
| Defect rulings | a source defect whose evident intent only the step's purpose shows | P1 | the process owner | — | the step's `User ruling`; the defect index | migration |
| Open intent details | an evident intent leaves options open ([extracted-genome-guide.md § Source Defects](../shared/extracted-genome-guide.md)) | P1 | the process owner | — | the step | migration |
| Not covered and unused objects | the Source Map has a `Not covered` or `Unused` row | P1 | the process owner | — | partial re-extraction ([edit-guide.md](../edit/edit-guide.md)) | migration |
| Values not in the export | a Configuration Question's default is "not in the export" | P2 | the environment's owners | — | the question's default | migration |

An Agent or Coded App gap stays the question of [scope-recommendation-guide.md](../design/scope-recommendation-guide.md) § Gap Handling for Agent / Coded App, asked in `design` Step 5; a Case design adds the entries [case-product-guide.md](../design/case-product-guide.md) sends to Step 6, as P0.

## The Offer

Before writing, one structured question, with the counts from the gap list — of the user's roles' entries alone when the request names them:

> The source leaves <P0> points open that change the design: <what they decide, in a few words>. Should I ask them before I write? Everything else — <the other open points, and other roles', in a few words> — I write as questions in the <SDD | genome>, each with who answers it and what is built until then.
>
> 1. **Interview me** — I ask those points, a few at a time; you can stop or accept defaults at any point.
> 2. **No interview** — <the verb's own questions: `design` asks at most 5 clarifying questions; `author` its follow-up rounds>, then defaults for the rest.

Option 1 is Recommended. Before writing, a request that asks to be interviewed has chosen it: the offer's text is stated without its question and options, so the user knows what waits until after writing, and the first batch follows. After writing, the offer is § After Writing's first question, which a request to be interviewed does not answer.

## Asking

1. **Roles first.** One multi-select structured question: which of the gap list's answerer roles does the user answer for? Only those entries are asked: a process owner is asked which system the work runs in, never how a robot reaches it, which is the system's owner's. The question is skipped when the entries name one answerer between them, or the request names the user's roles.
2. **Order.** Before writing: missing before needs confirmation, then process order. After writing: § After Writing.
3. **Batches.** One prompt holds at most 4 questions, one entry each, with at most 4 options, the Recommended option first (with none recommended, the one built now first), the default named. While entries remain after a batch, its fourth question offers "use the defaults for the rest" (after writing, the rest of the group). A batch before writing is asked alone; its answers can change the verb's product selection.
4. **New gaps.** An answer that opens a gap adds an entry: before writing, a P0 one is asked in turn and any other is written as an item; after writing, it is a new entry at the end of the genome's Open Decisions, with its default ([open-questions-guide.md](../shared/open-questions-guide.md) § Where Answers Go).
5. **Unclear or partial answers.** Take the best reading, write it as the verb writes any gap (`[SME REVIEW]` in an SDD, `*[Inferred: D<n>]*` in a genome) and move on; never ask the same entry twice.
6. **Stop** when the user says stop or accepts defaults for everything left, or when the user's roles have no entry left.
7. **What remains.** The closing summary counts the items still open by role, and says how each reaches whoever answers it: an SDD item reaches its answerer in the SDD; with no SDD, the summary offers to write it ([edit-guide.md](../edit/edit-guide.md), "Write the SDD") whenever an open item's answerer is not in the session; the readiness file carries the build's own questions. Their answers come back through `interview <file>`, the filled-in SDD, or a reply pasted into any later request.

## After Writing

The gap list is the document's open items: the SDD's Action Required, or, for a genome with no SDD beside it, the open entries of its Open Decisions in the item form of [open-questions-guide.md](../shared/open-questions-guide.md) under their genome ids; plus, when a readiness file is beside the genome, each of its items with a blank `Answer:`, the build's own questions included, an entry it lists under Decisions still open asked once and answered there; its tasks (`Status:`) are named in the closing, never asked. A genome's Configuration Questions are asked only where a file keeps the answer for the build: its SDD's Configuration values, or the readiness file's Decisions still open; with neither, the build asks them. An item the request, an answers file, the preferences file or its own answer already settles is never asked.

1. **How to answer.** One structured question comes first, skipped when the request already says. Inside `extract`, where it is the offer, "not now" takes the place of its last option and leaves every item open. Its options:
   - every item, a batch at a time (Recommended when an item has no default);
   - only what needs a decision: the items with no default and the business outcomes, the rest keeping their defaults;
   - the defaults: a value item is answered `default`, and a choice stays open, built as marked, since a default nobody confirmed decides nothing;
   - the defaults, with the overrides the user names.
2. **Roles**, as § Asking rule 1, from each item's `Answer (by <role>):` line or entry's `answered by:`, a readiness item's from its section's "Usually answered by" line, whose roles (the engineer, the architect) the question lists with the genome's.
3. **Order.** Items with no default come first. Then the business outcomes, run behaviours, readings, material and configuration values, each group in step order.
4. **Batches** as § Asking rule 3, one question per item, its options from the item's `Options:` and a value item's `Default:` named. An item with one option is asked with "something else, in your words" beside it, never with an option the item lacks.
5. **Write, then apply.** Each answer goes after its item's `Answer` in the file that holds it — the option's letter, a value, or `default`, alone or for the rest of a group — and for a genome with neither an SDD nor a readiness file is held for the edit. Then, in the same turn and with no request for it, apply them to the genome as [edit-guide.md § Applying the Answers](../edit/edit-guide.md) states, and run the strict check after the last edit: the interview's result is the files edited, and a request not to build stops only the build; an SDD with no genome yet takes them as § Where Answers Go states.

## Where Answers Go

- **Conflicts.** An answer outranks the source documents and the defaults, never a platform or compliance constraint or tenant evidence ([design-guide.md](../design/design-guide.md) Verb Rule 11): an answer that breaks one is written as the constraint or the evidence allows and named in the closing summary. In an extracted genome the source is the ground truth: an answer that changes a source behaviour is a ruling, written as one.
- **`design`.** Each answer is the fact the section in the Home column is written from in Phases 2–3, with no `[SME REVIEW]` for it. An answer that changes a product signal reruns Phase 1 Step 4 before scope confirmation. The SDD's Document History gets one row ([sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 1): `Interview: <n> points answered by <roles>; <n> left open`.
- **`author`.** Each answer is the fact Step 7 writes in its genome section. An answer that changes a product signal reruns Step 5 first.
- **After writing** — `extract`, and `interview <SDD_OR_GENOME>`. Each answer is applied as its item's row of [edit-guide.md § Applying the Answers](../edit/edit-guide.md): a ruling, a step change, a partial re-extraction for a `Not covered` or `Unused` object, an answered reading; on a genome with a `Designed in:` line, an item taken from the SDD's own design is a `design` revise first. Its entry reads decided, and an SDD beside the genome is written again from it. An SDD answered this way gets the Document History row too.
- **An SDD with no genome yet** (its `Genome` handoff row names none on disk). Each answer is a `design` revise: the section that holds its subject states it, its marker goes, and its item leaves Action Required; an item answered `default` stays, default-carried ([sdd-writing-guide.md](../design/sdd-writing-guide.md) Step 1.5). The Document History row is added, Step 2 items 8 and 9 run again, and a `draft` whose blocking items are all answered flips to `ready`. The genome follows on the next turn (its Step 3).
- **Unanswered entries** stay items, with the marker and default the verb writes for any gap.
