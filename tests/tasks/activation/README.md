# Skill activation eval

Measures whether a skill activates iff a user prompt warrants it. Treated as a
binary classifier (yes/no) and scored with accuracy / precision / recall / F1
plus a confusion matrix.

## Layout

| File | Purpose |
|------|---------|
| `<skill>.jsonl` | Positives for that skill — every prompt should fire that skill. The file's existence is the label, so `should_trigger` is omitted. |
| `negatives.jsonl` | Shared negatives — prompts that should fire **no** skill (small talk, unrelated dev tasks, ambiguous one-liners). |
| `activation.yaml` | coder-eval task config. Reads `dataset.jsonl` (generated). |
| `build_dataset.py` | Merges `<skill>.jsonl` + `negatives.jsonl` (+ other skills as cross-skill negatives) → `dataset.jsonl`. |

Each prompt lives in **exactly one** file. When scoring skill X:
- `<X>.jsonl` rows count as positives (`should_trigger=yes`).
- `negatives.jsonl` rows count as negatives.
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

1. Create `<new-skill>.jsonl` with positive prompts (one JSON object per line, fields: `id`, `prompt`, optional `source`, optional `curation_note`).
2. Optional: add must-not-fire prompts that touch your skill's domain to `negatives.jsonl` as adversarial negatives.
3. Copy `activation.yaml` to `<new-skill>-activation.yaml`, replace `task_id` and the criterion's `skill_name`.
4. Run with `--skill <new-skill>` in `build_dataset.py`.

## Provenance

Curated dataset — 118 positives + 142 negatives = 260 rows.

- 244 synthetic rows from initial generation (Akshaya, Mar 2026).
- 16 human-curated / Slack-mined positives (real user phrasing).
- 13 yes→no relabels and 1 no→yes correction during May 2026 review.
- 3 unrealistic prompts dropped.

See git log on this dir for relabeling rationale per row.
