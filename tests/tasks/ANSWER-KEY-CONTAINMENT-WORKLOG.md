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
