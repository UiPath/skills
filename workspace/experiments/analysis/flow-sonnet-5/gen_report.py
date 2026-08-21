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
        if r["opt"]["scripts"].get("flow_edit",0)>=8: a.append("script granularity: `flow_edit` ×%d (one call per mutation)"%int(r["opt"]["scripts"]["flow_edit"]))
        if r["d_thinking_blocks"]>=8: a.append("more reasoning steps (RB1/RB2 backfire, +%d thinking blocks)"%r["d_thinking_blocks"])
        if r["d_turns"]>=10: a.append("turn inflation → cache-read (`r·(TR+G)·(T−t)`)")
        if r["d_tool_result_tokens"]>=5000: a.append("more tool-result into context (`w·TR`)")
        if not a: a.append("gray zone: only %s moved, single rep"%(", ".join(r["levers_moved"]) or "nothing"))
    else:
        if r["d_turns"]<=-8: a.append("turn collapse (WS2 chain / WS7 skip-unneeded)")
        if r["fb"].get("todo",0)>0 and r["fo"].get("todo",0)==0: a.append("dropped to-do ceremony (WS2/WS7, −%d TaskCreate/Update)"%r["fb"]["todo"])
        if r["fb"].get("tool_Grep",0)>=4 and r["fo"].get("tool_Grep",0)<r["fb"].get("tool_Grep",0): a.append("stopped fishing (WS4/WS7, Grep %d→%d)"%(r["fb"]["tool_Grep"], r["fo"].get("tool_Grep",0)))
        if r["d_thinking_blocks"]<=-5: a.append("fewer reasoning steps (RB1, %d thinking blocks)"%r["d_thinking_blocks"])
        if r["d_tool_result_tokens"]<=-5000: a.append("less tool-result in context (WS3/WS6)")
        if r["opt"]["bundled_calls"] and r["d_tool_calls"]<0: a.append("bundled script replaced manual steps")
        if not a: a.append("gray zone: only %s moved, single rep"%(", ".join(r["levers_moved"]) or "nothing"))
    return "; ".join(a[:3])

# ---------- per-task narrative ----------
HAND = {}
HAND["skill-flow-bindings-reconfigure-different-connection"]=(
 "Read `CAPABILITY.md` + `greenfield.md`, then thrashed: scaffolded the solution, `rm -rf`'d it, re-scaffolded under a second name, read the task YAML and the grader's `check_bindings.py`, hunted `flow_files` layout by grep — 48 calls / 97 turns / 30 reasoning steps before the 3 binding Edits.",
 "Pulled the connection list first, read one reference (`greenfield.md`), grepped once for the `project.uiproj` layout, scaffolded once, configured the connector, then 3 Edits — 26 calls / 53 turns / 17 reasoning steps. No bundled script.",
 "Turns fell 97→53 and calls 48→26, so the whole context is re-read 44 fewer times: cache-read carries the `r·(TR+G)·(T−t)` saving. Output tokens fell 43k→15k as well. This is a pure working-style win (WS2 plan-then-chain, WS7 skip-unneeded) with no script involvement.")
HAND["skill-flow-bellevue-weather-simulated"]=(
 "Ran a 12-call to-do ceremony (`TaskCreate`×5, `TaskUpdate`×7) around the build, `sed`-paged 250 lines of connector reference, 9 Edits, 65 calls / 127 turns / 33 reasoning steps.",
 "No to-do calls at all; read three references once, then `flow_edit` ×9 for the nodes/edges and `audit_flow` ×2 — 41 calls / 72 turns / 23 reasoning steps.",
 "Dropping the to-do ceremony and the re-paged reference removed 24 calls and 55 turns; cache-read shrinks with `(T−t)`. The bundled scripts did not reduce the call count here (9 mutation calls ≈ the 9 BASE Edits) — the saving is WS2/WS7 turn collapse.")
