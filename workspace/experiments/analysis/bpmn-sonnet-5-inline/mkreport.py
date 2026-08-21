#!/usr/bin/env python3
"""Compose report.md for the Sonnet-5 BPMN inline-CLI A/B.
Numbers come from rows.json/reps.json; attribution text is authored judgment."""
import json, os, collections

OUT = "/home/azureuser/projects/skills/tmp/experiments/analysis/bpmn-sonnet-5-inline"
D = json.load(open(os.path.join(OUT, "rows.json")))
rows, meta = D["rows"], D["meta"]
reps = json.load(open(os.path.join(OUT, "reps.json")))
rows.sort(key=lambda r: r["delta"]["cost"] / r["base"]["cost"])  # rank by % cost reduction
N = len(rows)
R_OUT, R_CR, R_CC, R_UNC = 15e-6, 0.30e-6, 3.75e-6, 3e-6
S = lambda a, k: sum(r[a][k] for r in rows)
SD = lambda k: sum(r["delta"][k] for r in rows)

A = {
"skill-bpmn-callactivity-agentic-process": ("WS2/WS7 plan-then-act instead of blind CLI probing",
 "The largest win in the set and the cleanest WS2 case: the BASE trace opens `Bash`×35 **consecutively** — 35 probe calls before a single line of BPMN exists — for 46 calls total. OPT reads `structural-bpmn.md`, writes the file, and finishes in 14 calls. Tool-result falls 25,301→12,251 and every avoided call also removes its `r·(TR+G)·(T−t)` re-read tail across the remaining trace, which is why a −32-call change buys −74.3%."),
"skill-bpmn-inclusive-gateway-forkjoin": ("WS2/WS7 plan-then-act > WS3 fewer refs",
 "BASE probes in four bursts (`Bash`×9, ×4, ×4, ×9) around four reference reads, 35 calls total; OPT reads two references, greps once for the variable type, and writes — 12 calls. Tool-result −6,747 and calls −23 compound through the cached-read tail: −72.7%."),
"skill-bpmn-edit-update-node": ("WS7 don't do anything unnecessary",
 "A one-constant edit. BASE edits it in call 3 and then spends 19 more calls — `Bash`×11, a read of `structural-bpmn.md`, `Bash`×6, four `validate` runs — re-confirming a change it had already made. OPT edits and validates twice: 9 calls. Nothing was learned in BASE's extra 13 calls; they are pure `w·TR` + re-read tail. −67.4%."),
"skill-bpmn-http-weather": ("WS4/WS7 stop reading the grader > WS2 shorter path",
 "BASE spends 83 calls and reads the eval's own harness — `check_http_weather.py`, `http_weather.yaml`, `bpmn_check.py` (twice) — plus six references, 15 inline-python calls and a subagent spawn. OPT reads two references, greps eight times against the fixtures, and writes: 39 calls. Tool-result collapses 60,980→25,494 (−58%), the largest absolute tool-result cut in the set."),
"skill-bpmn-rpa-job": ("WS4/WS7 stop grep-fishing for `entryPointId`",
 "BASE issues 8 Greps — `entryPointId` three separate times, plus `uipath:bindings`, `inputOutput`, `Orchestrator.StartJob` — interleaved with six reference reads, 39 calls. OPT greps zero times and lands in 25. Tool-result barely moves (−1,427); the win is the 14 removed turns and the generation they carried."),
"skill-bpmn-hitl-completed-wired": ("WS3/WS7 skip refs > WS4 don't re-read generated metadata",
 "BASE reads 18 files: five HITL references, `SKILL.md`, and all four generated metadata JSONs (`entry-points`, `bindings_v2`, `operate`, `package-descriptor`) — then edits. OPT reads six, greps `entryPointId` once, and uses `format`×2. Calls 58→41, tool-result 52,292→32,104 (−39%). −50.5%."),
"skill-bpmn-parallel-fork-join": ("noise (levers flat)",
 "Calls −2, tool-result +397, output under the bar. BASE reads `structural-bpmn.md`; OPT reads a scratch `.txt` and writes. The −45.3% is a point-estimate swing on a 5-call task, not a measured behavior change."),
"skill-bpmn-event-trigger-start": ("WS2/WS7 plan-then-act",
 "BASE opens `Bash`×34 consecutively with no reference reads at all, then writes — 39 calls. OPT reads three references first and writes in 22, adding a `DRAFT_NOTES.md` for the enrichment handoff. Tool-result is nearly flat (−663), so this is a turn-and-generation win: −43.4%."),
"skill-bpmn-edit-add-node": ("WS7 fewer redundant validates",
 "Same three edits in both arms. BASE runs `validate` four times and re-reads `OrderIntake.bpmn` between edits (13 calls); OPT validates twice and reads once (9 calls). −42.8% on a small task where each avoided call is a large share of the trace."),
"skill-bpmn-script-jint-guidance": ("WS4 don't repeat work > WS3 skip refs",
 "BASE greps eight times for `entryPointId`/`elementId`/`inputOutput` variants and reads all five metadata files **twice** — once before writing and again after — for 71 calls. OPT greps once and reads the metadata set once: 48 calls, tool-result 41,051→31,475. −40.8%."),
"skill-bpmn-script-task-group-by": ("WS2 plan-then-act",
 "BASE runs `Bash`×14 then `Bash`×18 around a single reference read, with 14 inline-python calls, for 43 calls. OPT reads three references up front and writes in 31. Tool-result actually rises (+7,659) because OPT reads more reference text, but the 12 removed turns and lower generation still net −40.8%."),
"skill-bpmn-debug-instance-inspect": ("noise (levers flat)",
 "Calls −1, tool-result −422, output under the bar; both arms read the same two references and probe `--help` once. −37.9% is a point-estimate swing."),
"skill-bpmn-safety-sanitize": ("noise (levers flat)",
 "Identical four-Edit scrub in both arms; calls +1, tool-result +1,256. The −36.0% is not attributable."),
"skill-bpmn-edit-remove-node": ("WS7 stop re-validating",
 "Identical edit sequence; the difference is the tail — BASE closes with `Bash`×10, OPT with `Bash`×5. Calls 16→11, tool-result −2,091. −35.3%."),
"skill-bpmn-author-validate": ("WS3/WS7 skip refs > WS4 less grepping",
 "BASE reads four references and greps three times for `entryPointId`/`entryPoint` before writing (21 calls); OPT writes after five Bash calls, greps once, and reads one file back (15 calls). Tool-result 18,714→13,551. −34.8%."),
"skill-bpmn-registry-discovery": ("WS2/WS6 fewer, tighter CLI calls",
 "Both arms run the same 7 `registry` calls; BASE wraps them in 16 Bash calls with 7 inline-python invocations, OPT in 10 with 2. Calls −6, tool-result −2,129 — the discovery itself is identical, the scaffolding around it is not. −34.4%."),
"skill-bpmn-diagnose-job-traces": ("WS7 follow the ladder without extra probes",
 "Same two references, same verdict. BASE runs `Bash`×7 (including an `instance` call the ladder doesn't need); OPT runs 4 and stops at `job`/`incident`. Calls 11→8. −30.9%."),
"skill-bpmn-diagnose-deployed-drift": ("noise (levers flat)",
 "Calls +2, tool-result +866, output under the bar. OPT reads `CAPABILITY.md` and the deployed asset JSON that BASE inferred without reading. −29.6% is a point-estimate swing on a 5-call task."),
"skill-bpmn-debug-not-validation": ("WS7 don't do anything unnecessary",
 "BASE runs `Bash`×3 before writing and `Bash`×2 after (8 calls); OPT validates once before and once after (5 calls). Same artifact, same discipline verdict — the cloud-debug trap is avoided in both. −29.0%."),
"skill-bpmn-edit-add-output": ("WS4 inspect-once (dominant)",
 "BASE reads `Invoicing.bpmn` three separate times — before editing, again mid-edit, and again at the end — plus `structural-bpmn.md`. OPT reads it once and does the two edits. Tool-result 11,613→5,658 (−51%), the only lever over threshold, for −27.4%. Pure `w·TR` + re-read tail."),
"skill-bpmn-e2e-customer-escalation": ("WS6/WS3 less context per probe > WS2 fewer turns",
 "Both arms grep 12 times, so the fishing itself is unchanged; what changes is what lands in context. BASE reads nine files including `cli-conventions.md` and `CAPABILITY.md` and runs 64 calls; OPT reads eight, keeps probes tighter, and runs 46. Tool-result 54,511→28,614 (−48%) — the second-largest absolute cut. −28.2%."),
"skill-bpmn-expr-computed-js": ("WS4/WS7 stop fishing (including the grader) ",
 "BASE greps **14 times** — `entryPointId` and `uipath:input` variants over and over — and reads the eval's own `bpmn_check.py`, `check_computed_js.py` and `computed_js.yaml`. OPT greps 7 times and reads none of the harness. Tool-result 53,178→29,673 (−44%) with calls nearly flat (−3): a context win, not a turn win. −24.3%."),
"skill-bpmn-feet-inches": ("WS4/WS7 stop fishing > generation-side reduction",
 "BASE greps 12 times, reads eight files, and aborts a subagent (`TaskStop`) across 59 calls. OPT works directly against the file — `Bash`×38 then targeted reads — in 62 calls. Tool-result rises (+10,565) because OPT dumps more file content, but output tokens fall enough to net −23.8%. A mixed case: the win is generation-side, and the tool-result lever moved the wrong way."),
"skill-bpmn-timer-start": ("WS4 stop grepping for variable types",
 "BASE greps four times for `variableType`/`inputOutput`/`type=` variants around 16 Bash calls (27 total); OPT reads two references and writes, with one `format` call, in 18. Tool-result −916; the win is the 9 removed turns. −23.8%."),
"skill-bpmn-hitl-brownfield-insert": ("WS7 marginally tighter loop",
 "Same three edits, same fixture. BASE reads `hitl-node-apptask.md` mid-edit and re-reads the .bpmn at the end (26 calls); OPT front-loads its probing and skips the extra reference (23 calls). Tool-result +547 — only the call lever clears threshold, and barely. −22.3%, treat as gray-zone."),
"skill-bpmn-loop-multiply": ("WS5 less inline-python thrash",
 "BASE runs `Bash`×43 consecutively with 17 inline-python invocations — hand-rolling checks against the file — for 60 calls. OPT uses 6 inline-python calls across 48. Tool-result rises (+5,631) as OPT reads a sibling `.bpmn` for reference, but the generation saving dominates: −19.2%."),
"skill-bpmn-debug-workflow-mocked": ("noise (levers flat)",
 "Calls identical (8), tool-result −111. BASE writes an `inputs.json` first; OPT passes inputs inline. −17.1% is a point-estimate swing."),
"skill-bpmn-timer": ("noise (all four levers flat)",
 "Calls identical (4), tool-result +526. The most tightly matched pair in the set. −17.1% unattributed."),
"skill-bpmn-dice-roller": ("noise (levers flat)",
 "Calls −2, tool-result +152. BASE greps three times for `entryPointId`/`manual`; OPT reads a scratch file instead. Nothing clears threshold — −17.2% unattributed."),
"skill-bpmn-operate-diagnose-minimal-fault-triage": ("noise (levers flat)",
 "Call counts are identical (10 each) and tool-result moves +367. The arms differ in shape but not in size: BASE goes straight to `Bash`×8 with no reference reads, OPT reads `CAPABILITY.md` and `troubleshooting-guide.md` first and needs only 6 Bash calls. Same ladder, same recommended action, no lever over threshold — the −19.1% is a point-estimate swing."),
"skill-bpmn-diagnose-scoped-variables": ("noise (levers flat)",
 "Both arms issue the same five `instance` calls and reach the same scoped-variable verdict. Calls +1, tool-result −200. −16.9% unattributed."),
"skill-bpmn-gateway-sequence-flows": ("WS4 less repeated grepping (generation lever only)",
 "BASE greps nine times, `entryPointId` alone four times, across 40 calls; OPT greps six times in 39. Calls are effectively flat (−1) and tool-result −2,211, so only the output-token lever clears threshold — the win is that OPT re-derives less per turn, not that it takes fewer turns. −15.6%."),
"skill-bpmn-timer-boundary-noninterrupting": ("noise (levers flat)",
 "Calls +1, tool-result −3,412 (under the 5k bar). OPT reads two registry JSONs BASE skipped but drops five `registry` calls. −15.2% unattributed."),
"skill-bpmn-script-task-map": ("WS6 grep-instead-of-dump wins on context, WS4 backfires on turns",
 "The most internally contradictory task here. OPT greps **29 times** — the heaviest fishing in either arm — pushing calls 44→57 (+13). But because it greps the fixtures instead of dumping them, tool-result collapses 35,488→14,849 (−58%). The context saving outweighs the extra turns for a −14.3% net. Directionally this is WS6 working and WS4 failing in the same trace."),
"skill-bpmn-diagnose-validate-fix-loop": ("noise (identical traces)",
 "Byte-for-byte the same 5-call trace in both arms: validate → read → edit → validate. Calls Δ0, tool-result Δ−3. −12.9% is pure run-to-run variance and must not be credited."),
"skill-bpmn-edit-move-node": ("noise (levers flat)",
 "Calls +2, tool-result +413. OPT does one extra read-and-edit round. −5.3% unattributed."),
"skill-bpmn-queue-create-and-wait": ("WS4 stop grepping, offset by WS2 turn sprawl",
 "BASE greps seven times for `uipath:binding`/`entryPointId` variants; OPT greps zero. But OPT spends the saving back on `Bash`×14 and 10 inline-python calls, so calls rise 41→44 while tool-result falls 4,316. Net −4.6% — the fishing win is real, the turn discipline is not."),
"skill-bpmn-error-boundary-handler": ("noise (levers flat)",
 "Calls −2, tool-result +4,091 (under the 5k bar). OPT reads two extra references and a registry JSON. −4.1% unattributed."),
"skill-bpmn-calculator": ("WS6 context win vs WS2 turn sprawl — nearly cancelling",
 "OPT runs 51 calls to BASE's 37 (`Bash`×17 and ×10 runs, 8 inline-python) yet still lands cheaper, because tool-result falls 32,854→26,848: BASE read three sibling `.bpmn` files wholesale, OPT greps `entryPointId` instead. All four levers are real and they nearly cancel: −2.5%."),
"skill-bpmn-diagnose-stuck-gateway": ("turn sprawl, nearly cancelling the context win",
 "OPT takes 14 calls to BASE's 9 — including `--help` probing BASE didn't need — while tool-result falls 818. The call lever is real and points the wrong way; the −2.0% is what's left after the two offset. Gray-zone."),
"skill-bpmn-simple-approval-bpmn": ("read-first backfire (WS3)",
 "OPT reads **24 files** — four registry JSONs, all four generated metadata files, six references — against BASE's seven, pushing tool-result 39,767→52,400 (+12,633) at `w·TR` plus the re-read tail over a 78-call trace. Calls are flat (+2) and it still lands +2.2%. The extra reading bought no turn saving."),
"skill-bpmn-hitl-boolean-decision": ("WS2/WS4 turn sprawl backfire",
 "OPT adds four Greps for `Actions.HITL`/`outputSchema` and reads two sibling fixtures plus `SKILL.md`, taking 44 calls to BASE's 37. Tool-result falls 2,866 — not enough to pay for seven extra turns of generation. +2.9%."),
"skill-bpmn-multi-city-weather": ("generation-side regression despite a context win",
 "Calls are identical (55) and tool-result falls 6,293, yet cost rises 5.0% — because output tokens go up: OPT re-reads `MultiCityWeatherBpmn.bpmn` three times mid-authoring and regenerates around it. A case where the context lever and the generation lever disagree; `g·G` wins."),
"skill-bpmn-subprocess": ("WS2 turn sprawl + read-first backfire",
 "BASE greps eight times but keeps the trace at 32 calls. OPT abandons grepping for `Bash`×27 consecutively (30 Bash total, 6 inline-python), and tool-result rises 18,887→24,187. Calls barely move (+1), so this is a pure context-and-generation regression: +13.8%."),
"skill-bpmn-hitl-result-downstream": ("WS5 inline-python sprawl backfire",
 "Inline-python doubles (5→11) and calls go 27→37 as OPT works the file through shell loops, with `format`×2 and `init` round trips. Tool-result falls 1,444 — far too little to cover ten extra turns. +12.5%."),
"skill-bpmn-event-based-gateway": ("`format` round trips + added fishing",
 "OPT calls `format` twice and `validate` twice (BASE: none and twice), adds a Grep, and re-reads the file after editing: 19 calls to BASE's 14, tool-result +2,672. The artifact is the same race gateway in both arms. +16.8%."),
"skill-bpmn-message-catch": ("WS2 turn sprawl backfire",
 "OPT takes 26 calls to BASE's 16 — `Bash`×5 up front, then a write, then `Bash`×5 more, then two separate edit-and-validate rounds — with `format` added. Tool-result actually falls 1,511, so the regression is entirely turns and the generation they carry. +21.4%."),
"skill-bpmn-terminate": ("noise (levers flat)",
 "Calls +2, tool-result +515. OPT reads a scratch `.txt` and re-reads the artifact. Nothing clears threshold, so the +23.6% is a point-estimate swing, not a backfire."),
"skill-bpmn-error-event-subprocess": ("added fishing + turn sprawl",
 "OPT greps twice (`triggeredByEvent|eventSubprocess`, then `bpmn:task` variants) and reads `registry-workflow.md` that BASE skipped: 18 calls to 13, tool-result +2,347. +25.4%."),
"skill-bpmn-diagnose-incident-root-cause": ("noise (levers flat)",
 "Identical references, identical `incident`/`instance` calls, same root-cause verdict. Calls +1, tool-result +8. The +28.6% is a point-estimate swing and must not be blamed on the optimization."),
"skill-bpmn-switch": ("WS3 read-first + `format` round trip",
 "A 7-call task in BASE becomes 11 in OPT: an extra `registry-workflow.md` read, a `format` call, and a read-back of the artifact. Tool-result +3,504. Small absolute cost either way, but +28.5%."),
"skill-bpmn-smoke-registry-discovery": ("noise (levers flat)",
 "Both arms run the same three `registry` calls; OPT adds one `--version` probe and two inline-python invocations. Calls +1, tool-result −884. +31.2% on a $0.26 task — a point-estimate swing."),
"skill-bpmn-hitl-rpa-wrappers": ("WS3 read-first + WS2 turn sprawl",
 "OPT reads six files to BASE's three — including two sibling fixture `.bpmn`s and `public-safety.md` — greps once, and calls `format`: 28 calls to 20, tool-result +4,488. Time nearly triples (139s→348s). +34.0%."),
"skill-bpmn-hitl-multi-outcome-routing": ("WS2 turn sprawl backfire",
 "Same four references in both arms, but OPT spreads them across `Bash`×7, ×7 and ×5 runs with `init`×2 and `format`, re-reading the artifact before rewriting it: 31 calls to BASE's 20. Tool-result +1,472. +35.5%."),
"skill-bpmn-reading-list": ("WS5 inline-python sprawl (dominant)",
 "BASE greps nine times but writes after 39 calls. OPT abandons grep for shell: inline-python 7→19 across `Bash`×13, ×8 and ×11 runs, 50 calls. Tool-result falls hard (−11,060) because it stops dumping fixtures — but the generation cost of 19 hand-rolled python invocations more than covers it, and wall-clock doubles (400s→796s). +36.4%."),
"skill-bpmn-e2e-live-debug": ("live-debug spiral (WS2/WS4 backfire on the one executing task)",
 "The only task that runs a real process, and the worst wall-clock regression in the set: 380s→1,874s (~5×). OPT issues `debug-instance` eight times to BASE's three and spawns four `TaskOutput` polls, for 82 calls to BASE's 63, with tool-result +9,568. BASE reached the same verdict with `update-metadata`×3 and three `debug-instance` reads. +54.9%."),
"skill-bpmn-expr-error-mapping": ("`entryPointId` fishing spiral (worst regression)",
 "OPT takes **61 calls to BASE's 24** — greps `entryPointId` five times (three of them consecutive), Globs `*bpmn*`, then makes five Edits and 11 inline-python calls chasing the same field. Tool-result +9,034, time 343s→913s. BASE wrote the error mapping after four reference reads and 16 Bash calls. At +119.1% this is the single clearest example of the prompt licensing exploration instead of curbing it."),
}


