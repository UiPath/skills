# Answer-key leak audit — nightly runs, 2026-07-29 … 2026-08-03

Question: can an agent reach graded material (reference answers, fixtures, checker scripts) instead of the
evidence a scenario intends, and did that happen in tasks graded SUCCESS?

Answer: yes, on two of three arms, and it is still possible on all of them.

## What was scanned

| Run | Arm | Scope | Passing tasks scanned |
|---|---|---|---|
| 2026-07-29_23-17-31 | delegate | troubleshoot | 111 |
| 2026-07-29_04-14-45 | antigravity | troubleshoot | 155 |
| 2026-07-30_04-38-11 | codex | troubleshoot | 150 |
| 2026-07-31_04-38-51 | codex | troubleshoot | 77 |
| 2026-08-03_04-43-50 | codex | troubleshoot + all other skills | 52 + 333 |

Leak = the agent opened graded material **and** used it in its answer. Path appearing in a directory
listing does not count.

## Findings

| Arm | Leaking passes | What they read |
|---|---|---|
| antigravity (07-29) | **93 / 155 (60%)** | mock manifest (90), plaintext fixtures (13), dispatcher source (30), `RESOLUTION.md` (5), task definitions (9) |
| delegate (07-29) | **8 / 111** | decoded `m/.store` (7), `RESOLUTION.md` (1) |
| codex (07-30, 07-31, 08-03) | **4 / 612** | `check_*.py` grader + own task YAML (2), another task's golden solution (1), mock fixture JSON (1) — all in non-troubleshoot suites |

Representative quotes:

- antigravity, `cv-element-not-found`, score 1.0: *"I will search for the file `RESOLUTION.md` to see the
  reference resolution and ensure my diagnosis perfectly matches it."*
- delegate, `job-stopped-exit-code-e0434352`: *"I cracked the sealed fixture store and recovered the actual traces."*
- codex, `skill-agent-coded-hitl-create-task-with-app`, score 1.0: read its own `check_*.py`, then ran that
  grader repeatedly until it printed `OK`.

## Two separate problems

**1. Mock machinery — fixed.** PR #2313 (seal the store) + #2334 (hide the shim and call log) removed the
manifest, plaintext fixtures and readable dispatcher from the sandbox. Those files no longer exist, so the
90/13/30-task leak paths above are impossible now on any arm. Not fixed by obfuscation alone: the readable
launcher still names the encoding, and `.store` is `base64(zlib(...))` with no key.

**2. Answer key — open.** Unaffected by the seal work:

- `tests/tasks/**` (`RESOLUTION.md`, `task.yaml`, `check_*.py`) sits in the same checkout the agent
  legitimately reads the skill from, with `ignore_patterns: []`.
- `/work/input/task.yaml` and `context.json` expose the success criteria.
- `m/_cache/*.json` escaped the seal — plaintext in 27 tasks of the 07-30 run, and one entry embeds an
  authoring question naming the root cause and asking for the fixed version.
- Only troubleshoot seals anything. Other suites stage fixtures in plaintext: bpmn 54 tasks, ixp 50,
  agents 20, case 15, review 12, platform 9, flow 7, planner 6, mcp-servers 3.
- `uipath-ixp`: `mocks/calls.log` is the sole grading oracle for 3 criteria per integration task, plaintext
  and writable in the agent's own working directory. No forgery seen; nothing prevents it.

## Also worth knowing

- Nightly SUCCESS counts include `mature_skipped` tasks that never ran (571 of 1006 on 08-03). Executed
  counts are much smaller than headline pass counts.
- On the delegate arm the mock was never on PATH, so only 10 of 158 tasks ever invoked it; 102 passes were
  graded with the intended evidence never served. Those results carry no signal.
- Fixtures still emit harness-flavoured identifiers (`MOCK-HOST`, `MOCK-ROBOT-07`) that agents quote in
  final answers.

## Next steps

Harness (coder_eval):

1. Make `tests/tasks/**` and `/work/input` unreadable from the sandbox; run criteria from a path the agent
   cannot reach.
2. Taint-on-read backstop: void the score when a transcript opens graded material. Catches all four codex
   cases and both delegate classes.
3. Fail a mock-dependent task when the mock was never invoked (no call log), instead of passing it.

This repo (`tests/**`):

4. Fold `m/_cache/**` into `.store`.
5. `uipath-ixp`: move `calls.log` out of the agent-writable working directory, or stop grading on it.
6. Add a gating evidence-anchor criterion so an unanchored answer cannot clear a lone `llm_judge`.

Not worth further effort: deepening obfuscation of `.store`. Against an agent with a shell on the same
filesystem each layer buys one guess; detection is what holds.
