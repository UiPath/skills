# Generate Confluence Coding-Agents Scorecard

Build a Coding-Agents Scorecard Confluence page from two data sources and the canonical product→skill mapping below. Combines **test coverage** (static) with **eval scores + pass/fail** (a coder_eval run), maps both onto the org scorecard's product rows, and publishes a new Confluence page.

**Input:** `$ARGUMENTS`
- **Run dir** (required) — path to a coder_eval run, e.g. `/Users/<you>/src/coder_eval/runs/2026-05-26_04-05-02`. Must contain `run.json`.
- **`--coverage <path>`** (optional) — coverage summary path; defaults to `tests/reports/SUMMARY.md`. If stale or missing, see Phase 2.
- **`--variant <id>`** (optional) — which run variant to score; see Phase 1 nuance 5.
- **`--draft`** (optional) — create the page as a draft instead of `current`.
- **`--target <pct>`** (optional) — pass-rate bar for the gap-to-target headline; defaults to **95** (the org scorecard's stated bar). See Phase 4.
- **`--parent <pageId>`** (optional) — parent page; defaults to the org scorecard page (see Publish Target).

**Argument parsing.** The first bare (non-`--`) token is the **run dir**. Do NOT treat a second bare path as the coverage source — coverage must be passed via `--coverage` to avoid ambiguity (two raw paths are indistinguishable). If `$ARGUMENTS` is empty, ask for the run dir; do not guess the "latest" run.

**Run date** (used in the title and panels): take the run-dir folder name if it is a timestamp (`YYYY-MM-DD...`), else `run.json.start_time` (date portion). State which you used.

**Output:** A new Confluence page in space **CA** under the org scorecard, titled `Coding Agents Scorecard — Eval Scores & Test Pass/Fail (run <run-date>)`. Returns the page URL.

> This command **creates** a page (never overwrites the org scorecard). The numbers it fills are **derived only** — Build/Operate/Diagnose eval scores and Tests Pass/Fail come from the run; Test Coverage comes from the coverage source. It leaves Product-Coverage / Exhaustive / FDE-Golden columns blank (not derivable here).

---

## Publish Target (defaults)

| Field | Value |
|---|---|
| cloudId | `uipath.atlassian.net` |
| spaceId (CA) | `90537164849` |
| Parent page (org scorecard) | `90748321845` |

Confirm these still resolve with `getConfluenceSpaces`/`getConfluencePage` before publishing.

**Stale parent.** The org scorecard is re-created weekly, so the hard-coded parent id (`90748321845`) may 404. If `getConfluencePage` on it fails: search the CA space for the most recent page whose title starts with `Coding Agents Scorecard` (`searchConfluenceUsingCql`: `space=CA AND title ~ "Coding Agents Scorecard*"`, newest first), use that as parent, and tell the user which parent you picked. If none found, create the page at the space root and flag it.

**Auth / access.** If the Atlassian tools are unavailable or the CA space is not accessible, stop and report — do not write the page anywhere else.

---

## Phase 1 — Parse the coder_eval run

First check `<run-dir>/run.json` exists and parses. **If missing or not valid JSON, stop** and tell the user (point at `experiment.json`/`run.md` as alternates, but do not screen-scrape `experiment.md` for per-skill numbers — `run.json` is the only structured source). Then aggregate per **skill** (derive skill from each task's `task_path`: the path segment after `tests/tasks/`).

Run this (adjust the path):

```python
import json, re
from collections import defaultdict, Counter
d = json.load(open('<run-dir>/run.json'))
tr = d.get('task_results') or []
if not tr: raise SystemExit('run.json has no task_results — run incomplete or wrong file')

# --- multi-variant guard: score exactly one variant ---
variants = sorted({t.get('variant_id') for t in tr})
TARGET = '<variant>' if '<variant>' in variants else ('default' if 'default' in variants else variants[0])
if len(variants) > 1: print(f'NOTE multiple variants {variants}; scoring {TARGET!r}')
tr = [t for t in tr if t.get('variant_id') == TARGET]

DIAG = {'diagnose','troubleshoot'}        # both merge into the Troubleshoot column
STD  = ['build','operate','diagnose']     # the three scorecard eval columns
def new(): return {'pass':0,'total':0,'scores':[],'mode':defaultdict(list)}
def add(b, t, ws):                         # fold one task_result into a bucket
    b['total'] += 1
    if t.get('status') == 'SUCCESS': b['pass'] += 1
    if ws is not None:
        b['scores'].append(ws)             # None scores excluded consistently
        for tag in (t.get('tags') or []):
            if tag.startswith('mode:'):
                v = tag[5:]; b['mode']['diagnose' if v in DIAG else v].append(ws)

agg  = defaultdict(new)     # per skill (first path segment under tests/tasks/)
psub = defaultdict(new)     # per uipath-platform sub-dir — for the 5 platform product rows
unmapped = []; nonstd = Counter()
for t in tr:
    ws = t.get('weighted_score')
    m = re.search(r'/tests/tasks/([^/]+)/', t.get('task_path',''))
    if not m: unmapped.append(t.get('task_id')); continue   # don't fold into a skill
    skill = m.group(1); add(agg[skill], t, ws)
    if skill == 'uipath-platform':
        m2 = re.search(r'/tests/tasks/uipath-platform/([^/]+)/', t.get('task_path',''))
        add(psub[m2.group(1) if m2 else '(root)'], t, ws)
    for tag in (t.get('tags') or []):      # collect every non-scorecard mode value
        if tag.startswith('mode:') and tag[5:] not in (DIAG | {'build','operate'}):
            nonstd[tag[5:]] += 1

def pct(xs): return round(100*sum(xs)/len(xs)) if xs else None
def cells(b):                              # per-COLUMN fallback (not per-skill)
    mean = pct(b['scores']); out = {}
    for col in STD:
        xs = b['mode'].get(col)
        out[col] = (f"{pct(xs)} (n={len(xs)})" if xs                 # real mode-tagged mean
                    else (f"{mean}*" if mean is not None else None)) # else overall-mean fallback (*)
    return mean, out
def line(name, b):
    mean, c = cells(b)
    extra = {k: f"{pct(v)} (n={len(v)})" for k,v in b['mode'].items() if k not in STD}
    print(f"{name:32} {b['pass']}/{b['total']:<4} mean={mean}  "
          f"build={c['build']}  operate={c['operate']}  troubleshoot={c['diagnose']}"
          + (f"  NON-SCORECARD-MODES={extra}" if extra else ''))

print('=== PER SKILL ===')
for s in sorted(agg): line(s, agg[s])
print('\n=== uipath-platform SUB-DIRS (split eval/passfail across the 5 platform rows) ===')
for s in sorted(psub): line(s, psub[s])
run_n = len(tr); succ = sum(1 for t in tr if t.get('status')=='SUCCESS')
sc = [t['weighted_score'] for t in tr if t.get('weighted_score') is not None]
print('\nTOTAL', run_n, 'run,', succ, 'passed,', (round(100*succ/run_n,1) if run_n else 0), '% success,',
      'overall mean', (round(100*sum(sc)/len(sc),1) if sc else 0), '%')
print('status counts:', Counter(t.get('status') for t in tr))   # ERROR vs FAILURE vs MAX_TURNS …
print('skipped_tasks:', len(d.get('skipped_tasks') or []))
if nonstd:   print('NON-SCORECARD mode values seen (surface, never drop/fold):', dict(nonstd))
if unmapped: print('UNMAPPED task_ids (no tests/tasks/<skill>/ in path):', unmapped)
```

Record per skill: **Tests Pass/Fail** (`pass/total`), **mean score %**, per-mode % for `build`/`operate`/`diagnose` (each with its `(n=…)` tagged-task count), plus any `NON-SCORECARD-MODES`. The script also prints the **`uipath-platform` sub-dir breakdown** (Phase 3 platform split), the **status-code counts** (ERROR vs FAILURE vs MAX_TURNS_EXHAUSTED — use for the failures note in Phase 4), the **overall mean weighted score**, and any `NON-SCORECARD` mode values / `UNMAPPED` task_ids. Headline numbers come from this script (`run_n`, `succ`, overall mean) — **recompute for the scored variant**, do not copy `d['tasks_run']`/`experiment.md` blindly (those count all variants).

**Critical nuances:**
1. **Mode tags are sparse — fall back PER COLUMN, not per skill.** Only mode-tagged tasks feed Build/Operate/Troubleshoot. For **each** of the three columns independently: if the skill has ≥1 task tagged for that mode, show that mode's mean; otherwise fill the cell with the skill's **overall mean** marked `*` (footnote: "overall mean — no `mode:<x>` tasks"). Consequences: a skill with zero mode tags shows `mean*` in all three (the original all-or-nothing case); a skill tagged only `build` shows its real Build % and `mean*` for Operate/Troubleshoot — never leave those two blank, which would falsely read as "no signal" when the skill ran many untagged tasks. The script's `cells()` does this; the `(n=…)` count rides on every non-fallback cell. Keep the `(n=…)` counts **only in the Source Data table** (not the Product scorecard, whose columns must match the org card exactly) so reviewers can see how thin a column is — e.g. a `build 0 (n=1)` is one bad task, not a systemic failure.
2. **Status → pass.** `SUCCESS` = pass; `FAILURE`/`ERROR`/`MAX_TURNS_EXHAUSTED`/`TIMEOUT` = fail.
3. **Skipped tasks.** `run.json.skipped_tasks` lists tasks the runner excluded (`skip: true` in the YAML). Pass/Fail denominators are *run* tasks, so authored-count may exceed run-count. Note skips in the per-skill table (e.g. HITL: "23 authored, 1 skipped → 19/22 run").
4. **`mode:diagnose` ≡ `mode:troubleshoot`** (merged into the Troubleshoot column). **Every other mode value** — anything not in `{build, operate, diagnose, troubleshoot}` — has **no scorecard column**: `mode:inspect` (BPMN), `mode:edit-validate` (RPA legacy), and any future value. The script's `NON-SCORECARD-MODES` / `NON-SCORECARD mode values seen` output catches them all. Surface every such value in a note (per-skill in Source Data, plus a one-line global note) with its score and `(n=…)`; **never silently drop one or fold it into Troubleshoot.** Do not invent a column for it either — these tasks still count in the skill's overall mean and pass/fail, just not in a Build/Operate/Troubleshoot cell.
5. **Multiple variants.** A/B experiments put one `task_result` per variant per task; scoring all of them double-counts. The script scores one variant (`--variant`, else `default`, else the only/first one) and prints which. If the user wants per-variant scorecards, run once per variant.
6. **Skill in run not in product mapping.** Connector/aux skills (e.g. `uipath-troubleshoot`, `uipath-review`, `uipath-planner`, `uipath-tasks`, `uipath-feedback`, `uipath-salesforce-*`, `uipath-dev`) have run data but no product row. Include them in the **Source Data — Per Skill** table; do NOT force them into a product row. List any `UNMAPPED task_ids` to the user (malformed paths / tasks outside `tests/tasks/`).
7. **Directory ≠ `skill:` tag.** The script keys on the `task_path` directory, not the `skill:` tag in the YAML (a connector task under `uipath-maestro-flow/` aggregates to flow even if its `skill:` tag differs). This matches how the product mapping is defined; don't switch to tag-based keying.

## Phase 2 — Parse the coverage source

**Prefer the structured sidecar.** If `tests/reports/coverage.json` exists (written by `/test-coverage all`), read it instead of scraping markdown — `skills.<name>.overall_pct` is the Test Coverage value, `planned` flags planned skills, and you also get `top_untested`, per-dimension counts, and contributions for free. This is the stable contract; fall back to parsing `SUMMARY.md` only when the JSON is absent (older runs). If both exist but disagree, trust `coverage.json` and note the staleness (regenerate with `/test-coverage all`).

Read the coverage source (default `tests/reports/SUMMARY.md`). For each skill take the **Overall** % from the Overview table — this is the **Test Coverage vs Skills** value (coverage of taught capabilities by tests; **not** a pass-rate). Planned-but-missing skills are `0% (planned)`.

**Anchor to the right table — `SUMMARY.md` has more than one skill-row table.** It contains several tables with `| uipath-… |` rows (the **## Overview** table AND the **Minimum Bar Check** table, possibly others). A naive `line.startswith('| uipath-')` parse reads them **all** and double-counts skills. Parse **only the Overview table**: locate the `## Overview` heading, take the next markdown table (its header row contains `Overall`), and stop at the following `##` heading. The Overall % is that table's 7th column (`Overall`), not any column from the Minimum Bar table.

**Cell parsing.** The Overall cell carries markup and non-numeric decoration: strip bold (`**77%**` → `77%`); preserve a leading `~` for approximate values (`~7%`, e.g. coded-apps) and the `(planned)` suffix verbatim; a value may also be `0%` or a bare `—`. Use the **percentage string**, not the raw fraction.

**Skill set mismatch** (the two snapshots rarely list the same skills):
- *In run, absent from coverage* (new skill, SUMMARY not regenerated) → coverage `—` for its rows; warn and recommend `/test-coverage all`. Do not write `0%` (that reads as "tested, no coverage" — false).
- *In coverage, absent from run* (skill not exercised this run) → coverage fills normally; Tests Pass/Fail = `not in run`, eval `—`.
- *Planned skills* (`0% (planned)`) → carry through verbatim.

**If the coverage source is missing** (`tests/reports/SUMMARY.md` does not exist — e.g. fresh clone, folder never generated): this command does **not** create `tests/reports/` itself. Invoke **`/test-coverage all`** first; its Phase 5 creates `tests/reports/` and writes `SUMMARY.md` plus per-skill reports. Then re-read. Do not proceed with empty/zeroed coverage — that would silently publish a scorecard with a blank Test Coverage column.

If the file exists but its `*Generated:*` date is far from the run date, warn the user and offer to re-run `/test-coverage all` so the two snapshots align.

## Phase 3 — Apply the canonical product→skill mapping

The org scorecard's product rows are **not** 1:1 with skill folders. Use this mapping (verified 2026-05-26). A task counts toward **every** product it exercises (double-counting is intended).

**The mapping is a snapshot — reconcile it.** The org scorecard's product list drifts. Read the parent page's Product table and diff its rows against this table:
- *Row on the org scorecard but not here* → emit the row with all-derived columns blank and flag it ("new product row, no skill mapping — confirm owner"). Never silently drop it.
- *Row here but gone from the org scorecard* → omit it and note the removal.
- *New skill folder under `skills/` mapping to no product row* → surface in the Source Data table and tell the user (candidate for a new product row).
Do not edit this embedded table on the fly; report drift so a human updates the command.

| Product row | Skill / test dir | Notes |
|---|---|---|
| Flow (uip maestro flow) | `uipath-maestro-flow` | |
| Case Management | `uipath-maestro-case` (`uipath-case-management/` empty) | |
| BPMN | `uipath-maestro-bpmn` | |
| Integration Service (uip is) | `uipath-platform/integration-service` | 5 dedicated + cross-cutting connector tasks in flow/agents |
| HITL (uip hitl) | `uipath-human-in-the-loop` | no `uip hitl` verb; +`uipath-maestro-flow/hitl` cross-cutting |
| Low & Code Agents | `uipath-agents` | |
| IXP | `uipath-ixp` | |
| RPA / Studio / Computer Vision | `uipath-rpa` (incl. `legacy/`) | three product rows share one skill |
| Data Fabric (df / entities) | `uipath-data-fabric` | |
| API Workflow | `uipath-api-workflow` | +api-workflow-tool tasks in agents |
| Coded Apps | `uipath-coded-apps` | skill exists, 0 tests |
| Orchestrator | `uipath-platform/orchestrator` + `uipath-platform/resources` | |
| ECS / Context Grounding | none dedicated | exercised in agents (context_index/deeprag) |
| Test Manager | `uipath-test` | |
| Solutions | `uipath-solution` | +~many agent tasks publish via `uip solution` (cross-cutting only) |
| Governance | `uipath-governance` | |
| Identity & Auth Z | `uipath-admin` | |
| Licensing | `uipath-platform/licensing` | |
| LLMOPS/Traces | `uipath-platform/traces` | |
| LLM GW | `uipath-platform/llmgateway` | |
| Notification Service | none | no tests |
| Serverless | none dedicated | incidental in agents bindings (`uip functions`) |
| DU / Process Mining / Insights / Task Mining | planned skills (no folder) | `0% (planned)` |

**Platform — split eval/pass-fail by sub-dir, keep coverage aggregate.** `uipath-platform` is one skill spanning 5 product rows, but the run's `task_path` already carries the sub-dir, so the Phase 1 script's `psub` breakdown gives **per-sub-product eval % and pass/fail directly from the run** — use it. This matters: the skill-level aggregate hides real variance (e.g. a 33% Build aggregate may be one weak sub-product dragging four healthy ones). Map sub-dir → product row:

| Platform sub-dir(s) | Product row |
|---|---|
| `integration-service` | Integration Service (uip is) |
| `orchestrator` + `resources` | Orchestrator (uip or) — **sum both** buckets |
| `licensing` | Licensing |
| `traces` | LLMOPS/Traces |
| `llmgateway` | LLM GW |

Apply each sub-dir's pass/fail and the three eval cells (with the same per-column fallback as any skill) to its row. **Coverage stays the skill-level aggregate** (`SUMMARY.md` only carries the one `uipath-platform` Overall %, e.g. 77%) applied to all 5 rows — unless `tests/reports/uipath-platform.md` provides per-sub-dir coverage, in which case split that too. Footnote ³ now means: *eval/pass-fail are this sub-product's own run numbers; Test Coverage is the platform-wide value.* If a sub-dir has too few tasks (e.g. `n<3`) for a stable eval, fall back to the skill aggregate for that row and say so in the cell's Source-Data note.

**Dedicated vs cross-cutting.** The "Product → Test Mapping" output table reports **dedicated** task counts (tasks authored in that product's own dir) plus a cross-cutting note. To compute dedicated counts and CLI-surface cross-cutting, count task YAMLs per dir and scan `command_executed` `command_pattern`s for the product's `uip` verb (see Appendix A).

## Phase 4 — Build the page body (HTML)

Produce these sections, in this order:

1. **Source + caveat panels** — `panel-info` with run id/path, variant scored, tasks run/passed/success-rate/overall-mean score, generated date. `panel-warning` listing column semantics: Tests Pass/Fail = run outcomes; Test Coverage = SUMMARY "Overall"; Eval `*` = **per-column** overall-mean fallback (no `mode:<x>` tasks for that column); non-scorecard mode tags (e.g. `inspect`, `edit-validate`) excluded from the three columns; platform rows (³) carry per-sub-product eval/pass-fail but the platform-wide coverage; run is a snapshot whose task counts may differ from the current repo; Product-Coverage/Exhaustive/FDE blank.
2. **Gap-to-target headline** (`panel-note`, near the top) — state run success-rate vs the `--target` bar (default 95%): e.g. `78.8% vs 95% target → 16.2pp gap; ≈ N more passing tasks needed` where `N = ceil(target/100 × run_n) − succ`. List the products **below bar** (pass-rate < target), worst first, so the page answers the org's own stated question. If success-rate ≥ target, say so plainly.
3. **Product Level Scorecard** — reproduce the org scorecard's product table **columns exactly** (Product/Capability, Build/Operate/Troubleshoot Product Coverage, Test Coverage vs Skills, Build/Operate/Diagnose Eval %, Tests Pass/Fail, Exhaustive, FDE Golden). Fill only: Test Coverage, the three Eval %, Tests Pass/Fail. Leave the rest blank. **Do not put `(n=…)` here** — these columns must match the org card. Footnotes: platform sub-product split + platform-wide coverage (³), rpa-shared (²), per-column overall-mean fallback (*), non-scorecard mode tags (†).
4. **Coverage × Eval risk reads** — the analytical payoff of merging the two sources. For each product with both a coverage % and a pass-rate, classify into a quadrant (thresholds: coverage ≥ 50% = "tested", pass-rate ≥ `--target` = "passing"):

   | Coverage | Pass-rate | Quadrant | Read |
   |---|---|---|---|
   | high | low | **Weak** | well-tested, agent fails — genuine product gap (e.g. Orchestrator) |
   | low | high | **False confidence** | passes the little that exists; high score is not reassurance (e.g. API Workflow 34% cov / 1-1, Coded Apps ~7% / 1-1) |
   | low | low | **Unmeasured** | thin tests AND failing — flag for both |
   | high | high | **Healthy** | — |

   Render as a short table or panel listing only the **Weak**, **False confidence**, and **Unmeasured** products (skip Healthy). Note the `(n=…)` denominator for any "passing" verdict resting on < 3 tasks — a 1/1 pass is not evidence. This is the section that says what no single column can.
5. **Source Data — Per Skill** — one row per skill: coverage %, pass/fail, mean %, build/operate/troubleshoot % (**with the `(n=…)` counts and `*` fallback markers**), notes. Notes carry: skips (authored vs run), any non-scorecard mode values + scores, and run-vs-repo task-count divergence where notable.
6. **Product → Test Mapping (authoritative)** — Product, test dir, dedicated tasks, coverage %, cross-cutting note.

Close with a short **failures note** drawn from the script's status-code counts — name the worst 2–3 skills by pass-rate (e.g. `uipath-troubleshoot 3/36`) and the ERROR/FAILURE/MAX_TURNS split — so the page is actionable, not just a number board.

Keep prose terse (repo token-optimization rules). Use `—` for not-applicable, `*`/`²`/`³`/`†` footnote markers consistently.

## Phase 5 — Publish

1. Verify target with `getConfluenceSpaces keys=CA` (spaceId) and `getConfluencePage` on the parent (apply the Stale-parent fallback above if it 404s).
2. **Duplicate-title check.** A page titled `… (run <run-date>)` may already exist from a prior run of this command (re-runs are common). Search CA for that exact title first. If found, ask the user: **update** the existing page (`updateConfluencePage` — safe, it's our child page, not the org scorecard), **create a new one** with a ` (v2)`/timestamp suffix, or **abort**. Default to update. Never blindly create a second page with an identical title.
3. `createConfluencePage` (or `updateConfluencePage` per step 2) with `cloudId`, `spaceId`, `parentId`, `contentFormat: html`, `status: current` (or `draft` if `--draft`), title `Coding Agents Scorecard — Eval Scores & Test Pass/Fail (run <run-date>)`.
4. **HTML rejection.** `createConfluencePage` rejects invalid ADF nesting (block elements inside inline, headings in table cells, etc.) with a descriptive error. On rejection, fix the offending markup and retry — do not fall back to markdown (it loses panels/footnotes). Common cause: stray block tags inside `<td>`.
5. **Round-trip verification.** A successful create response does NOT guarantee the body rendered intact — HTML→ADF conversion can silently drop or merge cells/panels. Re-fetch the page (`getConfluencePage`, `contentFormat: html`) and assert: the Product Level Scorecard table has the expected **row count** (one header + one per org product row, e.g. 29 data rows) and **11 columns**; the Source Data and Product→Test tables are present with their expected row counts; and the panels survived (info/note/warning macros present). If a table was mangled, fix the markup and `updateConfluencePage` — do not leave a corrupted page live. Report the assertion result.
6. Return the `webui` URL. Summarize what was filled, what was left blank, the gap-to-target and risk-read findings, and any drift/mismatch/skip notes surfaced in Phases 1–3.

---

## Appendix A — CLI-surface cross-cutting scan (optional)

To attribute a task to a product by the CLI command its success criteria verify, scan each task's `command_executed` `command_pattern` and match the leading `uip <verb>`:

```python
import re, glob
from collections import defaultdict
RULES = [(r'^uip (maestro )?flow\b','Flow'),(r'^uip (maestro )?bpmn\b','BPMN'),
 (r'^uip (maestro )?case\b','Case Management'),(r'^uip is\b','Integration Service'),
 (r'^uip (agent|codedagent)\b','Low & Code Agents'),(r'^uip ixp\b','IXP'),
 (r'^uip rpa(-uia)?\b','RPA / Studio / CV'),(r'^uip (df|entities)\b','Data Fabric'),
 (r'^uip api-workflow\b','API Workflow'),(r'^uip codedapp\b','Coded Apps'),
 (r'^uip (or|orchestrator|resource)\b','Orchestrator'),(r'^uip context-grounding\b','ECS'),
 (r'^uip tm\b','Test Manager'),(r'^uip solution\b','Solutions'),(r'^uip (gov|governance)\b','Governance'),
 (r'^uip platform\b','Licensing'),(r'^uip traces\b','LLMOPS/Traces'),(r'^uip functions\b','Serverless'),
 (r'^uip llm-configuration\b','LLM GW'),(r'^uip admin\b','Identity & Auth Z'),(r'^uip tasks\b','Action Center Tasks')]
def norm(p):
    p = p.replace('\\\\','\\').replace('(?s)','')
    p = re.sub(r'\(\?[=!][^)]*\)','',p); p = re.sub(r'\\s[+*]',' ',p)
    p = re.sub(r'\(\?:?\s*maestro\s*\)\?','maestro ',p)
    p = p.replace('(?:maestro )?','maestro ').replace('(maestro )?','maestro ')
    p = re.sub(r'\(uip\|[^)]*UIP[^)]*\)','uip',p)
    p = p.replace('\\$UIP','uip').replace('${UIP}','uip').replace('$UIP','uip').replace('\\','')
    return re.sub(r'\s+',' ',p).strip()
pat = re.compile(r'command_pattern:\s*(.+)')
prod = defaultdict(set)
for f in glob.glob('tests/tasks/**/*.yaml', recursive=True):
    if '/_shared/' in f: continue
    for ln in open(f):
        m = pat.search(ln)
        if not m: continue
        n = norm(m.group(1).strip().strip('"').strip("'"))
        if not n.startswith('uip'): continue
        for rx,lab in RULES:
            if re.search(rx,n): prod[lab].add(f)
for lab in sorted(prod): print(lab, len(prod[lab]))
```

Exclude the generic `uip … --output json` sentinel pattern (unattributable). Note `uip hitl`/`uip api-workflow`/`uip codedapp`/`uip context-grounding` often resolve to 0 — those products are exercised via flow/solution commands, not their own verb; prefer the dedicated-dir count from Phase 3 for those rows.

## Edge cases & failure modes (quick reference)

| Situation | Handling | Phase |
|---|---|---|
| `run.json` missing / not JSON | Stop, report; don't scrape `experiment.md` for per-skill numbers | 1 |
| `task_results` empty (run incomplete) | Stop, report | 1 |
| Multiple variants in run | Score one (`--variant`/`default`/first); print which | 1 |
| `tasks_run` = 0 | Guarded — headline shows 0%, no divide-by-zero | 1 |
| `task_path` outside `tests/tasks/<skill>/` | Listed as UNMAPPED, not folded into a skill | 1 |
| Skill has no `mode:` tags | Overall-mean fallback in all 3 eval columns, `*` footnote | 1 |
| Skill has SOME but not all modes tagged | Per-column fallback: tagged columns use real mean, untagged columns get `mean*` (never blank) | 1 |
| `mode:troubleshoot` vs `mode:diagnose` | Merged into Troubleshoot column | 1 |
| `mode:inspect` / `mode:edit-validate` / any value ∉ {build,operate,diagnose,troubleshoot} | No scorecard column; surfaced via `NON-SCORECARD-MODES`, noted with score+`(n=)`, never dropped/folded | 1 |
| Skipped tasks (`skip: true`) | Denominator = run tasks; authored = run + skipped (this snapshot), not current dir count; note authored vs run | 1 |
| Run task counts differ from current repo | Expected (run is a snapshot); note divergence, don't reconcile to dir counts | 1 |
| `tests/reports/coverage.json` present | Prefer it over scraping `SUMMARY.md` (stable contract; gives top_untested + contributions too) | 2 |
| `SUMMARY.md` has multiple `\| uipath- \|` tables | Only when no `coverage.json`: parse the `## Overview` table only (header has `Overall`); naive parse double-counts | 2 |
| Coverage cell has `~` / `(planned)` decoration | Strip bold only; keep `~` and `(planned)` verbatim | 2 |
| `tests/reports/` missing | Run `/test-coverage all` first (it creates the folder) | 2 |
| Coverage stale vs run date | Warn; offer regenerate | 2 |
| Skill in run, absent from coverage | Coverage `—` (not `0%`); warn | 2 |
| Skill in coverage, absent from run | Eval/pass `—`/`not in run` | 2 |
| Org scorecard adds/removes a product row | Reconcile vs embedded map; emit/flag, don't drop | 3 |
| New skill folder maps to no product row | Surface in Source Data; tell user | 3 |
| `uipath-platform` sub-product eval/pass-fail | Split from the run's `psub` breakdown by default (orchestrator+resources summed); coverage stays platform-wide unless `uipath-platform.md` splits it | 3 |
| Parent page 404 (weekly rotation) | Fallback: newest `Coding Agents Scorecard*` in CA | 5 |
| Page with same title already exists | Ask: update (default) / new-with-suffix / abort | 5 |
| `createConfluencePage` rejects HTML | Fix ADF nesting and retry; don't downgrade to markdown | 5 |
| Body rendered but table/panels mangled | Round-trip verify (re-fetch, assert row/col counts); `updateConfluencePage` to fix | 5 |
| "Passing" verdict rests on < 3 tasks | Mark the `(n=…)`; a 1/1 pass is not evidence — not "Healthy" | 4 |
| Success-rate ≥ `--target` | Say so plainly in the gap-to-target panel; still list any below-bar products | 4 |
| Atlassian tools / CA space unavailable | Stop, report; never publish elsewhere | 5 |

## Anti-patterns

- **Don't invent eval scores.** If a column has no `mode:` tasks, use the overall-mean fallback with `*`; never fabricate a per-mode split that the tags don't support.
- **Don't leave a mode column blank just because some other mode is tagged.** Fallback is per column — a build-only skill still gets `mean*` for Operate/Troubleshoot, not `—`.
- **Don't fold non-scorecard mode values into Troubleshoot** (or any column). `inspect`/`edit-validate`/etc. are surfaced in notes only.
- **Don't overwrite the org scorecard.** Always `createConfluencePage` under it; never `updateConfluencePage` on the parent.
- **Don't split `uipath-platform` coverage** unless `tests/reports/uipath-platform.md` provides per-sub-dir values — but DO split its eval/pass-fail from the run's `psub` breakdown (that data is always present in `task_path`).
- **Don't double-count coverage from `SUMMARY.md`'s second table.** Parse the `## Overview` table only.
- **Don't mix snapshots silently.** If the coverage source and run dates diverge, surface it in the warning panel and to the user.
- **Don't double-count variants.** Score exactly one variant; an A/B run has N task_results per task.
- **Don't create duplicate pages.** Same-title page exists → update it (default) or suffix the new one; never leave two identical-title pages.
- **Don't force unmapped skills into a product row.** Aux/connector skills with no product row belong only in the Source Data table.
