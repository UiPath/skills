# Skill activation eval

Measures whether a skill activates iff a user prompt warrants it. Treated as a
binary classifier (yes/no) and scored with accuracy / precision / recall / F1
plus a confusion matrix.

## Layout

| File | Purpose |
|------|---------|
| `<skill>.jsonl` | Positives for that skill — every prompt should fire that skill. The file's existence is the label, so `should_trigger` is omitted in the source files and injected by `activation.yaml`. |
| `negative.jsonl` | Shared negatives — prompts that should fire **no** skill (small talk, unrelated dev tasks, adjacent UiPath products, other workflow tools). |
| `activation.yaml` | coder-eval task config. Uses `dataset.paths` to load every skill's jsonl + `negative.jsonl` directly, injecting `should_trigger` per file. |

When scoring skill X:
- `<X>.jsonl` rows count as positives (`should_trigger=yes`).
- `negative.jsonl` rows count as negatives.
- Every other `<Y>.jsonl` row counts as a negative for X (cross-skill confusion).

## Run

```bash
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
3. Copy `activation.yaml` to `<new-skill>-activation.yaml`, replace `task_id` and the criterion's `skill_name`. Add the new file to every existing `*-activation.yaml`'s `dataset.paths` block as a negative.

## Cost

On Sonnet 4.6 via Bedrock, ~$0.05–$0.10 per row. The current dataset is
~950 rows total per skill being scored (50 positives + ~900 negatives), so
roughly $50–95 per full run. Use `--sample N` for cheaper iteration.

## Provenance

Per-skill positives were curated by mining real user prompts from skill-specific
Slack channels (read-only) and synthesizing the rest from each `SKILL.md`'s
canonical task verbs. Some skills have narrower scope than 50 prompts can fill
without padding (e.g., `uipath-feedback` at 26, `uipath-tasks` at 34) — the
file just stops at the highest count quality could sustain.
