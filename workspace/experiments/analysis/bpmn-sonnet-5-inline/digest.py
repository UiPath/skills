#!/usr/bin/env python3
"""Per-task behavioral digest for narrative writing. Draws a *recurring* rep
(median-cost among surviving reps) from each arm and compresses its action trace."""
import json, os, statistics, collections, itertools, sys

OUT = "/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-sonnet-5-inline"
rows = json.load(open(os.path.join(OUT, "rows.json")))
reps = json.load(open(os.path.join(OUT, "reps.json")))


def compress(trace, cap=34):
    """Collapse consecutive identical labels into label xN."""
    out = []
    for k, g in itertools.groupby(trace):
        n = len(list(g))
        out.append(f"{k}x{n}" if n > 1 else k)
    if len(out) > cap:
        out = out[: cap - 1] + [f"…(+{len(out)-cap+1} more)"]
    return " → ".join(out)


def pick(task, arm, kept_names):
    cand = [r for r in reps[task][arm]
            if r["status"] == "SUCCESS" and os.path.basename(os.path.dirname(r["path"])) in kept_names]
    if not cand:
        cand = [r for r in reps[task][arm] if r["status"] == "SUCCESS"]
    cand.sort(key=lambda r: r["cost"])
    return cand[len(cand) // 2]


lines = []
for r in rows["rows"]:
    t = r["task"]
    b = pick(t, "base", set(r["base"]["reps"]))
    o = pick(t, "opt", set(r["opt"]["reps"]))
    d = r["delta"]
    lines.append(f"### {t}")
    lines.append(f"DESC: {r['task_description'][:400]}")
    lines.append(
        f"DELTA cost ${r['base']['cost']:.3f}->${r['opt']['cost']:.3f} ({d['cost']/r['base']['cost']*100:+.1f}%) "
        f"| thk {r['base']['thk_tok']:.0f}->{r['opt']['thk_tok']:.0f} ({d['thk_tok']:+.0f}) "
        f"| tr {r['base']['tr_tok']:.0f}->{r['opt']['tr_tok']:.0f} ({d['tr_tok']:+.0f}) "
        f"| calls {r['base']['tool_calls']:.1f}->{r['opt']['tool_calls']:.1f} ({d['tool_calls']:+.1f}) "
        f"| time {r['base']['time']:.0f}->{r['opt']['time']:.0f}s "
        f"| REAL={r['is_real']} levers={','.join(r['real_levers']) or 'none'} "
        f"| n(kept) B={r['base_kept']}/{r['base_success_reps']} O={r['opt_kept']}/{r['opt_success_reps']}")
    for nm, arm, rep in (("BASE", r["base"], b), ("OPT", r["opt"], o)):
        tc = collections.Counter(x.split(":")[0] for x in rep["trace"])
        uv = {k: round(v, 2) for k, v in sorted(arm["uip_verbs"].items(), key=lambda kv: -kv[1])[:6]}
        lines.append(f"{nm} rep={os.path.basename(os.path.dirname(rep['path']))} "
                     f"tools={dict(tc)} uip={uv} inline_py={arm['inline_py']:.1f} "
                     f"bursts>=1.5k={rep['bursts'][:8]}")
        lines.append(f"{nm} TRACE: {compress(rep['trace'])}")
    lines.append("")

open(os.path.join(OUT, "digest.txt"), "w").write("\n".join(lines))
print(f"wrote digest.txt ({len(lines)} lines, {len(rows['rows'])} tasks)")
