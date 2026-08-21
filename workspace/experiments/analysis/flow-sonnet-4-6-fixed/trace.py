#!/usr/bin/env python3
import json, sys, re
D=json.load(open("rows.json")); rows={r["task"]:r for r in D["rows"]}
task=sys.argv[1]; r=rows[task]
for side in ("base","opt"):
    print("=== %s %s  cost $%.3f calls %d turns %d TR %dk out %dk thkblk %d"%(
        side.upper(), task, r[side]["cost"], r[side]["tool_calls"], r[side]["turns"],
        r[side]["tool_result_tokens"]/1000, r[side]["output"]/1000, r[side]["thinking_blocks"]))
    for i,c in enumerate(r[side]["trace"]):
        d=re.sub(r"\s+"," ",c["detail"])[:118]
        print("  %2d %-6s %6d  %s"%(i+1,c["tool"],c["result_tokens"],d))
    print()
