import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, json

with open('/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-tmp/per_task_rows.json') as f:
    data = json.load(f)
rows = data['rows']
def s(k): return sum(r[k] for r in rows)
n = len(rows)
base_cost=s('b_cost'); opt_cost=s('o_cost')
base_time=s('b_time'); opt_time=s('o_time')
base_tr=s('b_tool_result'); opt_tr=s('o_tool_result')
base_tc=s('b_tool_calls'); opt_tc=s('o_tool_calls')
base_turns=s('b_turns'); opt_turns=s('o_turns')
base_out=s('b_output'); opt_out=s('o_output')
metrics = [
    (f'Total cost (${base_cost:.1f}→${opt_cost:.1f})', base_cost, opt_cost),
    (f'Total time ({base_time/60:.0f}→{opt_time/60:.0f} min)', base_time, opt_time),
    (f'Cost/task (${base_cost/n:.2f}→${opt_cost/n:.2f})', base_cost/n, opt_cost/n),
    (f'Output tokens ({base_out//1000}k→{opt_out//1000}k)', base_out, opt_out),
    (f'Tool-result tokens ({base_tr//1000}k→{opt_tr//1000}k)', base_tr, opt_tr),
    (f'Tool-calls ({base_tc}→{opt_tc})', base_tc, opt_tc),
    (f'Cost-model turns ({base_turns}→{opt_turns})', base_turns, opt_turns),
]
labels=[m[0] for m in metrics]; base_vals=[m[1] for m in metrics]; opt_vals=[m[2] for m in metrics]
opt_pct=[ov/bv*100 if bv else 100 for bv,ov in zip(base_vals,opt_vals)]
fig,ax=plt.subplots(figsize=(11,6))
y=list(range(len(metrics))); h=0.35
ax.barh([i+h/2 for i in y],[100]*len(y),h,color='#888888',label='BASE',alpha=0.8)
ax.barh([i-h/2 for i in y],opt_pct,h,color='#0072B2',label='OPT',alpha=0.8)
for i,(pct,bv,ov) in enumerate(zip(opt_pct,base_vals,opt_vals)):
    red=(1-pct/100)*100
    ax.text(pct+0.5,i-h/2,f'−{red:.1f}%' if red>0 else f'+{-red:.1f}%',va='center',fontsize=8,color='#333')
ax.set_yticks(y); ax.set_yticklabels(labels,fontsize=9)
ax.set_xlabel('Value relative to BASE (BASE=100%)',fontsize=9)
ax.set_xlim(0,115); ax.axvline(100,color='gray',linewidth=0.7,linestyle='--')
ax.legend(loc='lower right',fontsize=9)
ax.set_title('uipath-maestro-bpmn: OPT vs BASE (normalized, BASE=100%)',fontsize=11)
plt.tight_layout()
plt.savefig('/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-tmp/images/overall-results.png',dpi=150,bbox_inches='tight')
print('Chart saved')
