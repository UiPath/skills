# Answer-key leak work — handoff

Start here. Read this, then [ANSWER-KEY-LEAK-AUDIT.md](ANSWER-KEY-LEAK-AUDIT.md) (the problem) and
[ANSWER-KEY-CONTAINMENT-WORKLOG.md](ANSWER-KEY-CONTAINMENT-WORKLOG.md) (everything done, with evidence and
the mistakes corrected along the way).

## State in one paragraph

Eval agents can read the material they are graded on — reference answers (`RESOLUTION.md`), grader scripts
(`check_*.py`), task YAMLs, `_fixtures/` golden solutions, mock fixture stores — because all of it sits in
the same checkout the agent legitimately reads its skill from. Measured, this happens. A detector that
voids such runs is written and tested in coder_eval but **catches only 2 of the 5 known cases**; the
containment that would make the files unreadable is **not written**. Nothing is pushed or merged.

## Branches and where things live

| What | Where | State |
|---|---|---|
| Docs (audit, worklog, this file) | skills repo, branch `docs/answer-key-leak-audit`, worktree `skills-leakaudit` | pushed, 6 commits, docs only |
| Leak detection | coder_eval, branch `feat/leak-detection`, worktree `coder_eval-leakdet` | **current work**, 5 commits off main `b390d7dc`, not pushed, no upstream |
| Dropped delegate/fail-closed work | coder_eval, branch `feat/integrity-checks`, worktree `coder_eval-integrity` | untouched at `fef1e2bb`, keep for retrieval |
| Durable evidence copies | `investigations/answer-key-leak/` outside both repos | 2 leaking transcripts + the sweep script |

Do **not** switch branches in the primary coder_eval checkout — it backs the editable install the skills
test venv uses, so switching silently changes which harness code local eval runs execute. Use worktrees.

## What is done

**`feat/leak-detection`** (5 commits, main `b390d7dc`, full suite 6 failed / 3889 passed vs main's
6 failed / 3765 — same six failures by name, all pre-existing):

| sha | commit |
|---|---|
| `d4ef50e2` | Add IntegrityInfo telemetry with run.json wiring and an INTEGRITY_MODE switch |
| `f15e0d7c` | Count sub-agents whose inner tool calls could not be recovered |
| `2916f918` | Add a graded-material read detector for finished transcripts |
| `1024ec8a` | Void a passing row whose transcript read graded material |
| `e303ce5c` | Stop handing the scenario folder and the raw task YAML to the container |

Behaviour: after a run, `integrity.py` scans the transcript for reads of graded material; a `TAINTED`
verdict flips `SUCCESS`→`FAILURE` with `voided=True` when `INTEGRITY_MODE=void`. Ships defaulting to
`detect` (record, never flip). Verdicts: `CLEAN` / `TAINTED` / `INCONCLUSIVE` / `SKIPPED`; `INCONCLUSIVE`
never voids and is forced when sub-agent telemetry is incomplete. Results surface in `task.json`
(`integrity` object) and `run.json` (`integrity_verdict`, `integrity_voided`, `integrity_findings`).

## What is left, in priority order

### 1. Fix the detector before running any nightly (blocking)

A review reconstructed the five measured leaks and ran them through the real code. It catches
`hitl-create-task-with-app` and `functions-deploy-tenant`; it **misses** `inline-is-connector-tool`
(`_fixtures/` golden solution), `push-resource-not-found` (`mocks/responses/manifest.json`) and the
delegate `.store` decode.

- **H1 — spec derivation is incomplete.** `derive_graded_material` in `integrity.py` never consults
  `sandbox.mock_path_dirs` or `template_sources[*].mount_point`, and `_fixtures/` is not in the
  conservative globs. Add them as **path-segment** patterns (`/mocks/`, `/m/`, `/_fixtures/`), not resolved
  absolutes — agents type them relatively (`../mocks/…`, `<artifacts>/m/.store`). Consider a separate
  `MOCK_DATA_READ` finding kind so these trigage apart from `GRADED_READ` during the first `detect` run.
