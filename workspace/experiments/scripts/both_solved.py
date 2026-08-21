#!/usr/bin/env python3
"""Restrict the scripted-vs-unscripted comparison to tasks BOTH arms can solve.

For tasks with >=1 SUCCESS in each arm, compares efficiency (cost/turns/thinking/inline)
scripted vs unscripted — isolating the efficiency effect from the success-rate effect.
Same metric shape as full-tasks-scripted-vs-unscripted-repeat3-detailed.md.
"""

from __future__ import annotations

import glob
import importlib.util
import json
import os
import re
import statistics as st
import sys
from pathlib import Path

INLINE_RE = re.compile(r"python3?\s+(?:-\s+)?<<|python3?\s+-c\b")


def _flag_val(name: str, default: str) -> str:
    """Pull a `--name value` pair from argv (and strip both tokens); else return default."""
    if name in sys.argv:
        i = sys.argv.index(name)
        val = sys.argv[i + 1] if i + 1 < len(sys.argv) else default
        del sys.argv[i : i + 2]
        return val
    return default


# --success-only: average metrics over SUCCESSFUL repeats only (cost-to-solve), not all repeats.
SUCCESS_ONLY = "--success-only" in sys.argv
# --cost-model: `turns` = turn_stats.py agentic steps T (build_steps) instead of total_assistant_turns.
COST_MODEL = "--cost-model" in sys.argv
# glob for a run path's task.json (relative to each run path); task id = 3rd-from-last path part.
TASK_GLOB = _flag_val("--task-glob", "*/*/task.json")
_TS_FLAG = _flag_val("--turn-stats", "")

USAGE = (
    "usage: both_solved.py <treatment-run-path> <baseline-run-path> <class-md-path> <output.md> "
    "[--success-only] [--cost-model] [--task-glob '*/*/task.json'] [--turn-stats PATH]\n"
    "  run-path    : directory containing <task>/<rep>/task.json (e.g. runs/<name>/default)\n"
    "  class-md    : conversion-class file; '-' (or a missing file) => single 'ALL' group\n"
    "  output.md   : written verbatim (relative to CWD if not absolute)"
)
_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(_pos) != 4:
    sys.exit(USAGE)
TREAT_PATH, BASE_PATH = Path(_pos[0]), Path(_pos[1])
CLASS_MD = None if _pos[2] in ("-", "none", "") else Path(_pos[2])
OUT_PATH = Path(_pos[3])


def _run_name(p: Path) -> str:
    """Human/heuristic name for a run path: the run folder (skip a trailing 'default')."""
    parts = p.resolve().parts
    return parts[-2] if len(parts) >= 2 and parts[-1] == "default" else (parts[-1] if parts else str(p))


SCR, UNSCR = _run_name(TREAT_PATH), _run_name(BASE_PATH)

if COST_MODEL:
    # Locate turn_stats.py: --turn-stats, else next to this script, else up the tree, else rglob.
    _here = Path(__file__).resolve()
    _cands = ([Path(_TS_FLAG)] if _TS_FLAG else []) + [_here.parent / "turn_stats.py"] + [
        p / "turn_stats.py" for p in _here.parents
    ]
    _ts_path = next((c for c in _cands if c.exists()), None)
    if _ts_path is None:
        _ts_path = next(iter(sorted(_here.parents[-1].rglob("turn_stats.py"))), None)
    if _ts_path is None:
        sys.exit("error: --cost-model needs turn_stats.py; pass --turn-stats PATH")
    _ts_spec = importlib.util.spec_from_file_location("turn_stats", _ts_path)
    assert _ts_spec and _ts_spec.loader, f"cannot load {_ts_path}"
    _ts = importlib.util.module_from_spec(_ts_spec)
    _ts_spec.loader.exec_module(_ts)


def _cost_model(d: dict) -> tuple[int, float]:
    """(T agentic steps, C cost-model total) for one task.json, matching turn_stats.py defaults."""
    turns = d.get("iterations") or d.get("turns") or []
    residual = sum(_ts.analyze_turn(t)["residual_tokens"] for t in turns)
    steps = _ts.build_steps(turns)
    cm = _ts.model_cost(steps, _ts.W_WRITE, _ts.R_READ, _ts.G_GEN, prefix=None, residual=residual)
    return cm["T"], cm["C_total"]