HAND["skill-flow-interactive-customer-escalation-triage"]=(
 "Fished through the skill with `Grep`×12 plus 9 reference `Read`s, 32 calls / 60 turns / 21 reasoning steps, 46k output tokens.",
 "Zero greps, 6 reference reads, one `audit_flow` call, 16 calls / 32 turns / 10 reasoning steps, 19k output.",
 "The grep fishing and half the reasoning steps disappeared (WS4 don't-repeat, WS7 don't-do-unnecessary): −16 calls, −28 turns, −12k tool-result, −27k output. Both `g·G` and `r·(TR+G)·(T−t)` fall.")
HAND["skill-flow-devcon-billing-invoice-lookup"]=(
 "Read the connector plugin (16.8k), `greenfield.md`, `CAPABILITY.md`, built the flow with 7 Edits, 46 calls / 78 turns / 24 reasoning steps.",
 "Read the same references (16.9k + 9.1k + 9.0k + 7.9k), then drove the build through `flow_edit` ×26 and `audit_flow` ×2 — 87 calls / 167 turns / 63 reasoning steps, and 77 of 87 calls were Bash.",
 "Same references, same artifact, but the per-mutation script turned 7 Edits into 26 script calls and the turn count more than doubled (78→167). Cache-read is charged on every one of those extra turns, so `r·(TR+G)·(T−t)` explodes: +$2.95 (+106%). Reasoning steps also went 24→63, i.e. the reasoning-budget bullets did not curb per-step thinking here.")
HAND["skill-flow-devcon-billing-dispute-resolution"]=(
 "Wrote its own `build_flow.py` once and ran it (WS5-style batching before the prompt existed), plus 4 `Write`s and 23 reference reads; 137 calls / 232 turns; $10.94 — the most expensive task in the set.",
 "Called the bundled `flow_edit` **104 times** plus `wire_agent_inputs` ×5, `audit_flow` ×3, `node_ownership` ×1; 149 calls / 261 turns / 89 reasoning steps.",
 "The bundled primitive replaced a single agent-authored batch script with 104 separate turns. Output tokens actually fell (165k→130k) because the agent stopped hand-writing JSON, but the extra 29 turns of full-context re-read outweigh it: +$1.36. This is the clearest case that per-mutation granularity is the wrong unit.")
HAND["skill-flow-multi-city-weather"]=(
 "10 reference reads, then 7 Edits to author the flow; 26 calls / 39 turns / 8 reasoning steps.",
 "Same 10 reads, then `flow_edit` ×16 + `audit_flow` ×2; 43 calls / 75 turns / 24 reasoning steps.",
 "Sixteen one-mutation script calls replaced seven batched Edits, nearly doubling turns (39→75) and tripling reasoning steps. +$1.26 (+98%), all of it cache-read on the added turns.")
HAND["skill-flow-remove-node"]=(
 "Read the flow once (19.4k) and `editing-operations.md`, then removed the node with 6 Edits; 15 calls / 31 turns / 9 reasoning steps.",
 "Read the flow, then grepped the references for expression semantics (3.1k), paged `scripts/audit_expressions.py` source (1.5k), read `node-output-wiring.md`, ran `audit_flow` ×2 and still hand-Edited 7 times; 41 calls / 76 turns / 23 reasoning steps.",
 "A 6-Edit task became a 41-call investigation because the agent inspected script source and re-derived the expression rules instead of applying them. +$1.00 (+123%) with turns +45 — script-discovery overhead with no offsetting automation (`flow_edit` was never called).")
HAND["skill-flow-e2e-escalation-orchestrator-paths"]=(
 "26 Bash + 11 reads + 7 Edits, no to-do calls; 45 calls / 73 turns / 19 reasoning steps.",
 "Added a 16-call to-do ceremony (`TaskCreate`×6, `TaskUpdate`×10), 13 reads, `flow_edit` ×7, `audit_flow` ×3, 49 Bash; 82 calls / 148 turns / 48 reasoning steps.",
 "OPT doubled turns (73→148) and re-introduced exactly the ceremony WS2/WS7 are meant to remove, while reasoning steps went 19→48. +$2.18 (+86%): cache-read on 75 extra turns dominates.")
