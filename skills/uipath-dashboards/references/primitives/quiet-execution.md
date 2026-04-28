# quiet-execution

## Purpose
Hide low-level file edits, npm output, and tooling noise from non-developer users during the Generate phase of Build mode. The user sees high-level milestones and a final ready-to-use dashboard — not 50 file edits, not `npm install` chatter, not type errors fixed mid-flight.

User feedback verbatim: *"I got a feedback currently claude code shows too many file edits etc, can we hide that part somehow and only show the high level summaries which are informative."*

## When to apply
**Everything between approval-receipt and summary-emit.** That includes PAT-write, mkdir, scaffold-templates render, npm install, shadcn init/add, manifest introspection, widget generation, route registration, and all validation. Plan and Preview are conversational; they SHOULD be visible. Build itself MUST NOT be.

## Mechanics

### One Task call covers everything (the strict rule)

After the user replies "approved, my PAT is rt_…", the main agent does **exactly two things**:
1. Print one progress line: `⚙ Building your dashboard…  (this usually takes 2–4 minutes; longer for the first build in a fresh workspace)`
2. Issue **a single Task tool call** that performs the entire Build pipeline.

Then it waits for the Task to return and emits the friendly summary (per the "Two messages" section below). **No Read, Write, Bash, Edit, or other tool calls in the main agent in between.** Not even to write `.env.local` with the PAT. Not even to `mkdir` the project directory. The subagent's first action is to write the PAT; the main agent never touches the filesystem during build.

Why so strict: the user's harness may have hooks (`.remember/`, telemetry, security audit) that fire on every tool call and surface output in the visible chat. Each main-agent tool call → one round of hook noise. The user's screenshot of a build session showed a `Bash mkdir`, two `Write`s, and a `Read` happening in the main agent — each one triggered a `PostToolUse:* hook error` line. The cure isn't fixing the user's hooks; it's not making those tool calls in the main agent.

The Task subagent receives:
- The approved plan (widget list with descriptions, time windows, sources).
- The PAT verbatim (so the subagent can write `.env.local`).
- `auth-context` output (env / orgName / tenantName).
- The resolved project path: `<cwd>/.uipath-dashboards/<app.name>/`.
- The skill's reference paths so it can read primitives + templates as needed.

The subagent does ALL the heavy lifting, but maximizes parallelism to keep wall-clock low:
- **Boot:** read all required reference files in ONE message with parallel Reads (saves ~21s vs serial)
- **Scaffold:** ONE bash call to `assets/scripts/scaffold-project.sh` handles mkdir + .env.local + state.json + template rendering + npm install + shadcn init/add + restore + sanity checks (saves ~60-90s vs ~30 individual Write+Bash calls)
- **Widget generation:** for each widget, write its 4 files (widget tsx, view tsx, hook, list hook) in ONE message with parallel Writes (saves ~100s across 12 widgets vs serial)
- Type-check, API-existence-check, smoke-check
- Self-heal validation failures
- Boot dev server
- Return ONE structured result with **evidence, not assertions** (see § "Evidence-based subagent reporting")

These three batching rules — boot-time parallel reads, single-shot scaffold script, per-widget parallel writes — together cut subagent wall-clock by ~50% on first build. They're documented in detail in [../plugins/build/impl.md § Subagent throughput discipline](../plugins/build/impl.md).

The user sees ONE conversational line going in and ONE rich summary coming out. Tool-call hook events fire inside the subagent's context — invisible in the user's main view.

### Anti-pattern that triggered this rule

What NOT to do (real example from a dogfood session):

```
User: "lgtm, my PAT rt_..."

Main agent (bad):  "Approved. Writing PAT, scaffolding, then delegating
                    generation to a subagent for quiet execution."
Main agent calls:  Read 3 files            ← user sees these
                   Bash mkdir -p ...        ← user sees this; .remember hook fires
                   Write .env.local         ← user sees this; .remember hook fires
                   Write state.json         ← user sees this; .remember hook fires
                   Task("generate widgets") ← finally delegates, but the noise damage is done
```

What TO do:

