# maestro-bpmn: per-task behavior-diff findings (OPT vs BASE)

Source: `runs/maestro-bpmn-optimized-report-1` (OPT) vs `runs/maestro-bpmn-baseline-report-1` (BASE), both-solved (47/48), **1 rep per task** (rep 00). Trajectories read from `task.json` (`iterations[].messages[].content_blocks`, `iterations[].commands[]`). For each task: how the agent solved it pre- (BASE) and post-optimization (OPT), why the approach differs, script invocations, and whether/why cost fell.

**Optimization block** (in OPT SKILL.md): **RB1** "match reasoning to step difficulty, bias toward acting; if a script covers a mechanical step, run it — don't re-derive"; **RB2** "reserve deep reasoning for the one hard judgment". **WS1** understand skill/scripts first; **WS2** plan up front then chain (fewer turns); **WS3** inspect input once; **WS4** don't repeat work; **WS5** write code once; **WS6** keep outputs small (redirect to file); **WS7** don't do anything unnecessary. Scripts: `scaffold_metadata.py` (emits the 5 package-metadata files), `check_metadata_drift.py` (verifies them), `generate_diagram.py` (emits the BPMN diagram).

**Recurring BASE anti-patterns the optimization removed:** (a) multi-burst re-derivation of structure/metadata already implied by the reference; (b) hand-authoring the 5 package-metadata files with 6 individual Writes; (c) TaskCreate/TaskUpdate to-do ceremony; (d) filesystem fishing (`Glob`/`find` for fixtures, reading validator samples); (e) pulling bulk command output into context (then re-Writing it) instead of `> file` redirect; (f) reading the heavy `registry-reference.md` (2,816 tok) instead of targeted CLI `registry get`.

**Two fixed costs both arms pay** (not optimized): the `structural-bpmn.md` read (7,125 tok, every run) and the validator npm-install "dance" (`node_modules` absent both arms — per-rep environment variance).

---

## Big wins driven by the thinking-budget prompt (RB1/RB2)

### hitl-multi-outcome-routing — $1.393→$0.502 (−64%)
- **BASE:** 5 thinking bursts = 44,604 tok (T20=11,383, T30=9,744, T18=9,482, T34=7,793, T28=3,847), ~11 TaskCreate/Update calls, `find *.uiproj`/`find *.bpmn` fishing, 2 Writes.
- **OPT:** one 6,123-tok burst → registry gets → 1 Write → `generate_diagram.py`. No todos, no fishing.
- **Why:** RB2 concentrates reasoning into one burst; WS2/WS7 remove the todo ceremony and fishing.
- **Scripts:** generate_diagram ×1 (minor).
- **Helps? Yes** — −37,694 thinking × g≈5 is ~$0.57 of the ~$0.89 saved.

### edit-group-to-subflow — $0.987→$0.448 (−55%)
- **BASE:** 5 bursts = 29,426 tok; fished hard (`Glob **/*.bpmn`→1,942 tok + 3 fixture reads ~4,833, one re-read twice); 1 Write.
- **OPT:** one 5,850-tok burst → Write → validate. Same target+ref reads, no Glob/fixtures/re-reads.
- **Why:** RB1/RB2 collapse 5 reasoning rounds to 1; WS3/WS4 kill the fishing.
- **Scripts:** 0/0/0.
- **Helps? Yes** — −23k thinking is the largest mover; tr −6,614 secondary.

### timer-start — $0.824→$0.392 (−52%)
- **BASE:** 3 bursts = 15,029 tok interleaved with **6 TaskCreate + ~10 TaskUpdate** turns; 42 tool-turns.
- **OPT:** one 3,522-tok burst, calls chained up front, 1 Write, no todos; 28 turns.
- **Why:** tool-results are *flat* (9,207 vs 9,328) and billed-T flat — savings are almost purely the g bucket: thinking −10.5k + far fewer tool-use generations (the 16 removed todo turns).
- **Scripts:** 0/0/0.
- **Helps? Yes** — clean thinking + generation-count win.