HAND["skill-flow-feet-inches"]=(
 "Read 9 references, scaffolded in one chained Bash, 3 `registry get`s, then 2 Edits authored every node and edge; validate → format → validate; 22 calls / 39 turns / 8 reasoning steps.",
 "`cat`/`sed`-paged the same references through Bash, called `flow_edit.py --help` twice, paged 400 lines of `flow_edit.py` source (3.8k) and 250 lines of `flow_lib.py` (1.6k), grepped the references for Jint/merge/optional-chaining details, wrote 4 input JSON files, then ran `flow_edit` per node/edge; 46 calls / 78 turns / 24 reasoning steps.",
 "The script-discovery detour (2 `--help` + 2 source pages ≈ 6.3k tool-result tokens) plus per-mutation calls turned a 2-Edit build into 46 calls. +$0.98 (+90%). WS1 (\"understand the scripts before you act\") is the direct cause of the source reads.")

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
        w="All four levers are ~flat (Δcalls %+d, Δturns %+d, Δtool-result %+d, Δoutput %+d); only the dollars moved, so this is **n=1 noise**, not an optimization effect."%(
            r["d_tool_calls"], r["d_turns"], r["d_tool_result_tokens"], r["d_output"])
    if len(r["levers_moved"])==1:
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
A("Scope: the **83 tasks that succeeded in both runs** (OPT `maestro-flow-optimized-sonnet-5-full`, BASE `maestro-flow-baseline-sonnet-5`), n=1 rep per task, so every per-task number is a point estimate. Headline: the optimization **raised** cost by **+$16.95 (+12.4%)** on this set.\n")

A("## Script Generation of uipath-maestro-flow\n")
A(lead+"\n")
A("**12 out of 34 areas** can be turned into scripts, and the corresponding scripts are: `audit_flow.py` (orchestrator over the five local audits), `check_topology.py`, `audit_expressions.py`, `lint_jint.py`, `check_bindings.py`, `check_runtime_gaps.py`, `flow_edit.py`, `flow_compose.py`, `node_ownership.py`, `validate_mermaid.py`, `encode_parameter_values.py`, `wire_agent_inputs.py`, `diagnose_run.py` (plus the shared `flow_lib.py` helper, which is imported rather than invoked).\n")
A("Codifiability is taken from `/home/azureuser/projects/skills/tmp/experiments/classification/flow/classification-details-uipath-maestro-flow.md`.\n")
A("Many of the remaining 22 areas are `uip` CLI calls rather than derivations — scaffold, registry lookup, `node add`/`configure`, `validate`, `format`, `solution upload`, `flow debug`, the `eval` subtree. Those are not script targets; the working-style prompt is what is supposed to compress them, by planning the path up front and chaining independent calls into one turn (WS2) instead of issuing them one per turn.\n")
A(table+"\n")

A("## Summary\n")
A("### Overall Results\n")
A("![BASE vs OPT across the three cost dimensions](images/overall-results.png)\n")
A("Per-task means over the 83 both-solved tasks (n=1 rep each). Every measured dimension moved the wrong way: cost $1.651 → $1.856 (+12.4%), time 320s → 352s (+10.0%), reasoning steps 15.3 → 19.7 blocks (+28.9%), tool-result tokens 48,783 → 50,190 (+2.9%), tool-calls 31.9 → 36.5 (+14.5%), cost-model turns 56.3 → 64.8 (+15.2%).\n")
A("**Where the $16.95 *increase* comes from** (OPT − BASE; a negative Δ is the only bucket that improved):\n")
A("| bucket | Δ tokens (sum) | share | cost-model term |")
A("|---|---|---|---|")
buck=[("thinking (unmeasurable in this dump — see methodology)", 0, "`g·thk`"),
      ("cache-read", D("cache_read"), "`r·(TR+G)·(T−t)`"),
      ("non-thinking output = output − thinking", D("output"), "`g·(cl+tc)`"),
      ("cache-create + uncached", D("cache_create")+D("uncached"), "`w·TR`")]