def refs_of(rep):
    seen, out = set(), []
    for l in rep["trace"]:
        if l.startswith("Read:") and l.endswith(".md"):
            b = l.split(":", 1)[1]
            if b not in seen:
                seen.add(b); out.append(b)
    return out


def pick(task, arm, kept):
    c = [r for r in reps[task][arm] if r["status"] == "SUCCESS"
         and os.path.basename(os.path.dirname(r["path"])) in kept]
    if not c:
        c = [r for r in reps[task][arm] if r["status"] == "SUCCESS"]
    c.sort(key=lambda r: r["cost"])
    return c[len(c) // 2]


def describe(row, arm):
    rep = pick(row["task"], arm, set(row[arm]["reps"]))
    tc = collections.Counter(l.split(":")[0] for l in rep["trace"])
    refs = refs_of(rep)
    verbs = sorted(row[arm]["uip_verbs"].items(), key=lambda kv: -kv[1])[:3]
    vs = ", ".join(f"`{k}`×{v:.0f}" for k, v in verbs if v >= 0.5) or "no `uip` verbs"
    p = ["invoked the skill" if tc.get("Skill") else "**did not invoke the skill**",
         f"read {len(refs)} reference(s)" + (f" ({', '.join(refs[:4])})" if refs else ""),
         f"{tc.get('Bash',0)} Bash ({vs})",
         f"{tc.get('Write',0)} Write / {tc.get('Edit',0)} Edit"]
    if tc.get("Grep", 0) or tc.get("Glob", 0):
        p.append(f"**{tc.get('Grep',0)+tc.get('Glob',0)} Grep/Glob**")
    p.append(f"{row[arm]['inline_py']:.0f} inline-python")
    p.append(f"{row[arm]['thk_sec']:.0f}s thinking time")
    return f"rep `{os.path.basename(os.path.dirname(rep['path']))}` — " + "; ".join(p) + "."


L = []; w = L.append
w("# uipath-maestro-bpmn skill optimization — cost-reduction report")
w("")
w("Cost reduction is measured by **3 cost dimensions** — (1) thinking tokens, (2) tool-result tokens, "
  "(3) tool-calls/turns — targeted by **3 optimization techniques**:")
w("")
w("- **Scripted skills**: turn deterministic procedures found in the skill files into scripts to cut "
  "tool-calls/turns; they also cut thinking (the agent doesn't re-derive an encoded procedure) and, for some "
  "scripts, tool-result tokens (output written to a file instead of into context).")
w("- **Thinking budget prompt (RB1, RB2)**: softly curb reasoning to cut thinking tokens.")
w("- **Working style prompt (WS1–WS7)**: 7 bullets, each targeting different cost dimensions.")
w("")
w("> **Read this first — two structural facts about this run pair.**")
w(">")
w(f"> **1. n = 1.** Each arm ran **one repeat per task** ({meta['base_tasks']} tasks × 1 rep). Every per-task "
  "number in this report is therefore a **point estimate**, and the outlier-exclusion step described in the "
  "methodology is inert (nothing to exclude). The four-lever real-vs-noise test is doing all the work of "
  "separating signal from run-to-run variance, and single-task percentages should not be quoted on their own.")
w(">")
w("> **2. Thinking tokens are not measurable in these runs.** Thinking-only assistant messages exist in "
  f"quantity (1,655 in BASE / 1,551 in OPT across all {meta['base_tasks']} tasks) but every one carries "
  "`output_tokens: 0` and an **empty** `thinking` string; the reasoning tokens are folded into the following "
  "`tool_use` message's `output_tokens`. The prescribed metric (Σ `output_tokens` of thinking-only messages) "
  "therefore returns ~0 for a **schema** reason, not a behavioral one — reasoning did not vanish. Two "
  "substitutes are used throughout and are flagged wherever they appear: **total output tokens** as the "
  "generation-side lever (replacing thinking in the four-lever test, threshold 5k), and **thinking generation "
  "time** — the summed `generation_duration_ms` of thinking-only messages — as a directional proxy "
  f"({S('base','thk_sec'):,.0f}s → {S('opt','thk_sec'):,.0f}s, "
  f"{(S('opt','thk_sec')/S('base','thk_sec')-1)*100:+.1f}%). As a consequence the saving table below cannot "
  "split thinking from non-thinking output; it reports one generation bucket.")
w("")
w("> **Arm definition.** OPT is `maestro-bpmn-optimized-inline-sonnet-5` (skill `tmp:uipath-maestro-bpmn`), BASE "
  "is `maestro-bpmn-baseline-sonnet-5` (skill `uipath:uipath-maestro-bpmn`); both on `claude-sonnet-5`. The OPT "
  "skill carries the RB1/RB2 + WS1–WS7 block at the top of `SKILL.md` and teaches three inline `uip` CLI verbs "
  "(`maestro bpmn format`, `update-metadata`, `update-metadata --dry-run`). Neither arm ships a bundled "
  "`.py`/`.sh` script, so the *scripted-skills* technique appears in CLI-verb form — see the note under "
  "[Per Task Table](#per-task-table). Note BASE reaches `update-metadata` 9 times on its own via `--help`, so "
  "that verb is not exclusive to OPT.")
w("")
w("## Script Generation of uipath-maestro-bpmn")
w("")
w("The skill covers five distinct work areas: authoring, validation, metadata management, operate "
  "(packaging / lifecycle), and diagnose. Below is a breakdown of each area and whether its procedures are "
  "codifiable.")
w("")
w("**3 out of 14 areas** can be turned into scripts, and the corresponding scripts are: "
  "`generate_diagram.py` (diagram auto-layout, area 5), `scaffold_metadata.py` (package metadata scaffolding, "
  "area 8), and `check_metadata_drift.py` (package metadata drift check, area 9). Area 6 (BPMN validation) is "
  "counted separately as **already scripted** (`validator/validate-bpmn.mjs`) and excluded per instructions. In "
  "this OPT arm those three procedures are delivered as inline CLI verbs rather than bundled scripts — `format` "
  "covers area 5, `update-metadata` area 8, `update-metadata --dry-run` area 9 — which is why every per-task "
  "script-invocation count is 0 and the CLI-verb counts carry the signal instead.")
w("")
w("Codifiability is taken from "
  "`/home/azureuser/projects/skills/tmp/experiments/classification/bpmn/classification-details-uipath-maestro-bpmn.md` "
  "(classification: **Partial**).")
w("")
w("Many of the remaining areas are plain CLI calls — registry discovery, connector enrichment, packaging, "
  "upload/publish/deploy, run/debug/manage, and the diagnose ladder. Those are not script material, but the "
  "working-style prompt (WS2) is meant to chain them by planning the path ahead instead of discovering the CLI "
  "surface one `--help` at a time. In this pair that is exactly where the results split: it works on the "
  "authoring tasks and backfires on several others.")
w("")
w("| # | Area | Codifiable? | Notes |")
w("|---|------|-------------|-------|")
w("| 1 | Registry discovery (pull / list / search / get, IS connections list) | No | CLI calls requiring user confirmation and intent mapping |")
w("| 2 | Connector enrichment (`registry get --connection-id --object-name`) | No | CLI call; resource identifiers come from discovery or user |")
w("| 3 | Template placeholder filling (`{id}`, `{name}`, `{incomingEdge}`, etc.) | No | Requires agent judgment for process structure and content |")
w("| 4 | Structural BPMN authoring (process scaffold, sequence flows, gateways, events, boundary events, subprocesses, multi-instance markers) | No | Generative/creative; process shape comes from requirements |")
w("| 5 | **Diagram generation (`bpmndi:BPMNDiagram`)** | **Yes — BUILD-MODEL** | Fixed sizes (tasks 100×80, events 36×36, gateways 50×50), left-to-right layout; fully deterministic given the process graph |")
w("| 6 | **BPMN validation** | **Already scripted** | `validator/validate-bpmn.mjs` — runs all 19 PO.Frontend rules offline; this is an existing skill script, excluded per instructions |")
w("| 7 | Expression authoring (`=vars.X`, `=bindings.X`, `=js:`, scoping rules) | Marginal | Rules are explicit but application is part of authoring; a post-hoc syntax checker is a VALIDATE, but minor value |")
w("| 8 | **Package metadata scaffolding** (`project.uiproj`, `operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`) | **Yes — FORMAT-CONVERT / BUILD-MODEL** | `local-metadata-regeneration-guide.md` gives exact JSON shapes and derivation rules from BPMN root elements |")
w("| 9 | **Package metadata drift check** | **Yes — VALIDATE** | `local-metadata-regeneration-guide.md` §Drift Handling gives explicit rules: `entry-points.json` ids must match root `uipath:entryPointId`s; `bindings_v2.json` version must be `\"2.0\"`; `operate.json` must point at the correct BPMN file |")
w("| 10 | Packaging (`uip maestro bpmn pack`) | No | CLI call |")
w("| 11 | Upload / publish / deploy | No | CLI calls; require explicit user consent |")
w("| 12 | Run / debug / manage instances | No | CLI calls; require explicit user consent and post-run judgment |")
w("| 13 | Diagnose priority ladder (incidents → variables → deployed asset → element executions → package files → traces) | No | CLI reads requiring interpretation and analysis at each step |")
w("| 14 | Agent wrapper selection (processType → extension type) | No (marginal) | A 4-row lookup table; too small to warrant a standalone script |")
w("")
w("## Summary")
w("")
w("### Overall Results")
w("")
w("![Normalized BASE-vs-OPT comparison across the eight headline metrics](images/overall-results.png)")
w("")
w(f"*Every metric normalized to BASE=100%. The top two rows are totals across all {N} both-solved tasks; the "
  f"rest are **per-task means** (sum ÷ {N}). Thinking time is a proxy for the unmeasurable thinking-token "
  "metric; output tokens cover all generation. Total time is the one metric that got **worse**, shown in red.*")
w("")
w(f"Across the {N} both-solved tasks OPT costs **${S('opt','cost'):.2f}** against BASE's "
  f"**${S('base','cost'):.2f}** — a **{abs((S('opt','cost')/S('base','cost')-1)*100):.1f}%** reduction — while "
  f"cutting output tokens {abs((S('opt','output_tok')/S('base','output_tok')-1)*100):.1f}%, tool-result tokens "
  f"{abs((S('opt','tr_tok')/S('base','tr_tok')-1)*100):.1f}%, tool-calls/turns "
  f"{abs((S('opt','tool_calls')/S('base','tool_calls')-1)*100):.1f}% and thinking time "
  f"{abs((S('opt','thk_sec')/S('base','thk_sec')-1)*100):.1f}%. **Wall-clock moved the other way: "
  f"{S('base','time'):,.0f}s → {S('opt','time'):,.0f}s "
  f"({(S('opt','time')/S('base','time')-1)*100:+.1f}%)** — OPT is cheaper but slightly slower overall, driven by "
  "a handful of long regressions (`e2e-live-debug` alone adds 1,494s).")
w("")
dc = SD("cost")
b_out, b_cr = SD("output_tok") * R_OUT, SD("cache_read") * R_CR
b_cc, b_un = SD("cache_create") * R_CC, SD("uncached") * R_UNC
w(f"**Where the ${abs(dc):.2f} saving comes from**")
w("")
w("| bucket | Δ tokens (sum) | share | cost-model term |")
w("|--------|----------------|-------|-----------------|")
w(f"| cache-read | {SD('cache_read'):+,.0f} | {b_cr/dc*100:.1f}% | `r·(TR+G)·(T−t)` |")
w(f"| output — all generation (thinking **not separable**, see note) | {SD('output_tok'):+,.0f} | {b_out/dc*100:.1f}% | `g·G` = `g·(thk+cl+tc)` |")
w(f"| cache-create | {SD('cache_create'):+,.0f} | {b_cc/dc*100:.1f}% | `w·TR` |")
w(f"| uncached | {SD('uncached'):+,.0f} | {b_un/dc*100:.1f}% | `w·TR` |")
w("")
w("The `Δ tokens` column holds **exact sums over tasks**, while the chart's per-task figures are **rounded for "
  "display** — multiplying a rounded chart delta by the task count will not exactly reproduce these sums (a small "
  f"rounding gap). The exact sums and the ${abs(dc):.2f} total (from `total_cost_usd`) are authoritative; the "
  "`share` column is the one derived split. The prescribed **thinking** and **non-thinking output** rows are "
  "merged into a single generation bucket because this run pair does not record per-message thinking tokens "
  "(see the note at the top); uncached is a small **negative** contribution (it grew).")
w("")
w("### Where the cost comes from before optimization — and how OPT cuts it")
w("")
w(f"**The BASE bill is overwhelmingly context-driven.** Over the {N} tasks BASE accumulates "
  f"**{S('base','cache_read')/1e6:.1f}M cache-read tokens** and **{S('base','cache_create')/1e6:.2f}M "
  f"cache-create tokens** against **{S('base','output_tok')/1000:.0f}k output tokens** and "
  f"**{S('base','tr_tok')/1000:.0f}k tool-result tokens** — cache-read alone is ~87× the tool-result footprint, "
  f"because a {S('base','tool_calls')/N:.0f}-call average trace re-reads everything already in context on every "
  "remaining turn. The pathologies that feed it are visible in the traces, and they are different from what a "
  "to-do-heavy model does: **there is no to-do ceremony at all** in either arm (0 `TaskCreate`/`TaskUpdate` "
  "calls) and essentially no hand-written metadata JSON (1 file across the whole BASE arm). What BASE does "
  "instead is **fish**: 106 Grep/Glob calls, dominated by the same handful of queries repeated — "
  "`entryPointId` is grepped four separate times in `gateway-sequence-flows`, three times in `subprocess`, twice "
  "in `calculator`; `expr-computed-js` greps 14 times and `feet-inches` 12. It also **probes blind**: "
  "`callactivity-agentic-process` opens with 35 consecutive `Bash` calls before writing anything, "
  "`event-trigger-start` with 34, `loop-multiply` with 43. And it **reads what it should not** — in "
  "`http-weather` and `expr-computed-js` BASE reads the eval's own grader (`check_http_weather.py`, "
  "`bpmn_check.py`, `computed_js.yaml`), and in `script-jint-guidance` it reads all five generated metadata "
  "files twice.")
w("")
w(f"**OPT's win is shorter, tighter traces — and it is concentrated, not uniform.** Tool-calls fall "
  f"{abs(SD('tool_calls')):.0f} ({abs((S('opt','tool_calls')/S('base','tool_calls')-1)*100):.1f}%), reference "
  "reads 161→144, Grep/Glob 106→86, and inline-python drops on most authoring tasks. Because every removed call "
  "also removes its re-read tail, cache-read falls "
  f"{abs(SD('cache_read'))/1e6:.1f}M tokens — **{b_cr/dc*100:.0f}% of the entire saving**, far more than the "
  f"generation bucket's {b_out/dc*100:.0f}%. That is the headline mechanism here: the optimization does not "
  "mainly make the model think less per turn, it makes the trace shorter so context is re-read fewer times. "
  "`format` is invoked 33 times in OPT against 0 in BASE and `registry` probing falls 159→122, but the biggest "
  "single wins are plain trace-length collapses: `callactivity-agentic-process` 46→14 calls, "
  "`inclusive-gateway-forkjoin` 35→12, `http-weather` 83→39, `edit-update-node` 22→9.")
w("")
w("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
w("|------------------------------|------|------------------|")
w("| **Plan the path instead of probing blind** — read the reference, then act, rather than opening with 30+ consecutive `Bash` probes (WS1/WS2/WS7) | `g·(cl+tc)` + `r·(TR+G)·(T−t)` | `callactivity-agentic-process` 46→14 calls (−$1.436, −74.3%); `inclusive-gateway-forkjoin` 35→12 (−$1.459, −72.7%); `event-trigger-start` 39→22 (−$0.571, −43.4%); `script-task-group-by` 43→31 (−$0.621, −40.8%) |")
w("| **Stop fishing** — no repeated `entryPointId` greps, no reads of the eval's own grader or of generated metadata already written (WS4/WS7) | `w·TR` + `r·TR·(T−t)` | `http-weather` grader reads →0, tool-result 60,980→25,494 (−$2.343, −64.9%); `expr-computed-js` 14→7 Greps, tool-result −23,505 (−$0.682, −24.3%); `rpa-job` 8→0 Greps (−$0.941, −50.7%); `script-jint-guidance` metadata read twice→once (−$1.253, −40.8%) |")
w("| **Inspect once; don't re-validate what you already fixed** (WS4/WS7) | `w·TR` + `r·TR·(T−t)` | `edit-add-output` 3 reads→1, tool-result −5,955 (−$0.140, −27.4%); `edit-update-node` 22→9 calls (−$0.620, −67.4%); `edit-add-node` 4 validates→2 (−$0.263, −42.8%); `edit-remove-node` tail 10→5 Bash (−$0.254, −35.3%) |")
w("| **Skip references the task doesn't need** (WS3/WS7) | `w·TR` | `hitl-completed-wired` 18 reads→6, tool-result −20,188 (−$1.734, −50.5%); `author-validate` 4 refs→1 (−$0.350, −34.8%); `e2e-customer-escalation` tool-result −25,897 (−$0.879, −28.2%) |")
w("| **Grep instead of dumping** — search fixtures rather than reading them whole (WS6) | `w·TR` | `script-task-map` tool-result 35,488→14,849 even while calls rise 44→57 (−$0.244, −14.3%); `calculator` sibling-file reads→greps, tool-result −6,006 (−$0.045, −2.5%) |")
w("")
wins = [r for r in rows if r["delta"]["cost"] < 0]; regs = [r for r in rows if r["delta"]["cost"] > 0]
wr = [r for r in wins if r["is_real"]]; wn = [r for r in wins if not r["is_real"]]
rr = [r for r in regs if r["is_real"]]; rn = [r for r in regs if not r["is_real"]]
sc = lambda g: sum(r["delta"]["cost"] for r in g)
w("**Real vs. noise.** With n=1 per task, a dollar difference only counts as an optimization effect when the "
  "agent **measurably did something different**. \"Different\" is judged on the four levers the prompts target — "
  "tool-calls, turns, tool-result tokens, and generation tokens — with a task counting as **real** if any one "
  "moved non-trivially: **≥3 tool-calls, ≥3 turns, ≥5k tool-result tokens, or ≥5k output tokens**. The fourth "
  "threshold is the substitution described at the top: thinking tokens are unmeasurable in this pair, so total "
  "output tokens stand in, at 5k rather than the usual 1.5k to keep roughly the same relative strictness against "
  f"a ~{S('base','output_tok')/N/1000:.0f}k-per-task generation base. If all four are ~flat and only the dollars "
  f"moved, the task is **noise** and is not credited. Of the **{len(wins)} wins**, **{len(wr)} are real** "
  f"(carrying **−${abs(sc(wr)):.2f}**) and **{len(wn)} are noise** (carrying **−${abs(sc(wn)):.2f}**). The noise "
  "wins are: " + ", ".join(f"`{r['task'].replace('skill-bpmn-','')}`" for r in wn) + ". `hitl-brownfield-insert` "
  "(calls −3, exactly at the bar) and `diagnose-stuck-gateway` (calls +5 against a −2.0% bill) are gray-zone and "
  "want replication.")
w("")
w("### Why cost increases in some tasks")
w("")
w(f"**{len(regs)} of {N} tasks cost more**, together **+${sc(regs):.2f}** against **−${abs(sc(wins)):.2f}** of "
  f"wins. By the same four-lever test, **{len(rr)} are attributable** (**+${sc(rr):.2f}**) and **{len(rn)} are "
  f"noise** (**+${sc(rn):.2f}**). Unlike the wins — which cluster on authoring tasks where BASE probed blindly — "
  "the regressions cluster where the prompt licensed *more* exploration than the task needed, and they are "
  "large: the worst three (`expr-error-mapping` +119.1%, `e2e-live-debug` +54.9%, `reading-list` +36.4%) carry "
  "$3.38 between them, 62% of all regression cost.")
w("")
w("| Mechanism (what OPT changed) | Term | Examples (Δcost) |")
w("|------------------------------|------|------------------|")
w("| **Fishing spiral** — WS1's \"understand first\" read as license to keep searching; the same field grepped over and over before any edit (WS1/WS4/WS7 backfire) | `g·(cl+tc)` + `w·TR` | `expr-error-mapping` 24→61 calls, `entryPointId` grepped 5× plus a `*bpmn*` Glob, tool-result +9,034 (+$1.518, +119.1%); `error-event-subprocess` 2 new Greps, 13→18 calls (+$0.183, +25.4%) |")
w("| **Inline-python sprawl** — WS5's \"write code once\" taken as a mandate to hand-roll shell/python instead of one CLI round trip | `g·(cl+tc)` | `reading-list` inline-python 7→19, 39→50 calls, time 400s→796s (+$0.660, +36.4%); `hitl-result-downstream` 5→11, 27→37 calls (+$0.216, +12.5%) |")
w("| **Turn sprawl on small tasks** — extra `format`/`init` round trips and read-backs on artifacts BASE finished in one pass (WS2 backfire) | `g·(cl+tc)` + `r·G·(T−t)` | `hitl-multi-outcome-routing` 20→31 calls (+$0.343, +35.5%); `message-catch` 16→26 (+$0.149, +21.4%); `event-based-gateway` 14→19 with `format`×2 (+$0.119, +16.8%); `switch` 7→11 (+$0.103, +28.5%) |")
w("| **Read-first over applied** — more references and fixtures pulled into context without shortening the trace (WS3 backfire) | `w·TR` | `simple-approval-bpmn` 7→24 files read, tool-result +12,633 on a flat call count (+$0.085, +2.2%); `hitl-rpa-wrappers` 3→6 reads, 20→28 calls (+$0.269, +34.0%); `subprocess` tool-result +5,300 (+$0.213, +13.8%) |")
w("| **Live-execution spiral** — the one task that really runs a process polls it far harder | `g·G` + `w·TR` | `e2e-live-debug` `debug-instance` 3→8 plus 4 `TaskOutput` polls, 63→82 calls, **380s→1,874s** (+$1.202, +54.9%) |")
w("")
w(f"**Real vs. noise (regressions).** Applying the test defined above: **{len(rr)} of {len(regs)}** regressions "
  f"are real (**+${sc(rr):.2f}**) and **{len(rn)}** are noise (**+${sc(rn):.2f}**): "
  + ", ".join(f"`{r['task'].replace('skill-bpmn-','')}`" for r in rn) + ". All three noise regressions are "
  "sub-$0.10 tasks whose traces are step-for-step identical between arms — `diagnose-incident-root-cause` runs "
  "the same references and the same `incident`/`instance` calls in both — so their +23% to +31% headline "
  "percentages must not be read as backfires.")
w("")
w(f"**Netting.** Across all {N} tasks, **{len(wr)+len(rr)} are real** and **{len(wn)+len(rn)} are noise**. The "
  f"noise is *not* symmetric here: noise wins carry **−${abs(sc(wn)):.2f}** against noise regressions of only "
  f"**+${sc(rn):.2f}**, netting **−${abs(sc(wn)+sc(rn)):.2f}** — about "
  f"{abs((sc(wn)+sc(rn))/dc)*100:.0f}% of the **−${abs(dc):.2f}** total, and in the same direction as the "
  "headline rather than cancelling. That asymmetry is the main caveat of this pair: at n=1 there is no "
  "within-task replication to average it out, so roughly one dollar in fourteen of the reported saving rests on "
  f"tasks that show no measured behavior change. The real effects still carry **−${abs(sc(wr)+sc(rr)):.2f}** "
  f"(~{abs((sc(wr)+sc(rr))/dc)*100:.0f}% of the headline), so the conclusion holds — but it holds with a wider "
  "error bar than a 5-repeat run would give, and the per-task percentages should be treated as indicative only.")
w("")
w("The regressions imply four remediation targets: (1) **bound WS1/WS4** — \"understand first\" needs a stop "
  "condition, because the worst regression is an agent grepping `entryPointId` five times before editing; "
  "(2) **bound WS5** — state that a supported CLI verb beats a hand-rolled python heredoc, since inline-python "
  "rose in every sprawl regression; (3) **make `format` a finishing step, not a probe** — the small-task "
  "regressions are mostly `format`/`init` round trips on artifacts that were already done; (4) **cap live-debug "
  "polling** — `e2e-live-debug` is the single worst wall-clock outcome in the set and explains most of the +2.0% "
  "total-time regression.")
w("")
w("### How Are results Collected")
w("")
w(f"Every figure is read from `<run>/default/<task>/<rep>/task.json` under the two run roots "
  f"(`{os.path.basename(meta['opt_run'])}` and `{os.path.basename(meta['base_run'])}`) by `extract.py` → "
  "`rows.json` (per-task rows incl. the four lever deltas) and `reps.json` (per-rep raw), so the tables, chart "
  "and noise test all draw from the same numbers.")
w("")
w("- **thinking tokens** — prescribed as Σ `output_tokens` over assistant messages under "
  "`iterations[].messages[]` whose `content_blocks` block-types are exactly `{\"thinking\"}`. **In this run pair "
  "that sum is 26 tokens in BASE and 0 in OPT**, because the messages are recorded like this:")
w("")
w("  ```json")
w("  {\"role\": \"assistant\", \"content_blocks\": [{\"block_type\": \"thinking\", \"thinking\": \"\", ...}],")
w("   \"output_tokens\": 0, \"generation_duration_ms\": 8360.01, \"tool_use_ids\": []}")
w("  ```")
w("")
w("  The thinking text is empty and the token count is 0, while `generation_duration_ms` shows the reasoning "
  "really happened; the tokens land on the next `tool_use` message. Substitutes used: **total output tokens** "
  "(`total_token_usage.output_tokens`) for the generation lever, and **thinking time** (Σ "
  "`generation_duration_ms` over those same thinking-only messages) as a directional proxy.")
w("- **tool-result tokens** — Σ `result_tokens` over `iterations[].commands[]`.")
w("- **tool-calls** — `len(iterations[].commands[])`. A **script invocation** is a `commands[]` entry with "
  "`tool_name==\"Bash\"` whose `parameters.command` matches `python3 …/<script>.py` (a `Read`/`grep`/`cat` of the "
  "script source does not count); there are **none** in either arm. Real example:")
w("")
w("  ```json")
w("  {\"tool_name\": \"Skill\", \"parameters\": {\"skill\": \"tmp:uipath-maestro-bpmn\"},")
w("   \"result_status\": \"success\", \"result_tokens\": 11, \"sequence_number\": 0}")
w("  ```")
w("")
w("- **turns T** — the cost-model agentic-step count, computed as the number of assistant messages with a "
  "non-empty `tool_use_ids`. **Caveat:** every such message carries exactly one tool call (4,485 of 4,485 have "
  "`len(tool_use_ids)==1`), so turns are numerically identical to tool-calls in both arms, and WS2's \"batch "
  "into one turn\" can only show up as *fewer total calls*.")
w("- **cost and token buckets** — `total_token_usage`. Real example:")
w("")
w("  ```json")
w("  {\"uncached_input_tokens\": 62, \"output_tokens\": 61984, \"cache_creation_input_tokens\": 63931,")
w("   \"cache_read_input_tokens\": 4182924, \"total_cost_usd\": 2.06135445, \"input_tokens\": 4246917}")
w("  ```")
w("")
w("  Bucket **token counts are read directly**; `total_cost_usd` is the only stored dollar and is authoritative. "
  "Per-bucket dollars are **derived** at output **$15/M**, cache-read **$0.30/M**, cache-create **$3.75/M**, "
  "uncached **$3/M**. These rates were not assumed: they were recovered by least-squares from the runs "
  "themselves and then verified by reconciliation on **all "
  f"{meta['recon_files']} `task.json` files**, where "
  "`output×$15/M + cache_read×$0.30/M + cache_create×$3.75/M + uncached×$3/M` equals `total_cost_usd` to a "
  f"maximum error of **${meta['recon_max_err_usd']:.2e}** (exact to floating point). One `task.json` carries no "
  "`total_token_usage` at all and is excluded from the rate fit.")
w("- **time** — `duration_seconds`. **task instruction** — `task_description`. **ordered action trace** — "
  "`iterations[].commands[]` walked in order (Skill / Read / Write / Edit / Bash / TaskCreate·Update / "
  "Glob·Grep).")
w("")
w(f"**Scope and n.** Success is `final_status == \"SUCCESS\"`. Both runs hold **{meta['base_tasks']} tasks × 1 "
  f"repeat**; **{N} are both-solved** and only those are compared. The 13 excluded tasks failed or errored in at "
  "least one arm (OPT: 5 `MAX_TURNS_EXHAUSTED`, 3 `ERROR`, 1 `FAILURE`; BASE: 2 `MAX_TURNS_EXHAUSTED`, 4 "
  "`ERROR`, 1 `FAILURE`, 1 `TIMEOUT`). **Because n=1, the recurring-behavior filter (drop reps deviating from "
  "the median by more than `max(floor, 3·MAD)` on any lever) has nothing to exclude and excluded 0 reps in both "
  "arms** — every per-task value is a single observation, i.e. a point estimate, and is reported as such "
  "throughout.")
w("")
w("## Case Analysis")
w("")
w("## Reference")
w("")
w("### Per Task Table")
w("")
fmt_tasks = [r for r in rows if any("format" in k or "update-metadata" in k for k in r["opt"]["uip_verbs"])]
fc = [r for r in fmt_tasks if r["delta"]["cost"] < 0]; fe = [r for r in fmt_tasks if r["delta"]["cost"] > 0]
w(f"**Script usage & benefit:** **0 of {N} tasks invoked a bundled skill script** — neither arm ships one, so "
  f"the `scripts sc/dr/gd` column (scaffold / drift / diagram) is `0/0/0` throughout. The three codifiable "
  f"procedures appear as inline CLI verbs instead: **{len(fmt_tasks)} tasks invoked `format` or "
  f"`update-metadata`** ({len(fc)} got cheaper, {len(fe)} got more expensive, 0 flat), with `format` at 33 "
  "invocations against **0 in BASE**. Unlike the previous Sonnet-4.6 pair, the CLI verb is **not the dominant "
  "driver in any task here**: no task in this run hand-writes the metadata set (BASE writes 1 metadata JSON "
  "across all 57 tasks), so `format` has almost no manual work to displace — and on several small tasks it adds "
  "a round trip that shows up as a regression. BASE itself reaches `update-metadata` 9 times via `--help`. The "
  "`CLI fmt·upd` counts are appended to the scripts column for reference.")
w("")
w("Ranked by **percentage cost reduction**, largest reduction first. With n=1 every row is a point estimate; the "
  "`REAL` column records whether any of the four levers cleared threshold.")
w("")
w("| # | task | Δcost | Δoutput tok ($) | Δtool-result tok | Δtool-calls | Δtime | scripts sc/dr/gd (CLI fmt·upd) | REAL | attribution (ranked) |")
w("|---|------|-------|-----------------|------------------|-------------|-------|-------------------------------|------|----------------------|")
for i, r in enumerate(rows, 1):
    d, B, O = r["delta"], r["base"], r["opt"]
    fm = sum(v for k, v in O["uip_verbs"].items() if "format" in k)
    up = sum(v for k, v in O["uip_verbs"].items() if "update-metadata" in k)
    w(f"| {i} | `{r['task'].replace('skill-bpmn-','')}` "
      f"| ${B['cost']:.3f}→${O['cost']:.3f} ({d['cost']/B['cost']*100:+.1f}%) "
      f"| {d['output_tok']:+,.0f} (${d['output_tok']*R_OUT:+.3f}) "
      f"| {d['tr_tok']:+,.0f} | {d['tool_calls']:+.0f} "
      f"| {B['time']:.0f}s→{O['time']:.0f}s ({d['time']/B['time']*100:+.1f}%) "
      f"| 0/0/0 ({fm:.0f}·{up:.0f}) | {'yes' if r['is_real'] else 'no'} "
      f"| {A.get(r['task'],('—',''))[0]} |")
w("")
w("### Per Task Behavior")
w("")
for r in rows:
    d, B = r["delta"], r["base"]
    attrib, why = A.get(r["task"], ("—", "—"))
    w(f"**{r['task']}** ({d['cost']/B['cost']*100:+.1f}%, {attrib.split('>')[0].strip()})")
    w(f"- Task: {r['task_description']}")
    w(f"- Before (BASE): {describe(r,'base')}")
    w(f"- After (OPT): {describe(r,'opt')}")
    w(f"- **{'Why cheaper:' if d['cost'] < 0 else 'Why MORE expensive:'}** {why}")
    w("")

open(os.path.join(OUT, "report.md"), "w").write("\n".join(L) + "\n")
print("wrote report.md:", len(L), "lines")
print("attribution entries:", len(A), "tasks:", N,
      "missing:", [r["task"] for r in rows if r["task"] not in A])
