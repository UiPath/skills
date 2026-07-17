---
# Front-matter = metadata ABOUT the command (YAML). Every field is optional.
description: Convert agent skills into runnable scripts
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

The skills path is `$1`. The path is either a parent path that contains multiple skills or a single skill's path. Each skill has a SKILL.md with optional references/, scripts/, assets/, etc. 

The output path is `$2`.


## Step 1: Find codifiable procedures

For each skill, read its SKILL.md and optional files to find out any deterministic, repeatable thing the SKILL.md makes the agent do. If no such procedure exists, the skill is not script-ify-able. Don't include the skill's own scripts as part of the codifiable procedures. If a skill has been fully scripted by itself, then the skill should be classified as None.

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

Based on your findings, classify a skill into one of Strong, Partial, and None.

- Strong: Most of the skill are codifiable procedures
- Partial: Part of the skill are codifiable procedures
- None: the skill doesn't have any codifiable procedures

## Step 3: Write you classification
The final output should contain 2 files: classification.json and classification-details.md.

- classification.json: the keys are the class label, and the values are list of skills
- classification-details.md: for each skill, you need to include the justifications for making the classification decision and where the justifications are derived.

