---
name: run-dogfood-fixes
description: "Lead the fixes for a batch of dogfooding findings on any product: trace each finding to the layer that produces it, fan out one fix session per root cause, and accept a fix only with before/after evidence from the product where the user hit it — running the changed build, on the same path, checked against the product's own engine. Use when handed a dogfooding issue log or batch of field findings to fix. One bug with an obvious cause→fix it directly."
---

# Run Dogfood Fixes

Findings are symptoms a real user saw in a real product. Turn each into a merged fix that is proven in that product, not believed. You lead: triage, brief, verify evidence, unblock, report. Sessions write the fixes. Treat every claim — yours, a session's, a reviewer's — as unverified until evidence shows it.

## Critical Rules

1. **No fix without a reproduced failure.** Reproduce on the unchanged baseline, in the product where it was found, with the user's verbatim input. If it won't reproduce, the finding isn't understood yet — investigate, don't fix a guess.
2. **Prove the thing under test is the thing running — before every run.** Use an observable signature from inside the running instance (bundle hash, version, text it quotes back). A file on disk, a served-file hash, or a session saying "restarted" is a claim. Output quoting pre-change text means stale; every run since the last proof is void.
3. **Fix the class, not the instance.** State the cause as a behavior that would also fail on inputs nobody reported. No special cases for the reported domain or example.
4. **Smallest change that removes the cause.** Prefer deleting a wrong instruction or duplicate over adding a counter-instruction. State rules, never predicted counts or outputs — derived facts rot. A guard test heavier than its fix gets trimmed to the smallest assertion that catches the regression.
5. **The product is the source of truth.** When a tool disagrees with the product, find whether it calls the product's own engine or keeps a local copy. Fix the source or bump the pin; don't extend the copy. Name what stops the next drift. Before building anything, ask whether it already exists.
6. **Never shorten the path to green.** Don't reword a test prompt, loosen a grader, add a suppression, skip a step, or dismiss a product question to make a run pass. A red you understand beats a green you don't.
7. **Read state from the system that owns it, at the time you report it** — PRs and CI from `gh` and logs, results from the artifact, progress from the transcript. Never from memory, a summary, or a watcher's last line.
8. **Approval does not travel.** Destructive or outward actions (delete, merge, bypass, post, sign-in) need the user's words in the session that acts. Never relay approval; never ask a peer to do what your permissions blocked — give the user the exact command instead.
9. **Evidence outlives the resources that produced it.** Log each test resource when created; copy cited evidence somewhere durable before deleting anything. Nothing important lives only in temp folders.

## Phase 1 — Triage

1. Read the whole log, including free-text notes — they often explain other rows. Capture per finding: verbatim input, what the user saw, environment (surface, model/variant, build), artifacts.
2. **Group by root cause, not symptom.** One cause, one fix; one finding with two causes gets split.
3. Assign the **producing layer** with evidence — instructions/content, tooling, library, product engine, environment — and spot-check each claim on the default branch (file:line) before assigning. Mark "unknown" rather than guess.
4. Treat the reporter's scope ("only on X") as a hypothesis to measure.
5. Findings another team owns get a repro and a handoff, not a workaround in your layer. Findings with no repro get a triage-only pass or are deferred, said in one line.
6. Show the user the grouping and owner map before launching anything.

## Phase 2 — Locate the Producer

Answer in order; stop when evidence names the producer.

1. **Who emits the exact text?** Search the literal error, warning, field or output string across every layer's source. The emitter is where the decision lives.
2. **Is it a copy?** If it reimplements something the product owns (validation, schema, allowlist, defaults, layout), diff against the product's current source and latest published package. Version lag is a cause in itself.
3. **Why does it exist?** `git log -S '<string>'` and blame. A rule that looks wrong may encode a past fix.
4. **What did the agent actually have in front of it?** Reconstruct the instructions loaded at the moment of the mistake. Missing, contradictory, ambiguous, unreachable, or outweighed by a stronger cue are different causes with different fixes. Include context the environment supplies (knowledge bases, memory, templates).
5. **Which path did it take?** Find the branch of behavior where the bug lives; the repro must go through it.
6. **Competing hypotheses.** Write two or three explanations; run the test that rules one out, not the one that confirms your favorite.
7. **Shrink and bisect.** Cut to the smallest input that still fails; bisect versions or commits to find when it started.
8. **Where else does this class occur?** Grep siblings, references, templates, tests. Fix all in scope or list what you leave.
9. **Does it collide with open work?** Check open PRs touching the same rule or file.

## Phase 3 — Fan Out

