#!/usr/bin/env python3
import json, sys, statistics as st
R={"out":15.0/1e6,"cr":0.30/1e6,"cc":3.75/1e6,"un":3.0/1e6}
def load(d): return json.load(open(d+"/features.json"))
def slope(xs,ys):
    mx,my=sum(xs)/len(xs),sum(ys)/len(ys)
    num=sum((a-mx)*(b-my) for a,b in zip(xs,ys)); den=sum((a-mx)**2 for a in xs)
    return num/den if den else 0
for d in ("flow-sonnet-5","flow-sonnet-4-6"):
    rows=load(d); n=len(rows)
    print("="*90); print(d, "| tasks", n)
    S=lambda s,k: sum(r[s][k] for r in rows)
    # 1. cost of a turn
    per_turn_base = S("base","cache_read")*R["cr"]/S("base","turns")
    per_turn_opt  = S("opt","cache_read")*R["cr"]/S("opt","turns")
    sl = slope([r["d_turns"] for r in rows],[r["d_cost"] for r in rows])
    print("cache-read $ per assistant turn: BASE %.4f OPT %.4f | empirical slope Δ$/Δturn = %.4f"%(per_turn_base,per_turn_opt,sl))
    # 2. flow_edit
    fe_calls=sum(r["opt"]["scripts"].get("flow_edit",0) for r in rows)
    fe_tasks=[r for r in rows if r["opt"]["scripts"].get("flow_edit",0)]
    print("flow_edit: %d calls over %d tasks (mean %.1f/task, max %d)"%(fe_calls,len(fe_tasks),
          fe_calls/max(1,len(fe_tasks)), max([r["opt"]["scripts"].get("flow_edit",0) for r in rows]+[0])))
    surplus=sum(max(0,r["opt"]["scripts"].get("flow_edit",0)-1) for r in rows)
    print("  turns that batching would remove (N-1 per task): %d  -> at slope %.4f = $%.2f (%.0f%% of the arm's Δ$%.2f)"%(
          surplus, sl, surplus*sl, 100*surplus*sl/sum(r["d_cost"] for r in rows), sum(r["d_cost"] for r in rows)))
    if fe_tasks:
        print("  Δcost on flow_edit tasks: $%.2f (mean %+.3f) | Δturns %+d | Δ$ per flow_edit call %+.4f"%(
          sum(r["d_cost"] for r in fe_tasks), sum(r["d_cost"] for r in fe_tasks)/len(fe_tasks),
          sum(r["d_turns"] for r in fe_tasks), sum(r["d_cost"] for r in fe_tasks)/fe_calls))
        print("  correlation slope Δ$ ~ flow_edit calls: %.4f $/call"%slope(
          [r["opt"]["scripts"].get("flow_edit",0) for r in rows],[r["d_cost"] for r in rows]))
    # 3. audit_flow
    af=[r for r in rows if r["opt"]["scripts"].get("audit_flow",0)]
    noaf=[r for r in rows if not r["opt"]["scripts"].get("audit_flow",0)]
    print("audit_flow: %d calls over %d tasks | Δ$ %.2f (mean %+.3f) vs no-audit tasks %d, Δ$ %.2f (mean %+.3f)"%(
        sum(r["opt"]["scripts"].get("audit_flow",0) for r in rows), len(af), sum(r["d_cost"] for r in af),
        sum(r["d_cost"] for r in af)/max(1,len(af)), len(noaf), sum(r["d_cost"] for r in noaf), sum(r["d_cost"] for r in noaf)/max(1,len(noaf))))
    multi_af=[r for r in rows if r["opt"]["scripts"].get("audit_flow",0)>=2]
    print("  tasks with >=2 audit_flow runs: %d | Δ$ %.2f (mean %+.3f) | Δvalidate %+d | Δoutput %+d"%(
        len(multi_af), sum(r["d_cost"] for r in multi_af), sum(r["d_cost"] for r in multi_af)/max(1,len(multi_af)),
        sum(r["fo"].get("validate",0)-r["fb"].get("validate",0) for r in multi_af),
        sum(r["d_output"] for r in multi_af)))
    # 4. script wins
    winners=[r for r in rows if r["d_cost"]<-0.10 and r["opt"]["bundled_calls"]>=5]
    print("script-heavy WINS (>=5 bundled calls, <-$0.10): %d  Δ$%.2f"%(len(winners),sum(r["d_cost"] for r in winners)))
    for r in sorted(winners,key=lambda r:r["d_cost"])[:5]:
        print("   %-44s Δ$%+.2f | bundled %d | ΔTR %+d | Δout %+d | Δturns %+d | BASE Write %d->%d"%(
            r["task"].replace("skill-flow-",""), r["d_cost"], r["opt"]["bundled_calls"], r["d_tool_result_tokens"],
            r["d_output"], r["d_turns"], r["fb"].get("tool_Write",0), r["fo"].get("tool_Write",0)))
    losers=[r for r in rows if r["d_cost"]>0.10 and r["opt"]["bundled_calls"]>=5]
    print("script-heavy REGRESSIONS: %d  Δ$%.2f"%(len(losers),sum(r["d_cost"] for r in losers)))
    # 5. inspection
    insp=[r for r in rows if r["fo"].get("script_source_read",0) or r["fo"].get("script_help",0)]
    print("script-inspection tasks: %d | Δ$%.2f | source tokens %d"%(len(insp),sum(r["d_cost"] for r in insp),
          sum(r["fo"].get("src_tokens",0) for r in rows)))
    # 6. BASE full-file rewrite baseline
    bw=[r for r in rows if r["fb"].get("tool_Write",0)>0]
    print("tasks where BASE used Write: %d | their Δ$ %.2f (mean %+.3f)"%(len(bw),sum(r["d_cost"] for r in bw),
          sum(r["d_cost"] for r in bw)/max(1,len(bw))))