def _arm_meta(run: str) -> tuple[str, str]:
    """(short label, one-line description) for an arm, inferred from its run name."""
    if "optimized" in run:
        return "scripted+budget+opt", "converted skills + budget prompt **+ token-reduction optimizations** (compact output, inspect-once, coding budget)"
    if "thinking-budget" in run:
        return "scripted+budget", "converted skills **+ the soft `## Reasoning budget` prompt**"
    if "unscripted" in run:
        return "unscripted", "original SKILL.md, no scripts"
    if "scripted" in run:
        return "scripted", "converted skills (STRONG=orchestrator · PARTIAL=sub-step · NONE=unchanged)"
    return run, ""


NEW_LABEL, NEW_DESC = _arm_meta(SCR)      # treatment (SCR)
BASE_LABEL, BASE_DESC = _arm_meta(UNSCR)  # baseline (UNSCR)
IS_BUDGET = "thinking-budget" in SCR
# both arms scripted+budget, only the optimizations differ -> isolates the token-reduction changes
OPT_ISOLATION = "optimized" in SCR and "optimized" not in UNSCR
# both arms scripted, only the prompt differs -> isolates the reasoning-budget prompt
BUDGET_ISOLATION = (IS_BUDGET and "unscripted" not in UNSCR) and not OPT_ISOLATION
# the thing being isolated, for prose/findings
CHANGE = "the token-reduction optimizations" if OPT_ISOLATION else "the reasoning-budget prompt"


def load_classes() -> dict[str, str]:
    """Task -> conversion class (STRONG/PARTIAL/NONE) from CLASS_MD. Returns {} if the file is
    absent, in which case the caller assigns every task the single class 'ALL'."""
    cls: dict[str, str] = {}
    if CLASS_MD is None or not CLASS_MD.exists():
        return cls
    cur = None
    for line in CLASS_MD.read_text().splitlines():
        m = re.match(r"## (STRONG|PARTIAL|NONE)", line)
        if m:
            cur = m.group(1)
            continue
        if cur and line.startswith("|"):
            name = line.strip().strip("|").split("|")[0].strip().rstrip("*").strip()
            if name and not name.lower().startswith("task") and set(name) - set("-: "):
                cls[name] = cur
    return cls


def _think(d: dict) -> int:
    tot = 0
    for it in d.get("iterations") or []:
        for m in it.get("messages") or []:
            if m.get("role") == "assistant" and {b.get("block_type") for b in (m.get("content_blocks") or [])} == {"thinking"}:
                tot += int(m.get("output_tokens", 0) or 0)
    return tot


def _inline(d: dict) -> int:
    n = 0
    for it in d.get("iterations") or []:
        for c in it.get("commands") or []:
            if c.get("tool_name") == "Bash":
                n += len(INLINE_RE.findall((c.get("parameters") or {}).get("command", "") or ""))
    return n