### hitl-completed-wired — $0.604→$0.427 (−29%)
- **BASE vs OPT:** structurally identical trajectories (same reads, 4 gets, 1 Write, 17 calls / 6 turns). Only difference: planning burst **9,000→3,991** thinking.
- **Why:** pure RB1/RB2.
- **Scripts:** 0/0/0.
- **Helps? Yes** — −4,886 thinking × g ≈ the whole $0.18 delta. The cleanest thinking-only isolation in the suite.

### simple-approval-bpmn — $1.258→$0.890 (−29%)
- **BASE:** 42,112 thinking (14,849+11,913+8,706+5,882), 2 Writes.
- **OPT:** 21,389 thinking (12,219+7,009+1,609); inspected the agent-job/queue-item templates with one inline-python dump (T10=1,462) instead of many reads; scaffold+drift; 1 Write. tool-results flat (Δ449).
- **Why:** genuinely hard task; RB2 halves the reasoning but can't remove it — even optimized it's the priciest.
- **Scripts:** scaffold+drift ran but replaced nothing BASE did.
- **Helps? Yes, modestly** — g-share 100%; scaffold negligible here.

### hitl-boolean-decision — $1.414→$1.090 (−23%)
- **BASE:** 48,673 thinking (4 bursts, T26=17,526, T10=15,352); read registry-catalog AND ran 3 gets; `find`/`Glob` + 3 fixtures; re-read refs twice.
- **OPT:** 27,312 thinking (2 bursts); skipped the 2,816 catalog read, dumped templates to `/tmp/*.json` and grep/head-sliced them; 1 fixture; no re-reads.
- **Why:** RB1/RB2 (4 bursts→2) + WS3/WS6/WS4 (dump→grep, keep-outputs-small, no re-reads).
- **Scripts:** 0/0/0.
- **Helps? Yes** — thinking −21k dominant, tr −4,975 secondary.

### reading-list — $0.822→$0.617 (−25%)
- **BASE:** 20,889 thinking (T14=9,114, T8=8,474); authored with 4 Write/Edit churn ops; `find` fishing.
- **OPT:** 12,023 thinking; 1 Write, no Edit churn.
- **Why:** RB1/RB2 (modest — OPT still carried a 7.2k burst, keeping the floor high); WS5 write-once; WS7/WS4.
- **Scripts:** 0/0/0.
- **Helps? Yes, but smallest of the RB wins** — the retained burst caps it.

---

## Big wins driven by scripts (scaffold_metadata replaces hand-authored metadata)

### business-rule-task — $0.882→$0.482 (−45%)
- **BASE:** 51 turns; T22=9,218 metadata-derivation burst → **6 hand-Writes** (bpmn + 5 metadata files); 4 useless Globs; read registry-md(2,816)+metadata-guide(2,250).
- **OPT:** 32 turns; small bursts; **1 Write**; scaffold(1)+drift(1).
- **Why:** scaffold generates the 5 metadata files from the bpmn → the derivation burst and the 2,250-guide read vanish.
- **Scripts:** scaffold 1, drift 1. scaffold replaced 5 hand-Writes + the 9,218-tok burst + the guide read.
- **Helps? Yes** — the eliminated burst (g) dwarfs the collapsed Writes (w).

### calculator — $1.090→$0.627 (−43%)
- **BASE:** 48 turns; **T20=16,437** (largest burst in the whole suite) + T14=3,997; 6 hand-Writes; TaskCreate/Update; registry-md read.
- **OPT:** 34 turns; small bursts; 1 Write; scaffold+drift; briefly skims the scaffold script (WS1, ~1,130 tok).
- **Scripts:** scaffold 1, drift 1 — replaced the 16,437-tok burst + 5 Writes.
- **Helps? Yes** — scaffold ≫ RB > WS.