tot=D("cost")
for name,tok,term in buck:
    if name.startswith("thinking"): dollars=0.0
    elif name=="cache-read": dollars=D("cache_read")*R["cr"]
    elif name.startswith("non-thinking"): dollars=D("output")*R["out"]
    else: dollars=D("cache_create")*R["cc"]+D("uncached")*R["un"]
    A("| %s | %+d | %+.1f%% | %s |"%(name, tok, 100*dollars/tot, term))
A("")
A("Note: the `Δ tokens` column holds **exact sums over the 83 tasks**, while the chart above reports **per-task means, rounded for display**, so multiplying a rounded chart delta by the 83 tasks will not exactly reproduce these sums. The exact sums and the `$` total (from `total_cost_usd`) are authoritative. Buckets sum to $16.947 = the measured total to the cent; the per-bucket dollar split reconciles to `total_cost_usd` exactly on every `task.json` (max gap $0.000000), so the split is a faithful decomposition, not an estimate.\n")

A("### Where the cost comes from before optimization — and how OPT cuts it\n")
A("**BASE is context-driven, not reasoning-driven.** Across the 83 both-solved tasks BASE spends **247.8M cache-read tokens** and **10.1M cache-create tokens** against **1.67M output tokens** and only **10.3k uncached** input tokens. Two orders of magnitude more context is re-read than is generated, because this skill's references are large (`connector/impl.md` 16.8k tokens, `file-format.md` 8.9k, `greenfield.md` 8.8k, `CAPABILITY.md` 7.7k) and a task pulls 4–10 of them into context in the first few turns, after which every later turn pays `r` on the whole pile. BASE's own pathologies add turns on top: to-do ceremony (173 `TaskCreate`/`TaskUpdate` calls), grep fishing through the references (e.g. 12 greps in `interactive-customer-escalation-triage`), scaffold-then-`rm -rf`-then-rescaffold thrash (`bindings-reconfigure-different-connection`), and 136 `validate` + 73 `format` invocations. With 4,673 assistant steps over 2,647 tool calls, the derived split of BASE's $137.07 is **54.2% cache-read + 27.5% cache-create + 0.02% uncached = 81.8% context, against 18.2% generation** — the bill is a context bill, and turns are its multiplier.\n")
A("**OPT did not cut that; it added to it.** Reference loading barely moved (2.64M → 2.49M tool-result tokens spent on skill references), while assistant steps rose 4,673 → 5,382 (+709) and tool calls 2,647 → 3,031 (+384). Cache-read therefore rose **+48.9M tokens (+19.7%)** — 86.6% of the cost increase — and output rose **+287.6k (+17.3%)**. The one genuine improvement is cache-create: **−623k tokens (−6.2%)**, i.e. the scripts really did keep some bulk output out of context (`audit_flow --json-out`, `registry get > /tmp/def.json`), but that saving (−$2.34) is swamped by the extra re-reads (+$14.68). The mechanism is visible in the dose-response: tasks that never called a bundled script (9 tasks) average **−$0.25**, tasks with 1–3 bundled calls **+$0.13**, and tasks with 15+ bundled calls **+$1.02**. Δturns correlates with Δcost at **r = 0.898**.\n")
A("Where OPT *did* win, it won by the working-style bullets, not by the scripts:\n")
A("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
A("|---|---|---|")
A("| Turn collapse — plan the path, then chain (WS2) instead of exploring turn-by-turn | `r·(TR+G)·(T−t)` | `bindings-reconfigure-different-connection` −$1.67 (97→53 turns); `ipe-ceql-where` −$0.79 (108→77); `merge-parallel-sync` −$0.39 (44→27) |")
A("| Dropped to-do ceremony (WS2/WS7) — 173 → 138 `TaskCreate`/`TaskUpdate` calls overall, 13 → 10 tasks | `g·G` + `r·(TR+G)·(T−t)` | `bellevue-weather-simulated` −$1.47 (12 → 0); `ipe-ceql-where` −$0.79 (12 → 0); `ipe-dtl-load-by-default-false` −$0.25 (13 → 0) |")
A("| Stopped fishing / re-reading (WS4/WS7) | `r·(TR+G)·(T−t)` | `interactive-customer-escalation-triage` −$1.01 (Grep 12→0, turns 60→32); only 2 wins show a Grep drop ≥4, so this mechanism is real but narrow |")
A("| Fewer reasoning steps per task (RB1) — every removed reasoning step is one fewer billed assistant turn | `g·thk` + `r·(TR+G)·(T−t)` | `bindings-reconfigure-different-connection` 30→17 blocks (−$1.67); `ipe-required-groups` 28→18 (−$0.84); `slack-channel-description` 24→16 (−$0.64); `paginated-reference-lookup` 20→13 (−$0.52) |")
A("| Bulk output to a file instead of context (WS6, `audit_flow --json-out`, `registry get > /tmp/*.json`) | `w·TR` + `r·(TR+G)·(T−t)` | `bindings-idempotent-reconfigure` −$0.45 (tool-result 45k→20k, the largest drop in the set, despite turns rising 62→83); `merge-parallel-sync` −$0.39 (29k→12k); `paginated-reference-lookup` −$0.52 (68k→50k) |")
A("")
A("**Real vs. noise.** Because each task is a single rep, a dollar difference only counts as an optimization effect when the agent **measurably did something different** on one of the four levers the prompts target: **tool-calls (≥3), cost-model turns (≥3), tool-result tokens (≥5k), or generation/thinking tokens (≥1.5k output)**. Applying that test to the wins: **35 of 35 wins are real ($−12.63); 0 are noise**, though 5 of them sit in a **gray zone** where exactly one lever moved (`transform-group-by` −$0.23, `init-validate` −$0.19, `ipe-path-params` −$0.06, `solution-select-ask` −$0.05, `eval-local-crud` −$0.01, together −$0.53). The median absolute lever movement across the set is 7 tool-calls, 14 turns, 8.6k tool-result and 4.2k output tokens, so essentially every task in this comparison changed behavior materially — this is a set of long tasks (BASE mean 32 calls / 56 turns per task), not a set of coin-flips. Under a stricter relative test (any lever moving ≥10% of its BASE value) 82 of 83 tasks still qualify; the single marginal task is `ipe-path-params` (Δ$−0.06). Note that thinking tokens themselves cannot be measured in this dump (see methodology), so the reasoning lever is judged by **thinking-block count** and total output tokens; single-burst reasoning changes are therefore gray-zone and would need replication.\n")

A("### Why cost increases in some tasks\n")
A("**48 of 83 tasks cost more (+$29.58), and all 48 are attributable rather than noise** by the four-lever test — 2 of them only marginally (`decision` +$0.02, moved output +1.9k only; `registry-discovery` +$0.04, moved turns +6 only), so those two are gray zone rather than firm effects. The regressions are concentrated: the **30 tasks in which the agent inspected the shipped scripts** (`--help` ×39, `scripts/*.py` source read ×76, 48.8k tool-result tokens of script source) carry **+$17.47** — more than the entire net regression — while the other 53 tasks net **−$0.52**.\n")
A("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
A("|---|---|---|")
A("| Script-discovery overhead — WS1 \"understand the scripts before you act\" turned into `--help` calls and paging `flow_edit.py` / `flow_lib.py` / `audit_expressions.py` source, then re-deriving the rules anyway | `w·TR` + `r·(TR+G)·(T−t)` + `g·G` | `feet-inches` +$0.98 (2 `--help`, 5.4k of source); `remove-node` +$1.00 (paged `audit_expressions.py`, never called a mutation script); `ixp-scaffold-minimal` +$0.74 |")
A("| Script granularity — `flow_edit.py` is one mutation per invocation, so an N-node flow costs N turns where BASE used 2–7 batched `Edit`s | `r·(TR+G)·(T−t)` | `devcon-billing-dispute-resolution` +$1.36 (`flow_edit` ×104 vs BASE's one self-written `build_flow.py`); `devcon-billing-invoice-lookup` +$2.95 (×26 vs 7 Edits); `multi-city-weather` +$1.26 (×16 vs 7 Edits) |")
A("| Reasoning-budget backfire — RB1/RB2 did not reduce reasoning frequency; thinking blocks rose 1,268 → 1,634 (+28.9%), and each extra reasoning step is another assistant turn billed a full context re-read | `g·thk` + `r·(TR+G)·(T−t)` | 22 tasks with ≥+8 thinking blocks carry **+$22.91**: `devcon-billing-invoice-lookup` 24→63; `e2e-escalation-orchestrator-paths` 19→48; `devcon-billing-discrepancy-detector` 25→58 |")
A("| Ceremony re-introduced instead of removed (WS2/WS7 not firing) | `g·G` | `e2e-escalation-orchestrator-paths` +$2.18 (0 → 16 to-do calls); `devcon-billing-discrepancy-detector` +$3.13 (103→149 turns) |")
A("")
A("**Real vs. noise (regressions).** By the same four-lever test: **48 of 48 regressions are real (+$29.58); 0 are noise**. Across all 83 tasks: **83 real / 0 noise** under the absolute test, and 82/83 under the stricter ≥10%-of-BASE relative test. The residual gray zone — the **7 tasks where exactly one lever moved** — nets **−$0.48** and is near-symmetric (+$0.05 across 2 tasks, −$0.53 across 5), i.e. ~3% of the headline in the *opposite* direction, so it cannot explain the regression. The direction is what matters here — this optimization is a net regression on this skill, and the attribution says why: the script set traded a small `w·TR` saving for a large `r·(TR+G)·(T−t)` cost by adding turns.\n")
A("Remediation targets implied by the regressions: (1) **batch the mutation script** — replace per-node/per-edge `flow_edit` invocations with one call that applies a whole node/edge/variable plan from a single JSON file, so an N-node flow costs one turn, not N; (2) **make the scripts self-describing in SKILL.md** so WS1 is satisfied without `--help` calls or source paging (the 30 inspection tasks are the whole regression); (3) **stop shipping a script whose job the agent still has to re-derive** — `remove-node` paged `audit_expressions.py` and then hand-edited anyway; (4) revisit RB1/RB2 wording, which increased reasoning-step count by 29% instead of curbing it.\n")

A("### How Are results Collected\n")
A("All numbers come from `<run>/default/<task>/<rep>/task.json`, computed by `extract.py` / `features.py` in this directory (`rows.json`, `features.json` hold the per-task rows).\n")
A("- **thinking tokens** — Σ `output_tokens` over `iterations[].messages[]` where the message's `content_blocks` block-types are exactly `{\"thinking\"}`. In this dump every thinking block is **redacted** and carries no tokens, e.g. `{\"block_type\": \"thinking\", \"text\": null, \"thinking\": null, \"signature\": \"EpYCCnIIEBABGAIqQ…\"}` with `\"output_tokens\": 0` and `\"reasoning_tokens\": 0`; the sum is therefore **0 in both arms** (BASE 14 thinking messages carry any tokens at all) and message-level `output_tokens` already sums to within 12k of `total_token_usage.output_tokens`. Thinking cost is consequently **not separable** here: this report uses **thinking-block count** (BASE 1,268 → OPT 1,634) as the reasoning-frequency proxy and total `output_tokens` as the generation lever.")
A("- **tool-result tokens** — Σ `result_tokens` over `iterations[].commands[]`, e.g. `{\"tool_name\": \"Read\", \"result_tokens\": \"7913\"}`.")
A("- **tool-calls** — `len(iterations[].commands[])`. A **script invocation** is a `commands[]` entry with `tool_name == \"Bash\"` whose `parameters.command` matches `python3 …/<script>.py`; a `Read`/`cat`/`sed` of the script source does **not** count (those are tallied separately as script-source reads). Counted per script: `flow_edit` 373, `audit_flow` 139, `wire_agent_inputs` 10, `node_ownership` 4, `encode_parameter_values` 3, `flow_compose` 1 in OPT; the agent's own scripts (`find_channel`, `paginate_drive`, `paginate_slack_channels`) are tracked apart from the bundled ones.")
A("- **cost-model turns T** — count of assistant messages in `iterations[].messages[]` (each is one billed step: think → call tools → observe). Reported as \"cost-model turns\"; the number of tool-calling messages equals the tool-call count in both arms (no batching was observed in either run), which is why the two rows move together.")
A("- **cost / cache buckets** — `total_token_usage.total_cost_usd`, `.cache_read_input_tokens`, `.cache_creation_input_tokens`, `.output_tokens`, `.uncached_input_tokens`, e.g. `{\"uncached_input_tokens\": 507, \"output_tokens\": 8236, \"cache_creation_input_tokens\": 69123, \"cache_read_input_tokens\": 836307, \"total_cost_usd\": 0.63516435}`.")
A("- **time** — `duration_seconds`; **task instruction** — `task_description`; **ordered action trace** — `iterations[].commands[]` walked in order.")
A("Bucket **token counts are read directly**; `total_cost_usd` is the only dollar figure stored, so per-bucket dollars are derived as tokens × rate (output $15/M, cache-read $0.30/M, cache-create $3.75/M, uncached $3/M). Reconciliation was verified on **every** `task.json` in both runs: max |derived − `total_cost_usd`| = **$0.000000**.\n")
A("Scope: tasks with ≥1 `final_status == \"SUCCESS\"` rep in **both** runs → 83 tasks; only successful reps are used. Every both-solved task has **n=1** successful rep in each arm, so no repeat-aggregation or outlier exclusion was needed (0 reps excluded) and all per-task figures are point estimates. For completeness outside the scope: BASE produced 92 successes vs OPT 84 — 9 tasks solved only by BASE (`bindings-no-duplicates`, `file-attachment-debug`, `group-to-subflow`, `ipe-jira-lifecycle`, `ipe-searchable-joins`, `ixp-e2e-invoice-extraction-greenfield`, `move-node`, `scheduled-trigger`, `wiki-pageviews`) against 1 solved only by OPT (`customer-escalation`), so the cost regression comes with a success-rate regression.\n")

A("## Case Analysis\n")
A("## Reference\n")
A("### Per Task Table\n")
bu=[r for r in rows if r["opt"]["bundled_calls"]>0]
dom=[r for r in rows if r["d_cost"]>0 and (r["opt"]["scripts"].get("flow_edit",0)>=8 or insp(r))]
A("Script usage & benefit: **74 of 83** tasks invoked a bundled script; of those **26 got cheaper, 1 flat, 47 more expensive**. The 9 tasks that invoked no bundled script net **−$2.21**. A bundled script (per-mutation `flow_edit`, or the `--help`/source-reading detour needed to use one) is the **dominant driver in %d regressions**. Δthinking column reports **thinking-block count** and the $ of the Δ**output** tokens, because thinking tokens are 0/unrecoverable in this dump (see methodology).\n"%len(dom))
A("| # | task | Δcost | Δthinking blk (Δoutput $) | Δtool-result tok | Δtool-calls | Δtime | scripts fe/af/other | attribution (ranked) |")
A("|---|---|---|---|---|---|---|---|---|")
for i,r in enumerate(rows,1):
    fe=int(r["opt"]["scripts"].get("flow_edit",0)); af=int(r["opt"]["scripts"].get("audit_flow",0))
    other=int(sum(v for k,v in r["opt"]["scripts"].items() if k in BUNDLED and k not in ("flow_edit","audit_flow")))
    A("| %d | %s | $%.2f→$%.2f (%+.0f%%) | %+d (%+.3f) | %+d | %+d | %.0fs→%.0fs (%+.0f%%) | %d/%d/%d | %s |"%(
        i, r["task"].replace("skill-flow-",""), r["base"]["cost"], r["opt"]["cost"], pct(r["base"]["cost"],r["opt"]["cost"]),
        r["d_thinking_blocks"], r["d_output"]*R["out"], r["d_tool_result_tokens"], r["d_tool_calls"],
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
