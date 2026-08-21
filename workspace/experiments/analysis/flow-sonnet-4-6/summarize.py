#!/usr/bin/env python3
import json, sys
D = json.load(open("rows.json")); rows = D["rows"]
R = {"output":15.0/1e6,"cache_read":0.30/1e6,"cache_create":3.75/1e6,"uncached":3.0/1e6}
def s(k, side=None):
    if side: return sum(r[side][k] for r in rows)
    return sum(r["d_"+k] for r in rows)
n=len(rows)
print("both-solved tasks:", n, "| reconcile gap $%.6f"%D["reconcile_max_gap_usd"])
print("opt-only success:", D["opt_only_success"])
print("base-only success:", D["base_only_success"])
multi=[(r["task"], r["n_base"], r["n_opt"], r["base"]["n_success"], r["opt"]["n_success"], r["base"]["dropped"], r["opt"]["dropped"]) for r in rows if r["base"]["n_success"]>1 or r["opt"]["n_success"]>1]
print("\nmulti-rep tasks (task, n_base_used, n_opt_used, n_base_succ, n_opt_succ, dropped_base, dropped_opt):")
for m in multi: print("  ", m)
print("\n--- TOTALS ---")
for k in ["cost","duration","thinking_blocks","tool_result_tokens","tool_calls","tool_turns","turns","output","cache_read","cache_create","uncached"]:
    b,o=s(k,"base"),s(k,"opt")
    print("%-20s BASE %14.2f  OPT %14.2f  Δ %14.2f  (%+.1f%%)"%(k,b,o,o-b,100*(o-b)/b if b else 0))
print("cost/task: BASE $%.4f OPT $%.4f"%(s("cost","base")/n, s("cost","opt")/n))
print("\n--- $ SAVING BY BUCKET (derived from token deltas) ---")
tot_d = s("cost")
buckets = {"thinking (g·thk)": s("thinking_tokens")*R["output"],
           "cache-read (r·(TR+G)·(T−t))": s("cache_read")*R["cache_read"],
           "non-thinking output (g·(cl+tc))": (s("output")-s("thinking_tokens"))*R["output"],
           "cache-create+uncached (w·TR)": s("cache_create")*R["cache_create"]+s("uncached")*R["uncached"]}
for k,v in buckets.items():
    print("%-34s Δ$%8.3f  share %6.1f%%"%(k,v,100*v/tot_d if tot_d else 0))
print("sum of buckets Δ$%.3f vs total Δ$%.3f (gap $%.4f)"%(sum(buckets.values()),tot_d,sum(buckets.values())-tot_d))
print("Δtokens: thinking %d | cache_read %d | non-thinking output %d | cache_create %d | uncached %d"%(
    s("thinking_tokens"), s("cache_read"), s("output")-s("thinking_tokens"), s("cache_create"), s("uncached")))
wins=[r for r in rows if r["d_cost"]<0]; regs=[r for r in rows if r["d_cost"]>0]
print("\n--- WINS/REGRESSIONS ---")
print("wins %d ($%.2f) | regressions %d ($%.2f) | flat %d"%(len(wins),sum(r["d_cost"] for r in wins),len(regs),sum(r["d_cost"] for r in regs),n-len(wins)-len(regs)))
for label,grp in (("wins",wins),("regressions",regs)):
    real=[r for r in grp if r["real"]]; noise=[r for r in grp if not r["real"]]
    print("%s: real %d ($%.2f) | noise %d ($%.2f)"%(label,len(real),sum(r["d_cost"] for r in real),len(noise),sum(r["d_cost"] for r in noise)))
    print("   noise tasks:", ", ".join(r["task"] for r in noise) or "none")
allreal=[r for r in rows if r["real"]]; allnoise=[r for r in rows if not r["real"]]
print("ALL: real %d ($%.2f) | noise %d ($%.2f)  [noise +$%.2f / -$%.2f]"%(
    len(allreal),sum(r["d_cost"] for r in allreal),len(allnoise),sum(r["d_cost"] for r in allnoise),
    sum(r["d_cost"] for r in allnoise if r["d_cost"]>0), sum(r["d_cost"] for r in allnoise if r["d_cost"]<0)))
print("\n--- BUNDLED vs OWN SCRIPTS (OPT / BASE) ---")
print("bundled calls OPT %d BASE %d | own-script calls OPT %d BASE %d"%(
  s("bundled_calls","opt"), s("bundled_calls","base"), s("own_script_calls","opt"), s("own_script_calls","base")))
bu=[r for r in rows if r["opt"]["bundled_calls"]>0]
print("tasks using a bundled script: %d/%d | of those cheaper %d, flat %d, dearer %d"%(
  len(bu), n, sum(1 for r in bu if r["d_cost"]<-0.01), sum(1 for r in bu if abs(r["d_cost"])<=0.01), sum(1 for r in bu if r["d_cost"]>0.01)))
nb=[r for r in rows if r["opt"]["bundled_calls"]==0]
print("tasks with NO bundled script: %d | cheaper %d dearer %d | Δ$%.2f"%(len(nb), sum(1 for r in nb if r["d_cost"]<0), sum(1 for r in nb if r["d_cost"]>0), sum(r["d_cost"] for r in nb)))
print("Δcost by bundled-call bucket:")
import collections
bk=collections.defaultdict(lambda:[0,0.0])
for r in rows:
    c=r["opt"]["bundled_calls"]; key="0" if c==0 else "1-3" if c<=3 else "4-7" if c<=7 else "8-14" if c<=14 else "15+"
    bk[key][0]+=1; bk[key][1]+=r["d_cost"]
for k in ["0","1-3","4-7","8-14","15+"]:
    if k in bk: print("   %-5s tasks %3d  Δ$%7.2f  mean Δ$%6.3f"%(k,bk[k][0],bk[k][1],bk[k][1]/bk[k][0]))
print("\n--- SCRIPT USAGE (OPT) ---")
sc={}
for r in rows:
    for k,v in r["opt"]["scripts"].items(): sc[k]=sc.get(k,0)+v
for k,v in sorted(sc.items(), key=lambda kv:-kv[1]): print("  %-28s %.1f"%(k,v))
used=[r for r in rows if r["opt"]["scripts"]]
print("tasks invoking any python script: %d/%d"%(len(used),n))
