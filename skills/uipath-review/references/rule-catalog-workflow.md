# Rule Catalog — Workflow (SKILL.md Step 2.5)

Step 2.5 of the review workflow. Runs **after** Step 2 (`uip agent validate` and related CLI validation) and **before** Step 3 (manual checklist review). Adds rule-ID-level findings to the report from two sources, in order:

1. **The review CLI** (`uip agent review` / `uip codedagent review`) — all deterministic static checks.
2. **The judgment catalog** (`agents-*-rules.md`) — checks that require the agent to read source and reason.

## Procedure

### 2.5a — Run the review CLI first

Run the review command for the agent type, once, capturing JSON:

| Agent type | Command |
|---|---|
| Low-code (`agent.json`) | `uip agent review --project-dir "<PROJECT_DIR>" --output json` |
| Coded (`main.py` + framework config) | `uip codedagent review --project-dir "<PROJECT_DIR>" --output json` |

Parse the JSON. Findings live under `Data.Issues[]`; each issue is:

```json
{
  "RuleId": "LOWCODE_ENTRY_POINTS_MISSING",
  "Category": "schema",
  "Severity": "error",
  "Description": "...",
  "File": "entry-points.json",
  "SuggestedFix": "..."
}
```

The response also carries `Data.Verdict` (PASS/FAIL), `Data.Score`, `Data.Grade`, and `Data.Stats` — report the verdict/score if useful, but the `Issues[]` are the findings. Carry each issue into the report **verbatim**; do not re-derive, rename, or re-rank. These `RuleId`s are authoritative as the CLI emits them and are **not** duplicated in the skill catalog.

If the review command is unavailable (CLI not installed, or a version without `agent review` / `codedagent review`), record one line in the report's "Rules Skipped" subsection with `reason: "uip agent review / codedagent review CLI not available"`, then continue with 2.5b.

### 2.5b — Apply the judgment catalog

1. **Identify which catalog files apply.** Use the detection table below.
2. **Read each catalog file in full.**
3. **Apply each rule's `detection_method`** (always the judgment form): read the named source material, reason about it, emit a finding when the criteria hold. Log the reasoning in the finding's `description`.
4. **Track skipped rules.** If a rule cannot apply (`status: deferred`, missing optional file, no eval set to assess against), record `rule_id` + reason for the report's "Rules Skipped" subsection. **Never silently skip.**
5. **Merge findings into the Step 5 report** under the "Rule Findings" subsection. Use the canonical line format:

   ```
   [<prefix><n>] `<rule_id>` — <file> — <description>. Fix: <suggested_fix>.
   ```

   where prefix is `C-D-` (Critical), `W-D-` (Warning), or `I-D-` (Info) per the severity mapping in [`rule-format.md`](rule-format.md).

## Detection table

Maps project signals to the judgment catalog files that must be loaded. Extend this table when adding new artifact types — do not edit SKILL.md.

| Signals present | Project type | Catalog files |
|---|---|---|
| `agent.json` AND no `main.py` AND no `pyproject.toml` | Agent (low-code) | `agents/agents-common-rules.md` + `agents/agents-lowcode-rules.md` |
| `pyproject.toml` + `main.py` + any framework config (`langgraph.json` / `llama_index.json` / `openai_agents.json` / `google_adk.json` / `pydantic_ai.json` / `agent_framework.json`) | Agent (coded) | `agents/agents-common-rules.md` + `agents/agents-coded-rules.md` |
| `pyproject.toml` + `main.py` + `uipath.json[functions]` only (no framework config) | Agent (coded — Simple Function) | same as Agent (coded) |
| `agent.json` + `pyproject.toml` + `main.py` (agent-builder coded layout) | Agent (low-code + coded) | all three: common + lowcode + coded; tag each finding with its source file |
| `project.json` + `.xaml` / `.cs` | RPA | *(phase 2 — catalog not yet authored)* |
| `*.flow` + `project.uiproj` with `ProjectType: "Flow"` | Flow | *(phase 2)* |
| `.uipath/` or `app.config.json` | Coded App | *(phase 2)* |
| None of the above with no agent signal | unknown | Skip Step 2.5; flag in the report's "Notes" section that no catalog matched. |

## Why the split

Deterministic checks (file presence, schema walks, counts, set-membership, regex, run-artifact analysis) are faster and byte-reproducible in code, so they live in the review CLI — the agent does not re-implement them. The catalog carries only what code cannot decide reliably: prompt quality, tool-selection ambiguity, framework fit, semantic schema/eval mismatches, whole-program dataflow. Running the CLI first means the catalog never re-litigates a deterministic finding.

## Coexistence with manual checklists (Step 3)

- The CLI + judgment catalog cover what can be checked mechanically or with focused judgment. The checklists in `references/<type>/<type>-review-checklist.md` cover broader semantic / contextual checks (PDD alignment, business-logic correctness, architectural fit).
- Checklist rows that overlap with a rule are tagged like `*(rule: \`RULE_ID\`)*` — when reviewing, that rule (CLI or judgment) already covered it; do not re-flag.
- Findings from the CLI + judgment catalog appear in the "Rule Findings" subsection; findings from manual review use the Critical / Warning / Info sections.

## Determinism contract

Two consecutive runs over the same project produce identical findings *for the review-CLI checks*. Judgment-catalog rules are best-effort identical — the agent should reason from the same evidence in the same order, but minor wording variation in `description` is acceptable.

- Sort findings by (severity, category, rule_id, file, line) — never by discovery order.
- Do not include timestamps in finding text.
- Use relative paths from project root in finding `file` values; absolute paths in project metadata only.

## Anti-patterns

1. **Do not invent rule IDs.** If you observe a real issue covered by neither the review CLI nor the judgment catalog, surface it under the Critical / Warning / Info sections as a normal finding — do not promote it to a `rule_id`.
2. **Do not re-rank severities.** The CLI's `Severity` and the catalog's `severity` are authoritative for `error` / `warning` / `info`. For `judgment` rows, log the reasoning when picking the report band.
3. **Do not silently skip rules.** Every skip belongs in the report's "Rules Skipped" subsection with a reason.
4. **Do not run the catalog before the CLI.** Run `uip agent review` / `uip codedagent review` first (2.5a), then `uip agent validate` is assumed already passed (Step 2) — so the judgment catalog focuses only on reasoning the CLI cannot do.
5. **Do not load catalog files outside the detection table.** Loading low-code rules against a non-agent project produces false positives.
6. **Do not re-implement deterministic checks inline.** Counts, regex, schema-presence, and set-membership are the review CLI's job. The skill itself ships no executable code.
