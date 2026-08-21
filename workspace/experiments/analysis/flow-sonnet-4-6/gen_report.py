#!/usr/bin/env python3
import json, re, collections

rows = json.load(open("features.json"))
rows.sort(key=lambda r: r["d_cost"])
n = len(rows)
R = {"out": 15.0/1e6, "cr": 0.30/1e6, "cc": 3.75/1e6, "un": 3.0/1e6}
def S(side,k): return sum(r[side][k] for r in rows)
def D(k): return sum(r["d_"+k] for r in rows)
BUNDLED = {"flow_edit","flow_compose","audit_flow","check_topology","audit_expressions","lint_jint",
           "check_bindings","check_runtime_gaps","node_ownership","validate_mermaid",
           "encode_parameter_values","wire_agent_inputs","diagnose_run"}

cls = open("cls_table.md").read()
lead = cls.split("LEAD:::")[1].split("\nTABLE:::")[0].strip()
table = cls.split("TABLE:::\n")[1].strip()

def pct(a,b): return 100.0*(b-a)/a if a else 0.0
def insp(r): return r["fo"].get("script_source_read",0) or r["fo"].get("script_help",0)

wins=[r for r in rows if r["d_cost"]<0]; regs=[r for r in rows if r["d_cost"]>0]
real=[r for r in rows if r["real"]]; noise=[r for r in rows if not r["real"]]
I=[r for r in rows if insp(r)]; NI=[r for r in rows if not insp(r)]
fe_heavy=[r for r in rows if r["opt"]["scripts"].get("flow_edit",0)>=8]
thk_up=[r for r in rows if r["d_thinking_blocks"]>=8]

def money(g): return sum(r["d_cost"] for r in g)
def names(g,k=6): return ", ".join("`%s`"%r["task"].replace("skill-flow-","") for r in g[:k])

def attribution(r):
    a=[]
    if r["d_cost"]>0:
        if insp(r):
            bits=[]
            if r["fo"].get("script_help",0): bits.append("`--help` ×%d"%r["fo"]["script_help"])
            if r["fo"].get("script_source_read",0): bits.append("script source read ×%d"%r["fo"]["script_source_read"])
            a.append("script-discovery overhead (WS1 backfire: %s)"%", ".join(bits))
        if r["opt"]["scripts"].get("flow_edit",0)>=5: a.append("script granularity: `flow_edit` ×%d (one call per mutation)"%int(r["opt"]["scripts"]["flow_edit"]))
        if r["d_thinking_tokens"]>=3000: a.append("bigger reasoning bursts (RB2 backfire, +%.1fk thinking tok)"%(r["d_thinking_tokens"]/1000))
        if r["d_turns"]>=10: a.append("turn inflation → cache-read (`r·(TR+G)·(T−t)`)")
        if r["d_tool_result_tokens"]>=5000: a.append("more tool-result into context (`w·TR`)")
        if not a:
            a.append("gray zone: only %s moved, single rep"%", ".join(r["levers_moved"]) if r["levers_moved"] else "n=1 noise (no lever moved materially)")
    else:
        if r["d_turns"]<=-8: a.append("turn collapse (WS2 chain / WS7 skip-unneeded)")
        if r["fb"].get("todo",0)>0 and r["fo"].get("todo",0)==0: a.append("dropped to-do ceremony (WS2/WS7, −%d TaskCreate/Update)"%r["fb"]["todo"])
        if r["fb"].get("tool_Grep",0)>=4 and r["fo"].get("tool_Grep",0)<r["fb"].get("tool_Grep",0): a.append("stopped fishing (WS4/WS7, Grep %d→%d)"%(r["fb"]["tool_Grep"], r["fo"].get("tool_Grep",0)))
        if r["d_thinking_tokens"]<=-3000: a.append("less reasoning (RB1, %.1fk thinking tok)"%(r["d_thinking_tokens"]/1000))
        if r["d_tool_result_tokens"]<=-5000: a.append("less tool-result in context (WS3/WS6, %+dk)"%(r["d_tool_result_tokens"]/1000))
        if r["fb"].get("tool_Write",0)>r["fo"].get("tool_Write",0): a.append("stopped full-file rewrites (WS5, Write %d→%d)"%(r["fb"]["tool_Write"], r["fo"].get("tool_Write",0)))
        if r["opt"]["bundled_calls"] and r["d_tool_calls"]<0: a.append("bundled script replaced manual steps")
        if not a:
            a.append("gray zone: only %s moved, single rep"%", ".join(r["levers_moved"]) if r["levers_moved"] else "n=1 noise (no lever moved materially)")
    return "; ".join(a[:3])

