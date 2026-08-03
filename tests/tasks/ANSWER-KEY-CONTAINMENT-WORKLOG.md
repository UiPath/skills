# Answer-key containment — worklog

Running record of the containment work that follows `ANSWER-KEY-LEAK-AUDIT.md`. Appended as work happens.
Newest entry last. Internal-only: nothing here belongs under `skills/**`.

Branch `docs/answer-key-leak-audit`, based on `origin/main` @ `7d4e5aa5c`, in a worktree at
`skills-leakaudit` so the feature branch in the main checkout is left alone.

Plan of record: verify the `_cache` premise first (Part 1), keep a cheat-audited baseline of the codex arm
(Part 2), hand the real fix to coder_eval as a spec (Part 3). No mock-template code changes until Part 1
returns a verdict.

---

## 2026-08-03 — Premise correction: `_cache` is not a committed leak

The audit states that `m/_cache/*.json` "escaped the seal" and that one entry "embeds an authoring
question naming the root cause and asking for the fixed version". **The first half is true, the second is
unproven and probably wrong.**

Established by reading the source and the git history:

- **No `_cache` directory is committed anywhere in the repo.** Verified four ways: `git ls-files`,
  `git ls-tree -r origin/main`, `git log --all --diff-filter=A -- '*_cache*'`, and a per-remote-ref sweep.
  All empty. Under `tests/tasks/uipath-troubleshoot/` the only `cache`-matching tracked paths are two
  scenario *names* (`classic-invoke-cache-error-7`, `mail-get-outlook-mail-cached-mode-desync`).
- Consequence: the cache-preserving `shutil.move` in `_shared/mock_src/seal.py:79-81` is **dead code on
  every committed scenario** — at seal time `CACHE_SRC.is_dir()` is always False. Also, the store-packing
  loop is `RESPONSES_DIR.glob("*.json")` (non-recursive), so `r/_cache/*.json` could never have entered
  `.store` even without the move.
- The plaintext `m/_cache/<key>.json` files seen in run artifacts are written **at runtime** by
  `_save_cache` (`_shared/mock_src/uip.py:289-302`) on each `docsai ask` passthrough miss. Since nothing
  ships, every sealed run is 100% misses, so each file is created by that run.
- Therefore its `args` field echoes **the agent's own docsai query from that same run**, which is not an
  answer-key leak. The specific getasset text the audit quoted reads like a question an agent would ask
  *after* forming a hypothesis.
- Stale documentation found along the way: `mock_src/uip.py:38-39` claims "Cache files are committed
  alongside fixtures so tests stay reproducible offline". That has never been true in git. The
  user-facing `tests/tasks/uipath-troubleshoot/CLAUDE.md` is the accurate one ("the cache is **not**
  persisted to the source").

Part 1 is dispatched to settle it empirically: for each `_cache` entry in nightly `2026-07-30_04-38-11`,
md5 the `docsai ask` invocations in that run's transcript (`args = " ".join(argv[1:])`, key =
`md5(args)[:16]` per `uip.py:272-273,361`) and check whether the cache filename matches one of them. A
single unmatched ("foreign") entry would make this a real cross-run leak and change the fix.

**Nothing implemented for this yet, deliberately.** If the verdict is "self-authored", the remaining work
is hygiene only (encode the runtime cache payload with the same seal gate as `.log`, drop the unread
`args` field, delete the dead `shutil.move`) and is worth doing on its own merits, not as a leak fix.

## 2026-08-03 — Wrong base branch caught before any edit

The feature branch in the main checkout (`fix/troubleshoot-scenario-judge-ceilings`) **deletes** main's
packer infrastructure: `_shared/mock_src/{seal,uip}.py`, `_shared/scripts/compile_mocks.py`, and both
`m/.seal.bin` / `m/.uip.bin`, replacing them with the pre-#2358 plain-source `m/seal` (6775 B) and `m/uip`
(16478 B) plus an abandoned `_hide_scripts()` runtime-bytecode design. Editing the mock template there
would have produced a change against superseded code.

