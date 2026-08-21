#!/usr/bin/env python3
"""Extract per-task cost/behavior rows from coder_eval task.json files for two runs."""
import argparse
import glob
import json
import os
import re
import statistics as st

RATES = {"output": 15.0 / 1e6, "cache_read": 0.30 / 1e6, "cache_create": 3.75 / 1e6, "uncached": 3.0 / 1e6}
SCRIPT_RE = re.compile(r"python3?\s+(?:\S*/)?([A-Za-z0-9_]+)\.py")
FLOORS = {"tool_calls": 6, "turns": 6, "tool_result_tokens": 20000, "thinking_tokens": 6000}
BUNDLED = {"flow_edit", "audit_flow", "diagnose_run",
           # v1 names, kept so a mixed run is still classified correctly
           "flow_compose", "check_topology", "audit_expressions", "lint_jint", "check_bindings",
           "check_runtime_gaps", "node_ownership", "validate_mermaid", "encode_parameter_values",
           "wire_agent_inputs", "flow_lib"}
LEVERS = list(FLOORS)


def rep_metrics(path):
    d = json.load(open(path))
    thinking = 0
    bursts = []
    tool_turns = 0
    thinking_blocks = 0
    reasoning = 0
    for it in d.get("iterations") or []:
        for m in it.get("messages") or []:
            if m.get("role") != "assistant":
                continue
            blocks = m.get("content_blocks") or []
            types = {b.get("block_type") for b in blocks}
            ot = m.get("output_tokens") or 0
            reasoning += m.get("reasoning_tokens") or 0
            if types == {"thinking"}:
                thinking += ot
                if ot >= 1500:
                    bursts.append(ot)
            thinking_blocks += sum(1 for b in blocks if b.get("block_type") == "thinking")
            if "tool_use" in types:
                tool_turns += 1
    tr = 0
    calls = []
    scripts = {}
    for it in d.get("iterations") or []:
        for c in it.get("commands") or []:
            tr += int(c.get("result_tokens") or 0)
            tool = c.get("tool_name")
            params = c.get("parameters") or {}
            if isinstance(params, str):
                params = {}
            cmd = params.get("command") or ""
            calls.append({
                "tool": tool,
                "detail": (cmd or params.get("file_path") or params.get("skill") or "")[:300],
                "result_tokens": int(c.get("result_tokens") or 0),
                "status": c.get("result_status"),
            })
            if tool == "Bash" and cmd:
                for name in SCRIPT_RE.findall(cmd):
                    scripts[name] = scripts.get(name, 0) + 1
    tu = d.get("total_token_usage") or {}
    row = {
        "task": d["task_id"],
        "rep": os.path.basename(os.path.dirname(path)),
        "status": d["final_status"],
        "score": d.get("weighted_score"),
        "desc": d.get("task_description") or "",
        "cost": tu.get("total_cost_usd") or 0.0,
        "output": tu.get("output_tokens") or 0,
        "cache_read": tu.get("cache_read_input_tokens") or 0,
        "cache_create": tu.get("cache_creation_input_tokens") or 0,
        "uncached": tu.get("uncached_input_tokens") or 0,
        "thinking_tokens": thinking,
        "thinking_blocks": thinking_blocks,
        "reasoning_tokens": reasoning,
        "bursts": sorted(bursts, reverse=True),
        "tool_result_tokens": tr,
        "tool_calls": len(calls),
        "tool_turns": tool_turns,
        "turns": d.get("total_assistant_turns") or 0,
        "iterations_n": d.get("iteration_count") or 0,
        "duration": d.get("duration_seconds") or 0.0,
        "scripts": scripts,
        "trace": calls,
    }
    derived = (row["output"] * RATES["output"] + row["cache_read"] * RATES["cache_read"]
               + row["cache_create"] * RATES["cache_create"] + row["uncached"] * RATES["uncached"])
    row["derived_cost"] = derived
    row["recon_gap"] = derived - row["cost"]
    return row


