#!/usr/bin/env python3
"""Normalized BASE-vs-OPT bar chart (BASE=100%) for the BPMN inline-CLI A/B."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-sonnet-5-inline"
rows = json.load(open(os.path.join(OUT, "rows.json")))["rows"]
N = len(rows)
S = lambda arm, k: sum(r[arm][k] for r in rows)

PT = lambda arm, k: S(arm, k) / N  # per-task mean over the both-solved set

METRICS = [
    (f"Total cost ($, all {N} tasks)", S("base", "cost"), S("opt", "cost"), "${:,.2f}"),
    (f"Total time (s, all {N} tasks)", S("base", "time"), S("opt", "time"), "{:,.0f}s"),
    ("Cost / task ($)", PT("base", "cost"), PT("opt", "cost"), "${:,.3f}"),
    ("Thinking time / task (s, proxy)", PT("base", "thk_sec"), PT("opt", "thk_sec"), "{:,.0f}s"),
    ("Output tokens / task (all generation)", PT("base", "output_tok"), PT("opt", "output_tok"), "{:,.0f}"),
    ("Tool-result tokens / task", PT("base", "tr_tok"), PT("opt", "tr_tok"), "{:,.0f}"),
    ("Tool-calls / task", PT("base", "tool_calls"), PT("opt", "tool_calls"), "{:,.1f}"),
    ("Cost-model turns / task", PT("base", "turns"), PT("opt", "turns"), "{:,.1f}"),
]

GRAY, BLUE, RED = "#8C8C8C", "#0072B2", "#B3462F"
fig, ax = plt.subplots(figsize=(11.5, 7.0))
y = np.arange(len(METRICS))[::-1]
h = 0.36
for i, (label, b, o, fmt) in enumerate(METRICS):
    yy = y[i]
    ax.barh(yy + h / 2, 100.0, height=h, color=GRAY, zorder=3)
    ax.barh(yy - h / 2, o / b * 100.0, height=h, color=BLUE, zorder=3)
    ax.text(101.5, yy + h / 2, fmt.format(b), va="center", ha="left", fontsize=8.5, color="#333")
    ax.text(o / b * 100.0 + 1.5, yy - h / 2, fmt.format(o), va="center", ha="left",
            fontsize=8.5, color=BLUE, fontweight="bold")
    pct = (o / b - 1) * 100
    ax.text(-2.0, yy, ("−" if pct < 0 else "+") + f"{abs(pct):.1f}%", va="center", ha="right",
            fontsize=10.5, fontweight="bold", color=(BLUE if pct < 0 else RED))

ax.set_yticks(y)
ax.set_yticklabels([m[0] for m in METRICS], fontsize=10)
ax.set_xlim(-16, 128)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.set_xlabel("Value relative to BASE (BASE=100%)", fontsize=10)
ax.xaxis.grid(True, color="#DDD", zorder=0)
ax.set_axisbelow(True)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#CCC")
ax.tick_params(axis="y", length=0)
handles = [plt.Rectangle((0, 0), 1, 1, color=GRAY), plt.Rectangle((0, 0), 1, 1, color=BLUE)]
ax.legend(handles, ["BASE (canonical skill)", "OPT (RB/WS block + inline uip CLI)"],
          loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, frameon=False, fontsize=10)
ax.set_title(f"uipath-maestro-bpmn (Sonnet 5, n=1) — BASE vs OPT across {N} both-solved tasks", fontsize=12, pad=12)
fig.tight_layout()
p = os.path.join(OUT, "images", "overall-results.png")
fig.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
print("wrote", p)
for label, b, o, fmt in METRICS:
    print(f"{label:30s} {fmt.format(b):>14s} -> {fmt.format(o):>14s}  {(o-b)/b*100:+.2f}%")