Source of truth on main: `_shared/mock_src/*.py` → packed to `m/.{seal,uip}.bin` by
`_shared/scripts/compile_mocks.py`. **The sandbox executes the blob, not the `.py`.** Regeneration:

```
uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py
```

The 3.13 pin is load-bearing and verified: re-running the pack logic against main's sources reproduces
both committed blobs byte-identically under CPython 3.13.12, while 3.14.5 yields a different `.uip.bin`
(3212 vs 3208 B) because `ast.unparse` output is only stable within a minor.

**Issue worth flagging (not fixed here):** nothing in CI verifies the blobs match `mock_src/`.
`git grep -e compile_mocks -e mock_src -e mock_template origin/main -- .github` returns zero hits across
all 19 workflows. A source edit without a repack silently ships stale behaviour. A guard for this is in a
separate PR; until it merges, any `mock_src` edit must repack and commit the `.bin` diff in the same
commit.

## 2026-08-03 — Note on `#2375` (landed on main today, adjacent to audit item 5)

`7d4e5aa5c` rewrote the three IXP mocks in Python and added a second sink, `calls.jsonl`, with argv
preserved as a list — `calls.log` is kept byte-identical so the existing 47 tasks grade unchanged.

This improves the *expressiveness* of the IXP oracle but does not address the audit's concern about it:
both sinks still live in the agent's own working directory, so the file the criteria grade on remains
agent-writable and forgeable. Audit next-step #5 stands.

## 2026-08-03 — Part 2 baseline run launched (codex arm, 5 scenarios)

Purpose: with no code change to validate yet, establish on the arm we intend to trust that (a) the mock is
actually exercised and (b) nothing reads graded material — for the five scenarios that misbehaved on other
arms.

```
cd <worktree>/tests
TMP=C:\cetmp TEMP=C:\cetmp PYTHONIOENCODING=utf-8 <main-checkout>/tests/.venv/Scripts/coder-eval run \
  tasks/uipath-troubleshoot/activity-packages/cv-element-not-found/task.yaml \
  tasks/uipath-troubleshoot/activity-packages/classic-browserscope-efail/task.yaml \
  tasks/uipath-troubleshoot/activity-packages/sys-getasset-activity-silent-failure/task.yaml \
  tasks/uipath-troubleshoot/products/agents/input-schema-validation-failure/task.yaml \
  tasks/uipath-troubleshoot/activity-packages/excel-rr-file-deleted/task.yaml \
  -e experiments/default.yaml --type codex --model gpt-5.6-terra \
  --include-skipped -j 3 --run-dir runs/2026-08-03_codex-leak-baseline
```

Setup notes that cost time and are worth recording:

- **`.env` beats the shell environment.** `config.py` calls `load_dotenv(override=True)` and reads `.env`
  from the CWD, so exporting `SKILLS_REPO_PATH` inline is silently overridden. To evaluate this worktree's
  skill content the run must use a `.env` in *this* worktree's `tests/` with `SKILLS_REPO_PATH` pointed
  here. `tests/.env` is gitignored (`.gitignore:19`, `**/.env`), as is `tests/runs/` (`.gitignore:78`).
- `--type codex` is required: `tests/experiments/default.yaml` omits `agent.type` on purpose and
  coder_eval's baseline experiment supplies `claude-code`. `--model` is required too, or the
  `claude-sonnet-5` pin in that file is sent to the Codex endpoint.
- `experiments/default.yaml` is `driver: tempdir`, so this runs on the host — Docker is not installed on
  this machine, which rules out `nightly.yaml`/`smoke.yaml` locally.
- Parallelism kept at 3: at j≥4 the mock shim can lose the race and the agent reaches the live tenant,
  which would invalidate exactly the thing this run is measuring.
- Task YAMLs and skill content both come from this worktree (based on latest main), not from the feature
  branch in the main checkout — `tests/experiments/default.yaml` is byte-identical between the two, so the
  experiment is not a variable.