# ---------- per-task narrative ----------
HAND = {}
HAND["skill-flow-ixp-invoice-extraction-simulated"]=(
 "16 `Read`s including the flow itself twice at 22.7k and 14.3k tokens, three full-file `Write`s and one `Edit`; 50 calls / 82 turns; 136k tool-result and 53k output tokens.",
 "8 `Read`s, then `flow_edit` ×16 and `audit_flow` ×1 with 2 `Edit`s and 2 `Write`s; 45 calls / 74 turns; 59k tool-result and 27k output.",
 "The scripts replaced the read-whole-flow / rewrite-whole-flow cycle: tool-result −77k (`w·TR` and the per-turn `r` base both fall) and output −26k (`g·(cl+tc)`), with turns also down 8. −$1.06 (−38%), the largest win in the set and the clearest case where a bundled script paid for itself.")
HAND["skill-flow-ixp-integration-handle-routing"]=(
 "44 calls / 75 turns, 11 reasoning blocks totalling 16.0k thinking tokens, 51k tool-result, 31k output.",
 "21 calls / 39 turns, 7 reasoning blocks totalling 5.4k thinking tokens, 30k tool-result, 15k output; `flow_edit` ×1, `audit_flow` ×1.",
 "Every lever moved the right way at once: −23 calls, −36 turns, −21k tool-result, −10.6k thinking. −$0.99 (−57%). The turn halving is the dominant term (`r·(TR+G)·(T−t)`), with RB1 visible in the thinking drop.")
HAND["skill-flow-group-to-subflow"]=(
 "5 `Read`s (the flow at 19.4k, `file-format.md` 8.9k, `editing-operations.md` 8.6k, `CAPABILITY.md` 7.7k), one delegated `Agent` call, then a single full-file `Write` that emitted 49k output tokens; 13 calls / 27 turns.",
 "4 `Read`s (the same 19.4k flow, `CAPABILITY.md`, and two targeted 3.5k/2.5k reference slices), the same `Agent` call, 6 `Bash` steps and **no** `Write`; 13 calls / 26 turns; 34k tool-result, 28k output. No bundled script.",
 "Identical call and turn counts — the saving is entirely in what was generated and written: output 49k→28k and tool-result 48k→34k, i.e. `g·(cl+tc)` plus `w·TR`. −$0.62 (−42%) with zero script involvement; this is WS5 (edit, don't rewrite) and WS3 (read the slice, not the file).")
HAND["skill-flow-bellevue-weather-simulated"]=(
 "21 calls / 39 turns but 25.7k thinking tokens, including a single 18.5k-token burst; 47k tool-result, 38k output.",
 "30 calls / 52 turns with 6.0k thinking tokens, largest burst 3.7k; 30k tool-result, 13k output; `audit_flow` ×1.",
 "Turns rose 13, yet cost fell 37% because the 18.5k reasoning burst collapsed to 3.7k and output fell 25k: `g·thk` and `g·(cl+tc)` dominate this task. −$0.52. This is the cleanest RB1 win in the set — and a reminder that turns are not the only term.")
HAND["skill-flow-feet-inches"]=(
 "38 calls / 66 turns, 9 reasoning blocks, 34k tool-result, 21k output.",
 "17 calls / 32 turns, 8 reasoning blocks, 33k tool-result, 22k output; `audit_flow` ×1.",
 "Tool-result and output are flat; the entire −$0.51 (−39%) comes from halving calls (38→17) and turns (66→32), i.e. `r·(TR+G)·(T−t)` with the same context. Note the contrast with the Sonnet-5 arm, where this same task regressed +90% because the agent paged the script sources.")
HAND["skill-flow-customer-escalation-simulated"]=(
 "9 `Read`s (`planning-arch.md` 11.7k, connector plugin 9.7k, `greenfield.md` 8.8k, `CAPABILITY.md` 7.7k), 34 `Bash`, 5 `Edit`s; 49 calls / 78 turns; 16k output.",
 "11 `Read`s (including the flow twice at 10.8k and 10.2k), 56 `Bash`, 5 `Edit`s, `audit_flow` ×4; 73 calls / 125 turns; 41k output, 15 reasoning blocks.",
 "The four `audit_flow` runs did not converge the build: output rose 16k→41k and Bash 34→56, so turns rose 78→125 while tool-result barely moved (79k→82k). +$1.08 (+67%) is `g·(cl+tc)` plus cache-read on 47 extra turns — the audit findings were re-planned rather than applied.")
