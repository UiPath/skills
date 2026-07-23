#!/usr/bin/env python3
"""Overall-results chart for the bpmn optimization report: BASE vs OPT per metric,
normalized to BASE=100% so metrics of different scale share one axis."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

# (label, BASE, OPT, raw-format, reduction%)  — ordered by reduction magnitude (top = biggest)
M = [
    ("Total cost\n(USD, 47 tasks)",           31.87, 24.37, "${:.2f}",   24),
    ("Total time\n(minutes, 47 tasks)",       217.6, 154.2, "{:.0f} min", 29),
    ("Cost\n(USD / task)",                    0.68,  0.52,  "${:.2f}",   24),
    ("Thinking tokens\n(tokens / task)",      12571, 6741,  "{:,.0f}",   46),
    ("Tool-result tokens\n(tokens / task)",   12707, 9924,  "{:,.0f}",   22),
    ("Tool-calls\n(calls / task)",            22.6,  18.5,  "{:.1f}",    19),
    ("Cost-model turns\n(turns / task)",      9.9,   8.2,   "{:.1f}",    17),
]

# CVD-safe: neutral gray "before", Okabe-Ito blue "after"
C_BASE, C_OPT = "#9a9a9a", "#0072B2"
INK, MUTED, GRID = "#1a1a1a", "#5c5c5c", "#e6e6e6"

labels = [m[0] for m in M]
base_pct = [100.0] * len(M)
opt_pct = [m[2] / m[1] * 100 for m in M]

fig, ax = plt.subplots(figsize=(9.2, 6.8), dpi=150)
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
y = range(len(M)); h = 0.38

b1 = ax.barh([i + h/2 for i in y], base_pct, height=h, color=C_BASE, label="BASE (canonical skill)", zorder=3)
b2 = ax.barh([i - h/2 for i in y], opt_pct, height=h, color=C_OPT, label="OPT (scripted skill + prompt)", zorder=3)

# direct raw-value labels inside/at end of each bar
for i, m in enumerate(M):
    ax.text(base_pct[i] - 1.5, i + h/2, m[3].format(m[1]), va="center", ha="right",
            color="white", fontsize=9, fontweight="bold", zorder=4)
    ax.text(opt_pct[i] - 1.5, i - h/2, m[3].format(m[2]), va="center", ha="right",
            color="white", fontsize=9, fontweight="bold", zorder=4)
    # reduction callout to the right of the BASE bar
    ax.text(101.5, i, f"−{m[4]}%", va="center", ha="left", color=C_OPT, fontsize=11, fontweight="bold")

ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9.5, color=INK)
ax.invert_yaxis()
ax.set_ylabel("Metric (unit + scope in each row)", color=MUTED, fontsize=9.5, labelpad=8)
ax.set_xlim(0, 116)
ax.xaxis.set_major_formatter(PercentFormatter())
ax.set_xticks([0, 25, 50, 75, 100])
ax.tick_params(axis="x", colors=MUTED, labelsize=8.5)
ax.set_xlabel("Value relative to BASE  (BASE = 100%)", color=MUTED, fontsize=9.5)

for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.axvline(100, color=GRID, lw=1, zorder=1)
ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
ax.set_axisbelow(True)

ax.set_title("Overall results — OPT vs BASE across 47 both-solved tasks",
             fontsize=13, fontweight="bold", color=INK, pad=26, loc="left")
ax.text(0, 1.045, "Each metric normalized to BASE = 100%. Headline: cost −24% ($31.87 → $24.37 over 47 tasks).",
        transform=ax.transAxes, fontsize=9.5, color=MUTED)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False, fontsize=9.5)

plt.tight_layout()
out = "/home/azureuser/projects/skills/tmp/experiments/bpmn-skill-report/images/overall-results.png"
plt.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)