### hitl-rpa-wrappers — $0.780→$0.499 (−36%)
- **BASE:** 42 turns; bursts 3,756+4,488; 6 hand-Writes split; fished fixtures (Glob 1,889 + reads) + registry-md + metadata-guide.
- **OPT:** 27 turns; single 3,557 burst; 1 Write; scaffold+drift.
- **Scripts:** scaffold 1, drift 1 — replaced 5 Writes + metadata reasoning + guide read; OPT also skipped fishing.
- **Helps? Yes** — scaffold primary; WS4/WS3 strong secondary (tr −10,097).

### script-jint-lifecycle — $0.795→$0.526 (−34%)
- **BASE:** 39 turns; T14=8,168 burst → 6 hand-Writes; TaskCreate/Update; metadata-guide.
- **OPT:** 35 turns; 2,931 burst; 1 Write; scaffold+drift; reads scaffold script once (WS1, 1,493 tok).
- **Scripts:** scaffold 1, drift 1 — replaced the 8,168 burst + 5 Writes + guide.
- **Helps? Yes** — scaffold primary; small WS1 read cost dwarfed by the burst elimination.

### e2e-wiki-pageviews — $1.220→$0.826 (−32%)
- **BASE:** 42 turns; 41,592 thinking (T10=20,950 planning + T16=20,161 metadata/bpmn derivation) → 6 hand-Writes.
- **OPT:** 39 turns; one 7,212 burst; scaffold+drift; 2 Writes; inline-python for registry inspection.
- **Scripts:** scaffold 1, drift 1 — replaced 5 Writes + the metadata portion of T16.
- **Helps? Yes** — RB (trims the 20,950 planning burst) + scaffold (removes the 20,161 metadata burst) co-dominant; −32k thinking.

### feet-inches — $1.108→$0.634 (−43%) — script as *thinking-avoider*, not write-collapse
- **BASE:** 49 turns; wrote only 2 files (bpmn+uiproj); 4 bursts ≈23k; fished validator/test/fixtures (~4.4k tok) for a uiproj template.
- **OPT:** 42 turns; bursts ≈3.7k; no fishing; scaffold(2)+drift(1) — produced *more* files than BASE yet cheaper.
- **Why:** scaffold gave a mechanical metadata path so OPT never fished or derived uiproj structure. Here scaffold replaced **no** BASE Writes (BASE wrote none of the 5) — it replaced the *research/derivation thinking*.
- **Scripts:** scaffold 2, drift 1.
- **Helps? Yes** — RB1/RB2 + WS4 (no fishing) co-primary; scaffold the enabler.

### e2e-invoice-exception-triage — $0.991→$0.841 (−15%)
- **BASE:** read 4 refs; grepped validator samples + 2 inline-python heredocs to reverse-engineer the metadata schema; wrote 6 metadata files by hand (T42–46); re-validated.
- **OPT:** read 1 ref; extracted template fields via inline-python; wrote bpmn (Write+10 Edits); scaffold(T45)+drift(T46).
- **Scripts:** scaffold 1, drift 1 — replaced ~6 Writes + schema-derivation + re-validation loop.
- **Helps? Yes** — cleanest full-bucket win: thinking −2k, tr −5,946 (no sample-grepping), turns 16→11.

---

## Wins driven by working style (context / turns)

### registry-discovery — $0.555→$0.145 (−74%)
- **BASE:** 41 turns; thinking flat (514); ~14 TaskCreate/Update turns; pulled ~5.8k tok registry JSON into context then **re-emitted via 7 Writes**.
- **OPT:** 12 turns; 3 capture commands with `> file` redirect (each →1 tok), 1 `ls`, no todos, 1 get.
- **Why:** **WS6** (keep outputs small) turns 5.8k context-resident tokens into ~1 tok each; WS7/WS2 kill the todos. Thinking flat — not a thinking win.
- **Scripts:** 0/0/0.
- **Helps? Yes** — biggest % in the suite; tool-calls 32→7.

