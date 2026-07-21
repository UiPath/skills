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

You need to reduce the cost of using coding agents by reducing the total number of turns it takes to complete a task. Your approach is to find out any codifiable works in skills where you can turn these works into scripts and complete these works in less turns. The reason is that a script bundles multiple turns into one script call.

The skills path is `$1`. The path is either a parent path that contains multiple skills or a single skill's path. Each skill has a SKILL.md with optional references/, scripts/, assets/, etc. Make sure you copy the skills into `$2` before working on the skills.


## Step 1: Find codifiable procedures

For each skill, read its SKILL.md and optional files to find out any deterministic, repeatable thing the SKILL.md makes the agent do. Write your findings to a `findings.md` file next to the SKILL.md. Your findings should include what the procedure is, where the procedure is derived in the SKILL.md, and how it can be turned into scripts. If no such procedure exists, the skill is not script-ify-able. You should leave the skill as-is.

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

## Step 2: Write scripts

Based on your findings, write scripts that complete the procedures in one call. If one procedure pipeline other procedures, you should write an orchestrator script that chains other scripts. Scripts live under `scripts/`.

Criteria are as follows:

- **Parameterized** — all paths, params, and constants-that-vary are CLI args; nothing task-specific hardcoded (no real input filenames, no expected/graded values baked in).
- **Deterministic** — same inputs → same output; no randomness, timestamps, or ordering that isn't fixed (sort explicitly).
- **Single responsibility** — one procedure per script; chain via a thin orchestrator, don't merge unrelated steps.
- **Clear I/O contract** — inputs as args, output to a stated file or stdout in a fixed schema; documented in `--help`.
- **Faithful** — implements the skill's exact formula/rule/edge-cases verbatim; if the skill ships logic, reuse/import it rather than re-deriving.
- **Meaningful exit code** — 0 on success, non-zero on failure/validation-fail, so the agent can branch on it.
- **Small output** — emit a compact result (value / summary / pass-fail); write large output to a file, not stdout, and provide a script to interact with the file.
- **Fails loudly** — validate inputs and raise a clear error rather than producing a silently-wrong result.
- **Self-contained deps** — use only libraries the skill already references and include extra libraries only when needed; declare them in `requirements.txt`.
- **Terse** — no comment banners or narration; readable code, no dead branches.
- **Verifiable** — runs end-to-end on a fabricated example and produces the expected output.

For each script, verify its correctness by grounding it against the original skill files and writing tests. You also need to document its usage and provide examples of how to use it in the findings.md. The tests should live under `script-tests/` next to the SKILL.md with sub-folders differentiate each script.

## Step 3: Update SKILL.md

You should update the SKILL.md and optional files based on what you have done. Don't mention `findings.md` and `script-tests/`.
- **Adapt** — change only what's needed to accommodate the scripts; keep all original understanding content verbatim (framing, domain rules, definitions, thresholds, reference sections). Never silently drop or lossily reword it.
- **Keep a conceptual overview** — before any command, explain what the skill is, what it does, and when and how to use it, so a mismatch with the task is visible.
- **Teach how to use the scripts, don't just list them** — for each: what it does (input→output), a concrete example command, and its key args/flags — enough to run it without opening the source. Add this to where a script is derived.
- **Document the orchestrator, not its parts** — if one script chains others, document only the orchestrator as primary; mark chained sub-scripts "internal — called by X". Mark heavier alternative/inspection paths "fallback only" so the agent doesn't default into them.
- **Drop inline code the script implements** — reference it (name + what it does + key params), never paste a duplicate implementation. Keep inline code only for what the scripts don't provide.
- **Mark the judgment explicitly** — call out the steps that are the agent's to decide (tune this, choose that, interpret this); never present them as scripted.
- **Never absolutist "run-and-done" prose** — no "this is the whole task / just run this / do not edit"; lead the agent to read, adapt, or add scripts when the task needs it.
- **Stay task-agnostic** — describe the script, not a specific task; no hardcoded task filenames or graded values; paths are args.
- **Plain facts, no filler** — no slogans or editorial labels ("single source of truth", "authoritative", "definitive").
- **Well-formed** — exactly one Scripts section, balanced code fences, no orphaned fragments or truncation.
