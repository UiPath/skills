---
description: Compare tasks solved by BOTH runs on cost-to-solve (cost-model turns, successful reps only)
argument-hint: <treatment-run-path> <baseline-run-path> <class-md-path|-> <output.md>
---

Compare two eval runs on **cost-to-solve**, restricted to tasks BOTH runs can solve, counting only successful repeats.

- **$1** = treatment run path — a directory containing `<task>/<rep>/task.json` (e.g. `.../runs/<name>/default`).
- **$2** = baseline run path — same shape.
- **$3** = conversion-class file path, or `-` for none (then everything is a single `ALL` group).
- **$4** = output `.md` path (written verbatim; relative to CWD if not absolute).

Semantics (do not deviate):
- **Both-solved**: include a task only if it has ≥1 SUCCESS rep in EACH run.
- **Don't count failed reps**: average every metric over the SUCCESSFUL reps only (a failed/timeout/error rep never enters a mean) — this is cost-to-solve.
- **Cost-model turns**: `turns = T`, turn_stats.py's agentic-step count (`build_steps`), NOT `total_assistant_turns`.

Steps:
1. Run the comparison (arg1 = treatment, arg2 = baseline, arg3 = class-md, arg4 = output):
   ```bash
   cd /home/azureuser/projects/skills/tmp/experiments/scripts
   python3 both_solved.py "$1" "$2" "$3" "$4" --success-only --cost-model
   ```
   It writes to `$4` and prints the path + the both-solved task count. If a run path has no `task.json` it errors clearly (naming the path + glob) — surface that and stop. Optional: `--task-glob '*/*/task.json'` (change if the per-run layout differs), `--turn-stats PATH` (if `turn_stats.py` isn't next to the script or up its tree).
2. Read the generated file and report a tight summary: the both-solved task count, and the overall deltas (treatment vs baseline) for **cost ($), turns (T), output tokens, thinking tokens** — each as `baseline → treatment (Δ%)`. Include the per-class breakdown **only if** `$3` was a real class file (with `-` the report has a single `ALL` group).
3. Sanity-check that arg1 is the treatment and arg2 the baseline (deltas read `baseline → treatment`), and that the auto-generated intro line names the arms correctly for THIS pairing (the label heuristic infers from the run-path folder name and can mislabel, e.g. calling an unscripted baseline "budget"). If it's wrong, note the correct framing and offer to fix the intro line.

Output: the file path, the headline table, and a one-line takeaway (where the cost-to-solve difference concentrates).