HAND["skill-flow-ipe-generate-schema"]=(
 "5 `Read`s (connector plugin 16.8k, `greenfield.md`, `CAPABILITY.md`), a `registry search` returning 4.1k, 15 `Bash`, 4 `Edit`s; 25 calls / 49 turns; 53k tool-result.",
 "6 `Read`s, 35 `Bash` (including `encode_parameter_values` ×1 and `audit_flow` ×1), 4 `Edit`s; 46 calls / 72 turns; 46k tool-result.",
 "Tool-result fell 7k, so context per step improved — but the work was decomposed into 20 more Bash steps and 23 more turns. +$0.79 (+95%): the added `r·(TR+G)·(T−t)` on those turns more than cancels the smaller payloads. `encode_parameter_values` was used correctly and is not the cause; the turn sprawl around it is.")
HAND["skill-flow-hitl-quality-boolean-decision"]=(
 "8 `Read`s (`greenfield.md` 8.8k, `CAPABILITY.md` 7.7k, the HITL quickform reference 5.6k), 4 `Bash` including one chained double `registry get` (3.7k), and a single `Write`; 14 calls / 28 turns; 33k tool-result.",
 "6 `Read`s, 22 `Bash` (including `audit_flow` ×3 and a grep for variable semantics), 3 `Edit`s; 32 calls / 57 turns; 25k tool-result.",
 "A 14-call task became 32 calls and 57 turns even though tool-result *fell* 8k. +$0.31 (+43%) is pure turn inflation (`r·(TR+G)·(T−t)`) — the textbook shape of this arm's regressions: less context per step, many more steps.")
HAND["skill-flow-wiki-pageviews"]=(
 "15 calls / 30 turns, 20.7k thinking tokens, 51k tool-result, 40k output.",
 "35 calls / 61 turns, 37.3k thinking tokens, 40k tool-result, 46k output; `flow_edit` ×8, `audit_flow` ×?.",
 "Both reasoning and turns went up: thinking +16.6k (`g·thk` ≈ +$0.25 on its own) and turns +31. Tool-result fell 11k, which is not enough. +$0.48 (+41%) — RB2 fired where it should have reserved depth, and the per-mutation `flow_edit` calls added the turns.")
def before_after(r):
    if r["task"] in HAND: return HAND[r["task"]]
    fb,fo=r["fb"],r["fo"]
    def mix(f):
        parts=[("Read",f.get("tool_Read",0)),("Bash",f.get("tool_Bash",0)),("Edit",f.get("tool_Edit",0)),
               ("Write",f.get("tool_Write",0)),("Grep",f.get("tool_Grep",0)),("todo",f.get("todo",0))]
        return ", ".join("%s×%d"%(k,v) for k,v in parts if v)
    b="%s; %d calls / %d turns / %d reasoning steps; %dk tool-result."%(
        mix(fb), r["base"]["tool_calls"], r["base"]["turns"], r["base"]["thinking_blocks"], r["base"]["tool_result_tokens"]/1000)
    sc=", ".join("`%s`×%d"%(k,int(v)) for k,v in sorted(r["opt"]["scripts"].items(), key=lambda kv:-kv[1]) if k in BUNDLED)
    o="%s; %d calls / %d turns / %d reasoning steps; %dk tool-result.%s"%(
        mix(fo), r["opt"]["tool_calls"], r["opt"]["turns"], r["opt"]["thinking_blocks"], r["opt"]["tool_result_tokens"]/1000,
        (" Bundled scripts: "+sc+".") if sc else " No bundled script.")
    if r["real"]:
        moved=", ".join("Δ%s %+d"%(k.replace("tool_result_tokens","tool-result").replace("tool_calls","calls").replace("output","output tok"), r["d_"+k]) for k in r["levers_moved"])
        w=("%s. %s"%("Cost rose" if r["d_cost"]>0 else "Cost fell", moved))
        if r["d_cost"]>0:
            if r["d_turns"]>0:
                w+=". The %d added assistant turns are each billed a full context re-read (`r·(TR+G)·(T−t)`), which is where the money goes."%r["d_turns"]
            else:
                w+=". Turns did not rise (Δ%+d), so the increase sits in generation (`g·G`) and in what was written into context (`w·TR`)."%r["d_turns"]
        else:
            if r["d_turns"]<0:
                w+=". %d fewer assistant turns means %d fewer full-context re-reads (`r·(TR+G)·(T−t)`), plus lower generation (`g·G`)."%(-r["d_turns"], -r["d_turns"])
            else:
                w+=". Turns did not fall (Δ%+d), so the saving is in generation (`g·G`) and in context written per turn (`w·TR`)."%r["d_turns"]
    else:
        w="All four levers are ~flat (Δcalls %+d, Δturns %+d, Δtool-result %+d, Δthinking %+d); only the dollars moved, so this is **n=1 noise**, not an optimization effect."%(
            r["d_tool_calls"], r["d_turns"], r["d_tool_result_tokens"], r["d_thinking_tokens"])
    if len(r["levers_moved"])==1 and r["real"]:
        w+=" Only one lever moved (%s), and the swing is $%.3f, so treat this as **gray zone** needing replication rather than a firm effect."%(r["levers_moved"][0], r["d_cost"])
    return b,o,w