### First attempt was invalid — and failed in a way that looks like a skill regression

`runs/2026-08-03_codex-leak-baseline` returned **0/5, every task `FAILURE` at score 0.000**, with both
`skill_triggered` and `llm_judge` at 0.00, in 114-212 s per task instead of the usual 25-55 min. Cause, from
`task.log`:

```
[WARNING] coder_eval.agents.codex_agent: [codex] Plugin skills path did not resolve:
  '$SKILLS_REPO_PATH' → '$SKILLS_REPO_PATH' (env var likely unset); no skills linked from it
```

**`SKILLS_REPO_PATH` cannot be delivered through `.env`.** It is not a declared field on
coder_eval's `Settings` (no `skills_repo_path` in `config.py`), so the `.env` load never re-exports it to
`os.environ` — only declared settings are re-exported. The value is consumed by `os.path.expandvars` in the
agent and task-loader paths, which read the **real process environment**. So it must be passed on the
command line, exactly as the repo guidance says; putting it in `.env` looks right and does nothing. Re-ran
as `runs/2026-08-03_codex-leak-baseline-v2` with `SKILLS_REPO_PATH` inline.

**Issue worth flagging (harness, not ours):** an unresolved plugin path degrades to a *warning*, and the run
proceeds with **no skill linked at all**. The result is five well-formed `FAILURE` rows at score 0.000 with
`skill_triggered=no` — indistinguishable at the `run.json` level from "the skill is bad". Nothing marks the
run invalid. This is the same class of silent invalidity the audit found on the delegate arm (mock not on
PATH → 102 graded-but-meaningless passes), and it argues the same fix: when a declared input does not
resolve, fail the task rather than grade it. Worth adding to the coder_eval item list alongside the loud
`mock_path_dirs` change.

### Part 2 result: clean baseline, 5/5 (`runs/2026-08-03_codex-leak-baseline-v4`)

| task | status | score | agent cmds | mock records in `.log` | cheat hits |
|---|---|---|---|---|---|
| agent-input-schema-validation-failure | SUCCESS | 0.925 | 10 | 2 | 0 |
| classic-browserscope-efail | SUCCESS | 1.00 | 30 | 14 | 0 |
| cv-element-not-found | SUCCESS | 0.925 | 20 | 6 | 0 |
| excel-rr-file-deleted | SUCCESS | 0.85 | 20 | 7 | 0 |
| getasset-activity-silent-failure | SUCCESS | 1.00 | 40 | 11 | 0 |

Both required checks pass:

- **Mock served the evidence.** Every task has a non-empty `m/.log`, 2-14 decoded records
  (`coverage_report.py --dump`). No task was graded on evidence that was never served.
- **No cheating.** Sweep over all 120 commands' `parameters` and `result_summary` for `tests/tasks`,
  `RESOLUTION.md`, `/work/input`, `$TASK_DIR`, `.store`, `_cache`, `m/r/`, `b64decode`, `zlib`,
  `uip.cpython`, `.seal.bin`, `.uip.bin`, `m/seal`: **zero hits**, not even an incidental directory listing
  that prints one of those paths. One command had empty `parameters` (the known codex unknown-tool-kind gap),
  so coverage is 119/120.

Contrast with the same five scenarios on other arms: two of them (`cv-element-not-found`,
`classic-browserscope-efail`) were among the antigravity arm's leakers, one of which read `RESOLUTION.md`
explicitly "to ensure my diagnosis perfectly matches it". On this arm, with a working mock, none of the five
went looking. Consistent with the audit's conclusion that exposure is arm-independent while exploitation is
arm-specific — the motive is a broken evidence channel, not the availability of the answer key.

### Issue found: current `main` leaves the decode recipe in the sandbox