- **H2 — `$TASK_DIR` operands are only emitted as `$TASK_DIR/x` and `/work/task_dir/x`.** Under
  `driver: tempdir` (the whole skills nightly) the agent reads the real checkout path, matching neither, so
  everything rests on the `check_*.py` glob — and at least one live task is graded by
  `python3 $TASK_DIR/check.py`, no underscore, no match. One line: also emit
  `(task_file.parent / suffix).resolve()`.
- **M1 — false positives that would get the detector switched off.** `cat > check_env.py`,
  `rm -f check_env.py`, `mv check_temp.py …`, `for f in check_*.py` all classify as reads (unknown leading
  utility → read, plus a location-independent basename glob). Treat `>`/`>>` before a match as a write; add
  `rm mv chmod git for while if do done then fi` to the neutral set; require `check_*.py` matches to carry a
  directory component under the task dir or a `tests/tasks` segment.
- **M2 — voided rows still count as passes in the experiment aggregate.** `reports_experiment.py` computes
  the pass rate from `weighted_score`, which the gate deliberately leaves at 1.0, so an all-voided variant
  still reports 100% in the summary used to compare arms. Exclude voided rows or show a `voided: N` column.
- **M4 — `Edit`/`Write`/`MultiEdit`/`NotebookEdit`/`WebFetch` are unclassified**, so merely mentioning
  graded material sends the whole row `INCONCLUSIVE`. Classify edits as reads, `Write` as neutral, keep the
  unknown-tool path for genuinely unknown MCP tools.
- Lower priority from the same review: atomic `task.json` rewrite in `_restore_source_yaml`; a voided row
  loses `error_log_tail` (allowlist runs pre-gate); a scan exception leaves `SKIPPED` where the contract
  says `INCONCLUSIVE`; `_iter_call_logs` does a full `rglob` over mock dirs at teardown.

Then: run **one nightly in `detect`**, read the findings, and only then consider `void`.

### 2. Containment — the part that actually closes the hole (needs Docker on a POSIX host)

Detection catches cheats after the fact. These make the material unreadable, and none are written. They are
plan commits 8-10 in the approved plan; the deferral was correct because Docker is unavailable on the
machine used so far and the whole docker-mount test suite is `skipif(win32)`.

- **8** — stage the reference *content* into `/work/input` and stop mounting `reference.file`'s directory.
  `load_reference` already short-circuits on a cached value, so pre-seed `Orchestrator._reference_code`.
- **9** — consume-and-unlink `/work/input` after startup (needs the input mount flipped `:ro` → rw).
- **10** — mask `reference.file` inside the task-dir mount with a zero-byte staging file (**requires 8**, or
  every judge silently grades an empty reference).

**Even after these, the build suites stay exposed**: `check_*.py` must be executable at grading time,
`run_command` runs with `cwd=sandbox_dir`, and the container runs the agent as root. 360 graders vs 297
reference answers, so that is the larger surface, and detection is the only control there. The real fix is
the grading-phase mount handshake (hand the material over only after the agent phase ends) — designed but
deliberately deferred as its own change.

### 3. Skills-repo items (this repo, `tests/**`)

- `uipath-ixp`: `mocks/calls.log` is the sole grading oracle for 3 criteria per integration task, plaintext
  and writable in the agent's own working directory. PR #2375 improved its expressiveness but left it there.
- Add a gating **evidence-anchor** criterion so an unanchored answer cannot clear a lone `llm_judge` at 0.7
  (one judge wrote "best-effort/generic rather than evidence-anchored" and still scored 0.8).
- The simulator line *"proceed with best-effort findings using the evidence already gathered"* rewards
  guessing when the evidence channel is broken. ~296 task YAMLs plus the generator.
- Optional hygiene, explicitly deferred by the owner: blank `m/seal` + delete `.seal.bin` after sealing.
  Only `seal` can be blanked — `uip` must stay executable, and any loader names its own decode, so the
  recipe cannot leave a readable `uip` without returning to a version-locked `.pyc`. Must run strictly after
  `rmtree` or a mid-seal crash turns the `pre_run` retry into a silent no-op.

## Decisions already made — do not re-litigate