# ---------- report ----------
L=[]
A=L.append
A("# uipath-maestro-flow skill optimization — cost-reduction report\n")
A("Cost reduction is measured by **3 cost dimensions** — (1) thinking tokens, (2) tool-result tokens, (3) tool-calls/turns — targeted by **3 optimization techniques**:\n")
A("- **Scripted skills**: turn deterministic procedures found in the skill files into scripts to cut tool-calls/turns; they also cut thinking (the agent doesn't re-derive an encoded procedure) and, for some scripts, tool-result tokens (output written to a file instead of into context).")
A("- **Thinking budget prompt (RB1, RB2)**: softly curb reasoning to cut thinking tokens.")
A("- **Working style prompt (WS1–WS7)**: 7 bullets, each targeting different cost dimensions.\n")
A("Scope: the **88 tasks that succeeded in both runs** (OPT `maestro-flow-optimized-sonnet-4-6`, BASE `maestro-flow-baseline-sonnet-4-6`, model `claude-sonnet-4-6`), n=1 rep per task, so every per-task number is a point estimate. Headline: the optimization hit three of its four target levers — tool-result tokens **−14.0%**, output **−6.5%**, thinking **−0.4%** — and still **raised** cost by **+$6.84 (+8.7%)**, because cost-model turns rose **+15.4%** and cache-read is the dominant cost term.\n")

A("## Script Generation of uipath-maestro-flow\n")
A(lead+"\n")
A("**12 out of 34 areas** can be turned into scripts, and the corresponding scripts are: `audit_flow.py` (orchestrator over the five local audits), `check_topology.py`, `audit_expressions.py`, `lint_jint.py`, `check_bindings.py`, `check_runtime_gaps.py`, `flow_edit.py`, `flow_compose.py`, `node_ownership.py`, `validate_mermaid.py`, `encode_parameter_values.py`, `wire_agent_inputs.py`, `diagnose_run.py` (plus the shared `flow_lib.py` helper, which is imported rather than invoked).\n")
A("Codifiability is taken from `/home/azureuser/projects/skills/tmp/experiments/classification/flow/classification-details-uipath-maestro-flow.md`.\n")
A("Many of the remaining 22 areas are `uip` CLI calls rather than derivations — scaffold, registry lookup, `node add`/`configure`, `validate`, `format`, `solution upload`, `flow debug`, the `eval` subtree. Those are not script targets; the working-style prompt is what is supposed to compress them, by planning the path up front and chaining independent calls into one turn (WS2) instead of issuing them one per turn.\n")
A(table+"\n")

A("## Summary\n")
A("### Overall Results\n")
A("![BASE vs OPT across the three cost dimensions](images/overall-results.png)\n")
A("Per-task means over the 88 both-solved tasks (n=1 rep each). Mixed directions, and the two that fell are the two that cost least: tool-result tokens 41,651 → 35,826 (−14.0%) and thinking tokens 7,280 → 7,249 (−0.4%), against tool-calls 22.3 → 26.1 (+17.1%), cost-model turns 40.3 → 46.5 (+15.4%), time 332s → 342s (+2.9%) and cost $0.894 → $0.972 (+8.7%).\n")
A("**Where the $6.84 *increase* comes from** (OPT − BASE; three of the four buckets fell, and the fourth outweighs all of them):\n")
A("| bucket | Δ tokens (sum) | share | cost-model term |")
A("|---|---|---|---|")
buck=[("thinking", D("thinking_tokens"), "`g·thk`"),
      ("cache-read", D("cache_read"), "`r·(TR+G)·(T−t)`"),
      ("non-thinking output = output − thinking", D("output"), "`g·(cl+tc)`"),
      ("cache-create + uncached", D("cache_create")+D("uncached"), "`w·TR`")]