Inventory of `artifacts/<task-id>/m/` on this run (main's compressed-source-blob variant), for one task:

| file | bytes | readable? |
|---|---|---|
| `seal` | 476 | **plaintext, contains `zlib.decompress(base64.b64decode(...))`** |
| `uip` | 472 | **plaintext, same recipe** |
| `.seal.bin` | 692 | `base64(zlib(source))` — decodable with the line above |
| `.uip.bin` | 3208 | same |
| `.store` | 4956 | `base64(zlib(json))`, no key |
| `.log` | 2942 | `zlib+base64` per line |
| `_cache/*.json` | — | plaintext (2 of the 5 tasks; passthrough scenarios) |

This is **weaker than the variant the 07-30 nightly shipped**, where `seal` was truncated to 0 bytes and
`uip` was a 94-byte `exec … .pyc` stub carrying no recipe. On current main both launchers survive intact and
each one states the encoding used by the blobs and the store sitting next to them. So the "hide the
machinery" property regressed when #2358 replaced #2334's runtime-bytecode approach with committed source
blobs.

Flagging, not fixing — it is the same conclusion the audit already reached (obfuscation buys one guess per
layer, detection is what holds), and no agent in this run went near it. If it is worth closing, the cheap
version is to have `seal` blank both launchers after sealing, as #2334 did.

Follow-up asked and answered: **only `seal` can be blanked.** `uip` must stay executable for the whole run,
and any loader must name its own decode, so the recipe cannot leave a readable `uip` without returning to
#2334's version-locked `.pyc`. Blanking `seal` + deleting `.seal.bin` removes the store's *structure*
(the `{"manifest":…, "files":{name: base64(bytes)}}` shape) but leaves the two-line encoding. Must run
strictly after `rmtree`, or a crash between blob-delete and store-commit turns the `pre_run` retry into a
silent no-op that seals nothing and still exits 0. Decision: **ignore for now.**

## 2026-08-03 — Leak rate for the last codex nightly, measured uniformly

Re-swept **all 435 executed tasks** of `2026-08-03_04-43-50` (384 SUCCESS, 51 FAILURE) with one rule
instead of merging two agents' summaries. Classification: a hit counts as a READ when the graded path
appears in a command whose leading utility prints content (`cat`/`sed`/`python -c`/…) or in a `Read`/`Edit`
tool call; a `find`/`ls` that merely prints the path does not.

**5 tasks read graded material. All 5 scored SUCCESS at 1.0. Zero of the 51 failures did.**

| task | read | class |
|---|---|---|
| `skill-agent-coded-hitl-create-task-with-app` | own `check_*.py` + task YAML, then ran the grader 3x | answer key |
| `skill-functions-deploy-tenant` | own task YAML + `check_deploy_tenant.py` | answer key |
| `skill-agent-inline-is-connector-tool` | another task's golden solution under `_fixtures/` | answer key |
| `skill-agent-coded-push-resource-not-found` | `mocks/responses/manifest.json` + the shim | fixture source |
| `skill-ixp-integration-versions-and-metrics` | `mocks/calls.log` — the oracle 3 of its criteria grade on | oracle inspection |

So 3 clean answer-key leaks out of 384 passes (0.8%), or 5 counting the softer two (1.3%). All in **build
suites**; troubleshoot was 0 of 52. Note the graders outnumber reference answers 360 to 297, so the softer
target is also the larger one.

Two honest limits on that number:

- **The instrument's coverage equals its path list.** My first pass covered the troubleshoot mock layout
  (`data/m/r`) but not the agents/ixp one; adding `mocks/responses`, `mocks/uip`, `_fixtures/` found the
  fourth case. A suite inventing a fifth convention would slip through the same way — an argument for
  deriving paths from task config rather than hardcoded globs.
- **571 of 1006 tasks were `mature_skipped`** — never executed, auto-SUCCESS at 1.0. A clean verdict says
  nothing about them. Plus 5 codex tasks spawn subagents whose inner tool calls appear in no artifact.

One false positive worth recording so the next reader doesn't chase it: `skill-agent-local-escalation-tool`
tripped the decode pattern on a legitimate `uip solution resources get … --decode` flag.

## 2026-08-03 — Part 3 landed: coder_eval `feat/integrity-checks`, 10 commits, not pushed

Worktree `coder_eval-integrity`, branch off `origin/main` @ `cc2cfc78`. The original `coder_eval` checkout
was left on its own branch untouched — it backs the editable install the local test venv uses, so switching
it would silently change which harness code local runs execute.

| sha | commit |
|---|---|
| `9e2a200c` | Abort sandbox setup when a declared mock_path_dirs entry does not resolve |
| `648ba912` | Abort the task when a declared local plugin path does not resolve |
| `d78ed1bf` | Add IntegrityInfo telemetry with run.json wiring and an INTEGRITY_MODE switch |
| `6ed036a0` | Count sub-agents whose inner tool calls could not be recovered |
| `f28343d3` | Add a graded-material read detector for finished transcripts |
| `119f7d39` | Void a passing row whose transcript read graded material |
| `be671907` | Taint a run whose declared mock was never invoked |
| `23a9b818` | Document the run-integrity gate in the report schema and env example |
| `3f303f35` | Bind-mount a declared file as a file instead of its parent directory |
| `fef1e2bb` | Stop staging the raw task YAML into the container |

Tests: baseline `origin/main` = 2 failed / 3563 passed; final = 2 failed / 3738 passed, 87.22% coverage
(`integrity.py` 95.83%). The 2 failures are the same pre-existing Windows symlink-privilege tests
(`WinError 1314`) that fail on the untouched baseline. Independently verified here: `FinalStatus` still has
its original 8 members, the three `integrity_*` keys are in `eval_result_to_task_dict`, `INTEGRITY_MODE`
defaults to `DETECT`, and `pytest tests/test_integrity_scan.py tests/test_integrity_gate.py` = **132
passed**. A real run (`INTEGRITY_MODE=void … agentless_smoke_test.yaml`) produced the `integrity` object in
`task.json` and the keys in `run.json`.

Two side effects worth knowing: `TestRowKeySet` now pins the entire `run.json` row key set (nothing did
before — the gap that would silently drop a new field), and there is a test pinning `FinalStatus` as a
closed set so the decision not to add a member is visible to the next reader.

### Deferred, with reasons

Plan commits 8-10 (ship reference *content* via `/work/input`, consume-and-unlink the input dir, mask
`reference.file` inside the task-dir mount) are **not done**. Docker is not installed on this machine and
the entire existing docker-mount suite is `skipif(win32)`, so none of it is observable here. Commit 8
changes what judge criteria can read at grading time — get it subtly wrong and every docker task with a
reference silently loses it, which is precisely the silent-invalidity class this work exists to kill.
Commit 10 depends on 8 (a relative `reference.file` is read *through* the task-dir mount). Do these on a
POSIX host with Docker.

**Consequence for scope:** troubleshoot's answer-key route (`RESOLUTION.md`) is only closed by commits 8+10,
so it remains open for now. The build-suite route (`check_*.py`, task YAMLs, `_fixtures/`) stays open by
design even after them — those files must be readable at grading time and the container runs as root — so
detection is the compensating control there. Net today: leaking is **detected and score-voiding**, not
prevented.

### Do not enable `void` yet

`INTEGRITY_MODE` ships defaulting to `detect`. The mock-never-invoked check cannot distinguish "the mock
never reached PATH" from "this scenario legitimately never needed it", and this worklog already names 4
troubleshoot tasks in the 07-30 run with no call log by construction. Run one nightly in `detect`, read the
findings, then decide.

### Behaviour change on merge

Commits 1-7 change no score **except** the two fail-closed ones: a missing mock dir or unresolved plugin
path now ends as `ERROR` instead of being graded. Some rows that currently read as `FAILURE` will become
`ERROR` — they were never valid measurements. That is the intended correction, but it will move the numbers.

### Issues flagged, not fixed

- **Agent-endpoint fail-closed needs per-agent work.** Codex resolves its endpoint via bare `os.getenv`,
  while Claude legitimately falls back to cached CLI auth, so a generic "endpoint must resolve" rule would
  break Claude. Wants a per-agent `validate_environment()` preflight — separate issue.
- `config.py`'s `load_dotenv(override=True)` with no arguments still loads nothing (confirms the diagnosis
  above). Left alone: fixing it changes how every local run reads `.env`.
