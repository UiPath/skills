import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = json.load(open("features.json"))
n = len(rows)
def S(side, k): return sum(r[side][k] for r in rows)
metrics = [
    ("Cost ($ / task)", S("base","cost")/n, S("opt","cost")/n, "{:.3f}"),
    ("Time (s / task)", S("base","duration")/n, S("opt","duration")/n, "{:.0f}"),
    ("Thinking tokens (/ task)", S("base","thinking_tokens")/n, S("opt","thinking_tokens")/n, "{:.0f}"),
    ("Tool-result tokens (/ task)", S("base","tool_result_tokens")/n, S("opt","tool_result_tokens")/n, "{:.0f}"),
    ("Tool-calls (/ task)", S("base","tool_calls")/n, S("opt","tool_calls")/n, "{:.1f}"),
    ("Cost-model turns (assistant steps / task)", S("base","turns")/n, S("opt","turns")/n, "{:.1f}"),
]
labels = [m[0] for m in metrics][::-1]
base_n = [100.0 for _ in metrics][::-1]
opt_n = [100.0*m[2]/m[1] for m in metrics][::-1]
base_v = [m[3].format(m[1]) for m in metrics][::-1]
opt_v = [m[3].format(m[2]) for m in metrics][::-1]
delta = [100.0*(m[2]-m[1])/m[1] for m in metrics][::-1]

fig, ax = plt.subplots(figsize=(11.5, 5.6))
y = range(len(labels))
h = 0.38
ax.barh([i+h/2 for i in y], base_n, height=h, color="#9A9A9A", label="BASE (skill as shipped)")
ax.barh([i-h/2 for i in y], opt_n, height=h, color="#0072B2", label="OPT (scripts + prompts)")
for i, (bv, ov, d, on) in enumerate(zip(base_v, opt_v, delta, opt_n)):
    ax.text(101, i+h/2, bv, va="center", ha="left", fontsize=8.5, color="#333333")
    ax.text(on+1, i-h/2, ov, va="center", ha="left", fontsize=8.5, color="#0072B2")
    ax.text(max(on, 100)+13, i, ("%+.1f%%" % d), va="center", ha="left", fontsize=9,
            fontweight="bold", color="#B00020" if d > 0 else "#1B7F3B")
ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("Value relative to BASE (BASE=100%)")
ax.set_xlim(0, 160)
ax.axvline(100, color="#555555", lw=0.8, ls=":")
ax.set_title("uipath-maestro-flow (Sonnet 4.6, batched scripts): BASE vs OPT per task, mean over 89 both-solved tasks", fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, frameon=False, fontsize=9)
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig("images/overall-results.png", dpi=150, bbox_inches="tight")
print("wrote images/overall-results.png")
for m in metrics: print("%-42s %14.2f -> %14.2f  %+.1f%%" % (m[0], m[1], m[2], 100*(m[2]-m[1])/m[1]))
