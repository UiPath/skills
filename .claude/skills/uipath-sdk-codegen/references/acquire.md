# Acquiring semantics we haven't captured

The semantics file starts incomplete and goes stale on its own. This is the loop that
fills it:

```
semantics-gaps.mjs  →  probe / mine docs / interview  →  semantics-update.mjs  →  emit-sdk.mjs
```

## The escalation ladder — never skip a rung

**1. PROBE** — an artifact can decide it. Always try this first.
**2. DOCS** — a document states it. Still needs a probe before it counts as `confirmed`.
**3. INTERVIEW** — only intent, policy, scope, roadmap. Things no artifact carries.

**Never interview for something probeable.** A human recalling platform behaviour
produced this repo's two worst wrong answers; both were confident, agreed with by a
second party, and false. A person's memory of an enum is a hypothesis, not evidence.

## 1. Probe

`node scripts/semantics-gaps.mjs --probe-plan` lists every unprobed (rule, slot) cell and
every schema member with no semantics entry. Work the list with the recipe in
`references/verify.md`, then record each result:

```bash
node scripts/semantics-update.mjs --cell "adhoc@stage-exit" --legal true \
  --verdict "Status: Valid"
```

The tool **refuses** a cell with no `--verdict`. That refusal is deliberate: only
verdict-backed cells may become hard errors in `check.ts`.

For `legal:false` against a *semantic* verdict it **requires `--class`**, because the
verdict text alone is ambiguous and both readings occur:

| verdict | class | meaning |
| --- | --- | --- |
| `has no SLA selected` | `payload-incomplete` | rule IS legal here; the probe omitted a field |
| `task selection missing` | `illegal-in-slot` | rule is genuinely illegal here — re-probed **with** `tasks` supplied and still rejected |
| `Invalid input` / `Invalid option` | `unrecognised` *or* `illegal-in-slot` | check rank 3: if it is in `VALID_RULE_TYPES`, the slot rejected it, the rule is not unknown |

Probe with a complete payload before recording `illegal-in-slot`. A short payload looks
identical to an illegal slot, and guessing there invents a false gate — one shipped in
`check.ts` on exactly that mistake and had to be removed.

There are ~60 rule×slot cells. Probing all of them is ~3 minutes of `uip` calls and it
is the single highest-value unattended job in this skill: it converts the placement
table from prose someone maintains into generated data with provenance.

## 2. Mine the docs

When a probe can't reach it, look — in this order, because it is trust order:

| source | reach for it when | caution |
| --- | --- | --- |
| `~/src/PO.Frontend/src/**` converter + zod | you need a **default** or a data shape | mainline ≠ published; check the version suffix |
| `docs/CASE_SDK_GAP_PLAN.md` | "is this a known gap, and who owns it?" | Gap statuses go stale as PRs land |
| `~/src/skills/skills/uipath-maestro-case/**` | the CLI/skill surface for the same feature | 57 KB + 67 files, older, no generator behind it — **likelier** to be stale than ours |
| `uip <cmd> --help` | flags, subcommands, payload shape | describes the CLI, not the schema |

Two rules when mining:

- **Read the version suffix before believing a declaration.** In
  `CaseManagementJsonEscalationsSchema.ts` the *wide* action enum is `…SchemaV0` (oldest)
  and the *narrow* one is `…SchemaV1`. Reading the wide enum and concluding the platform
  supports Slack escalations is exactly backwards.
- **Find the default in the converter, don't infer it.**
  `serviceType = data.serviceType || "Intsvc.SyncAgentExecution"` is a fact; "probably
  sync" is not.

A doc-sourced claim is recorded as `enumerated` at best. Promote it to `confirmed` only
after a probe.

## 3. Interview

`semantics-gaps.mjs` generates the questions, and it only generates ones no artifact can
answer. Each carries *why a human* and *what it changes* — ask a question whose answer
doesn't change the work and you have wasted the one channel that costs someone else time.

The standing questions today:

- **`version-pin-intent`** — we emit V20; the authority bundles V13; mainline is **V31**
  (0b11f5660, 2026-09-01; was V27 when this unknown was filed).
  Deliberate or inertia? If inertia, the V21→V31 diff is a list of things we currently
  cannot express, and re-pinning carries migration cost (V27 requires escalation
  `displayName`, which we don't emit).
- **`task-kind-scope`** — are any schema task types intentionally not authorable from this
  SDK (editor-internal), rather than gaps? Out-of-scope types deserve an allowlist entry
  with a reason, not permanent gap status.
- The open `knownUnknowns` — each needs a live `debug` run, currently blocked by the
  personal-robot tenant gap.

Record answers with attribution:

```bash
node scripts/semantics-update.mjs --interview version-pin-intent \
  --answer "..." --who <person>
```

Recorded as **`asserted`**, never `confirmed`, and `--who` is mandatory — an
unattributed assertion can't be re-checked with the person who made it. Answering a
`knownUnknown` attaches the answer but **leaves the question open**: a human answer is
context, not a settlement.

**Never invent an attribution.** If nobody has answered, the question stays unanswered.
Recording a plausible answer against someone's name manufactures evidence, and evidence
is the only thing this file is for.

## 4. Restamp, and know what that does and doesn't mean

```bash
node scripts/semantics-update.mjs --restamp
```

Refreshes `$provenance` from live tooling. It records **when**, not **whether** — if the
CLI or package moved, the cells may now be wrong and the probes need re-running.
`semantics-gaps.mjs` reports that drift at the top of its output.

## When to run the loop

- Before generating anything (`semantics-gaps.mjs` is Step 0's companion).
- After `npm ci` bumps `@uipath/case-schema`, or `uip` self-updates.
- When a probe contradicts a recorded cell — **the probe wins**; update the cell and note
  what changed.
- When main lands a builder feature: check whether a gap the file records is now closed.
  Two entries were superseded that way inside a single week.

## Mining the CLI repo (rank 3) — the cheapest source nobody reads

`~/src/cli/packages/case-tool/src/services/case-validate-service.ts` holds the CLI-layer
vocabulary as plain `Set`s:

```
VALID_RULE_TYPES  VALID_TASK_TYPES  VALID_NODE_TYPES  VALID_EDGE_TYPES
VALID_EXIT_CONDITION_TYPES  VALID_SLA_UNITS  VALID_ESCALATION_TRIGGER_TYPES
VALID_TRIGGER_SERVICE_TYPES
```

Reading it once corroborated three unions the published header got wrong, and corrected
a class that probing alone had produced (`timer`/`condition`/`stage-complete` are in
`VALID_RULE_TYPES`, so their `Invalid input` at task entry is a *slot* rejection).

Unlike probing, it is **git-historied**, so you can date a change instead of discovering
it:

```bash
git -C ~/src/cli log --oneline -S'"sla-status-change"' -- packages/case-tool
git -C ~/src/cli log --oneline -S'"external-workflow"' -- packages/case-tool
git -C ~/src/cli log --oneline --grep='migrate case schema'   # e.g. V19 -> V20
```

Two cautions:

- **A source checkout is not the installed tool.** Check
  `node -p "require('./packages/case-tool/package.json').version"` against
  `uip --version` — and note the launcher and the validating tool version
  *independently* (`uip` 1.202.0 vs `maestro-tool` 1.198.0, 2026-09-01).
- **The CLI layer is not the whole validator.** `case-tool` has never contained
  `sla-status-change`, yet `uip` accepts it — the message comes from the case-schema
  bundled inside `maestro-tool/dist/tool.js`. Absence from rank 3 does not mean absence
  from the platform; check rank 2 before concluding anything.