```
User: "lgtm, my PAT rt_..."

Main agent: "⚙ Building your dashboard…  (this usually takes 2–4 minutes)"
Main agent calls:  Task({
  description: "Build dashboard end-to-end",
  prompt: "Plan: <approved plan json>. PAT: rt_... .
           Project path: <resolved>. Auth context: <...>.
           Run the full Build pipeline per skills/uipath-dashboards/
           references/plugins/build/impl.md from PAT-write through
           dev-server-boot. Return {port, widgets, errors?, ready}.",
  subagent_type: "general-purpose"
})
[subagent runs invisibly for 2-4 min; main agent waits]

Main agent emits the friendly summary (per "Two messages" below) using
the Task return value.
```

The "delegating generation to a subagent" announcement in the bad case was technically true but operationally wrong — generation was a small fraction of the noise. Everything after approval is delegated.

### Two messages: brief progress while building, friendly summary when done

**During build** — minimal one-line progress so the user knows something is happening. Don't list every milestone (project scaffolded, SDK introspected, type-check passed, etc.) — that's developer-voice; collapse to a single rolling line:

```
⚙ Building your dashboard…  (this usually takes 2–4 minutes; longer for the first build in a fresh workspace)
```

If a step blocks long enough that the user might wonder, refine the line ("validating widgets…", "starting dev server…"). Avoid the milestone-checklist pattern — it reads like a build log.

**When done** — a friendly summary that describes WHAT the dashboard does and HOW to navigate it, NOT what was generated. Use the approved plan as the source: each widget has a name, a one-sentence description, and a time window — all of that becomes prose.

Template (substitute `{{title}}`, `{{port}}`, and the per-widget content from the approved plan):

```
✨ Your {{title}} dashboard is ready: http://localhost:{{port}}/

It tracks {{one-sentence purpose, lifted verbatim from the plan's description line}}.

Here's what you'll see:

{{For each KPI widget — render a one-liner:}}
  • {{Widget title}} — {{plain-language what-it-shows}} ({{time window}})
{{...}}

{{For each chart widget:}}
  • {{Widget title}} — {{plain-language what-it-shows}}, hour-by-hour / day-by-day / etc.
{{...}}

{{For each table widget:}}
  • {{Widget title}} — {{plain-language what-it-shows}}, sortable.

How to use it:
  • Click any tile or table row to drill into the underlying records.
  • Use the moon/sun icon top-right to switch between light and dark.
  • Refresh the browser to pull the latest data from your tenant.
  • Press Ctrl+C in the terminal when you're done previewing.

When you're ready to publish this to your tenant, just say "deploy this dashboard."
```

The summary is generated, not templated word-for-word. The tone is conversational — "It tracks how your agents are running today", not "It contains 4 KPI widgets, 2 chart widgets, 1 table widget." Talk about the data, not the components.

**Worked example for an agent-health dashboard:**

```
✨ Your Agent Health dashboard is ready: http://localhost:5176/

It tracks agent invocation volume, error rates, and performance over the
last day and week.

Here's what you'll see:

  • Active Agents — how many distinct agents ran a job in the last 24 hours
  • Invocations Today — total agent invocations since midnight
  • Avg Response Time — average time from start to finish across agent jobs
  • Error Rate — share of agent jobs that ended in a faulted/stopped state
  • Invocation Volume — hourly bar chart of agent calls over the last 24 hours
  • Error Rate Trend — daily error rate across the past 7 days
  • Top Agents — your busiest agents, ranked by invocations, with errors and average latency

How to use it:
  • Click any tile or row to drill into the underlying jobs.
  • Use the moon/sun icon top-right to switch between light and dark.
  • Refresh the browser to pull the latest data from your tenant.
  • Press Ctrl+C in the terminal when you're done previewing.

When you're ready to publish this to your tenant, just say "deploy this dashboard."
```

Nothing about scaffolding, SDK introspection, type-check, or API verification appears in the user's view. Those happen — and they MUST pass — but they're internal mechanics. The user sees what they HAVE, not what we DID.

### Forbidden in user-visible output during Generate
- File paths (`src/dashboard/widgets/ActiveAgentsKPI.tsx`)
- Package names (`@uipath/uipath-typescript@1.2.1`, `recharts`, `react-router-dom`)
- Tool-call previews (`Calling Read on...`, `Calling Bash with npm install...`)
- Type errors verbatim
- npm install output
- Vite dev-server warnings (chunk size etc.) — these go to a `BUILD_NOTES.md` file in `.uipath-dashboards/` for the curious dev-mode user

