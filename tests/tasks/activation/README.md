# Skill activation eval

Measures whether a skill activates iff a user prompt warrants it. Treated as a
binary classifier (yes/no) and scored with accuracy / precision / recall / F1
plus a confusion matrix.

## Layout

| File | Purpose |
|------|---------|
| `<skill>.jsonl` | Positives for that skill — every prompt should fire that skill. `expected_skill` is injected per file by `activation.yaml`. |
| `negative.jsonl` | Shared negatives — prompts that should fire **no** skill (small talk, unrelated dev tasks, adjacent UiPath products, other workflow tools). |
| `activation.yaml` | coder-eval task config. Uses `dataset.paths` to merge all skill jsonls + `negative.jsonl`, and stacks 22 `skill_triggered` criteria — one per skill — each computing its own confusion matrix from the same agent traces. |

The `expected_skill` field on each row is the row's true label (the skill it should fire, or `""` for negatives). Each criterion compares its own `skill_name` to `expected_skill`: `expected="yes"` iff they match. So for skill X:
- `<X>.jsonl` rows are positives.
- All other rows (`<Y>.jsonl` for Y≠X plus `negative.jsonl`) are negatives — exercising cross-skill confusion.

## Run

```bash
export SKILLS_REPO_PATH=/path/to/skills
uv run --project /path/to/coder_eval coder-eval run \
  skills/tests/tasks/activation/activation.yaml \
  -e skills/tests/experiments/activation.yaml \
  --backend bedrock \
  --preserve \
  -j 4

# Quick subsample for iteration:
uv run --project /path/to/coder_eval coder-eval run \
  skills/tests/tasks/activation/activation.yaml \
  -e skills/tests/experiments/activation.yaml \
  --backend bedrock --sample 20 -j 4
```

Reports land in `tmp/<run-id>/`. The suite gate fails per criterion on `recall.yes < 0.70`. Class imbalance (~50 yes / ~1140 no per skill) makes accuracy and recall.no trivially high; recall.yes is the only meaningful gate.

## Adding a new skill

1. Create `<new-skill>.jsonl` with positive prompts (one JSON object per line, fields: `id`, `prompt`).
2. Optional: add must-not-fire prompts that touch your skill's domain to `negative.jsonl` as adversarial negatives.
3. Edit `activation.yaml`: add the new file to `dataset.paths` and append a new `skill_triggered` criterion with `skill_name: uipath-<new-skill>`.

## Cost

On Sonnet 4.6 via Bedrock, ~$0.05–$0.10 per row. The dataset is ~1190 rows total. The agent runs ONCE per row regardless of criteria count, and the 22 stacked criteria are pure-Python evaluation against the same trace, so the full benchmark across all 22 skills costs **~$60–120**. Use `--sample N` for cheaper iteration (note: `--sample` slices first-N, which biases toward the first-listed paths; useful for smoke runs, not for metrics).

## Provenance

Per-skill positives were curated by mining real user prompts from skill-specific
Slack channels (read-only) and synthesizing the rest from each `SKILL.md`'s
canonical task verbs. `negative.jsonl` also carries adversarial negatives that
sit deliberately close to a skill's domain but must NOT fire it (e.g. classic
Document Understanding / AI Center vs `uipath-ixp`, a CNCF Serverless Workflow
spec vs `uipath-api-workflow`, a Claude Desktop / FastMCP server vs
`uipath-mcp-servers`) — these exercise cross-skill precision, not just recall.

## Coverage

Covers all 22 skills in the repo. Skill positives target user **intent** (the
task a prompt is asking for), not exact CLI surface, so coverage stays valid
while a Preview skill's commands are still in flux. Narrower-scope skills hold
fewer rows than 50 without padding (e.g. `uipath-ixp` at 30,
`uipath-automation-discovery` at 32, `uipath-feedback` at 26, `uipath-tasks` at
34) — the file stops at the highest count quality sustains.
