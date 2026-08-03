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

Checks to run against the baseline run once it finishes, and their results, will be appended below.

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
