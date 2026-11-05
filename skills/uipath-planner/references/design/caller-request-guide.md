# Caller Request Guide — `design` run for a calling skill

A skill that owns the business conversation (a business-analysis skill that wrote the PDD) hands `design` one request and takes back one result. The caller knows nothing else about this skill: its guides, phases, templates and questions stay internal. This guide is the whole contract; a change to a field, to the result or to the SDD signals below bumps its version.

A build skill that finds no SDD to build from is a different caller: [sdd-writing-guide.md](sdd-writing-guide.md) § Design Handed Over by a Build Skill.

## The Request

The caller's message carries one fenced block whose first line is `planner-design-request: v1`, one `key: value` per line:

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

| Key | Required | Meaning |
|---|---|---|
| `source` | yes | The PDD or process source `design` reads in Phase 1 Step 1. |
| `output` | yes | The SDD path. Solution scope writes the overview here and each per-project SDD beside it as `<PROJECT_NAME_KEBAB>-sdd.md`. |
| `facts` | no | Comma-separated files or folders of facts the user confirmed with the caller. They rank as "what the user said" in Verb Rule 11, above the source document and every default. Read them after the source; never ask what they answer. |
| `product` | no | The product the user chose: `case`, `bpmn`, `flow`, `rpa`, `agent`, `coded-app`, `api-workflow`. It is a product the user named (Verb Rule 12). `automation-task` names no product: it says the scope is one bounded task, and Level 1 still selects. |
| `language` | no | The SDD's prose language. Skip the Phase 1 Step 1 language question. Headings, section numbers, identifiers (`BR-01`, `E1`) and handoff fields stay English: build skills parse them verbatim. |
| `audience` | no | `business` → every question, the review and the result's prose use the caller's business terms: no verb, guide, file path, template, `[SME REVIEW]`, `[DEFAULT]`, genome or handoff field names. Default `technical`. |
| `open-item-marker` | no | The literal prefix the source uses for an open item (`==TBD:`). Each occurrence is one `[SME REVIEW]` item; the source's reason follows the closing bracket (`[SME REVIEW] retention period not confirmed`). The caller's marker never reaches the SDD. This is the one exception to Critical Rule 6's byte-for-byte carry-over: the source states a gap in another vocabulary, and the item is kept, not re-worded. |
| `existing-output` | no | `replace` → regenerate without the sdd-writing-guide.md Step 2 item 6 question; the caller already asked the user. Default: that question runs. |
| `stop-after` | no | `sdd` → the run ends at the result: no genome, no build, no Step 3 turn boundary, no genome progress task. The caller continues in the same turn. Default: § Chaining in [SKILL.md](../../SKILL.md). |
| `client-template`, `client-output` | no, together | Produce the client Word document after the SDD is finished: [asdd-crosswalk-guide.md](asdd-crosswalk-guide.md) from its step 2, with this template, written to `client-output`. Never ask for the template. |
| `revise` | no | Change one section of the existing `output` SDD: skip Phases 1 and 2, apply the change to that section only, then run sdd-writing-guide.md Step 2 items 8 and 9 and return the result. A change that moves a process fact belongs in the source; the caller regenerates instead. |

An unknown key is ignored. A missing required key, an unreadable `source`, or a `revise` with no `output` on disk → the result with `status: failed` and the reason; nothing is written.

## The Run

The user is present in the caller's host; questions use the host's structured question. The request changes these steps and nothing else:

1. **Phase 1 Step 0.** No execution-mode question: record `Execution autonomy: interactive`. The delivery model is asked only when its skip rule does not resolve it from `source` and `facts`.
2. **Phase 1 Step 6.** Present the scope recommendation only when no `product` was given and the choice is genuinely ambiguous (product-selection-guide.md); otherwise take the recommendation and record it in Decisions Made.
3. **Phase 2 Step 5 — the one review.** Always present the architecture review and wait for approval, in its own structure (a case: case-review-and-conformance-guide.md § Presenting the Case Design). This is the run's only checkpoint.
4. **Phase 3 Step 1.5.** Ask nothing. Every item keeps its default and its class in the Action Required table; a `blocking` item keeps `Status: draft` and is named in the result for the caller to resolve with the user.
5. **Decisions Made.** Emit the block (sdd-writing-guide.md Step 2 item 3), as in autonomous mode: the decisions taken without a question must stay scannable.
6. **End.** Write the result below. With `stop-after: sdd` the run ends there in the same turn; otherwise § Chaining applies.

The Agent / Coded App gap question (Phase 1 Step 5) still runs: a product gap is never filled silently.

## The Result

The run's last message is one fenced block, after any prose the audience needs:

```text
planner-design-result: v1
status: ready | draft | failed
complete: yes | no
documents: <PRIMARY_SDD_PATH>, <PER_PROJECT_SDD_PATH>, ...
blocking: <ITEM>; <ITEM> | none
client-document: <CLIENT_DOCX_PATH> | none | unavailable — <REASON>
reason: <WHY_IT_FAILED>
```

- `complete: yes` iff `Template validation: passed` — every required section is present. A `draft` can be complete: it waits on `blocking`.
- `documents` lists the overview first; a single-product SDD lists one path.
- `blocking` is in the audience's terms.
- `reason` only with `status: failed`.

## SDD Signals a Caller's Host May Read

Every SDD carries these, and they change only with a version bump:

| Signal | Meaning |
|---|---|
| `<!-- planner-handoff:v1 -->` and `## Planner Handoff` | The file is a planner SDD. |
| `\| **Template validation** \| pending \|` | The run did not finish; the file must not be presented as a finished design. |
| `\| **Status** \| draft \|` | Blocking review items are open. |
| `<!-- planner-sdd-body:v1 -->` | Every H2 above this line is front matter (history, handoff, decisions, review items, table of contents); the body starts below it. |