### edit-add-node — $0.446→$0.329 (−26%)
- **BASE:** read target bpmn (1,022) **and** the full `structural-bpmn.md` (7,125); 3 todos; 2 edits.
- **OPT:** read only the target bpmn; **zero reference docs**; 2 CLI gets (54+361 tok); 5 small edits.
- **Why:** OPT recognized an edit task needs the file, not the 7,125-tok authoring guide. Turns identical, thinking *rose* — the win is entirely the avoided 7,125-tok read (w + r×~24 turns).
- **Scripts:** 0/0/0.
- **Helps? Yes** — pure WS3/WS7 context lever.

### hitl-brownfield-insert — $0.495→$0.426 (−14%)
- **BASE:** `registry get/search HITL` + **4 inline-python heredocs** digging through `registry.json` for the HITL schema; then edits.
- **OPT:** `registry pull` + one `get` (773 tok) + one 3,823 burst → edit directly.
- **Why:** WS3/WS4 collapse 5 registry-spelunk calls to 1. Thinking flat, tr flat — the −14% is calls 22→17 / turns 10→8 cutting the re-read tax.
- **Scripts:** 0/0/0.
- **Helps? Yes** — best-in-class for a no-script task, purely from fewer exploration calls.

### edit-remove-node — $0.446→$0.309 (−31%)
- **BASE:** TaskCreate/Update list; 8 Edits → re-Read → 2 Edits → validator flailing → 3rd Read of same bpmn. 44 iters, T=15.
- **OPT:** no todos; planned edit path (small burst); 6 Edits → 1 re-Read → 3 Edits → validator. 29 iters, T=9.
- **Why:** WS7+WS2 (no todos, planned edits) → fewer edit→re-read loops; fewer turns (15→9) multiplies down the r term. Thinking rose slightly (RB trade).
- **Scripts:** 0/0/0.  **Helps? Yes** — working-style + turns.

### multi-city-weather — $0.860→$0.630 (−27%)
- **BASE:** 4 docs; two bursts (11,736+7,828); **wrote the bpmn twice** (T14 then rewrite T16); `find | sort` dump (2,728 tok).
- **OPT:** 2 docs; one 14,737 burst; single write; generate_diagram.
- **Why:** WS4/WS2 (no rework, fewer turns) ≈ WS7 (skip 2,816 doc + 2,728 dump) > RB2.
- **Scripts:** generate_diagram 2 — but atop an already-DI file → no credit.  **Helps? Yes.**

### loop-multiply — $0.729→$0.471 (−35%)
- **BASE:** 4 docs; 2 bursts (6,772+5,986); hunted validator fixtures (T14–18); wrote bpmn+uiproj; 43 turns.
- **OPT:** 2 docs; 1 burst (5,728); write; generate_diagram; 28 turns.
- **Why:** RB1/RB2 (~half) > WS2 (−15 turns → re-read multiplier on the shared 7,125 ref) + WS4/WS7 (no fixture hunt).
- **Scripts:** generate_diagram 2, atop already-DI file → no credit.  **Helps? Yes.**

### author-validate — $0.515→$0.325 (−37%)
- **BASE:** structural + registry-md; **9 TaskCreate/Update calls**; 2 bursts; write; validator.
- **OPT:** structural only; 2 small bursts; writes semantic-only bpmn (DI_in_written=False, 1,949 chars) then `generate_diagram.py` adds DI.
- **Why:** WS2/WS7 (−8 todo turns) > WS4 (skip registry-md) ≈ RB. **The one clean generate_diagram win** — it legitimately replaced manual DI authoring (BASE Write 3,667 chars vs OPT 1,949).
- **Scripts:** generate_diagram 1 (real, small).  **Helps? Yes.**

### parallel-fork-join — $0.477→$0.382 (−20%)
- **BASE:** structural only; one 5,067 burst; **6 TaskCreate/Update**; write.
- **OPT:** structural only; one 2,223 burst; write. Same information diet.
- **Why:** RB1/RB2 (5,067→2,223) ≈ WS2/WS7 (−6 todo turns).  **Scripts:** 0/0/0.  **Helps? Yes.**