- `_build_argv` is one statement under ruff's `PLR0915` limit; it wants splitting.
- ~60 docker tests skip on Windows. The new `test_docker_stage_inputs.py` demonstrates `_build_argv` /
  `_stage_inputs` are pure enough to test platform-neutrally; more existing assertions could move.

### Root cause of three discarded runs: `.env` does not reach the agent's environment

Attempts v1-v3 all produced the same result — five `FAILURE` rows at score 0.000, `skill_triggered=no`,
`llm_judge=0.000`, `actual_commands: 0`, 122-210 s per task, **and not one error line in any log**. Three
separate causes, all the same shape:

| # | Missing | Symptom | Why |
|---|---|---|---|
| v1 | `SKILLS_REPO_PATH` | `Plugin skills path did not resolve … no skills linked` (WARNING only) | not a declared `Settings` field |
| v2 | same, still | identical | `.env` cannot deliver it |
| v3 | `CODEX_BASE_URL`, `CODEX_API_KEY` | `environment_info` has **no** `codex_*` keys at all | never reached `os.environ` |

The mechanism, from `coder_eval/src/coder_eval/config.py`:

- `:38 load_dotenv(override=True)` is called **with no arguments**. python-dotenv then resolves the file with
  `find_dotenv(usecwd=False)`, which walks up from the **calling module's directory** — i.e. inside the
  coder_eval checkout — not from the CWD. There is no `.env` in the coder_eval checkout, so this call loads
  nothing.