def pick_recurring(reps):
    """Drop behaviorally aberrant reps: >max(floor, 3*MAD) from median on any lever."""
    if len(reps) < 3:
        return reps, []
    keep, dropped = [], []
    med = {k: st.median([r[k] for r in reps]) for k in LEVERS}
    mad = {k: st.median([abs(r[k] - med[k]) for r in reps]) for k in LEVERS}
    for r in reps:
        bad = [k for k in LEVERS if abs(r[k] - med[k]) > max(FLOORS[k], 3 * mad[k])]
        (dropped if bad else keep).append((r, bad))
    if len(keep) < max(1, (len(reps) + 1) // 2):
        return reps, []
    return [r for r, _ in keep], [(r["rep"], b) for r, b in dropped]


def agg(reps):
    keep, dropped = pick_recurring(reps)
    out = {"n_success": len(reps), "n_used": len(keep), "dropped": dropped, "reps_used": [r["rep"] for r in keep]}
    num = ["cost", "output", "cache_read", "cache_create", "uncached", "thinking_tokens", "thinking_blocks",
           "tool_result_tokens", "tool_calls", "turns", "tool_turns", "duration", "derived_cost"]
    for k in num:
        out[k] = sum(r[k] for r in keep) / len(keep)
    scripts = {}
    for r in keep:
        for k, v in r["scripts"].items():
            scripts[k] = scripts.get(k, 0) + v / len(keep)
    out["scripts"] = scripts
    out["bursts"] = keep[0]["bursts"]
    out["bundled_calls"] = sum(v for k, v in scripts.items() if k in BUNDLED)
    out["own_script_calls"] = sum(v for k, v in scripts.items() if k not in BUNDLED)
    out["tool_mix"] = {}
    for r in keep:
        for c in r["trace"]:
            out["tool_mix"][c["tool"]] = out["tool_mix"].get(c["tool"], 0) + 1 / len(keep)
    out["trace"] = keep[0]["trace"]
    out["desc"] = keep[0]["desc"]
    out["rep_path_rep"] = keep[0]["rep"]
    return out


def load_run(run):
    tasks = {}
    for p in sorted(glob.glob(os.path.join(run, "default", "*", "*", "task.json"))):
        r = rep_metrics(p)
        r["path"] = p
        tasks.setdefault(r["task"], []).append(r)
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("opt")
    ap.add_argument("base")
    ap.add_argument("--out", default="rows.json")
    a = ap.parse_args()
    opt_raw, base_raw = load_run(a.opt), load_run(a.base)
    gap = max(abs(r["recon_gap"]) for reps in list(opt_raw.values()) + list(base_raw.values()) for r in reps)
    rows = []
    for task in sorted(set(opt_raw) & set(base_raw)):
        o = [r for r in opt_raw[task] if r["status"] == "SUCCESS"]
        b = [r for r in base_raw[task] if r["status"] == "SUCCESS"]
        if not o or not b:
            continue
        O, B = agg(o), agg(b)
        row = {"task": task, "desc": B["desc"], "opt": O, "base": B,
               "n_opt": O["n_used"], "n_base": B["n_used"]}
        for k in ["cost", "thinking_tokens", "thinking_blocks", "tool_result_tokens", "tool_calls", "turns",
                  "tool_turns", "duration", "output", "cache_read", "cache_create", "uncached"]:
            row["d_" + k] = O[k] - B[k]
        THR = (("tool_calls", 3), ("turns", 3), ("tool_result_tokens", 5000), ("thinking_tokens", 1500))
        row["levers_moved"] = [k for k, thr in THR if abs(row["d_" + k]) >= thr]
        row["real"] = bool(row["levers_moved"])
        rows.append(row)
    json.dump({"reconcile_max_gap_usd": gap, "rows": rows,
               "opt_only_success": sorted(t for t in opt_raw if any(r["status"] == "SUCCESS" for r in opt_raw[t])
                                          and not any(r["status"] == "SUCCESS" for r in base_raw.get(t, []))),
               "base_only_success": sorted(t for t in base_raw if any(r["status"] == "SUCCESS" for r in base_raw[t])
                                           and not any(r["status"] == "SUCCESS" for r in opt_raw.get(t, [])))},
              open(a.out, "w"), indent=1)
    print("both-solved tasks:", len(rows), "| max reconciliation gap $%.6f" % gap)


if __name__ == "__main__":
    main()