### transform-map — $0.490→$0.404 (−18%)
- **BASE:** structural + registry-md; one 5,731 burst; write; **3 inline-python heredocs** poking the XML.
- **OPT:** structural + lighter expression doc; one 3,875 burst; write; generate_diagram.
- **Why:** WS7/WS5 (drop the 3 inline-python probes) > RB2 > WS3 (lighter ref).  **Scripts:** generate_diagram 1, trivial.  **Helps? Yes.**

### transform-filter — $0.408→$0.338 (−17%)
- **BASE:** structural + registry-md(2,816); write; validator.
- **OPT:** structural + expression(1,168); write; 1 inline-python check.
- **Why:** WS3 (registry-md→expression swap, −1,648 persistent tok) + WS2 (−2 turns). Thinking rose slightly (noise).  **Scripts:** 0/0/0.  **Helps? Yes, small.**

### terminate — $0.359→$0.319 (−11%)
- **BASE:** one 2,023 burst then work spread over 13 calls / 7 turns.
- **OPT:** one concentrated 3,177 burst up front → straight to Write→validate in 4 turns.
- **Why:** WS2 (plan-up-front → 7→4 turns) — the r term on the 7,125 ref drops. Thinking rose (RB2 concentration).  **Scripts:** 0/0/0.  **Helps? Yes.**

### operate-diagnose-minimal-fault-triage — $0.261→$0.233 (−11%)
- **BASE:** 11 `uip` diagnostic probes (job status ×2, incidents, incident get, variables ×2, asset, element-execs, cursors, …).
- **OPT:** 6 probes → one 927-tok "enough" reasoning step → wrote report.
- **Why:** WS7/WS4 pruned ~7 redundant probes (17→10 calls). Thinking rose (a little reasoning replaced brute force).  **Scripts:** 0/0/0.  **Helps? Yes.**