def read_run(run_path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for tj in glob.glob(str(run_path / TASK_GLOB)):
        t = tj.split(os.sep)[-3]
        d = json.loads(Path(tj).read_text())
        tu = d.get("total_token_usage") or {}
        cost = float(tu.get("total_cost_usd", 0) or 0)  # always actual USD
        turns = _cost_model(d)[0] if COST_MODEL else int(d.get("total_assistant_turns", 0) or 0)
        out.setdefault(t, []).append({
            "ok": d.get("final_status") == "SUCCESS",
            "turns": turns,
            "cost": cost,
            "output": int(tu.get("output_tokens", 0) or 0),
            "think": _think(d),
            "inline": _inline(d),
        })
    return out


def mean(x):
    return st.mean(x) if x else 0.0


def pct(a, b):
    return 100 * (b - a) / a if a else 0.0


def main() -> None:
    classes = load_classes()
    scr, unscr = read_run(TREAT_PATH), read_run(BASE_PATH)
    if not scr or not unscr:
        missing = ", ".join(str(p) for p, y in [(TREAT_PATH, scr), (BASE_PATH, unscr)] if not y)
        sys.exit(f"error: no task.json found under: {missing} (glob '{TASK_GLOB}')")
    if not classes:  # no class file -> single synthetic class so the by-class tables still render
        classes = {t: "ALL" for t in set(scr) | set(unscr)}
    both = sorted(
        t for t in scr
        if t in unscr and t in classes
        and any(r["ok"] for r in unscr[t]) and any(r["ok"] for r in scr[t])
    )
    # Class iteration order: canonical STRONG/PARTIAL/NONE first, then any others present (e.g. ALL).
    _present = {classes[t] for t in both}
    CLASS_ORDER = [c for c in ("STRONG", "PARTIAL", "NONE") if c in _present] + sorted(
        _present - {"STRONG", "PARTIAL", "NONE"}
    )
    HAS_TAXONOMY = bool(_present & {"STRONG", "PARTIAL", "NONE"})

    def tmean(arm, t, k):
        rows = [r for r in arm[t] if r["ok"]] if SUCCESS_ONLY else arm[t]
        return mean([r[k] for r in rows])

    isolates = (
        f"**{CHANGE}** (both arms are scripted+budget; only the optimizations differ)"
        if OPT_ISOLATION
        else "the reasoning-budget **prompt** (both arms are scripted; only the prompt differs)"
        if BUDGET_ISOLATION
        else "the *efficiency* effect of scripting from its *success-rate* effect"
    )
    runs_scope = (
        "**over the SUCCESSFUL repeats only** (failed/timeout/error repeats excluded — this is the "
        "cost *to actually solve*)"
        if SUCCESS_ONLY
        else "over the task's repeats"
    )
    title_suffix = " (successful runs only)" if SUCCESS_ONLY else ""
    L: list[str] = []
    L.append(f"# Both-solved tasks: {NEW_LABEL} vs {BASE_LABEL} efficiency{title_suffix} — Sonnet 4.6, 3 repeats")
    L.append("")
    L.append(
        f"Restricted to the **{len(both)} tasks that BOTH arms can solve** (≥1 SUCCESS in each). This "
        f"isolates {isolates} — on tasks where both already succeed, does the change make the solve cheaper?"
    )
    if SUCCESS_ONLY:
        L.append("")
        L.append(
            "**Success-only:** metric cells average **only the repeats that ended in SUCCESS**, so a "
            "failed/spiraled repeat in either arm does not distort the comparison — this is a clean "
            "cost-to-solve view. (Membership still requires ≥1 success in each arm.)"
        )
    L.append("")
    L.append(f"- **{BASE_LABEL}** (baseline) — `runs/{UNSCR}` ({BASE_DESC})")
    L.append(f"- **{NEW_LABEL}** (treatment) — `runs/{SCR}` ({NEW_DESC})")
    L.append("")
    if COST_MODEL:
        L.append(
            "`cost` = **actual USD** (`total_cost_usd`). `turns` = **T**, turn_stats.py's cost-model "
            "agentic-step count (`build_steps` — reconstructed think→call-tools→observe cycles, which "
            "folds parallel tool calls into one step), NOT `total_assistant_turns`. "
            "thinking=Σ`output_tokens` over `block_types=={thinking}` · inline-py=`python <<`/`-c` count. "
            f"Cells are mean per run {runs_scope}. Classes from `full-tasks-scripted/CONVERSION_CLASSIFICATION.md`."
        )
    else:
        L.append(
            "Cost USD · turns=`total_assistant_turns` · thinking=Σ`output_tokens` over `block_types=={thinking}` "
            f"messages · inline-py=`python <<`/`-c` count. Cells are mean per run {runs_scope}. "
            "Classes from `full-tasks-scripted/CONVERSION_CLASSIFICATION.md`."
        )
    L.append("")

    # ---- membership by class ----
    L.append("## Both-solved set (by class)")
    L.append("")
    L.append("| Class | tasks in suite | tasks solved by BOTH |")
    L.append("|---|---|---|")
    for c in CLASS_ORDER:
        n_suite = sum(1 for t in classes if classes[t] == c and t in scr and t in unscr)
        n_both = sum(1 for t in both if classes[t] == c)
        L.append(f"| {c} | {n_suite} | {n_both} |")
    L.append(f"| **TOTAL** | {sum(1 for t in classes if t in scr and t in unscr)} | **{len(both)}** |")
    L.append("")

    # ---- aggregate by class ----
    def agg_table(title, key, fmt):
        L.append(title)
        L.append("")
        L.append(f"| Class | #tasks | {BASE_LABEL} | {NEW_LABEL} | Δ |")
        L.append("|---|---|---|---|---|")
        for c in CLASS_ORDER + (["ALL"] if "ALL" not in CLASS_ORDER else []):
            ts = [t for t in both if c == "ALL" or classes[t] == c]
            if not ts:
                continue
            u = mean([tmean(unscr, t, key) for t in ts])
            s = mean([tmean(scr, t, key) for t in ts])
            L.append(f"| {c} | {len(ts)} | {fmt(u)} | {fmt(s)} | **{pct(u, s):+.0f}%** |")
        L.append("")

    cost_fmt = lambda v: f"${v:.3f}"  # always actual USD
    cost_title = "## COST ($) — mean per run (task-averaged)"
    turns_title = (
        "## TURNS (cost-model agentic steps T) — mean per run"
        if COST_MODEL
        else "## TURNS — mean per run (task-averaged)"
    )
    agg_table(cost_title, "cost", cost_fmt)
    agg_table(turns_title, "turns", lambda v: f"{v:.1f}")
    agg_table("## OUTPUT TOKENS (total, billed at output rate) — mean per run (task-averaged)", "output", lambda v: f"{v:,.0f}")
    agg_table("## THINKING TOKENS (subset of output) — mean per run (task-averaged)", "think", lambda v: f"{v:,.0f}")
    agg_table("## INLINE-PYTHON / run — mean (task-averaged)", "inline", lambda v: f"{v:.1f}")

    # ---- per-task ----
    L.append(f"## Per-task ({BASE_LABEL} → {NEW_LABEL})")
    L.append("")
    L.append(
        f"succ = SUCCESS runs / 3. Other cells = mean per run. Each cell is `{BASE_LABEL} → {NEW_LABEL}`. "
        "Grouped by class, sorted by treatment cost delta."
    )
    L.append("")
    L.append("| Task | cls | succ | cost | cost Δ% | turns | think | inline |")
    L.append("|---|---|---|---|---|---|---|---|")
    for c in CLASS_ORDER:
        rows = [t for t in both if classes[t] == c]
        for t in sorted(rows, key=lambda t: tmean(scr, t, "cost") - tmean(unscr, t, "cost")):
            su = sum(r["ok"] for r in unscr[t])
            ss = sum(r["ok"] for r in scr[t])
            cb = tmean(unscr, t, "cost")
            cs = tmean(scr, t, "cost")
            cpct = f"{100 * (cs - cb) / cb:+.0f}%" if cb else "n/a"
            L.append(
                f"| {t} | {c} | {su}→{ss} | "
                f"{cost_fmt(cb)}→{cost_fmt(cs)} | {cpct} | "
                f"{tmean(unscr,t,'turns'):.1f}→{tmean(scr,t,'turns'):.1f} | "
                f"{tmean(unscr,t,'think'):,.0f}→{tmean(scr,t,'think'):,.0f} | "
                f"{tmean(unscr,t,'inline'):.1f}→{tmean(scr,t,'inline'):.1f} |"
            )
    L.append("")

    # ---- findings ----
    def cls_cost(arm, c):
        ts = [t for t in both if classes[t] == c]
        return mean([tmean(arm, t, "cost") for t in ts]) if ts else 0.0

    def cls_key(arm, c, k):
        ts = [t for t in both if classes[t] == c]
        return mean([tmean(arm, t, k) for t in ts]) if ts else 0.0

    strc = pct(cls_cost(unscr, "STRONG"), cls_cost(scr, "STRONG"))
    strth = pct(cls_key(unscr, "STRONG", "think"), cls_key(scr, "STRONG", "think"))
    strt = pct(cls_key(unscr, "STRONG", "turns"), cls_key(scr, "STRONG", "turns"))
    parc = pct(cls_cost(unscr, "PARTIAL"), cls_cost(scr, "PARTIAL"))
    part = pct(cls_key(unscr, "PARTIAL", "turns"), cls_key(scr, "PARTIAL", "turns"))
    all_u = mean([tmean(unscr, t, "cost") for t in both])
    all_s = mean([tmean(scr, t, "cost") for t in both])
    allc = pct(all_u, all_s)

    L.append("## Findings")
    L.append("")
    if not HAS_TAXONOMY:
        # No conversion-class taxonomy available -> report the overall delta only.
        verb = "cuts" if allc < -3 else ("raises" if allc > 3 else "≈does not change")
        L.append(
            f"- Treatment **{verb} cost {allc:+.0f}%** on the shared-solvable set "
            f"(task-averaged, {'successful reps only' if SUCCESS_ONLY else 'all reps'})."
        )
    elif BUDGET_ISOLATION or OPT_ISOLATION:
        # both arms same family: this isolates a single change (the prompt, or the optimizations)
        verb = "cuts" if allc < -3 else ("raises" if allc > 3 else "≈does not change")
        L.append(
            f"1. **{CHANGE.capitalize()} {verb} cost on the shared-solvable set** — **{allc:+.0f}%** "
            f"overall (both arms are the same converted skills, so this isolates {CHANGE}, nothing else)."
        )
        L.append(
            f"2. **STRONG:** cost **{strc:+.0f}%**, thinking **{strth:+.0f}%**, turns **{strt:+.0f}%** — "
            f"the change acting on top of the one-shot orchestrator."
        )
        L.append(
            f"3. **PARTIAL:** cost **{parc:+.0f}%**, turns **{part:+.0f}%** — the class with a judgment "
            f"loop the script can't absorb, usually where {CHANGE} has the most room to act."
        )
        L.append(
            f"4. **Implication:** on already-scripted, already-solvable tasks, {CHANGE} is a pure "
            f"efficiency lever (no capability change). Net cost {allc:+.0f}% here."
        )
    else:
        if allc < -3:
            f1 = (f"1. **On the shared-solvable set, scripting IS a net efficiency win here** — cost "
                  f"**{allc:+.0f}%** overall, driven by STRONG with PARTIAL no longer a drag (see below).")
        elif allc > 3:
            f1 = (f"1. **On the shared-solvable set, scripting is NOT a net efficiency win** — cost "
                  f"**{allc:+.0f}%** overall. The average hides an opposite split by class.")
        else:
            f1 = (f"1. **On the shared-solvable set, scripting is ≈cost-neutral overall** ({allc:+.0f}%) — "
                  f"a split by class: STRONG down, PARTIAL up.")
        L.append(f1)
        L.append(
            f"2. **STRONG is pure efficiency here** — cost **{strc:+.0f}%**, thinking **{strth:+.0f}%**, turns "
            f"**{strt:+.0f}%**. The orchestrator collapses the think→inline-python→repeat loop even on tasks "
            f"the agent could already solve by hand."
        )
        if IS_BUDGET:
            par_word = "roughly neutral" if abs(parc) < 5 else ("cheaper" if parc < 0 else "costlier")
            f3 = (f"3. **PARTIAL becomes {par_word} with the budget prompt** — cost **{parc:+.0f}%**, turns "
                  f"**{part:+.0f}%**. Without the prompt the sub-step script *adds* to the judgment loop and "
                  f"PARTIAL is a tax; the reasoning-budget nudge trims that over-deliberation, so the extra "
                  f"sub-step no longer inflates cost on tasks both arms already solve.")
        elif parc > 3 or part > 3:
            f3 = (f"3. **PARTIAL is a tax on the shared set** — cost **{parc:+.0f}%**, turns **{part:+.0f}%**. "
                  f"The sub-step script runs *in addition to* the still-required judgment loop, so on a task "
                  f"both arms already solve it only adds work.")
        else:
            f3 = (f"3. **PARTIAL is ≈flat on the shared set** — cost **{parc:+.0f}%**, turns **{part:+.0f}%**. "
                  f"The sub-step neither clearly helps nor hurts efficiency where both arms already succeed.")
        L.append(f3)
        if IS_BUDGET and allc < -3:
            f4 = ("4. **Implication:** the budget prompt is what turns scripting into an efficiency win on the "
                  "shared set — it removes PARTIAL's tax, leaving STRONG's collapse to carry the whole class "
                  "into net savings. (Plain scripting without the prompt shows no such net win on this set — "
                  "see `full-tasks-scripted-vs-unscripted-both-solved-repeat3.md`.)")
        else:
            f4 = ("4. **Implication:** scripting's cost savings do NOT come from making already-solvable tasks "
                  "cheaper — they come from (a) STRONG tasks specifically, and (b) the *new* tasks scripting "
                  "solves that unscripted cannot. On shared-solvable PARTIAL tasks, scripting adds cost.")
        L.append(f4)
    L.append("")
    L.append("## Caveats")
    L.append("")
    L.append(
        "- **n=3/cell**; task-averaged means (each task weighted equally regardless of how many repeats "
        "succeeded). CVs are high — single-task deltas can be flake."
    )
    n_none = sum(1 for t in both if classes[t] == "NONE")
    if HAS_TAXONOMY and n_none == 0:
        L.append(
            f"- **NONE has 0 both-solved tasks** — no NONE task was solved by both `{BASE_LABEL}` and "
            f"`{NEW_LABEL}`, so the class can't appear here."
        )
    if SUCCESS_ONLY:
        L.append(
            "- Metric cells average **only successful repeats**; a task with 1/3 success contributes that "
            "one run's numbers. `succ` in the per-task table still shows the raw success counts."
        )
    else:
        L.append(
            "- Membership is defined by ≥1 success in each arm, so a task counted here may still have failed "
            "some repeats (e.g. 1/3 in one arm); the metric cells average over all repeats, successful or not."
        )
    L.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(L) + "\n")
    print(f"wrote {OUT_PATH}  ({len(both)} both-solved tasks)")


if __name__ == "__main__":
    main()
