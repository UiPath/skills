---
name: run-dogfood-fixes
description: "Orchestrate fixes for a dogfooding session's findings across this skills repo and the CLI: trace each finding to the layer that causes it, delegate one fix per root cause, and prove every fix with before/after evidence in the real product before merging. Use when handed a dogfooding issue log or batch of field findings to fix. One known bug with an obvious cause→just fix it."
---

# Run Dogfood Fixes

Turn field findings into merged fixes that are proven, not believed. Orchestrator delegates fixes and reviews, keeps only conclusions, and treats every claim — its own, a session's, a reviewer's — as unverified until evidence shows it.

## Critical Rules

1. **Fix the class, not the instance.** State the root cause as a behavior that would also fail on prompts nobody reported. A fix that only makes the reported prompt pass is overfit — reject it.
2. **Smallest change that removes the cause.** No new sections, checklists or special cases that no repro needs. Prefer deleting a wrong instruction over adding a counter-instruction.
3. **No fix without a reproduced failure.** Reproduce on the unchanged baseline first. If it won't reproduce, the finding isn't understood yet — keep investigating, don't fix a guess.
4. **Prove the thing under test is the thing running.** Before trusting any result, show the build, version or hash actually loaded matches the change. A result from a stale or stock build is no result.
5. **Never shorten the path to green.** Don't reword a test prompt, loosen a grader, add a suppression, bypass a check, or skip a step to make something pass. A red that's understood beats a green that isn't.
6. **Own copies of upstream logic are suspect.** When a tool disagrees with the product, first find whether the tool calls the product's own engine or keeps a local copy. Fix the source of truth or the dependency pin — never patch the copy.
7. **Read primary evidence, not summaries.** Status, CI results, merge state, test output and subagent claims come from the system that owns them (`gh`, CI logs, transcripts, the product UI), read at the time of reporting.
8. **Approval doesn't travel.** Destructive or outward actions (delete, merge, bypass, post) need the user's words in the session that acts. Never relay approval; never ask a peer to do what your permissions blocked.
9. **Leave nothing behind.** Every session records the test resources it creates in the product and they're removed once no longer needed.

## Where to Look

Work from symptom to producer. For each finding, answer in order:

1. **Which layer produced the behavior?** Agent instructions (skill text), tooling (CLI command or its local logic), product engine/package, or environment (tenant, data, permissions, infra). Most wrong guesses come from fixing the layer you happen to own.
2. **Who emits the exact text?** Search for the literal error, warning, field name or output string across the skill tree, the CLI source and the product packages. The emitter is where the decision lives.
3. **Is it a copy?** If the emitter reimplements something the product owns (validation rules, schemas, allowlists, layout), compare against the product's current version before anything else. Check the pinned version against the latest published.
4. **Why does the current behavior exist?** `git log -S '<string>'` and blame the rule. A rule that looks wrong may encode a past fix; changing it reopens that bug.
5. **What did the agent actually read?** Reconstruct which instructions were loaded at the moment of the mistake — file, section, and whether it was reachable from where the agent was. Missing, contradictory, ambiguous, or too-far-away instructions are distinct causes with distinct fixes.
6. **Where else does this class occur?** Grep sibling skills, references, templates and tests for the same pattern. Fix all instances in scope, or name the ones you're leaving.
7. **Does it contradict another open change?** Check open PRs touching the same rule or file before writing.

## Validation Ladder

Each fix climbs every rung. Record the evidence for each in the PR.

1. **Baseline red.** The finding reproduces on the unchanged baseline, in the real product surface where it was found, with the original prompt and answers.
2. **Change applied, provably.** Rule 4: show the running artifact matches the change (hash, version, release id inside the running app — not a file on disk).
3. **Same-input green.** Same prompt, same answers, same model: the failure is gone.
4. **Generalization.** New prompts the fix wasn't written against — written like a real user, never a spec that pre-designs the answer — on more than one model. Include at least one prompt where the old behavior was correct, to catch regressions.
5. **Negative control.** Something that must still fail does fail (a grader still rejects a bad output; a gate still stops when it should). A check that passes everything proves nothing.
6. **Repeat count.** Nondeterministic surfaces need n>1. One pass is an anecdote; one failure is a data point, not a verdict.
7. **Adversarial review to zero.** Fresh reviewers who see the code, not your conclusion, loop until a full pass has no findings. Validate the PR's claims against the product, not against the description.
8. **CI, once, at the end.** Read which tests failed and why before rerunning anything.
9. **Final real-surface run on the merged-candidate head** if anything the agent reads changed after step 3.

### Telling real failures from noise

- Same failing test across unrelated changes, or also failing on the baseline/main branch → pre-existing; rerun once, then report it with evidence. Don't fix it inside an unrelated PR.
- Failure in code the change doesn't touch, against a shared environment → environment; get evidence that the baseline fails the same way.
- Run killed by a time cap has no score — it's neither pass nor fail.
- Anything else is yours until shown otherwise.

### Before saying "done"

Ask of every claim: *what would I see if this were false, and did I look?* If the answer is "I didn't check", it's not done — check it or label it unverified.

## Orchestration

1. **Triage by root cause, not symptom.** Several reports can share one cause; one report can hide two. One bucket per cause; name it by the behavior to change. Defer findings without a repro, in one line each.
2. **One session per bucket, one writer per file.** When changes must share a file, name one owner; others carry an identical copy and re-sync after every owner change. Merge the owner first.
3. **Every brief contains:** the raw findings (input, observed, expected); the Critical Rules; the Validation Ladder; done = PR with ladder evidence, zero-finding review, green CI, test resources logged. Briefs state the problem, not your hypothesized fix — a session handed a hypothesis tends to confirm it.
4. **Shared real-surface environment:** one run at a time behind a lock; release it when the run ends; restore the stock build afterwards.
5. **Reviewer comments:** fix each valid one with the smallest general change, reply in one line with the commit SHA, resolve after verifying. If a fix changes what the agent reads, climb ladder rungs 3–5 again.
6. **After every merge, re-check every other open PR** — conflicts and shared-file drift cascade.
7. **Watch CI in the background**, and re-read state from the source when the watcher returns; watchers exit on network errors and before reruns start.
8. **Status:** flat bullets, `[#N](url) · state`, plus one clause on what blocks it. Distinguish our own review from human approval.

## Test Resource Hygiene

1. At creation time, each session appends `<id> <purpose> — keep: <what cites it> | delete` to a shared cleanup file named for the session.
2. Collect all files before deleting; show the user one combined list; delete from the session where the user confirmed.
3. Delete only recorded ids or ones the user picked from their own list.

## Anti-patterns

- Fixing the layer you own when the cause is in another layer.
- Calling a fix verified when the running build wasn't proven to be the changed one.
- A prompt or grader edited until the task passes.
- Patching a local copy of product logic to match the product.
- Accepting a subagent's or session's "it works" without its evidence.
- Rerunning CI or the real-surface check after every review round instead of once at the end.
- A deep investigation of a single flaky run.
- Evidence kept only in temporary directories.
- Reporting merged/approved/green from memory.
