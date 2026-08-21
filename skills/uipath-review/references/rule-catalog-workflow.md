# Rule Catalog — Workflow (SKILL.md Step 2.5)

Step 2.5 runs after Step 2 (`uip agent refresh` then `uip agent validate` for low-code agents, plus related CLI validation) and before Step 3 (manual checklist review). It adds rule-ID findings from the review CLI, then the judgment catalog.

## Procedure

### 2.5a — Run the review CLI first

Run the applicable review command once, even if another review pass already produced findings (SKILL.md Critical Rule 9), and capture JSON:

| Agent type | Command |
|---|---|
| Low-code (`agent.json`) | `uip agent review "<PROJECT_DIR>" --output json` |
| Coded (`main.py` + framework config) | `uip codedagent review "<PROJECT_DIR>" --output json` |

Parse `Data.Issues[]`. Carry every issue verbatim into the report as `<File>: <Description>. <SuggestedFix>.`; do not re-derive, rename, or re-rank it. Each issue contains `RuleId`, `Category`, `Severity`, `Description`, `File`, and `SuggestedFix`. CLI-emitted `RuleId`s are authoritative and are not duplicated in the skill catalog.

Use `Data.Grade` as **G_det**, the deterministic half of the Step 4.5 agent letter grade; read it here and never recompute it (see [agents/agent-grading-rubric.md](agents/agent-grading-rubric.md)). `Data.Verdict` is `PASS`/`FAIL`; `Data.Score`, `Data.Grade`, and `Data.Stats` may also be reported.

If the CLI is unavailable (not installed or lacking `agent review` / `codedagent review`), record one line in the report's "Rules Skipped" subsection with `reason: "uip agent review / codedagent review CLI not available"`, then continue with 2.5b.

### 2.5b — Apply the judgment catalog

1. Use the detection table to identify applicable catalog files.
2. Read every applicable catalog file in full.
3. Apply each rule's `detection_method` in its judgment form: read the named source, reason about it, and emit a finding when criteria hold. Log the reasoning in the finding's `description`.
4. Track every intended rule that cannot be applied (`status: deferred`, review CLI unavailable, guardrail catalog unavailable, or required source unreadable) in the report's "Rules Skipped" subsection with `rule_id` and reason. Never silently skip. An empty subject set is not a skip (SKILL.md Critical Rule 11).
5. Merge findings into the Step 5 report's Critical / Warning / Info tables, one row per finding:

   ```
   | <id> | `<rule_id>` | `<file>`: <issue>. <fix>. |
   ```

   Use `C-D-` (Critical), `W-D-` (Warning), or `I-D-` (Info), per [`rule-format.md`](rule-format.md).

## Detection table

Load only catalogs matched by these project signals. Extend this table for new artifact types; do not edit SKILL.md.

| Signals present | Project type | Catalog files |
|---|---|---|
| `agent.json.type == "lowCode"` | Agent (low-code) | `agents/agents-lowcode-rules.md` (+ `agents/guardrails/guardrails-review.md` when `guardrails[]` is present or a guardrail use case matches — see Step 2.5b item 3) |
| Python coded-agent signals or `agent.json.type == "coded"` | Agent (coded) | `agents/agents-coded-rules.md` (+ `agents/guardrails/coded-guardrails-review.md` when the entry source wires SDK guardrails or a guardrail use case matches — see Step 2.5b item 3) |
| `pyproject.toml` + `main.py` + `uipath.json[functions]` only (no framework config) | Agent (coded — Simple Function) | same as Agent (coded) |
| `project.json` + `.xaml` / `.cs` | RPA | *(phase 2 — catalog not yet authored)* |
| `*.flow` + `project.uiproj` with `ProjectType: "Flow"` | Flow | *(phase 2)* |
| `.uipath/` or `app.config.json` | Coded App | *(phase 2)* |
| None of the above with no agent signal | unknown | Skip Step 2.5; note in the report's "Notes" section that no catalog matched. |

The review CLI owns deterministic checks—file presence, schema walks, counts, set-membership, regex, and run-artifact analysis. The catalog owns judgment the CLI cannot reliably perform, including prompt quality, tool-selection ambiguity, framework fit, semantic schema/eval mismatches, and whole-program dataflow. Run the CLI first so the catalog does not re-litigate deterministic findings.

## Coexistence with manual checklists (Step 3)

- The CLI and judgment catalog cover mechanical and focused-judgment checks. `references/<type>/<type>-review-checklist.md` covers broader semantic/contextual checks, including PDD alignment, business-logic correctness, and architectural fit.
- Tag checklist rows overlapping a rule with `*(rule: \`RULE_ID\`)*`; do not re-flag them when the CLI or catalog already covered them.
- Put CLI, catalog, and manual findings in the same Critical / Warning / Info tables. Keep `-D-` prefixes for rule-driven findings and no infix for manual findings (see [`rule-format.md`](rule-format.md)). A finding appears exactly once in one table.

## Determinism contract

Two consecutive runs on the same project must produce identical findings for review-CLI checks. Judgment findings should be best-effort identical when evidence and order are unchanged; minor `description` wording variation is acceptable.

Sort findings by `(severity, category, rule_id, file, line)`, never discovery order. Do not include timestamps in finding text. Use paths relative to the project root in finding `file` values; use absolute paths only in project metadata.

## Anti-patterns

1. Do not invent rule IDs. If a real critical issue is covered by neither the CLI nor catalog, report it under Critical Findings as a normal finding, not with a `rule_id`; only critical issues qualify (SKILL.md Critical Rule 12).
2. Do not re-rank severities. CLI `Severity` and catalog `severity` are authoritative for `error` / `warning` / `info`. For `judgment` rows, log the reasoning used to select the report band.
3. Do not silently skip rules. Record every skip in "Rules Skipped" with its reason.
4. Do not run the catalog before the CLI. Run `uip agent review` / `uip codedagent review` first (2.5a). For low-code agents, run `uip agent refresh` then `uip agent validate` during Step 2; the catalog handles only reasoning the CLI cannot perform.
5. Do not load catalog files outside the detection table. Loading low-code rules for a non-agent project creates false positives.
6. Do not re-implement deterministic checks inline. Counts, regex, schema-presence, and set-membership belong to the review CLI; the skill ships no executable code.