1. One session per root cause, each in its own worktree. Start them early — a message to a busy session waits until its turn ends.
2. **Brief the problem, not your fix** — a session handed a hypothesis tends to confirm it. Include the finding, verbatim input, baseline evidence, owning layer, the Critical Rules, Phase 4, and done = PR with evidence, zero-finding review, green CI, resources logged.
3. Keep one durable shared notes folder (environment facts, briefs, findings). User corrections mid-round go to every session and into the briefs, so late starters get them.
4. **One owner per shared file.** Other PRs carry an identical copy and re-sync after each owner change; comments on the copy go to the owner.
5. **Shared environments get a lock** with owner, start time and expiry, and a queue; the releaser restores the baseline, verifies it, and pings the next. Watch for idle holders.
6. **Keep orchestration state in a file** (sessions, PRs, locks, pending checks), not in context or timers — compaction, usage caps and session exits erase both.
7. Check in with short reads (status, last few events), never full transcripts.

## Phase 4 — Validate

Decide the pass criteria **before** running. Record evidence for every step in the PR. The [Validation Toolkit](#validation-toolkit) says how to run each step on our systems.

1. **Baseline red, measured.** User's verbatim input on the unchanged build, in the product. Diff the shipped build against the branch base before claiming "reproduces on main". Record the rate per variant (model, persona, mode, path) — one run is an anecdote. If stock runs come out clean, say so: a failing offline test becomes the reproducible "before", and ask the user for the input that showed it — or defer the finding (Phase 1 step 5).
2. **Prove the build** (Rule 2), before every run — Toolkit A.3, D.2.
3. **Same input, same answers.** When the product asks a question, answer as a real user would, identically before and after. Dismissing or reshaping a question changes the path.
4. **Same path.** Read the run's actions and internals (traces, logs, state), not just the end state. A run that took another route is void, even if it looks fixed.
5. **Generalize.** New natural inputs in other domains, written like a real user — never a spec that pre-designs the answer — across every variant axis the fix is sensitive to, with n>1 on nondeterministic surfaces.
6. **Negative controls.** A case where behavior must *not* change still doesn't; a grader rejects a known-bad output. A check that passes everything proves nothing.
7. **Judge with the product's own eyes.** Run the artifact through the product's own engine at its latest version; open it in the product's editor or viewer; take screenshots there. Does it open, render, run? Warnings the product shows users are defects. Toolkit A.5, B, C.
8. **Parity and regression.** Check other surfaces running the same instructions or tool. Add a test that is red on baseline and green on the fix, grading side effects, never self-report. Toolkit D, E.
9. **Evidence must cover the head.** A later commit that changes what the agent reads makes the after-run stale; a main merge keeps it only if the PR's own files are byte-identical (show the diff).

## Validation Toolkit

How to run each Phase 4 check against UiPath products. Use every method the finding touches — each catches what the others miss. Placeholders: `<PROFILE>` = the `uip` login profile for the test org/tenant; `<AUTOPILOT>` = local Autopilot checkout serving Studio Web.

### A. Autopilot in Studio Web (where most findings come from)

1. Take the shared lock. Build: `npm run skills:build`; copy `build/skills/studioweb/` over the Studio Web skills package inside `<AUTOPILOT>`'s plugin (`autopilot-plugin-studioweb/node_modules/@uipath/skills-studioweb/skills`); rebuild the plugin.
2. **Restart the Autopilot dev watchers.** The iframe bakes the plugin release at startup; swapping files without a restart runs stock.
3. **Prove inside the iframe**: the bundled plugin release (`getBundledPluginReleases()` in the iframe console) equals `sha256(dist/index.json)`. A file hash on the dev server is not proof. Record both in the PR.
4. Drive Studio Web with browser automation (built-in browser, or the debug Chrome over CDP): new chat, verbatim prompt, answer every question as a user would, same answers before and after. Save the full chat transcript to the shared notes folder.
5. Open the resulting solution on the **Studio Web canvas**: does it render, do properties and expression editors open as intended, does debug run? Screenshots come from the canvas only.
6. Restore stock, restart watchers, verify the restore, release the lock.

### B. Studio Web without Autopilot

1. `uip solution upload <SOLUTION_DIR> --profile <PROFILE> --output json`; open the returned designer URL. Check the canvas, panels and validation badges a user sees.
2. Run it: `uip maestro bpmn debug <PROJECT_DIR> --profile <PROFILE> --output json`, then inspect `instances`, `incidents` and variables. Build success with a runtime failure is a failure.
3. **Manual canvas ground truth.** When unsure what the product writes for a construct, build it by hand on the canvas, then `uip solution download <SOLUTION_ID> --extract --profile <PROFILE>` and diff that file against the agent's output. The frontend's own serialization beats any doc or reading of the schema.

### C. Frontend and engine as source of truth

1. **Contract questions** (what a valid file looks like, variable scoping, mappings): read PO.Frontend at `origin/develop` — fetch first, never a stale tree. **Runtime questions**: PO.BpmnEngine. Never cite the CLI's behavior as proof of what's correct.
2. **Run the canvas's own validator.** Studio Web's rules ship as `@uipath/maestro-validation`; call `validateBpmnXml` (from its `/xml` entry) from node on the artifact, at the latest published version (`npm view @uipath/maestro-validation version`). `uip maestro bpmn validate` should match it exactly; when it doesn't, the CLI is the bug.
3. Check every pin the CLI holds on frontend packages against npm latest — lag is a cause.

### D. Terminal agent parity

1. Copy the built skill to `~/.claude/skills/<SKILL_NAME>` (back up first) and run the same turns in fresh Claude Code subagents across models.
2. Tell workers to invoke the skill by its exact **unprefixed** name — the plugin-prefixed copy keeps serving cached content all session. Verify each run from the "Base directory for this skill" line in its transcript.

### E. Automated tests (coder-eval)

1. Add or extend a task under `tests/tasks/<SKILL_NAME>/` that fails on baseline and passes on the fix; grade side effects, never self-report. Follow [tests/README.md](../../../tests/README.md).
2. Local runs: only tasks needing no live tenant, from the worktree's `tests/` with `SKILLS_REPO_PATH=<WORKTREE>`, default experiment.
3. Anything against a live tenant (e2e): push and dispatch `gh workflow run run-coder-eval.yml --ref <BRANCH> -f task_globs=<GLOB>`; read results from the CI run. Never run e2e locally.
4. Give each grader a negative control: run it on a known-bad fixture and see it fail.

### F. Environment rules for every method

- `--profile <PROFILE>` on every `uip` command; confirm org and tenant with `uip login status --profile <PROFILE> --output json` before uploads and deletes.
- Never sign in or switch tenant in a browser; ask the user, naming org and tenant.
- Log every solution you create (Phase 6). Missing ids are in the designer URL: `?solutionId=<SOLUTION_ID>`.

## Phase 5 — Review, CI, Merge

1. **Adversarial review to zero.** Fresh reviewers see the diff and the evidence, not your conclusion, and validate claims against the product. Loop until a full pass finds nothing. Then one final product run on that head — not one per review round.
2. **CI once, at the end.** The lead watches CI; sessions can't be woken by it.
3. **Classify failures before acting.** Ours until shown otherwise. Noise only when the same test also fails on the default branch or in unrelated PRs, the failing code isn't touched by the change, or the run hit a time cap (no score). Rerun noise once; still red → evidence to whoever can bypass.
4. **Human comments:** fix minimally, reply in one line with the commit SHA, resolve after verifying. If the fix changes behavior, revalidate steps 3–6.
5. Merge in dependency order (shared-file owner first). After each merge, re-check every other open PR — conflicts and drift cascade.

## Phase 6 — Close Out

1. Collect every session's resource log; show the user one list split into cited-nowhere and cited-as-evidence; delete from the session where the user confirmed. Never touch unrecorded resources.
2. File follow-ups for everything out of scope: other teams' bugs with repros, drift-prevention mechanisms, side observations.
3. Report one line per PR — link, state, what it fixes — then what's unverified or blocked. Say whether "reviewed" means your loop or a human.
4. Close the loop with the reporter: does the fix match what they expected?

## Before Saying "Done"

For every claim ask: *what would I see if this were false, and did I look?*

- Was the running build proven for this run?
- Did before and after take the same path with the same answers?
- Does the fix hold on inputs and variants nobody reported?
- Did a negative control fail?
- Is the status read from the owning system just now?

## Anti-patterns

- Fixing the layer you own when another layer produced the behavior.
- Patching a local copy of product logic instead of asking why it deviates.
- Trusting "restarted" or a file hash while the app serves a cached build.
- A "fixed" run that went down a different path than the bug.
- Testing only offline when the finding came from the product.
- Writing the fix into the brief and receiving it back "confirmed".
- Accepting a session's "it works" without its evidence.
- Revalidating after every review round instead of once at the end (unless a commit changed what the agent reads — Phase 4 step 9).
- A deep investigation of one flaky run.
