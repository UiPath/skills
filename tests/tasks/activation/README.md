# Skill activation eval

Measures whether a skill activates iff a user prompt warrants it. Treated as a
binary classifier (yes/no) and scored with accuracy / precision / recall / F1
plus a confusion matrix.

## Layout

| File | Purpose |
|------|---------|
| `<skill>.jsonl` | Positives for that skill — every prompt should fire that skill. The file's existence is the label, so `should_trigger` is omitted in the source files. |
| `negative.jsonl` | Shared negatives — prompts that should fire **no** skill (small talk, unrelated dev tasks, adjacent UiPath products, other workflow tools). |
| `activation.yaml` | coder-eval task config. Reads the merged `dataset.jsonl`. |
| `build_dataset.py` | **HACK** (see file header): merges `<skill>.jsonl` + `negative.jsonl` → `dataset.jsonl`. Exists because coder_eval's `dataset.path` only takes one JSONL. Remove once the framework supports `dataset.paths: [...]`. |

Each prompt lives in **exactly one** file. When scoring skill X:
- `<X>.jsonl` rows count as positives (`should_trigger=yes`).
- `negative.jsonl` rows count as negatives.
- Every other `<Y>.jsonl` row counts as a negative for X (cross-skill confusion).

## Run

```bash
# 1. Generate the merged dataset for the skill under test.
cd skills/tests/tasks/activation
uv run python build_dataset.py --skill uipath-maestro-flow

# 2. Run the eval. SKILLS_REPO_PATH is the plugin source the agent loads.
export SKILLS_REPO_PATH=/Users/bai.li/uipath/skills
uv run --project /Users/bai.li/uipath/coder_eval coder-eval run \
  skills/tests/tasks/activation/activation.yaml \
  -e skills/tests/experiments/activation.yaml \
  --backend bedrock \
  --preserve \
  -j 4

# Quick subsample for iteration:
uv run --project /Users/bai.li/uipath/coder_eval coder-eval run \
  skills/tests/tasks/activation/activation.yaml \
  -e skills/tests/experiments/activation.yaml \
  --backend bedrock --sample 20 -j 4
```

Reports land in `tmp/<run-id>/`. The suite gate fails on:
- `accuracy < 0.75`
- `recall.yes < 0.70`
- `recall.no < 0.70`

## Adding a new skill

1. Create `<new-skill>.jsonl` with positive prompts (one JSON object per line, fields: `id`, `prompt`).
2. Optional: add must-not-fire prompts that touch your skill's domain to `negative.jsonl` as adversarial negatives.
3. Copy `activation.yaml` to `<new-skill>-activation.yaml`, replace `task_id` and the criterion's `skill_name`.
4. Run with `--skill <new-skill>` in `build_dataset.py`.

## Cost

On Sonnet 4.6 via Bedrock, ~$0.05–$0.10 per row. The current 100-row set is
roughly $5–10 per full run. Haiku is ~5× cheaper if signal-to-noise is fine.

## Provenance

Curated dataset — 50 positives + 50 negatives = 100 rows.

Distilled from a larger 260-row pool (244 synthetic + 16 Slack-mined positives
during May 2026 review). Rows kept aim for category coverage (create / edit /
debug / CLI / triggers / subflows / connectors / generic-intent /
adjacent-products / other-workflow-tools). All 16 human-curated rows are
retained for real-user phrasing signal.