- **No new `FinalStatus` member** (blast radius: two exhaustive maps with import-time asserts, batch
  summaries, the run-count invariant, telemetry, evalboard). Void = flip `SUCCESS`→`FAILURE` +
  `voided=True`, leaving `weighted_score` as computed because the score is the diagnostic.
- **No criterion type** for the taint check — criteria are opt-in per YAML, and the author who leaks is the
  one who will not add it. It lives in `_finalize_result`.
- **Do not scan `result_summary` for path patterns** (result bodies false-positive this class) and **do not
  reuse `CommandExecutedChecker._matching_commands`** (2000-char ReDoS truncation hides long `cat`s).
- **`INTEGRITY_MODE` defaults to `detect`.**
- **Delegate-arm / silent-invalidity work is out of scope here** (unresolved mock dir or plugin path →
  ERROR, mock-never-invoked taint). Dropped from the branch, preserved on `feat/integrity-checks`.
- **The `_cache` "leak" was retracted** after verification — all 33 entries were the agent's own `docsai`
  queries. Do not resurrect it.

## Open questions for the owner

1. The delegate mock-PATH fix is said to be covered on another branch. A search of coder_eval's remote found
   no branch matching delegate/path-prepend/mock and nothing in the last 30 commits of main. Confirm before
   treating those three dropped commits as handled.
2. Should `CODEX_API_VERSION` and an "export these, `.env` will not deliver them" note go into
   `.env.example`? Their absence cost three discarded runs.
3. Who runs the containment work (plan 8-10) on a Docker-capable host?

## Practical notes that cost time

- **`.env` is inert for `CODEX_*` and `SKILLS_REPO_PATH`.** `config.py` calls `load_dotenv()` with no args,
  so python-dotenv resolves from coder_eval's own module directory (no `.env` there); only *declared*
  `Settings` fields are re-exported to `os.environ`. These are read via `os.getenv` /
  `os.path.expandvars`, so they must be **exported in the shell**. Symptom when missing: five well-formed
  `FAILURE` rows at 0.000, `skill_triggered=no`, zero tool calls, **no error anywhere**.
- Working local codex invocation: export the `CODEX_*` / `AWS_*` / `API_BACKEND` / `BEDROCK_*` block from
  `tests/.env`, then add `SKILLS_REPO_PATH` (the checkout under test) and
  `CODEX_API_VERSION=2025-04-01-preview`; run `coder-eval run <task.yaml…> -e experiments/default.yaml
  --type codex --model gpt-5.6-terra --include-skipped -j 3 --run-dir runs/<name>`. `--type` and `--model`
  are both required. Keep parallelism ≤3 (higher races the mock shim).
- **On the codex arm `task.log` has no agent tool calls** — the transcript is `task.json`
  (`iterations[].commands[].parameters` and `.result_summary`, both untruncated) or the rendered
  `task.html`. Read every artifact with explicit `encoding='utf-8'`.
- Proof the mock actually served evidence: non-empty `artifacts/<task-id>/m/.log`, decoded with
  `tests/tasks/uipath-troubleshoot/_shared/scripts/coverage_report.py --dump <path>`. Empty or absent means
  the score is meaningless regardless of verdict.
- **Nightly pass counts include `mature_skipped` rows that never executed** (571 of 1006 on 2026-08-03).
  Always compute rates over executed tasks.
- Broad `az storage blob list` paginates and truncates silently — pass `--num-results '*'`.
- Any edit to `_shared/mock_src/*.py` must be followed by
  `uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py` with the `.bin`
  diff committed; nothing in CI verifies it, and the sandbox executes the blob, not the `.py`.

## Working conventions to keep

- Keep appending to the worklog **as work happens** — decisions with rejected alternatives, issues found
  (flag, do not silently fix), commands with outcomes, verification evidence rather than claims.
- Pause and ask when a premise fails rather than improvising around it. Two premises failed here (`_cache`,
  and "the detector catches the measured cases") and both were caught by checking rather than assuming.
- One logical change per commit, single-line imperative messages, no AI attribution.
- Nothing under `skills/**` — it ships to clients. No tenant, org, host, account names or personal paths in
  anything committed, including test docs.
