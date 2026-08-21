#!/usr/bin/env python3
"""Extract per-rep and per-task cost/behavior metrics for the BPMN inline-CLI A/B.

OPT  = maestro-bpmn-optimized-inline-sonnet-5
BASE = maestro-bpmn-baseline-sonnet-5

Emits rows.json (per-task rows incl. the four lever deltas) + reps.json (per-rep raw).
All numbers are read straight from <run>/default/<task>/<rep>/task.json.
"""
import json, glob, os, re, statistics, sys

RUNS = "/home/azureuser/projects/skills/tmp/coder_eval/runs"
OPT = os.path.join(RUNS, "maestro-bpmn-optimized-inline-sonnet-5")
BASE = os.path.join(RUNS, "maestro-bpmn-baseline-sonnet-5")
OUT = "/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-sonnet-5-inline"

# Sonnet rates ($/token). g=output, r=cache-read, w=cache-create, u=uncached input.
R_OUT, R_CR, R_CC, R_UNC = 15e-6, 0.30e-6, 3.75e-6, 3e-6

# Behavioral-outlier floors: (tool_calls, turns, toolresult_tok, thinking_tok)
# NOTE (sonnet-5 pair): thinking-only messages carry output_tokens==0 and empty thinking
# text, so per-message thinking tokens are NOT separable here. The generation-side lever is
# total output_tokens instead; 5k keeps roughly the relative strictness the 1.5k thinking
# bar had against a ~10.7k/task thinking base (~14%) versus a ~32k/task output base.
FLOORS = {"tool_calls": 6, "turns": 6, "tr_tok": 20000, "output_tok": 20000}
LEVERS = ["tool_calls", "turns", "tr_tok", "output_tok"]
REAL = {"tool_calls": 3, "turns": 3, "tr_tok": 5000, "output_tok": 5000}

UIP_RE = re.compile(r"\buip\b|\$UIP")
PY_SCRIPT_RE = re.compile(r"python3?\s+\S*?([\w\-]+)\.py")


def rep_metrics(path):
    d = json.load(open(path))
    ttu = d.get("total_token_usage") or {}
    thk = 0
    thk_ms = 0.0
    turns = 0
    calls = 0
    tr = 0
    trace = []
    bursts = []
    uip_verbs = {}
    bundled_scripts = {}
    inline_py = 0
    for it in d.get("iterations") or []:
        for m in it.get("messages") or []:
            if m.get("role") != "assistant":
                continue
            bts = {b.get("block_type") for b in (m.get("content_blocks") or [])}
            ot = m.get("output_tokens") or 0
            if bts == {"thinking"}:
                thk += ot
                thk_ms += m.get("generation_duration_ms") or 0.0
                if ot >= 1500:
                    bursts.append(ot)
            if m.get("tool_use_ids"):
                turns += 1
        for c in it.get("commands") or []:
            calls += 1
            tr += c.get("result_tokens") or 0
            tn = c.get("tool_name") or "?"
            p = c.get("parameters") or {}
            label = tn
            if tn == "Bash":
                cmd = str(p.get("command") or "")
                # bundled skill script? python3 <path>/<name>.py where path is under a skill dir
                for mm in PY_SCRIPT_RE.finditer(cmd):
                    name = mm.group(1)
                    if "skill" in cmd.lower() or "/plugins/" in cmd:
                        bundled_scripts[name] = bundled_scripts.get(name, 0) + 1
                    else:
                        inline_py += 1
                if "python" in cmd and not PY_SCRIPT_RE.search(cmd):
                    inline_py += 1  # heredoc / -c inline python (WS5 territory)
                if UIP_RE.search(cmd):
                    mv = re.search(r"(?:uip|\$UIP)\s+([a-z0-9\-]+(?:\s+[a-z0-9\-]+){0,2})", cmd)
                    if mv:
                        v = " ".join(mv.group(1).split())
                        uip_verbs[v] = uip_verbs.get(v, 0) + 1
                label = "Bash"
            elif tn == "Skill":
                label = "Skill:" + str(p.get("skill") or "")
            elif tn in ("Read", "Write", "Edit", "Glob", "Grep"):
                fp = str(p.get("file_path") or p.get("pattern") or "")
                label = f"{tn}:{os.path.basename(fp)}" if fp else tn
            trace.append(label)
    cost = ttu.get("total_cost_usd") or 0.0
    out_t = ttu.get("output_tokens") or 0
    cr = ttu.get("cache_read_input_tokens") or 0
    cc = ttu.get("cache_creation_input_tokens") or 0
    unc = ttu.get("uncached_input_tokens") or 0
    recon = out_t * R_OUT + cr * R_CR + cc * R_CC + unc * R_UNC
    return {
        "path": path,
        "status": d.get("final_status"),
        "task_description": d.get("task_description"),
        "thk_tok": thk,
        "thk_sec": thk_ms / 1000.0,
        "tr_tok": tr,
        "tool_calls": calls,
        "turns": turns,
        "cost": cost,
        "recon_cost": recon,
        "recon_err": abs(recon - cost),
        "output_tok": out_t,
        "cache_read": cr,
        "cache_create": cc,
        "uncached": unc,
        "time": d.get("duration_seconds") or 0.0,
        "bursts": bursts,
        "uip_verbs": uip_verbs,
        "bundled_scripts": bundled_scripts,
        "inline_py": inline_py,
        "trace": trace,
        "max_turns_exhausted": d.get("max_turns_exhausted"),
    }


