# Classification Details — uipath-planner

**Classification: Partial**

---

## What the Skill Teaches

Turns a Process Design Document (PDD) or multi-project request into an implementation-ready Solution Design Document (SDD) and a task list, routing design lanes and emitting live TaskCreate calls.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Entry Guard routing (classify input, select lane) | **Yes — DETECT** | Explicit rule tree with deterministic signals (marker presence, keyword phrases, document structure) |
| 2 | Phase D — SDD design and architecture | No | Requires product selection judgment, constraint interpretation, and business-gap resolution |
| 3 | **Lane A — SDD header parsing and handoff field extraction** | **Yes — PARSE** | Reads `## Planner Handoff` marker + structured header fields with fixed schema |
| 4 | **Lane A — Task derivation from SDD project list** | **Yes — TRANSFORM-PIPELINE** | Fixed sequence: read SDD → parse project list → pick pattern → derive tasks → write tasks.md → emit TaskCreate |
| 5 | Phase D — template section superset check | **Yes — VALIDATE/CHECK** | Diff generated H2/H3 headings against template TOC; generated set must be a superset |
| 6 | Lane B — Non-PDD elicitation and plan writing | No | Open-ended preference elicitation; project-type inference uses judgment |
| 7 | docx PDD extraction | No | Already scripted via `scripts/docx-extract.{sh,ps1}` |

---

## Codifiable Procedures (not yet scripted)

### 1. Entry Guard — DETECT

**Source:** `skills/uipath-planner/SKILL.md` §Entry Guard

**What it does:** Classifies the input (document path, content type, marker presence, keyword phrases) and routes to Phase D, Lane A, or Lane B using a rule tree with explicit branch conditions. Inputs are the user message and, optionally, the first ~50 lines of a document. Output is one of three lane assignments. Line 79: "Contains `## Planner Handoff` OR `<!-- planner-handoff:v1 -->` → Lane A — PDD-driven. (Either signal alone is sufficient — redundant on purpose.)"

**Why it's mechanical:** All branch conditions are explicit and deterministic — marker presence is a text search, keyword phrases are enumerated, and the fallback is a fixed `AskUserQuestion` prompt. No judgment is required to fire the correct lane.

**Turn savings:** Without a script the agent re-reads and re-evaluates the guard logic from SKILL.md on every invocation; a script returns the lane label and detected signals in one call.

---

### 2. SDD Planner Handoff header parsing — PARSE

**Source:** `skills/uipath-planner/SKILL.md` §Lane A — PDD-driven (summary)

**What it does:** Reads the `## Planner Handoff` section of an SDD file and extracts structured fields (Status, Execution autonomy, Delivery model, SDD scope, Solution root, Project list, Tasks file, Generation date, Template validation). Output is a structured object used to decide whether to proceed with task derivation. Line 115: "Read the SDD's `## Planner Handoff` header. **`Status: draft` → refuse task derivation**"

**Why it's mechanical:** The header schema is fixed and fully documented; field extraction is a deterministic text parse with no interpretation.

**Turn savings:** The agent currently reads the header as free-text in one turn and then re-checks fields in subsequent turns; a parser returns all fields in one call with typed validation.

---

### 3. Template section superset validation — VALIDATE/CHECK

**Source:** `skills/uipath-planner/SKILL.md` §Critical Rules (Rule 6)

**What it does:** Diffs the H2/H3 headings of a generated SDD against the required headings from the applicable template TOC and reports any missing required sections. Takes the generated SDD file path and template path as inputs; outputs pass/fail plus a list of missing headings. Line 42: "After writing, diff the generated H2/H3 headings against the template TOC — the generated set MUST be a superset. A missing template-required H2/H3 is an SDD defect, not an `[SME REVIEW]` item — regenerate it."

**Why it's mechanical:** Heading extraction is a fixed regex over Markdown; set-membership comparison has no judgment.

**Turn savings:** Currently the agent re-reads both files and compares headings manually; a script produces pass/fail in one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The dominant activity of this skill is authoring the SDD (Phase D) — selecting product scope via the Product Selection Guide decision tree, writing architecture sections, resolving business gaps — and writing the Lane B plan via open-ended elicitation. Both are heavily judgment-driven. The codifiable procedures (Entry Guard, header parse, superset check) are gating and verification steps rather than the core teaching of the skill.

**Why not None:** The Entry Guard is a fully deterministic rule tree, the Planner Handoff header has a fixed schema that is parseable, and the template superset check is a pure set-membership test — all are codifiable without AI judgment.

**Evidence locations:**
- Entry Guard rule tree: `skills/uipath-planner/SKILL.md` §Entry Guard
- Planner Handoff schema and detection contract: `skills/uipath-planner/SKILL.md` §Critical Rules Rule 5, §Lane A
- Template superset requirement: `skills/uipath-planner/SKILL.md` §Critical Rules Rule 6
- Judgment dominance (Phase D): `skills/uipath-planner/SKILL.md` §Phase D — Design (summary), §Critical Rules Rules 3, 7, 10
