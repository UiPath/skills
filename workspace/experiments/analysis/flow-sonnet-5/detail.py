#!/usr/bin/env python3
import json, collections, sys
D=json.load(open("rows.json")); rows=D["rows"]
rows.sort(key=lambda r:r["d_cost"])
def sig(t):
    c=collections.Counter(x["tool"] for x in t["trace"]); return " ".join("%s:%d"%(k,v) for k,v in c.most_common())
print("== lever delta distribution ==")
import statistics as st
for k in ["tool_calls","turns","tool_result_tokens","output"]:
    v=[abs(r["d_"+k]) for r in rows]; print(" %-18s median|Δ| %.0f  p25 %.0f  p75 %.0f  max %.0f"%(k,st.median(v),sorted(v)[len(v)//4],sorted(v)[3*len(v)//4],max(v)))
print("\n== relative-threshold check (any lever moved >=10%% of BASE) ==")
def rel(r):
    out=[]
    for k in ["tool_calls","turns","tool_result_tokens","output"]:
        b=r["base"][k] or 1
        if abs(r["d_"+k])/b >= 0.10: out.append(k)
    return out
strict=[r for r in rows if rel(r)]
print(" real(strict) %d/%d  $%.2f | marginal %d  $%.2f"%(len(strict),len(rows),sum(r["d_cost"] for r in strict),
      len(rows)-len(strict),sum(r["d_cost"] for r in rows if not rel(r))))
print(" marginal tasks:", ", ".join(r["task"] for r in rows if not rel(r)))
print("\n== TOP 12 WINS ==")
for r in rows[:12]:
    print("%-52s Δ$%+6.2f (%+5.1f%%) calls %3d→%3d turns %3d→%3d TR %6dk→%6dk out %5dk→%5dk thkblk %2d→%2d bundled %d"%(
        r["task"], r["d_cost"], 100*r["d_cost"]/r["base"]["cost"], r["base"]["tool_calls"], r["opt"]["tool_calls"],
        r["base"]["turns"], r["opt"]["turns"], r["base"]["tool_result_tokens"]/1000, r["opt"]["tool_result_tokens"]/1000,
        r["base"]["output"]/1000, r["opt"]["output"]/1000, r["base"]["thinking_blocks"], r["opt"]["thinking_blocks"],
        r["opt"]["bundled_calls"]))
print("\n== TOP 12 REGRESSIONS ==")
for r in rows[-12:][::-1]:
    print("%-52s Δ$%+6.2f (%+5.1f%%) calls %3d→%3d turns %3d→%3d TR %6dk→%6dk out %5dk→%5dk thkblk %2d→%2d bundled %d"%(
        r["task"], r["d_cost"], 100*r["d_cost"]/r["base"]["cost"], r["base"]["tool_calls"], r["opt"]["tool_calls"],
        r["base"]["turns"], r["opt"]["turns"], r["base"]["tool_result_tokens"]/1000, r["opt"]["tool_result_tokens"]/1000,
        r["base"]["output"]/1000, r["opt"]["output"]/1000, r["base"]["thinking_blocks"], r["opt"]["thinking_blocks"],
        r["opt"]["bundled_calls"]))
print("\n== correlation: Δturns vs Δcost ==")
xs=[r["d_turns"] for r in rows]; ys=[r["d_cost"] for r in rows]
mx,my=sum(xs)/len(xs),sum(ys)/len(ys)
cov=sum((a-mx)*(b-my) for a,b in zip(xs,ys)); vx=sum((a-mx)**2 for a in xs); vy=sum((b-my)**2 for b in ys)
print(" pearson r = %.3f"%(cov/(vx*vy)**0.5))
xs=[r["opt"]["bundled_calls"] for r in rows]
mx=sum(xs)/len(xs); cov=sum((a-mx)*(b-my) for a,b in zip(xs,ys)); vx=sum((a-mx)**2 for a in xs)
print(" pearson r(bundled calls, Δcost) = %.3f"%(cov/(vx*vy)**0.5))