def mad(xs):
    if len(xs) < 2:
        return 0.0
    med = statistics.median(xs)
    return statistics.median([abs(x - med) for x in xs])


def pick_recurring(reps):
    """Drop behaviorally-aberrant reps; keep >= half. Returns (kept, dropped)."""
    if len(reps) <= 2:
        return reps, []
    keep, drop = [], []
    stats = {}
    for L in LEVERS:
        xs = [r[L] for r in reps]
        stats[L] = (statistics.median(xs), mad(xs))
    for r in reps:
        aberrant = False
        for L in LEVERS:
            med, m = stats[L]
            tol = max(FLOORS[L], 3 * m)
            if abs(r[L] - med) > tol:
                aberrant = True
                break
        (drop if aberrant else keep).append(r)
    if len(keep) < (len(reps) + 1) // 2:
        return reps, []
    return keep, drop


def agg(reps):
    n = len(reps)
    f = lambda k: sum(r[k] for r in reps) / n
    merged_uip, merged_scripts = {}, {}
    for r in reps:
        for k, v in r["uip_verbs"].items():
            merged_uip[k] = merged_uip.get(k, 0) + v
        for k, v in r["bundled_scripts"].items():
            merged_scripts[k] = merged_scripts.get(k, 0) + v
    return {
        "n": n,
        "thk_tok": f("thk_tok"), "tr_tok": f("tr_tok"), "tool_calls": f("tool_calls"),
        "turns": f("turns"), "cost": f("cost"), "time": f("time"),
        "output_tok": f("output_tok"), "thk_sec": f("thk_sec"), "cache_read": f("cache_read"),
        "cache_create": f("cache_create"), "uncached": f("uncached"),
        "inline_py": f("inline_py"),
        "uip_verbs": {k: v / n for k, v in merged_uip.items()},
        "bundled_scripts": {k: v / n for k, v in merged_scripts.items()},
        "reps": [os.path.basename(os.path.dirname(r["path"])) for r in reps],
    }


def load_arm(root):
    out = {}
    for p in sorted(glob.glob(os.path.join(root, "default", "*", "*", "task.json"))):
        task = p.split(os.sep)[-3]
        out.setdefault(task, []).append(rep_metrics(p))
    return out


