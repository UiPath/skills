# Rule Catalog — Workflow (SKILL.md Step 2.5)

Step 2.5 of the review workflow. Runs **after** Step 2 (`uip agent validate` and related CLI validation) and **before** Step 3 (manual checklist review). Adds rule-ID-level findings to the report.

The rule catalog is a single contract per project type, mixing mechanical rules (resolved via `Read` / `Grep` / `Glob` / `Bash` / `uip agent review`) and judgment rules (the agent reads source and reasons). Both kinds emit findings into the same report section.

## Procedure

1. **Identify which catalog files apply.** Use the detection table below for the current project type.
2. **Read each catalog file in full** (including its `## Constants` section).
3. **Group rows by detection method to avoid redundant work:**
   - Inline rows (Glob / Read+JSON / Grep / Bash) — execute each one with the agent's tools.
   - CLI rows — collect by checker section and invoke `uip agent review` once per section (see [CLI invocation](#cli-invocation) below).
   - Judgment rows — read the source material once and assess each rule against it.
4. **For each row, apply the `detection_method` verbatim:**
   - Mechanical rows → produce a finding when the condition holds.
   - Judgment rows → reason about the evidence; emit a finding when the criteria are met. Log the reasoning in the finding's `description`.
5. **Track skipped rules.** If a rule cannot apply (`status: deferred`, missing optional file, not a git repo, CLI not installed), record `rule_id` + reason for the report's "Rules Skipped" subsection. **Never silently skip.**
6. **Merge findings into the Step 5 report** under the "Rule Catalog Results" subsection. Use the canonical line format:

   ```
   [<prefix><n>] `<rule_id>` — <file> — <description>. Fix: <suggested_fix>.
   ```

   where prefix is `C-D-` (Critical), `W-D-` (Warning), or `I-D-` (Info) per the severity mapping in [`rule-format.md`](rule-format.md).

## Detection table

Maps project signals to the catalog files that must be loaded. Extend this table when adding new artifact types — do not edit SKILL.md.

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

## CLI invocation

For rows whose `detection_method` is the CLI form, batch by checker section to minimize invocations:

```bash
uip agent review --project-dir "<PROJECT_DIR>" --checks <name>[,<name>...] --output json
```

`--checks` accepts a comma-separated list of checker names matching catalog H2 sections: `evals`, `schema`, `tools`, `guardrails`, `general`, `lowcode`.

Expected stdout (JSON; one object):

```json
{
  "findings": [
    {
      "rule_id": "EVAL_LOW_DIVERSITY",
      "severity": "error",
      "category": "evals",
      "file": "evals/eval-sets/smoke.json",
      "line": null,
      "description": "...",
      "suggested_fix": "..."
    }
  ],
  "skipped": [
    {
      "rule_id": "EVAL_RUN_OUTDATED",
      "reason": "Not a git repository."
    }
  ]
}
```

Pick out only the findings whose `rule_id` matches the rule rows whose `detection_method` cited this CLI invocation. Other findings the CLI returns are not in scope for those rows — the catalog is authoritative for which rule_ids the skill applies, not the CLI.

If `uip agent review` is not available in the environment (CLI not installed, version doesn't support `agent review`), record every CLI-form rule in the report's "Rules Skipped" subsection with `reason: "uip agent review CLI not available"`.

## Coexistence with manual checklists (Step 3)

- The catalog covers what can be checked mechanically or with focused judgment. The checklists in `references/<type>/<type>-review-checklist.md` cover broader semantic / contextual checks (PDD alignment, business-logic correctness, escalation coverage, architectural fit).
- Checklist rows that overlap with a catalog rule are tagged like `*(rule: \`RULE_ID\`)*` — when reviewing, the catalog already covered them; do not re-flag.
- Findings from the catalog appear in their own report subsection; findings from manual review continue to use the existing Critical / Warning / Info sections.

## Determinism contract

Two consecutive runs over the same project produce identical findings *for mechanical rules*. Judgment rules are best-effort identical — the agent should reason from the same evidence in the same order, but minor wording variation in `description` is acceptable.

- Sort findings by (severity, category, rule_id, file, line) — never by discovery order.
- Do not include timestamps in finding text.
- Use relative paths from project root in finding `file` values; absolute paths in project metadata only.

## Anti-patterns

1. **Do not invent rule IDs.** If you observe a real issue not in the catalog, surface it under the existing Critical / Warning / Info sections as a normal finding — do not promote it to a catalog rule_id.
2. **Do not re-rank severities.** The catalog's `severity` column is authoritative for `error` / `warning` / `info`. For `judgment` severity rows, log the reasoning when picking the report band.
3. **Do not silently skip rules.** Every skip belongs in the report's "Rules Skipped" subsection with a reason.
4. **Do not run the catalog before Step 2.** `uip agent validate` often answers the same question (e.g., it catches `LOWCODE_GUARDRAIL_TOOL_REF_NONEXISTENT` semantically) — running it first lets the catalog focus on what validation misses.
5. **Do not load catalog files outside the detection table.** Loading low-code rules against a non-agent project produces false positives.
6. **Do not call helper scripts or install Python packages.** All code-execution rules go through `uip agent review`. The skill itself ships no executable code.