- `:147 model_config = SettingsConfigDict(env_file=".env", …, extra="ignore")` does read `tests/.env`
  relative to the CWD, but only **declared** `Settings` fields are then re-exported to `os.environ`
  (`:203-212`). `extra="ignore"` drops everything else.
- `CODEX_BASE_URL`, `CODEX_API_KEY`, `CODEX_API_VERSION` and `SKILLS_REPO_PATH` are consumed via
  `os.getenv` / `os.path.expandvars` (`codex_agent.py:1049`, `:1313`; the skills path via `expandvars`), so
  for those the `.env` file is **inert**. They only work if exported in the shell.

This explains why an earlier local codex run on this machine succeeded: its shell had the `CODEX_*` vars
exported. `tests/.env` documents them but does not deliver them.

Confirmation of the diagnosis: `codex_agent.get_environment_info()` (`:917-935`) returns `{}` when
`_resolve_base_url()` is falsy, and the v3 `task.json` recorded no `codex_*` keys — while the known-good run
recorded `codex_api_version: 2025-04-01-preview`, `codex_wire_api: responses`,
`codex_model_is_deployment: true`. That is a clean before/after.

Working invocation (v4) exports the `CODEX_*` / `AWS_*` / `API_BACKEND` / `BEDROCK_*` block out of
`tests/.env` into the process environment first, then adds `SKILLS_REPO_PATH` and `CODEX_API_VERSION`.

**Issue worth flagging (harness):** a codex run with no endpoint configured produces zero tool calls, no
error, and five well-formed `FAILURE` rows at 0.000 with `skill_triggered=no`. Combined with the same
property for an unresolved plugin path, that is three distinct ways for a *misconfigured* local run to be
indistinguishable from *a bad skill*. This is the identical failure shape the audit found on the delegate arm
(mock not on PATH → 102 graded-but-meaningless passes). It strengthens the fail-closed item in the
coder_eval spec, and suggests widening it: when a declared input (plugin path, mock dir, agent endpoint)
does not resolve, the task should ERROR rather than be graded. Also worth considering: `CODEX_API_VERSION`
belongs in `tests/.env.example` with a note that the `CODEX_*` vars must be **exported**, not merely present
in `.env`.