def main():
    opt_all, base_all = load_arm(OPT), load_arm(BASE)
    # reconciliation check over every task.json
    worst = 0.0
    nrec = 0
    for arm in (opt_all, base_all):
        for reps in arm.values():
            for r in reps:
                worst = max(worst, r["recon_err"])
                nrec += 1
    rows = []
    excluded = []
    for task in sorted(set(opt_all) & set(base_all)):
        o_ok = [r for r in opt_all[task] if r["status"] == "SUCCESS"]
        b_ok = [r for r in base_all[task] if r["status"] == "SUCCESS"]
        if not o_ok or not b_ok:
            continue
        o_keep, o_drop = pick_recurring(o_ok)
        b_keep, b_drop = pick_recurring(b_ok)
        excluded.append({"task": task,
                         "opt_dropped": [os.path.basename(os.path.dirname(r["path"])) for r in o_drop],
                         "base_dropped": [os.path.basename(os.path.dirname(r["path"])) for r in b_drop]})
        O, B = agg(o_keep), agg(b_keep)
        d = {k: O[k] - B[k] for k in ("thk_tok", "thk_sec", "tr_tok", "tool_calls", "turns", "cost",
                                      "time", "output_tok", "cache_read", "cache_create", "uncached")}
        real = {L: abs(d[L]) >= REAL[L] for L in LEVERS}
        rows.append({
            "task": task,
            "task_description": (b_ok[0]["task_description"] or "").strip(),
            "opt": O, "base": B, "delta": d,
            "real_levers": [L for L in LEVERS if real[L]],
            "is_real": any(real.values()),
            "opt_success_reps": len(o_ok), "base_success_reps": len(b_ok),
            "opt_kept": O["n"], "base_kept": B["n"],
            "opt_dropped": len(o_drop), "base_dropped": len(b_drop),
            "opt_bursts": [r["bursts"] for r in o_keep],
            "base_bursts": [r["bursts"] for r in b_keep],
        })
    rows.sort(key=lambda r: r["delta"]["cost"])
    meta = {
        "opt_run": OPT, "base_run": BASE,
        "recon_max_err_usd": worst, "recon_files": nrec,
        "rates": {"output": R_OUT, "cache_read": R_CR, "cache_create": R_CC, "uncached": R_UNC},
        "floors": FLOORS, "real_thresholds": REAL,
        "n_both_solved": len(rows),
        "opt_tasks": len(opt_all), "base_tasks": len(base_all),
    }
    json.dump({"meta": meta, "rows": rows, "excluded": excluded},
              open(os.path.join(OUT, "rows.json"), "w"), indent=1)
    # per-rep dump for narrative use (traces kept out of the main file's way)
    json.dump({t: {"opt": opt_all.get(t, []), "base": base_all.get(t, [])}
               for t in sorted(set(opt_all) & set(base_all))},
              open(os.path.join(OUT, "reps.json"), "w"), indent=1)
    print(f"both-solved tasks: {len(rows)}  (of {len(opt_all)} OPT / {len(base_all)} BASE)")
    print(f"reconciliation: max |derived - total_cost_usd| = ${worst:.6f} over {nrec} task.json")
    tot_o = sum(r['opt']['cost'] for r in rows); tot_b = sum(r['base']['cost'] for r in rows)
    print(f"total cost BASE ${tot_b:.2f} -> OPT ${tot_o:.2f}  ({(tot_o-tot_b)/tot_b*100:+.1f}%)")
    for k in LEVERS:
        so = sum(r['opt'][k] for r in rows); sb = sum(r['base'][k] for r in rows)
        print(f"  {k:11s} BASE {sb:12.1f} -> OPT {so:12.1f}  ({(so-sb)/sb*100:+.1f}%)")
    print("real:", sum(1 for r in rows if r['is_real']), "noise:", sum(1 for r in rows if not r['is_real']))
    print("wins:", sum(1 for r in rows if r['delta']['cost'] < 0),
          "regressions:", sum(1 for r in rows if r['delta']['cost'] > 0))
    print("reps excluded as aberrant: OPT",
          sum(len(e['opt_dropped']) for e in excluded), "BASE",
          sum(len(e['base_dropped']) for e in excluded))


if __name__ == "__main__":
    main()
