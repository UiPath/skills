# Triage Sub-Agent

Classify the problem, resolve reference paths, and gather data in two passes — match playbooks early, gather deep data only if needed.

**Follow `agents/shared.md` first** — all invariants apply.

## Inputs

- User's problem description (in your prompt)

## Outputs

1. `.local/investigations/state.json` — see `schemas/state.schema.md`
2. `.local/investigations/raw/triage-{command-name}.json` — raw CLI responses
3. `.local/investigations/evidence/triage-initial.json` — see `schemas/evidence.schema.md`

## Pass 1: Quick Match

Goal: get the error message and match playbooks as fast as possible.

1. **Classify scope** using the user's problem description.
2. **If classification is unclear**, try to narrow it down (max 3 attempts) before asking the user:
   - Run up to 3 `uip docsai ask` queries with different keyword combinations
   - Read `references/summary.md` and follow its links to filter down to a specific product/package
   - If after 3 queries you can pin the issue: proceed
   - If after 3 queries you still cannot classify: **stop searching**. Write `needs_input.json` (see shared.md) with a targeted question. Still write `state.json` with what you know.
3. **Resolve investigation guides** — write to `state.json.investigation_guides`:
   - Always include `references/investigation_guide.md`
   - Check if each matched product/package has an `investigation_guide.md`. If yes, include its path.
   - Read all resolved investigation guides and apply their data correlation rules.
4. **Resolve identity** — follow the matched investigation guide's Data Correlation prerequisites (e.g., Orchestrator requires folder → process → time window). If the entity is inaccessible (wrong ID, permissions, not found), STOP: write `state.json`, write `needs_input.json` (see shared.md) asking for the missing detail. Do NOT continue when you can't reach the primary entity.
5. **Fetch primary entity details** — follow the starting domain's investigation guide for initial data gathering commands. If multiple entities exist (e.g., multiple faulted jobs or incidents), select ONE entity using this priority order, then do NOT fetch details for the others:
   1. **Filter by process first.** If the user named a process explicitly, OR a process can be reasonably inferred from the working directory (e.g., the project's `project.json` name, the directory name), filter the candidate list to entities for that process and pick the most recent match.
   2. **Ambiguity check.** If multiple plausible processes can be inferred (e.g., the directory has been renamed/republished under a different name) and the candidate list contains entities for processes that do NOT match the inferred name, do NOT default — write `needs_input.json` (see shared.md) asking the user which process they meant. Do not pick the most recent overall when the inferred process disagrees with the candidate's process.
   3. **Fall back to most recent overall** only when no process can be inferred from the user's message OR the working directory.

   Write to raw/, write evidence summary.
6. **Match playbooks** — read the product/package summary for every domain in `state.json.scope.domain`. Record EVERY playbook whose signature the error data satisfies, across ALL confidence levels (high + medium + low) — not only the highest-ranked one. When multiple sibling playbooks share an overlapping signature but describe distinct causes or remediations, ALL of them MUST appear in `state.json.matched_playbooks`. The Confidence Gate below decides Pass 1→Pass 2 routing only; it does NOT decide which playbooks are recorded. Each entry carries confidence level and full path. Do NOT override confidence levels.

7. **Confirm source-code availability when the matched playbook needs it.** Some playbooks cannot reach a root cause without inspecting project source — typically runtime exceptions, selector failures, expression-evaluation errors, variable-binding issues, and any case where the error stack names a compiled workflow expression (e.g., `__Expr<n>Get`, `CSharpValue.Execute`, `InArgument.TryPopulateValue`) or a specific activity inside a `.xaml` / `.cs` / `.py` source file. Decide:

   a. **Does this investigation need source?** Read each matched playbook's `## Investigation` section. If it instructs reading XAML / `project.json` / activity arguments / variable bindings / expression text / compiled-expression mapping → source is required. If it only references CLI commands and platform-side fixtures → source is not required.

   b. **Is source already known?** Check `state.json.requirements.source_code_path`. It is "known" if:
      - The user's problem description named a directory or path (e.g., "the project at C:\…", "the source for X is in cwd", "this folder"), AND you recorded it during step 4 ("Resolve identity"), OR
      - The current working directory contains a recognisable UiPath project (`project.json`, `agent.json`, or `caseplan.json` at the top level) and you record `source_code_path = "."` here with a note that you auto-discovered it.

   c. **If source is required AND not yet known → STOP and ask the user.** Write `needs_input.json` (see shared.md) requesting the project source path. The question must be specific:
      ```
      "To trace the originating cause for <error class / activity name>, I need to inspect the project source (XAML / project.json / .py). Could you share the project's directory path? If you are already in the project directory, just reply `pwd` or `.`."
      ```
      Include in the `context` field the matched playbook(s) that drove this ask and which evidence types you need (e.g., "variable assignment chain for `myVar` in `ERN.xaml`"). Do NOT continue to the Confidence Gate or Pass 2 until the orchestrator re-spawns you with the user's answer.

   d. **On re-spawn with the answer:** record the answer in `state.json.requirements.source_code_path` (verify the path resolves to a directory before writing). Then continue normally.

   Do NOT use this rule for investigations that the matched playbook can resolve from platform-side data alone — asking for source unnecessarily is friction. Trigger only on the source-requiring conditions in (a).

### Confidence Gate

**If ANY high-confidence playbook matched** → STOP. Write `state.json` and evidence. Return to orchestrator. The error was enough to match — deep data gathering is not needed for playbook matching.

**If NO high-confidence playbook matched** → continue to Pass 2.

## Pass 2: Deep Gathering

Goal: collect richer data for medium/low confidence matching and hypothesis generation.

8. **Deep data gathering** — follow each matched domain's investigation guide "Domain-Specific Data Gathering" section for additional commands beyond the initial fetch (e.g., logs, traces, Healing Agent data, connection pings, element executions). Write each to raw/, write evidence summaries.
9. **Re-match playbooks** — with the richer data, some high/medium/low playbooks may now match that didn't match on error message alone. Update `state.json.matched_playbooks`. If Pass 2 surfaces a new `high`-confidence playbook, append it to `matched_playbooks` but do NOT return to Pass 1 — continue to the next step.
10. **Re-check source-code availability for any newly-matched playbooks** — if Pass 2 surfaced a new playbook from step 7's source-requiring categories and `source_code_path` is still unset, apply step 7c (write `needs_input.json` and STOP). Otherwise continue.
11. **Write evidence summary** — consolidate findings from both passes into `triage-initial.json`. Return to orchestrator.

## Boundaries

- Primary data-gathering agent that reads `references/summary.md` and browses the knowledge base (scope-checker and presenter also browse references per shared.md)
- Data-gathering uip commands only
- Do NOT generate hypotheses — that's the generator's job
- If you cannot get data about the specific entity the user reported, **STOP and say so**