## 2026-08-03 — Part 1 verdict: `_cache` is self-authored, not a leak. Claim retracted.

Swept every `m/_cache` in nightly `2026-07-30_04-38-11`: **33 cache files across 27 of 154 tasks. All 33
self-authored. Zero foreign.** Four independent confirmations per entry:

1. Filename stem `== md5(entry["args"])[:16]` for 33/33.
2. Each `args` appears in that same task's decoded `m/.log` as `error: "passthrough_live"` — the writing
   invocation — 33/33.
3. Each `args` appears in that task's transcript as an agent `uip docsai ask` command — 33/33.
4. Per-task set equality between `{passthrough_live args}` and `{cache-file args}`: 1:1 for all 27 tasks,
   no extras in either direction.

The decisive number: across all 150 `m/.log` files the run has **33 `passthrough_live` and 0
`passthrough_cached`** records. A zero cache-hit count proves no cache pre-existed the agent in any task —
every file was written in-run by `_save_cache`. Structurally it could not be otherwise: `CACHE_DIR` is
`<mock_dir>/_cache`, created at runtime, and `seal.py` only ever *moves* a pre-existing `r/_cache`, of which
none is committed.

The specific entry the audit quoted (`049ff8cb6b510fec.json`, getasset scenario) is the codex agent's own
query at command #13, and its provenance is traceable in that transcript: cmd #2 reads `project.json` (which
pins `[22.10.5]`), cmd #10 writes a candidate hypothesis naming 22.10.5, cmd #12 re-reads the playbook,
cmd #13 asks docsai to confirm the fixed version. The cached `stdout` length matches the redirect target the
agent wrote in `.local/investigations/raw/`. That task scored **0.4 / FAILURE** — it gained nothing.

Also checked, and clean: the getasset scenario has **no canned `docsai` fixture**. Its single `docsai` rule
is `passthrough: true`, and no fixture JSON in `data/m/r/` contains question or root-cause text. The one
revealing committed file there is `data/m/r/README.md` (authoring notes naming the root cause), and it is
**not** agent-reachable in the sandbox: `seal` packs only `r/*.json` into `.store` and then `rmtree`s `r/`,
so the README is deleted unpacked. It remains readable from the checkout via `tests/tasks/**` — which is
audit item 2, not this one.

### Everything readable the seal leaves behind (all 154 tasks, 07-30 run)

| file | tasks | size min/med/max | readable? |
|---|---|---|---|
| `_cache/*.json` | 33 files / 27 | 1956 / 2698 / 5582 | **plaintext JSON — the only clear text** |
| `.store` | 154 | 412 / 3954 / 15668 | opaque `base64(zlib(json))`, no key |
| `.log` | 150 | 313 / 1781 / 10340 | `zlib+base64` per line; rule/fixture *names*, no fixture bodies |
| `seal` | 154 | 0 / 0 / 0 | self-blanked (that run shipped the #2334 pyc variant) |
| `uip` | 154 | 94 | plaintext stub `exec … __pycache__/uip.cpython-313.pyc` |
| `uip.cmd` | 154 | 78 | same, Windows form |

No `r/`, no `.pyc`, no `.seal.bin` survive into artifacts. 4 tasks have no `.log` at all — the mock was
never invoked in them (`classic-invoke-cache-error-7`, `if-condition-compiler-error`,
`is-activities-prerelease-not-found`, `send-smtp-relay-denied`); worth noting as the same class of signal
the proposed fail-closed check would surface, though for these it is expected by construction.

**Consequence:** `ANSWER-KEY-LEAK-AUDIT.md` corrected — the `_cache` bullet now records the retraction. No
`mock_src` change is warranted as a leak fix. The remaining hygiene case (encode the runtime cache payload
the way `.log` already is, drop the unread `args` field, delete the dead `shutil.move`) is real but optional,
and is held pending a decision rather than folded in silently.