### Permitted in user-visible output
- Widget names from the plan ("Active Agents", "Invocation Volume", ...)
- Time estimates ("~2–4 minutes" — honest range, not a hopeful "~30 seconds")
- High-level state ("validating", "starting dev server")
- The final URL
- Friendly translations of validation failures (per `validation.md`)
- Recovery offers when something failed

## Evidence-based subagent reporting

Subagents that produce confident-sounding self-summaries ("dark mode wired", "type-check passed", "server boots") are unverifiable from the main agent's view, and assertions can mask wrong diagnoses or silent no-ops. The Quiet Execution rule (Rule 17) makes this worse by design — the main agent has zero visibility into intermediate state.

**Subagents must return EVIDENCE the main agent can verify, not assertions.** The structured result shape:

```json
{
  "ready": true,
  "port": 5176,
  "widgets": ["ActiveAgentsKPI", "InvocationVolume24h", "ErrorRateTrend7d", "TopAgentsTable"],
  "evidence": {
    "tsCheck": {
      "exitCode": 0,
      "stderrFirst200": ""
    },
    "viteBoot": {
      "port": 5176,
      "stdoutFirst5Lines": [
        "VITE v5.4.8  ready in 412 ms",
        "",
        "  ➜  Local:   http://localhost:5176/",
        "  ➜  Network: use --host to expose",
        "  ➜  press h + enter to show help"
      ]
    },
    "themeWired": {
      "indexCssHas": "--primary: 14 96% 53%",
      "indexHtmlHasFontLink": true,
      "bodyClassIsLight": true
    },
    "stateBadgeApplied": {
      "detailViewsReferencingStateBadge": ["InvocationVolumeView.tsx"],
      "detailViewsMissingStateBadge": []
    }
  },
  "errors": []
}
```

Each `evidence.*` field contains a fact the main agent (or a future reviewer) can verify by re-reading the file or running the same probe. Never let a subagent return only `{ready: true}` — that's an assertion, not evidence.

### Probes the subagent runs

| Claim | Probe | Evidence captured |
|---|---|---|
| Type check passed | `npx tsc --noEmit; echo "exit=$?"` | `exitCode`, first 200 chars of stderr |
| Server boots | `npm run dev &` then read first 5 stdout lines | `port`, those 5 lines verbatim |
| Theme correctly wired | grep `index.css` for the UiPath orange HSL value; read `index.html` for Poppins link and `<body class="light">` | the matched strings |
| State badges applied to detail views | grep every `dashboard/views/*View.tsx` for `<StateBadge`; cross-check against per-view column keys for `state`/`status`/`priority`/`severity` | list of files matching, list of files missing |
| Each widget routes to a real view | grep `App.tsx` for `<Route path="/<kebab>"` for every widget in the plan | per-widget pass/fail |

Probes are cheap (single bash commands or grep calls). The cost is offset by drastically reduced false-success reporting.

### Main agent's responsibility

When the Task subagent returns:
1. **Skim the `evidence` block** before accepting `ready: true`.
2. If `tsCheck.exitCode != 0`, treat as failed regardless of `ready`.
3. If `viteBoot.stdoutFirst5Lines` doesn't include a `Local: http://localhost:` line, treat as failed.
4. If `themeWired.indexCssHas` is missing the UiPath HSL string, halt with the friendly recovery prompt.
5. If `stateBadgeApplied.detailViewsMissingStateBadge` is non-empty, surface as a soft warning ("Some detail views render state as plain text — accept anyway?").

Evidence is cheap to produce, cheap to verify, expensive to fabricate. Asking subagents to produce it raises the floor on first-build correctness.

## Falling back when subagent isn't available

If the harness doesn't support subagent dispatch:
1. Set Claude Code's tool-output verbosity to "summary" mode for the Generate phase.
2. Wrap each cluster of related file writes (e.g., "all 4 KPI widgets") into a single high-level milestone log.
3. Suppress raw stderr; route through `validation.md`'s friendly-message translator.

## Anti-patterns

- **Showing every file write to the user.** Banned. They asked for a dashboard, not a tour of the codebase.
- **"Created src/dashboard/widgets/ActiveAgentsKPI.tsx (43 lines)".** Replace with: ✓ Active Agents widget done.
- **Letting npm output through.** It's noisy and uninformative. One line: ✓ dependencies installed.
- **Surfacing tsc errors directly.** They go through `validation.md` first.
- **Treating advanced users the same.** A user who uses the words "look at the code" or "show me what you wrote" can get the dev-mode view — but the default is quiet.
