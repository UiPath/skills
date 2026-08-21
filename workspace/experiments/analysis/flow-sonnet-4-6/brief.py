#!/usr/bin/env python3
import json,sys,re,collections
D=json.load(open("rows.json")); rows={r["task"]:r for r in D["rows"]}
for task in sys.argv[1:]:
    r=rows[task]
    print("###", task, "| Δ$%+.2f"%r["d_cost"])
    for side in ("base","opt"):
        s=r[side]; mix=collections.Counter(c["tool"] for c in s["trace"])
        top=sorted(s["trace"], key=lambda c:-c["result_tokens"])[:4]
        sc=", ".join("%s×%d"%(k,int(v)) for k,v in sorted(s["scripts"].items(), key=lambda kv:-kv[1]))
        print(" %-4s $%.2f calls %d turns %d TR %dk out %dk thk %d | mix %s | scripts: %s"%(
            side.upper(), s["cost"], s["tool_calls"], s["turns"], s["tool_result_tokens"]/1000,
            s["output"]/1000, s["thinking_blocks"], dict(mix), sc or "-"))
        for c in top: print("     big: %-5s %6d %s"%(c["tool"], c["result_tokens"], re.sub(r"\s+"," ",c["detail"])[:95]))
    print()
