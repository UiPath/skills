# Caller Request Guide — `design` run for a calling skill

Read this when the request carries a `planner-design-request: v1` block. Another skill has already held the business conversation (a business-analysis skill that wrote the PDD) and settled with the user what the block states. Take those answers as given, run `design` with the changes below, and end with one result block. Ask the user nothing the block answers, and expose none of this skill's guides, phases or templates in what you show them. A change to a field, to the result or to the SDD signals below bumps the version.

A build skill that hands over a request with no SDD to build from is a different case: [sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill.

## The Request

Read the block one `key: value` per line:

```text
planner-design-request: v1
source: <PDD_PATH>
facts: <PATH>, <PATH>
output: <SDD_PATH>
product: <PRODUCT>
language: <LANGUAGE>
audience: business
open-item-marker: <LITERAL_PREFIX>
existing-output: replace
stop-after: sdd
client-template: <TEMPLATE_DOCX_PATH>
client-output: <CLIENT_DOCX_PATH>
revise: <SECTION_HEADING> — <CHANGE>
```

| Key | Required | What to do with it |
|---|---|---|
| `source` | yes | Read it as the PDD or process source in Phase 1 Step 1. |
| `output` | yes | Write the SDD here. Solution scope: write the overview here and each per-project SDD beside it as `<PROJECT_NAME_KEBAB>-sdd.md`. |
| `facts` | no | Comma-separated files or folders of facts the user confirmed. Read them after the source and rank them as "what the user said" in Verb Rule 11, above the source document and every default. Never ask what they answer. |
| `product` | no | The product the user chose: `case`, `bpmn`, `flow`, `rpa`, `agent`, `coded-app`, `api-workflow`. Treat it as a product the user named (Verb Rule 12). `automation-task` names no product: the scope is one bounded task, so select the product at Level 1 as usual. |
| `language` | no | Write the SDD's prose in it and skip the Phase 1 Step 1 language question. Keep headings, section numbers, identifiers (`BR-01`, `E1`) and handoff fields in English: build skills parse them verbatim. |
| `audience` | no | `business` → word every question, the review and the result's prose in the user's business terms: no verb, guide, file path, template, `[SME REVIEW]`, `[DEFAULT]`, genome or handoff field names. Default `technical`. |
| `open-item-marker` | no | The literal prefix the source uses for an open item (`==TBD:`). Turn each occurrence into one `[SME REVIEW]` item and put the source's reason after the closing bracket (`[SME REVIEW] retention period not confirmed`). Never copy the source's marker into the SDD. This is the one exception to Critical Rule 6's byte-for-byte carry-over: the gap is kept, only its vocabulary changes. |
| `existing-output` | no | `replace` → regenerate without the sdd-writing-guide.md Step 2 item 6 question; the user already chose to. Without it, ask that question as usual. |
| `stop-after` | no | `sdd` → end the run at the result: no genome, no build, no Step 3 turn boundary, no genome progress task. Without it, § Chaining in [SKILL.md](../../SKILL.md) applies. |
| `client-template`, `client-output` | no, together | Once the SDD is finished, produce the client Word document: [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) from its step 2, with this template, written to `client-output`. Never ask for the template. |
| `revise` | no | Change one section of the existing `output` SDD: skip Phases 1 and 2, apply the change to that section only, run sdd-writing-guide.md Step 2 items 8 and 9, then write the result. A change that moves a process fact belongs in the source, and the request then comes without `revise`. |

Ignore a key you do not know. A missing required key, an unreadable `source`, or a `revise` with no `output` on disk → write the result with `status: failed` and the reason, and nothing else.

## The Run

The user is present in this session: ask in the host's own question tool, and do any subagent work inline. Change these steps and nothing else:

1. **Phase 1 Step 0.** Do not ask the execution mode: record `Execution autonomy: interactive`. Ask the delivery model only when its skip rule cannot resolve it from `source` and `facts`.
2. **Phase 1 Step 6.** Present the scope recommendation only when no `product` was given and the choice is genuinely ambiguous (product-selection-guide.md); otherwise take the recommendation and record it in Decisions Made.
3. **Phase 2 Step 5 — the one review.** Always present the architecture review and wait for approval, in its own structure (a case: case-review-and-conformance-guide.md § Presenting the Case Design). It is the run's only checkpoint.
4. **Phase 3 Step 1.5.** Ask nothing. Keep every item's default and class in the Action Required table; a `blocking` item keeps `Status: draft` — name it in the result, where the user's answer comes back through a later request.
5. **Decisions Made.** Write the block (sdd-writing-guide.md Step 2 item 3), as in autonomous mode: the decisions you took without a question must stay scannable.
6. **End.** Write the result below. With `stop-after: sdd`, end the run there, in the same turn; otherwise § Chaining applies.

Still ask the Agent / Coded App gap question (Phase 1 Step 5): never fill a product gap silently.

## The Result

Make your last message one fenced block, after any prose the audience needs:

```text
planner-design-result: v1
status: ready | draft | failed
complete: yes | no
documents: <PRIMARY_SDD_PATH>, <PER_PROJECT_SDD_PATH>, ...
blocking: <ITEM>; <ITEM> | none
client-document: <CLIENT_DOCX_PATH> | none | unavailable — <REASON>
reason: <WHY_IT_FAILED>
```

- Write `complete: yes` only when `Template validation: passed` — every required section is present. A `draft` can be complete: it waits on `blocking`.
- List the overview first in `documents`; a single-product SDD has one path.
- Word `blocking` in the audience's terms.
- Write `reason` only with `status: failed`.

## SDD Signals a Caller's Host May Read

Write these into every SDD, and change them only with a version bump — the calling skill's host reads them to register the SDD:

| Signal | Meaning |
|---|---|
| `<!-- planner-handoff:v1 -->` and `## Planner Handoff` | The file is a planner SDD. |
| `\| **Template validation** \| pending \|` | The run did not finish; the file must not be presented as a finished design. |
| `\| **Status** \| draft \|` | Blocking review items are open. |
| `<!-- planner-sdd-body:v1 -->` | Every H2 above this line is front matter (history, handoff, decisions, review items, table of contents); the body starts below it. |