tot=D("cost")
for name,tok,term in buck:
    if name.startswith("thinking"): dollars=D("thinking_tokens")*R["out"]
    elif name=="cache-read": dollars=D("cache_read")*R["cr"]
    elif name.startswith("non-thinking"): dollars=D("output")*R["out"]
    else: dollars=D("cache_create")*R["cc"]+D("uncached")*R["un"]
    A("| %s | %+d | %+.1f%% | %s |"%(name, tok, 100*dollars/tot, term))
A("")
A("Note: the `Δ tokens` column holds **exact sums over the 88 tasks**, while the chart above reports **per-task means, rounded for display**, so multiplying a rounded chart delta by the 88 tasks will not exactly reproduce these sums. The exact sums and the `$` total (from `total_cost_usd`) are authoritative. Buckets sum to $6.835 = the measured total to the cent; the per-bucket dollar split reconciles to `total_cost_usd` exactly on every `task.json` (max gap $0.000000), so the split is a faithful decomposition, not an estimate.\n")

A("### Where the cost comes from before optimization — and how OPT cuts it\n")
A("**BASE is context-driven, but reasoning is not negligible here.** Across the 88 both-solved tasks BASE spends **104.2M cache-read tokens** and **6.82M cache-create tokens** against **1.44M output tokens**, of which **641k are thinking tokens**, plus 87k uncached input. The derived split of BASE's $78.68 is **39.7% cache-read + 32.5% cache-create + 0.3% uncached = 72.5% context, 27.5% generation (12.2 points of it thinking)** — so unlike the Sonnet-5 arm, reasoning is a real line item, but context still dominates. What runs it up: the large references parked in context and re-read every turn (`connector/impl.md` 16.8k tokens, `planning-arch.md` 11.7k, `greenfield.md` 8.8k, `CAPABILITY.md` 7.7k — 2.55M tokens of reference tool-results across 445 reference touches), full-file rewrites of the `.flow` (`group-to-subflow` emits 49k output tokens for one `Write`; `ixp-invoice-extraction-simulated` re-reads the flow at 22.7k and 14.3k tokens and `Write`s it 3 times), to-do ceremony (36 `TaskCreate`/`TaskUpdate` calls) and 86 `validate` + 73 `format` invocations.\n")
A("**OPT cut the context per call and then spent the saving on turns.** Tool-result tokens fell **−512,588 (−14.0%)** and tool-result per call fell 1,871 → 1,374; output fell **−93,309 (−6.5%)**; cache-create fell **−724,780 (−10.6%)** and uncached −14,369; thinking fell **−2,799 (−0.4%)**. Those four movements are worth −$4.16 together. But assistant steps rose 3,548 → 4,095 (**+547, +15.4%**) and tool-calls 1,959 → 2,294 (**+335, +17.1%**), and cache-read per turn *also* grew 29.4k → 34.4k, so cache-read rose **+36.65M tokens (+35.2%) = +$11.00** and swamped them. The clearest evidence that turns, not context, decide the bill: **40 regressions had tool-result *fall* and still cost +$8.21 more**, adding +433 turns between them; conversely **15 of the 22 wins are tasks whose tool-result dropped >5k, carrying −$5.39 of the −$6.54 win total**. Δturns correlates with Δcost at **r = 0.788**, ΔTR only at **r = 0.378**.\n")
A("Where OPT won, it won by shrinking what enters context per step — and here the scripts did contribute, unlike in the Sonnet-5 arm:\n")
A("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
A("|---|---|---|")
A("| Scripts replaced full-file rewrites and whole-file re-reads (WS5 edit-don't-rewrite + WS6 keep-outputs-small) | `w·TR` + `g·(cl+tc)` | `ixp-invoice-extraction-simulated` −$1.06 (tool-result 136k→59k, output 53k→27k, 3 `Write`s → `flow_edit` ×16); `ixp-scaffold-multinode` −$0.44 (59k→32k); `bindings-idempotent-reconfigure` −$0.46 (47k→30k) |")
A("| Turn collapse — plan the path, then chain (WS2/WS7) | `r·(TR+G)·(T−t)` | `ixp-integration-handle-routing` −$0.99 (75→39 turns, 44→21 calls); `feet-inches` −$0.51 (66→32 turns, 38→17 calls); `eval-simulation-crud` −$0.28 (40→19 turns, 26→10 calls) |")
A("| Stopped rewriting the whole flow file (WS5), even with no script involved | `w·TR` + `g·G` | `group-to-subflow` −$0.62 (one 49k-output `Write` → none, tool-result 48k→34k, zero bundled calls); `scheduled-trigger` −$0.22 (33k→22k) |")
A("| Shorter reasoning bursts (RB1) — measurable here because thinking tokens are recorded | `g·thk` | `bellevue-weather-simulated` −$0.52 (thinking 25.7k→6.0k, largest burst 18.5k→3.7k); `ixp-integration-handle-routing` 16.0k→5.4k; `ipe-enum` −$0.15 (25.9k→12.0k) |")
A("| Dropped to-do ceremony (WS2/WS7) — 36 → 6 `TaskCreate`/`TaskUpdate` calls overall | `g·G` | `slack-channel-description` −$0.37; `eval-inline-agent` −$0.22 |")
A("")
A("**Real vs. noise.** Because each task is a single rep, a dollar difference only counts as an optimization effect when the agent **measurably did something different** on one of the four levers the prompts target: **tool-calls (≥3), cost-model turns (≥3), tool-result tokens (≥5k), or thinking tokens (≥1.5k)**. Thinking tokens *are* recorded in this arm (unlike the Sonnet-5 dump), so all four levers are measurable and the thinking lever fires on 52 of 88 tasks. Applying the test to the wins: **21 of 22 wins are real ($−6.53); 1 is noise** (`trigger-with-filter` −$0.01). The median absolute lever movement across the set is 4 tool-calls, 7 turns, 6.6k tool-result and 3.3k thinking tokens (BASE mean 22 calls / 40 turns per task). Under a stricter relative test (any lever moving ≥10% of its BASE value) 85 of 88 tasks qualify; the 3 marginal ones are `bindings-reconfigure-different-connection`, `bindings-no-duplicates` and `interactive-customer-escalation-triage`. Nine tasks moved exactly one lever (together +$0.21) and should be treated as gray zone needing replication, especially the six whose only mover is a single thinking or output swing.\n")

A("### Why cost increases in some tasks\n")
A("**66 of 88 tasks cost more (+$13.38), and 59 of those are attributable rather than noise** by the four-lever test (7 are noise, +$0.35 in total: `add-output`, `bindings-no-duplicates`, `eval-no-auto-upload`, `hitl-smoke-completed-port`, `init-validate`, `outlook-waitfor-email`, `registry-discovery` — all cent-level). The regression profile is different from the Sonnet-5 arm: script-source snooping is rare here (7 tasks read `scripts/*.py`, 6 called `--help`, 4.9k tool-result tokens in total, +$1.81 on those tasks), and the damage is instead **turn sprawl** — the agent decomposes work that BASE did in one `Write`/`Edit` into many small `Bash` steps, with inline python rising 125 → 475 calls and `validate` 86 → 121. In **40 of the 66 regressions the tool-result tokens actually fell** while cost still rose (+$8.21, +433 turns), which is the signature of paying `r·(TR+G)·(T−t)` on extra steps rather than `w·TR` on bigger payloads.\n")
A("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
A("|---|---|---|")
A("| Turn sprawl — one `Write`/`Edit` in BASE becomes many small `Bash` steps in OPT (WS2/WS5/WS7 backfire); inline python 125 → 475 calls, `validate` 86 → 121 | `r·(TR+G)·(T−t)` | `hitl-quality-boolean-decision` +$0.31 (14→32 calls, 28→57 turns, while tool-result *fell* 33k→25k); `ipe-jira-search-triage` +$0.76 (46→87 turns, tool-result 65k→59k); `ipe-generate-schema` +$0.79 (25→46 calls, Bash 15→35, tool-result 53k→46k) |")
A("| Script granularity — `flow_edit.py` is one mutation per invocation (146 calls over 73 tasks), so an N-node flow costs N turns where BASE used a couple of batched `Edit`s | `r·(TR+G)·(T−t)` | `ixp-e2e-invoice-extraction-greenfield` +$0.67 (`flow_edit` ×19, 79→98 turns); `wiki-pageviews` +$0.48 (×8, 30→61 turns); `ipe-drive-to-slack` +$0.34 (×5, 55→73 turns) |")
A("| Unprompted reasoning bursts where RB2 should have reserved depth — aggregate thinking is flat (−0.4%) but the per-task spread is wide | `g·thk` + `r·(TR+G)·(T−t)` | `wiki-pageviews` thinking 20.7k→37.3k (+$0.48); `hitl-schema-design-simulated` 9.7k→19.8k (+$0.18); `decision` 3.7k→12.9k (+$0.03) |")
A("| More generation per task despite fewer tool-results (`audit_flow` findings re-planned rather than applied) | `g·(cl+tc)` | `customer-escalation-simulated` +$1.08 (output 16k→41k, Bash 34→56, `audit_flow` ×4); `lowcode-agent` +$0.42 (output 9k→18k); `e2e-escalation-slack-alert` +$0.43 (output 15k→24k) |")
A("")
A("**Real vs. noise (regressions).** By the same four-lever test: **59 of 66 regressions are real (+$13.03); 7 are noise (+$0.35)**. Across all 88 tasks: **80 real ($+6.49) / 8 noise ($+0.34)** — the noise is 5% of the headline and mildly asymmetric (7 positive, 1 negative), which is worth stating plainly rather than claiming perfect cancellation; even attributing all of it to luck leaves +$6.5 of measured behavior change. Under the stricter ≥10%-relative test, 85 of 88 tasks qualify. The direction is the finding: this optimization delivered on three of the four levers it targets and still lost, because it traded −$4.16 of context/generation savings for +$11.00 of cache-read on 547 extra turns.\n")
A("Remediation targets implied by the regressions: (1) **batch the mutation script** — one `flow_edit` call per node/edge is the wrong unit; accept a whole node/edge/variable plan from a single JSON file so an N-node flow costs one turn (this alone addresses the 146 `flow_edit` calls and the 40 tool-result-fell-but-cost-rose tasks); (2) **make `audit_flow` findings directly actionable** (emit an apply-patch or exact edit list) so a clean audit does not turn into a re-planning loop — `validate` calls rose 86 → 121 and output rose on several regressions; (3) **discourage decomposing a single edit into many `Bash` steps** — the WS bullets currently reward small steps and inline python (125 → 475 calls) without penalising the turn count they create; (4) keep the RB wording, which is roughly neutral here (thinking −0.4% overall), but add an explicit ceiling for the outlier bursts (`wiki-pageviews` 20.7k → 37.3k).\n")

A("### How Are results Collected\n")
A("All numbers come from `<run>/default/<task>/<rep>/task.json`, computed by `extract.py` / `features.py` in this directory (`rows.json`, `features.json` hold the per-task rows).\n")
A("- **thinking tokens** — Σ `output_tokens` over `iterations[].messages[]` where the message's `content_blocks` block-types are exactly `{\"thinking\"}`, e.g. a message with `[{\"block_type\": \"thinking\", …}]` and `\"output_tokens\": 1792`. In this arm the counts are populated (BASE 640,678 → OPT 637,879 over the 88 tasks; every task has non-zero thinking on both sides), so the thinking lever is measured directly rather than by proxy. Bursts ≥1.5k tokens are also recorded per task (largest single burst: 18,538 tokens in BASE `bellevue-weather-simulated`).")
A("- **tool-result tokens** — Σ `result_tokens` over `iterations[].commands[]`, e.g. `{\"tool_name\": \"Read\", \"result_tokens\": \"7913\"}`.")
A("- **tool-calls** — `len(iterations[].commands[])`. A **script invocation** is a `commands[]` entry with `tool_name == \"Bash\"` whose `parameters.command` matches `python3 …/<script>.py`; a `Read`/`cat`/`sed` of the script source does **not** count (those are tallied separately as script-source reads). Counted per script in OPT: `flow_edit` 146, `audit_flow` 119, `encode_parameter_values` 4, `flow_compose` 3, `node_ownership` 1 — 273 bundled calls in total, against 0 in BASE; the agent's own scripts (one `build_flow.py`) are tracked apart from the bundled ones.")
A("- **cost-model turns T** — count of assistant messages in `iterations[].messages[]` (each is one billed step: think → call tools → observe). Reported as \"cost-model turns\"; the number of tool-calling messages equals the tool-call count in both arms (no batching was observed in either run), which is why the two rows move together.")
A("- **cost / cache buckets** — `total_token_usage.total_cost_usd`, `.cache_read_input_tokens`, `.cache_creation_input_tokens`, `.output_tokens`, `.uncached_input_tokens`, e.g. `{\"uncached_input_tokens\": 507, \"output_tokens\": 8236, \"cache_creation_input_tokens\": 69123, \"cache_read_input_tokens\": 836307, \"total_cost_usd\": 0.63516435}`.")
A("- **time** — `duration_seconds`; **task instruction** — `task_description`; **ordered action trace** — `iterations[].commands[]` walked in order.")
A("Bucket **token counts are read directly**; `total_cost_usd` is the only dollar figure stored, so per-bucket dollars are derived as tokens × rate (output $15/M, cache-read $0.30/M, cache-create $3.75/M, uncached $3/M). Reconciliation was verified on **every** `task.json` in both runs: max |derived − `total_cost_usd`| = **$0.000000**.\n")
A("Scope: tasks with ≥1 `final_status == \"SUCCESS\"` rep in **both** runs → 88 tasks; only successful reps are used. Every both-solved task has **n=1** successful rep in each arm, so no repeat-aggregation or outlier exclusion was needed (0 reps excluded) and all per-task figures are point estimates. For completeness outside the scope: BASE produced 95 successes vs OPT 90 — 7 tasks solved only by BASE (`devcon-billing-discrepancy-detector`, `e2e-escalation-orchestrator-paths`, `ipe-ceql-where`, `ipe-jira-lifecycle`, `non-catalog-http-fallback`, `remove-node`, `switch`) against 2 solved only by OPT (`devcon-billing-dispute-analyst`, `rpa`), so the cost regression comes with a small success-rate regression as well.\n")

A("## Case Analysis\n")
A("## Reference\n")
A("### Per Task Table\n")
bu=[r for r in rows if r["opt"]["bundled_calls"]>0]
dom=[r for r in rows if r["d_cost"]>0 and (r["opt"]["scripts"].get("flow_edit",0)>=8 or insp(r))]
A("Script usage & benefit: **73 of 88** tasks invoked a bundled script; of those **14 got cheaper, 2 flat, 57 more expensive**. The 15 tasks that invoked no bundled script net **−$1.08**. A bundled script (per-mutation `flow_edit`, or the `--help`/source-reading detour needed to use one) is the **dominant driver in %d regressions**; the largest single win (`ixp-invoice-extraction-simulated`, −$1.06) is also script-driven, so the script effect is genuinely two-sided in this arm. Δthinking is measured directly here (tokens, and the $ at $15/M).\n"%len(dom))
A("| # | task | Δcost | Δthinking tok ($) | Δtool-result tok | Δtool-calls | Δtime | scripts fe/af/other | attribution (ranked) |")
A("|---|---|---|---|---|---|---|---|---|")
for i,r in enumerate(rows,1):
    fe=int(r["opt"]["scripts"].get("flow_edit",0)); af=int(r["opt"]["scripts"].get("audit_flow",0))
    other=int(sum(v for k,v in r["opt"]["scripts"].items() if k in BUNDLED and k not in ("flow_edit","audit_flow")))
    A("| %d | %s | $%.2f→$%.2f (%+.0f%%) | %+d (%+.3f) | %+d | %+d | %.0fs→%.0fs (%+.0f%%) | %d/%d/%d | %s |"%(
        i, r["task"].replace("skill-flow-",""), r["base"]["cost"], r["opt"]["cost"], pct(r["base"]["cost"],r["opt"]["cost"]),
        r["d_thinking_tokens"], r["d_thinking_tokens"]*R["out"], r["d_tool_result_tokens"], r["d_tool_calls"],
        r["base"]["duration"], r["opt"]["duration"], pct(r["base"]["duration"],r["opt"]["duration"]),
        fe, af, other, attribution(r)))
A("")
A("### Per Task Behavior\n")
for r in rows:
    b,o,w = before_after(r)
    A("**%s** (%+.0f%%, %s)"%(r["task"].replace("skill-flow-",""), pct(r["base"]["cost"],r["opt"]["cost"]), attribution(r).split(";")[0]))
    A("- Task: %s"%re.sub(r"\s+"," ",r["desc"]).strip()[:400])
    A("- Before (BASE): %s"%b)
    A("- After (OPT): %s"%o)
    A("- **%s** %s"%("Why cheaper:" if r["d_cost"]<0 else "Why MORE expensive:", w))
    A("")
open("report.md","w").write("\n".join(L)+"\n")
print("wrote report.md", len(L), "lines")
