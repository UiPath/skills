---
# Front-matter = metadata ABOUT the command (YAML). Every field is optional.
description: Classify agent skills into Strong, Partial, and None
# Usage hint shown inline as you type:  <required>  [optional]
argument-hint: "[path-to-skill], [output-path]"
# Tool allowlist: this command may ONLY use these tools. Scoped tight for safety.
# Remove this line to inherit your session's normal tool permissions.
allowed-tools: Read(skills/*), Read(tmp/*) Glob(*), Grep(*), Bash(*), Write(tmp/*), Edit(tmp/*)
# Optional: pin a model. Omit to use the session's current model.
# model: claude-sonnet-4-6
---

## Context

You need to reduce the cost of using coding agents by reducing the total number of turns it takes to complete a task. Your approach is to find out any codifiable procedures in skills where you can turn these procedures into scripts and complete these procedures in less turns. The reason is that a script bundles multiple turns into one script call.

The skills path is `$1`. The path is either a parent path that contains multiple skills or a single skill's path. Each skill has a SKILL.md with optional references/, scripts/, assets/, etc. If it has multiple skills, create a sub-folder for each skill to store the output.

The output path is `$2`.


## Step 1: Find codifiable procedures

For each skill, read its SKILL.md and optional files to find out any deterministic, repeatable thing the SKILL.md makes the agent do. If no such procedure exists, the skill is not script-ify-able. Don't include the skill's own scripts (CLI commands count as well) as part of the codifiable procedures. If a skill has been fully scripted by itself, then the skill should be classified as None.

Also check the skill's existing scripts. If the skill directs the agent to run two or more of those scripts in a fixed sequence with no AI judgment required between them, that sequence is itself an unscripted TRANSFORM-PIPELINE (orchestration opportunity) — record it as a codifiable procedure even though the individual steps are already scripted.

Some examples (not limited to these) of codifiable procedures are as follows:

- **PARSE** — read a file/format into structured data (binary formats, XML/JSON/CSV, domain files, source → AST). Deterministic reader, one correct output.
- **COMPUTE/FORMULA** — a closed-form calculation with fixed constants (a stated equation, a scoring formula, a coefficient table applied, a metric, an encoding). Codify only when the formula and all constants are given.
- **TRANSFORM-PIPELINE** — a fixed ordered sequence of operations (a preprocessing/signal chain, a documented multi-step recipe, a rewrite driven by a fixed mapping).
- **LOOKUP/REFERENCE-TABLE** — map a key to a value from a table the skill provides (thresholds, conventions, command/flag references, category mappings).
- **VALIDATE/CHECK** — test inputs or outputs against explicit rules and return pass/fail (bounds, invariants, feasibility rules, round-trip consistency, error scans). Best shipped as an independent audit script.
- **FORMAT-CONVERT** — convert one format to another with no judgment on content (document↔text/markdown, pack/unpack, serialize to a fixed schema, template fill).
- **BUILD-MODEL/MATRIX** — assemble inputs into a standard model object or matrix from a given construction rule. Codify the mechanical scaffolding, not the formulation choice.
- **EXTRACT** — locate and pull a specific item from a larger artifact (a field, a position, metadata, a value from a solved model).
- **AGGREGATE/STATS** — reduce many rows to a summary metric (counts, resampling, regression/trend, decomposition, response metrics).
- **DETECT** — rule-thresholded classification, only when the thresholds are given in the skill (flag a condition when explicit numeric criteria hold).

## Step 2: Classify a skill

Based on your findings and how many things a skill teaches the agent to do, classify a skill into one of Strong, Partial, and None. 

For example, if a skill teaches the agent the following things: open a browser, extract a block from html, extract response header from a request, find out the request that takes the longest time, and search for certain texts, and 4 of them can be scripted, then the skill is Strong.

Compare the procedures you found with things the skill teaches:

- Strong: If the procedures take up half of the things a skill teaches
- Partial: If the procedures take up less than half of the things a skill teaches
- None: the skill doesn't have any codifiable procedures

## Step 3: Write your classification

Output two files. When classifying a single skill, append `-<skill-name>` to each filename (e.g., `classification-details-uipath-maestro-bpmn.md`).

### classification.json

Keys are the class labels (`Strong`, `Partial`, `None`); values are arrays of skill names.

```json
{
  "Strong": ["uipath-foo"],
  "Partial": ["uipath-bar"],
  "None": ["uipath-baz"]
}
```

### classification-details.md

Use **exactly** this structure for every skill (one skill = one file):

```
# Classification Details — <skill-name>

**Classification: <Strong|Partial|None>**

---

## What the Skill Teaches

<one sentence summary of the skill's scope>

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | <area description> | No | <reason> |
| 2 | **<area description>** | **Yes — <TYPE>** | <reason> |
…

---

## Codifiable Procedures (not yet scripted)

### 1. <Procedure name> — <TYPE>

**Source:** `<path/to/reference.md>` §<Section name>

**What it does:** <2–4 sentences: inputs → outputs, what is parsed/computed/validated. Close with a direct quote of the skill's own wording — not a paraphrase, and not an inference drawn from the skill's scripts — showing exactly where that description comes from, e.g. `Line 26: "Run local validation for XML, diagrams, entry point IDs, variables, mappings, binding references, and package metadata drift."`>

**Why it's mechanical:** <1–2 sentences: why no judgment is required>

**Turn savings:** <1 sentence: what the agent currently does without the script and how many turns it takes>

---

### 2. …

---

## Justification for Classification

**<Label>** — not <other label>, not <other label>.

**Why not Strong:** <reason the codifiable procedures don't dominate the skill>

**Why not None:** <reason at least one codifiable procedure exists>

**Evidence locations:**
- <finding>: `<file>` §<section>
- …
```

Formatting rules:
- In the "What the Skill Teaches" table, **bold** the entire row (Area cell and Codifiable? cell) for every Yes row.
- `Codifiable?` values: `No`, `**Yes — <TYPE>**`, or `Marginal` (use Marginal when a procedure is theoretically scriptable but too small or low-value to warrant a standalone script).
- List only procedures that are **not yet scripted** under "Codifiable Procedures". If a procedure is already scripted, note it as "Already scripted" in the table Notes column and omit it from the procedures section.
- `TYPE` must be one of the taxonomy labels from Step 1 (PARSE, COMPUTE/FORMULA, TRANSFORM-PIPELINE, LOOKUP/REFERENCE-TABLE, VALIDATE/CHECK, FORMAT-CONVERT, BUILD-MODEL/MATRIX, EXTRACT, AGGREGATE/STATS, DETECT).
- Every **What it does** must be traceable to a verbatim quote from the skill's own SKILL.md or reference file (`Line <N>: "<exact text>"`), not a paraphrase and not something inferred from reading the skill's scripts. A skill's scripts can implement less than what the skill's own docs describe — porting or summarizing from the script alone will silently inherit that gap. Read the actual reference file the procedure is scoped to (not just the script that happens to exist for it) before writing "What it does."
- "Justification for Classification" must always have all three subsections (Why not Strong, Why not None, Evidence locations), even for Strong or None classifications — adapt the language accordingly (e.g., for None: "Why not Strong: no codifiable procedures exist"; "Why not None: N/A — this skill is classified None").