### message-catch — $0.812→$0.726 (−11%)
- **BASE:** reads + heavy TaskCreate/Update; two mid bursts.
- **OPT:** pulled the registry template up front (T7→2,461 tok) to copy field shapes rather than reason them out; concentrated thinking into one 2,197 burst.
- **Why:** RB1 (fetch template, don't re-derive) — thinking −3,785 dominant; WS4 secondary. Tool-results rose slightly (the template pull) but g win dwarfs it.  **Scripts:** 0/0/0.  **Helps? Yes.**

### http-weather — $0.606→$0.544 (−10%)
- **BASE:** registry-discovery heavy (`tools install`, `pull`, searches/gets) + TaskCreate/Update churn; ~30 calls.
- **OPT:** fewer probes; one inline-python template extract; generate_diagram; ~22 calls.
- **Why:** thinking & tool-results flat → saving is entirely turn/call-driven (30→22, 12→11) shrinking the re-read multiplier. WS2/WS7.  **Scripts:** generate_diagram 1, minor.  **Helps? Yes.**

### dice-roller — $0.582→$0.419 (−28%)
- **BASE:** modest bursts (6,176 total, naturally cheap); 2 files; `find` dump T29=2,544; registry-md(2,816).
- **OPT:** tiny bursts (1,808); scaffold+drift+diagram; DI from generate_diagram.
- **Why:** WS3/WS6 (skip registry-md + find-dump) primary — tool-results −6,392; RB (already low) secondary; scripts minor.  **Scripts:** 1/1/1.  **Helps? Yes.**

---

## api-workflow — think-instead-of-crawl

### api-workflow-task — $1.102→$0.995 (−10%)
- **BASE:** after reads, a **filesystem-exploration spree** — Glob storms over `**/*.uiproj`/`**/operate.json` (T21=3,590-tok, T22=5,267-tok results), read validator fixtures, wandered into other tasks' run outputs. tool-results ballooned to 27,947.
- **OPT:** 2 refs, 2 `uip` calls, **two ~10k bursts** (T8=9,677, T12=9,920) to reason out the structure; scaffold+diagram+drift.
- **Why:** WS3+RB2 — OPT *thought* its way to the answer; BASE *searched the disk*. Thinking **rose** +6,308 (g against us) but tool-results collapsed 28k→14k over fewer turns, and the r·remaining re-read tax on the −13,692 tokens outweighs the thinking rise. Clearest case where turns/context beat the g term.
- **Scripts:** 1/1/1, secondary.  **Helps? Yes, modestly.**

---

## Flat / noise (≈±2%, or thinking down but cost unmoved)

### agent-job — $0.768→$0.761 (−1%)
- **BASE:** 3 massive bursts = 21.8k (T14=9,113) before one Write.
- **OPT:** 4 inline-python template inspections cut reasoning to 12,956.
- **Why flat:** turns unchanged (11→11) and the fixed big reads (7,125+2,816) identical, so the r term — the real $ floor here — didn't move. Thinking −9,294 but cost ≈flat. Shows the g-heuristic overstates output's share on input-heavy small-output tasks.  **Scripts:** generate_diagram 1, negligible.

### integration-service-boundary — $0.977→$0.965 (−1%)
- **BASE:** two big bursts (T15=10,051); wrote draft; validated.
- **OPT:** grep'd `scaffold_metadata.py` (T11) **only to learn how it reads `entryPointId` — never executed it** (correct: this is the "draft boundary, no package files" task); one 4,281 burst; then a long fix tail (validate→edit→validate→re-read).
- **Why flat:** RB2 halved thinking (−8,541) but the edit/re-validate/re-read tail (WS4/WS6 slip) clawed it back via extra turns + re-runs. Net ≈noise. **Constraint respected — scaffold correctly not run.**  **Scripts:** 0/0/0.

### transform-group-by — $0.414→$0.410 (−1%)
- **BASE:** 3 refs; one 4,517 burst.
- **OPT:** 2 refs; one 2,663 burst; **2 inline-python probes**; same 22 turns.
- **Why flat:** real savings (thinking −1,325, registry-md skipped) cancelled by identical turn count + the 2 re-added inline-python heredocs.  **Scripts:** 0/0/0.

---

## Regressions (OPT more expensive)

### gateway-sequence-flows — $0.651→$0.978 (+50%) — REAL BACKFIRE
- **BASE:** read 3 refs → **one** 11,757-tok burst → wrote bpmn → validated. Clean.
- **OPT:** read structural → 4 registry probes → **read `scaffold_metadata.py` (T12, T15) and `generate_diagram.py` (T17)** → then ran scaffold+diagram+drift → validated.
- **Why more:** thinking split into **four** bursts ≈27k (T10=8,260, T13=2,470, T16=8,700, T18=7,325), each opening with "let me plan the BPMN structure" and re-listing the same 10 nodes. Trigger: each script/reference Read re-armed the planning reflex. +17k thinking = the whole regression.
- **Attribution:** **WS1 ("understand scripts first") firing against RB1/WS4** — reading the source re-triggered re-derivation instead of just calling the script. Signal, not noise.  **Scripts:** 1/1/1 (all read + run).

### subprocess — $0.413→$0.557 (+35%) — mild backfire
- **BASE:** structural → one 4,932 burst → Write → validate. 20 turns.
- **OPT:** structural → **second ref (expression, WS3 violation)** → Write → **ran a diagram script → Read its output → Edit** → validator → **re-Read output**. 28 turns.
- **Why more:** extra ref + script + two output re-reads (tr +2,717). Script overhead + WS3 slip on a task that didn't need them.  **Scripts:** generate_diagram 1.

### switch — $0.248→$0.318 (+28%) — script overhead + env noise
- **BASE:** structural → 3,738 burst → Write → npm-install-in-place → validate. 12 turns.
- **OPT:** structural → 1,014 burst → Write → **`pip install` (diagram script)** → validator dance → **2 inline-python verifications**. 18 turns.
- **Why more:** thinking *fell* 3× (3,884→1,163); the +$0.07 is the pip-install + validator copy + 2 redundant verifications. Script overhead on a tiny task.  **Scripts:** generate_diagram 1.

### rpa-job — $0.379→$0.438 (+16%) — script overhead; reasoning improved
- **BASE:** one 6,063 burst → Write → validate. 22 turns.
- **OPT:** 2,858 burst → Write → **`pip install` (diagram script)** → validator dance → Read output. 26 turns.
- **Why more:** thinking halved and output dropped, yet cost rose — the 4 extra turns (pip install + validator copy) re-bill context via the carry term. Minor script overhead.  **Scripts:** generate_diagram 1.

### timer — $0.194→$0.261 (+34%) — pure validator dance (env noise)
- **BASE:** Read → one 2,649 burst → Write → `npm install --silent` worked in place → 7 turns.
- **OPT:** same → smaller 1,065 burst → Write → **8 turns of validator churn** (npm build, ls, mkdir, cp -r). 13 turns.
- **Why more:** thinking more than halved; the entire regression is the validator-copy dance BASE happened to avoid. Not the optimization.  **Scripts:** 0/0/0.

### event-trigger-start — $0.426→$0.517 (+22%)
- **BASE:** reads → registry probes → 2 bursts → Write once → validate.
- **OPT:** reads → registry probes → Write → **registry get → Write AGAIN** → validate.
- **Why more:** thinking down, tool-results flat; one extra author cycle (write→get→rewrite) raised output. Largely noise + a re-author.  **Scripts:** 0/0/0.

### smoke-registry-discovery — $0.158→$0.177 (+13%) — partial WS6 win, +2¢ net
- **BASE:** `tee` dumped 2,444 tok registry JSON into context. 15 turns, tr 7,044.
- **OPT:** redirected output to files (`> file`, near-zero result tokens) → tr **halved to 3,336** (WS6 worked) → then 3 inline-python parsing turns.
- **Why more:** the +$0.02 is higher thinking (429→687) + 3 python turns, outweighing the tool-result win. Essentially break-even / noise.  **Scripts:** 0/0/0.

### edit-move-node — $0.203→$0.326 (+61%), edit-update-node — $0.139→$0.230 (+65%), edit-add-output — $0.273→$0.299 (+10%)
- Tiny edit tasks (≤$0.33). Deltas are 2–12¢. Dominated by the validator npm-install dance (per-rep environment luck, `node_modules` absent both arms) and n=1 variance; edit-move-node has a minor WS3/WS4 slip (re-read a file already held; 3 edits vs 1 write). **Not reliable signals at n=1.**  **Scripts:** 0/0/0.

---

## Synthesis

- **Scripts contributed on ~6 tasks**, all where BASE hand-authored the 5 package-metadata files (business-rule, calculator, hitl-rpa, script-jint, e2e-invoice, e2e-wiki co-dom). Their value is the **derivation thinking they obviate** (g bucket), not the collapsed Writes (w, pennies). `generate_diagram.py` was a *real* win only on author-validate; elsewhere BASE built the diagram inline so it added turns.
- **Thinking-budget prompt (RB1/RB2)** is the largest lever overall — dominant on ~14 tasks, isolated perfectly on hitl-completed-wired (identical trajectory, only the burst halved).
- **Working style** is the reliable universal secondary and the sole driver on the no-script wins (registry-discovery WS6, edit-add-node WS3, hitl-brownfield WS3/4, operate-diagnose WS7, terminate WS2).
- **Scripts and RB attack the same bucket** (thinking) and separate by task shape; **working style attacks a different bucket** (tool-results × turns re-read tax).
- **1 real backfire** (gateway: reading scripts re-triggers re-planning) and **mild script-overhead** on 3 trivial tasks; the rest of the regressions are n=1 validator-dance noise on sub-$0.15 tasks.
