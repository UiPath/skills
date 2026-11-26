#!/usr/bin/env python3
"""Six static gates over the coder-eval task and experiment corpus.

Gate 1: no task YAML pins ``sandbox.driver: tempdir``
-----------------------------------------------------

The sandbox driver is decided by the run environment, NOT by the task:

  - The Linux nightly slice runs every non-windows task under ``driver: docker``
    (the ``skills-image`` bakes the full ``uip`` CLI + all tool plugins). The
    experiment config (``tests/experiments/nightly.yaml``) sets that default.
  - The Windows slice selects tasks by the ``windows`` tag and forces
    ``--driver tempdir`` on the CLI (which wins over any YAML). Windows tasks
    therefore do NOT need — and must not rely on — a YAML driver override.

A task that pins ``driver: tempdir`` opts out of the docker image and runs on
the bare host, where the tool plugins are NOT installed. Any task that then
calls a tool-backed command (e.g. ``uip maestro flow validate`` needs
``@uipath/maestro-tool``) fails with "No compatible version found", scoring
zero on an otherwise-correct run. This gate blocks that footgun.

If a task genuinely needs the Windows toolchain, tag it ``windows`` — do not
pin the driver.

Gate 2: experiment hook commands must be a single line
------------------------------------------------------

On Windows coder_eval runs hooks through ``create_subprocess_shell``, i.e.
cmd.exe, which parses only the FIRST line it is handed. A ``|-`` block scalar
therefore drops the rest, and ``PreRunCommand.fail_on_error`` defaults to
``True``, so an unparseable ``pre_run`` ERRORs every task in the split (skills
#2756, fixed by #3116). Just the newline rule: no false positives, no config.
It does not detect one-line POSIX sh; see the known-gap test for that cost.

Scope is what cmd.exe can reach: every experiment hook (they run for all tasks,
including the Windows split) plus the hooks of ``windows``-tagged tasks. A task
without that tag never runs on Windows, so its hooks are left alone.

Gate 3: no task stages a skill directory into the agent's sandbox
-----------------------------------------------------------------

``sandbox.template_sources`` is for pre_run/post_run tooling and fixtures. A
skill arrives through the plugin catalog (``agent.plugins``), which is what
selects the GENERATION under test — so a copy of ``skills/<name>/`` in the
agent's working directory hands a preview-arm run the shipped v1 guidance and
quietly destroys the comparison. Every uipath-maestro-bpmn task did this until
2026-09-23; agents read the cwd copy and authored against the wrong generation.
No other skill family ever did.

The README invariant alone did not hold: the porting brief kept telling authors
to add the line. This gate makes it fail instead.

Gate 4: no command_pattern backtracks catastrophically
-------------------------------------------------------

coder-eval 0.12 and 1.x both ``re.search`` every Bash call of a run with each
``command_executed`` / ``command_not_executed`` pattern, compiled with
``re.DOTALL``. A repeat whose alternatives can consume the same text (e.g.
``(?:\x27[^\x27\n]*\x27|[^\n;&])*?``, where ``'`` is in both) is exponential in
the input on a failing search; skills #4574 shipped one that took 0.8s at 14
quoted words and did not finish in 120s at 20. Grading then hangs on one long
agent command.

The gate builds a witness of each pattern's literal lead (``uip tm testcases
clone``), pumps a repeated word after it (``'a' ``, ``\\<newline>``, ...) that
the pattern cannot complete on, and runs the searches in worker processes. A
pattern whose probes exceed ``PROBE_BUDGET_SECONDS`` fails. A non-exponential
pattern finishes them in microseconds, so the budget has wide margin.

``SLOW_PATTERN_ALLOWLIST`` holds pre-existing offenders so the gate ratchets
instead of blocking every open PR. An entry whose pattern now passes fails the
gate as stale: remove it.

Gate 5: no pre_run/post_run command reads $REFERENCE_DIR or $TASK_DIR
----------------------------------------------------------------------

coder_eval expands those variables for ``success_criteria`` ``run_command``
only. A hook runs in the sandbox CWD with neither set, so ``python3
$REFERENCE_DIR/_setup/cleanup.py`` runs ``python3 /_setup/cleanup.py`` --
"No such file or directory", exit 2. Hook results are informational, so nothing
fails: the cleanup silently never ran, and a task that depends on its `pre_run`
grades against state the hook was supposed to have built.

A hook reaches its tooling through ``sandbox.template_sources``, which mounts
it into the sandbox; the command then names the mount point (``_setup/...``),
relative and with no variable at all.

Gate 6: every .py a criterion or hook names resolves and is runnable
---------------------------------------------------------------------

A ``run_command`` that names a grader which is not on disk, or which has no
``if __name__ == "__main__":`` to run, exits non-zero for a reason that has
nothing to do with the agent -- and the harness scores it exactly like a failed
submission, so a renamed or import-only grader reads as an agent that got the
answer wrong. Every task in the suite does, silently and forever.

``tests/tasks/uipath-rules/_shared/test_graders_refuse_an_empty_sandbox.py``
pins the narrower half of this for one suite by running each grader in an empty
directory; this gate is the static half, over every suite.

A path is resolved the way coder_eval resolves it: ``$REFERENCE_DIR`` against
the task's ``reference.directory``, and a bare relative path against the
``template_sources`` mount that supplies it. A path this gate cannot resolve to
either is reported -- an unresolvable grader is the finding, not an exemption.

Usage:
    python3 scripts/check-task-driver.py                              # tests/tasks
    python3 scripts/check-task-driver.py tests/tasks tests/experiments  # all gates

Exit codes:
    0 — every gate passes
    1 — one or more violations (paths printed, with GitHub annotations)
"""

from __future__ import annotations

import ast
import json
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from pathlib import Path

try:
    import re._constants as _sre_c
    import re._parser as _sre_p
except ImportError:  # Python < 3.11
    import sre_constants as _sre_c  # type: ignore[no-redef]
    import sre_parse as _sre_p  # type: ignore[no-redef]

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "tests" / "tasks"

_DRIVER_LINE = re.compile(r"^\s*driver:\s*tempdir\s*$")

# --- Gate 4: catastrophic backtracking -------------------------------------

PROBE_REPEATS = 20
PROBE_BUDGET_SECONDS = 0.5
PROBE_WORKERS = max(1, min(4, os.cpu_count() or 1))
# Words pumped after each pattern's witness. Each targets an overlap seen in a
# real offender: quotes (#4574 clone loop), line continuations (`\\\r?\n|\\.`).
PROBE_WORDS = ("'a' ", '"a" ', "\\\n", "a ", "\\a", "a'", " ", "-a ", "a\n", "a=", "--a ")
_GRADED_COMMAND_TYPES = ("command_executed", "command_not_executed")

# Pre-existing offenders: (repo-relative task path, criterion description).
# Ratchet: fix the pattern, then delete its entry (a passing entry fails as stale).
SLOW_PATTERN_ALLOWLIST: frozenset[tuple[str, str]] = frozenset({
    # `(?:[^&;|\r\n\\]|\\\r?\n|\\.)*` lookaheads: `\\.` also matches `\\\n` under DOTALL.
    ("tests/tasks/uipath-test/customfield_population_integration.yaml",
     "Created the free-text field definition `Eval Reviewer` scoped TestCase"),
    ("tests/tasks/uipath-test/customfield_population_integration.yaml",
     "Created the tag/label field definition `Eval Risk` scoped TestCase"),
    ("tests/tasks/uipath-test/link_automation_and_run.yaml",
     "Agent discovered folder key with `folders list -n|--name <folder-name> --all`"),
    ("tests/tasks/uipath-test/link_automation_and_run.yaml",
     "Agent ran the testcase with --test-case-id (UUID), --execution-type automated, "
     "and the requested execution name"),
    ("tests/tasks/uipath-test/perf_scenario_cleanup_smoke.yaml",
     "Agent deleted with `perf-scenario delete --scenario-key … --yes`"),
    ("tests/tasks/uipath-test/prompts_create_smoke.yaml",
     "Agent created the prompt with `uip tm prompts create … --mode-of-use …`"),
})

# Runs in a fresh interpreter: reads one JSON job per line, prints `s <i>` before
# and `d <i>` after each pattern's probes. The parent kills it on a slow pattern.
_PROBE_WORKER = r"""
import json, re, sys
for line in sys.stdin:
    idx, pattern, probes = json.loads(line)
    print("s", idx, flush=True)
    rx = re.compile(pattern, re.DOTALL)
    for probe in probes:
        rx.search(probe)
    print("d", idx, flush=True)
"""

_CATEGORY_RE = {
    _sre_c.CATEGORY_SPACE: r"\s", _sre_c.CATEGORY_NOT_SPACE: r"\S",
    _sre_c.CATEGORY_DIGIT: r"\d", _sre_c.CATEGORY_NOT_DIGIT: r"\D",
    _sre_c.CATEGORY_WORD: r"\w", _sre_c.CATEGORY_NOT_WORD: r"\W",
}


def _in_class(items, ch: str) -> bool:
    negate, hit = False, False
    for op, av in items:
        if op is _sre_c.NEGATE:
            negate = True
        elif op is _sre_c.LITERAL:
            hit |= ord(ch) == av
        elif op is _sre_c.RANGE:
            hit |= av[0] <= ord(ch) <= av[1]
        elif op is _sre_c.CATEGORY:
            hit |= bool(re.match(_CATEGORY_RE.get(av, r"(?!)"), ch))
    return hit != negate


def _witness(items, out: list[str]) -> bool:
    """Append text matching the pattern's fixed lead; False where it turns variable.

    Lookarounds are skipped; a repeat of one character class contributes its
    minimum and continues (`\\s+`); any other optional repeat ends the lead.
    """
    single = (_sre_c.IN, _sre_c.LITERAL, _sre_c.NOT_LITERAL, _sre_c.ANY)
    for op, av in items:
        if op is _sre_c.LITERAL:
            out.append(chr(av))
        elif op is _sre_c.NOT_LITERAL:
            out.append("b" if av == ord("a") else "a")
        elif op is _sre_c.ANY:
            out.append("a")
        elif op is _sre_c.IN:
            ch = next((c for c in " a-/=0" if _in_class(av, c)), None)
            if ch is None:
                return False
            out.append(ch)
        elif op in (_sre_c.AT, _sre_c.ASSERT, _sre_c.ASSERT_NOT):
            continue
        elif op is _sre_c.SUBPATTERN:
            if not _witness(av[-1], out):
                return False
        elif op is _sre_c.BRANCH:
            if not _witness(av[1][0], out):
                return False
        elif op in (_sre_c.MAX_REPEAT, _sre_c.MIN_REPEAT):
            low, high, body = av
            for _ in range(low):
                if not _witness(body, out):
                    return False
            if low == 0 or (high != low and not (len(body) == 1 and body[0][0] in single)):
                return False
        else:
            return False
    return True


def _probe_inputs(pattern: str, repeats: int = PROBE_REPEATS) -> list[str]:
    """Pumped inputs for ``pattern``: witness lead (per top-level alternative) + word * repeats."""
    leads = {"uip "}
    try:
        items = list(_sre_p.parse(pattern, re.DOTALL))
    except re.error:
        return []
    alternatives = [items]
    if len(items) == 1 and items[0][0] is _sre_c.BRANCH:
        alternatives = items[0][1][1]
    for alternative in alternatives:
        lead: list[str] = []
        _witness(list(alternative), lead)
        leads.add("".join(lead))
    return [lead + word * repeats + "\x00" for lead in sorted(leads) for word in PROBE_WORDS]


def _iter_graded_patterns(doc: dict) -> Iterator[tuple[int, str, str]]:
    """Yield ``(index, description, pattern)`` per command-grading criterion."""
    criteria = doc.get("success_criteria")
    if not isinstance(criteria, list):
        return
    for index, criterion in enumerate(criteria):
        if (
            isinstance(criterion, dict)
            and criterion.get("type") in _GRADED_COMMAND_TYPES
            and isinstance(criterion.get("command_pattern"), str)
        ):
            yield index, str(criterion.get("description") or ""), criterion["command_pattern"]


def _slow_patterns(patterns: list[str], budget: float = PROBE_BUDGET_SECONDS) -> set[int]:
    """Indexes of ``patterns`` whose probes do not finish within ``budget`` seconds each."""
    jobs = []
    for idx, pattern in enumerate(patterns):
        try:
            re.compile(pattern, re.DOTALL)
        except re.error:
            continue  # an invalid pattern is coder-eval's error to report, not this gate's
        jobs.append((idx, pattern, _probe_inputs(pattern)))
    lanes = [jobs[i::PROBE_WORKERS] for i in range(PROBE_WORKERS)]
    events: queue.Queue = queue.Queue()
    slow: set[int] = set()

    def start(lane_id: int, lane: list) -> subprocess.Popen:
        # Jobs go in through a file, not a pipe: killing a worker mid-pipe-write
        # raises BrokenPipeError in the writer.
        with tempfile.TemporaryFile("w+", encoding="utf-8") as jobs_file:
            jobs_file.writelines(json.dumps(job) + "\n" for job in lane)
            jobs_file.seek(0)
            proc = subprocess.Popen(
                [sys.executable, "-c", _PROBE_WORKER], stdin=jobs_file, stdout=subprocess.PIPE, text=True
            )

        def read() -> None:
            for line in proc.stdout:
                kind, idx = line.split()
                events.put((lane_id, proc, kind, int(idx)))
            events.put((lane_id, proc, "eof", -1))

        threading.Thread(target=read, daemon=True).start()
        return proc

    procs = {i: start(i, lane) for i, lane in enumerate(lanes) if lane}
    running: dict[int, tuple[int, float]] = {}  # lane -> (job idx, started at)
    done: dict[int, int] = {i: 0 for i in procs}  # lane -> jobs finished or skipped
    while procs:
        now = time.monotonic()
        deadline = min((t + budget for _, t in running.values()), default=now + budget)
        try:
            lane_id, proc, kind, idx = events.get(timeout=max(0.0, deadline - now))
        except queue.Empty:
            for lane_id, (idx, started) in list(running.items()):
                if time.monotonic() - started >= budget:
                    slow.add(idx)
                    procs[lane_id].kill()
                    del running[lane_id]
                    done[lane_id] += 1
                    rest = lanes[lane_id][done[lane_id]:]
                    lanes[lane_id] = rest
                    done[lane_id] = 0
                    if rest:
                        procs[lane_id] = start(lane_id, rest)
                    else:
                        del procs[lane_id]
            continue
        if procs.get(lane_id) is not proc:
            continue  # event from a worker already killed and replaced
        if kind == "s":
            running[lane_id] = (idx, time.monotonic())
        elif kind == "d":
            running.pop(lane_id, None)
            done[lane_id] += 1
        else:
            proc.wait()
            del procs[lane_id]
    return slow


def _iter_task_yamls(args: list[str]) -> list[Path]:
    roots = [Path(a) for a in args] if args else [DEFAULT_ROOT]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.yaml")))
            files.extend(sorted(root.rglob("*.yml")))
    return files


def _rel(path: Path) -> str:
    """Repo-relative path string, robust to relative/absolute inputs and cwd."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _driver_line_number(path: Path) -> int:
    """1-indexed line of the offending `driver: tempdir` (0 if not found textually)."""
    for n, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        if _DRIVER_LINE.match(line):
            return n
    return 0


def _iter_hook_commands(doc: dict) -> Iterator[tuple[str, str]]:
    """Yield ``(yaml_path, command)`` for every pre_run/post_run command."""
    scopes: list[tuple[str, dict]] = [("", doc)]
    for key, value in doc.items():
        if isinstance(value, dict):
            scopes.append((key, value))
        elif isinstance(value, list):  # variants[] holds per-variant overrides
            scopes.extend(
                (f"{key}[{i}]", v) for i, v in enumerate(value) if isinstance(v, dict)
            )
    for scope_name, scope in scopes:
        for hook in ("pre_run", "post_run"):
            steps = scope.get(hook)
            if not isinstance(steps, list):
                continue
            prefix = f"{scope_name}.{hook}" if scope_name else hook
            for index, step in enumerate(steps):
                if isinstance(step, dict) and isinstance(step.get("command"), str):
                    yield f"{prefix}[{index}].command", step["command"]


def _hook_line_number(path: Path, command: str) -> int:
    """1-indexed line where ``command`` starts in the raw file (0 if not found)."""
    needle = command.strip().splitlines()[0].strip()
    if len(needle) < 8:
        return 0
    for n, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        if needle in line:
            return n
    return 0


def _report_slow_patterns(graded: list[tuple[Path, int, str, str]]) -> int:
    """Gate 4. Print the result; return 1 on a new offender or a stale allowlist entry."""
    if not graded:
        return 0
    slow = _slow_patterns([pattern for _, _, _, pattern in graded])
    new_offenders, stale = [], []
    for idx, (path, index, desc, _) in enumerate(graded):
        allowed = (_rel(path), desc) in SLOW_PATTERN_ALLOWLIST
        if idx in slow and not allowed:
            new_offenders.append((path, index, desc))
        elif allowed and idx not in slow:
            stale.append((path, desc))
    if not new_offenders and not stale:
        print(
            f"OK — {len(graded)} command_pattern(s) finish pumped probes within "
            f"{PROBE_BUDGET_SECONDS}s ({len(SLOW_PATTERN_ALLOWLIST)} allowlisted)."
        )
        return 0
    if new_offenders:
        print(f"FAIL — {len(new_offenders)} command_pattern(s) backtrack catastrophically:\n")
        for path, index, desc in new_offenders:
            rel = _rel(path)
            print(f"::error file={rel}::success_criteria[{index}] command_pattern backtracks catastrophically")
            print(f"  {rel}  success_criteria[{index}]  ({desc})")
        print()
        print(
            "A failing search took over the probe budget: a repeat's alternatives can\n"
            "consume the same text, so the search is exponential in the command length.\n"
            "Make the alternatives disjoint, e.g. keep `'` out of the catch-all class:\n"
            "`(?:\\x27[^\\x27\\n]*\\x27|[^\\n;&\\x27])*?`. See Gate 4 in scripts/check-task-driver.py."
        )
        print()
    if stale:
        print(f"FAIL — {len(stale)} SLOW_PATTERN_ALLOWLIST entr(y/ies) now pass; remove them:\n")
        for path, desc in stale:
            print(f"  {_rel(path)}  ({desc})")
        print()
    return 1


# --- Gate 5: hook commands and the variables they cannot see ---------------

# Matched in either spelling a shell accepts, so `${REFERENCE_DIR}` is caught too.
_HOOK_VARIABLE = re.compile(r"\$\{?(REFERENCE_DIR|TASK_DIR)\b")


def _hook_variables(doc: dict) -> Iterator[tuple[str, str | None, str]]:
    """`(yaml_path, variable, command)` per pre_run/post_run command; `variable` None when clean.

    Every such command is yielded, not only the offenders, so the gate can say how many it
    read. `hooks_checked` counts Gate 2's scope -- Windows-reachable hooks only -- and reusing
    it meant a corpus of clean non-Windows hooks reported nothing at all.
    """
    for yaml_path, command in _iter_hook_commands(doc):
        if not yaml_path.startswith(("pre_run", "post_run")):
            continue
        found = _HOOK_VARIABLE.search(command)
        yield yaml_path, found.group(1) if found else None, command.strip()


# --- Gate 6: every grader a task names is on disk and runnable -------------

_PY_IN_COMMAND = re.compile(r"(?<![\w/.$-])((?:\$\{?REFERENCE_DIR\}?|[\w./-]+)(?:/[\w.-]+)*\.py)")

# Top-level statements that do nothing when the file is run. A module made only of these is a
# library: `python3 that.py` prints nothing, exits 0, and a criterion asking it a question gets
# no answer. Everything else -- a call, a branch, a loop, an assignment computed from one -- is
# work the module does on import, which is how every straight-line grader in the corpus runs.
_INERT_NODES = (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef,
                ast.ClassDef, ast.Pass)
_LITERAL_VALUES = (ast.Constant, ast.Name, ast.Tuple, ast.List, ast.Dict, ast.Set,
                   ast.JoinedStr, ast.ListComp, ast.DictComp, ast.SetComp)


def _is_runnable(source: str) -> bool:
    """Whether `python3 <file>` would execute anything -- a `__main__` guard, or top-level work."""
    try:
        module = ast.parse(source)
    except SyntaxError:
        return False
    for node in module.body:
        if isinstance(node, _INERT_NODES):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue  # a docstring
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if node.value is None or isinstance(node.value, _LITERAL_VALUES):
                continue  # a constant the module merely declares
        return True
    return False


def _mount_roots(doc: dict, task_dir: Path) -> dict[str, list[Path]]:
    """Sandbox path -> the directories on disk that supply it, in `template_sources` order.

    A `template_dir` lands its *contents* at the mount point, which defaults to the sandbox
    root -- so a source with no `mount_point` contributes each of its own children by name.
    A list rather than one path per mount, because several sources may share a mount point and
    merge there: uipath-admin stages both the task's own `_setup` and the suite's at `_setup`,
    and a resolver that kept only one of them read half the suite's hooks as missing.
    """
    roots: dict[str, list[Path]] = {}
    sandbox = doc.get("sandbox")
    for src in (sandbox.get("template_sources") or []) if isinstance(sandbox, dict) else []:
        if not isinstance(src, dict) or not src.get("path"):
            continue
        source = (task_dir / str(src["path"])).resolve()
        mount = str(src.get("mount_point") or "").strip("/")
        if mount:
            roots.setdefault(mount, []).append(source)
        elif source.is_dir():
            for child in source.iterdir():
                roots.setdefault(child.name, []).append(child)
    return roots


def _resolve_script(raw: str, task_dir: Path, reference: Path,
                    mounts: dict[str, list[Path]]) -> Path | None:
    """The repo file a command's `.py` argument names, or None when the repo does not supply it.

    None means "not this gate's business", not "missing". A command may name a path the *sandbox*
    supplies rather than the repo: a script the agent was asked to write, or one a `pre_run`
    copied in (`cp _setup/verify.py .` then `./verify.py`). Neither is on disk at the path the
    command spells, and neither is a defect. So only a path the repo is supposed to answer for
    is resolved -- `$REFERENCE_DIR`-rooted, or under a `template_sources` mount -- plus a bare
    relative one that does land in the repo, which is then held to the same bar.
    """
    variable = re.match(r"\$\{?REFERENCE_DIR\}?/(.*)", raw)
    if variable:
        return reference / variable.group(1)
    relative = raw.lstrip("./")
    head = relative.split("/")[0]
    if head in mounts:
        rest = relative[len(head):].lstrip("/")
        mounted = [root / rest if rest else root for root in mounts[head]]
        # The first that exists; failing that the first, so the report names where it belongs.
        return next((c for c in mounted if c.is_file()), mounted[0] if mounted else None)
    return next((c for c in (task_dir / relative, reference / relative) if c.is_file()), None)


def _iter_named_scripts(doc: dict, path: Path) -> Iterator[tuple[str, str, Path | None]]:
    """`(where, raw_path, resolved)` for each `.py` a criterion or hook command names."""
    task_dir = path.parent
    reference = (task_dir / str((doc.get("reference") or {}).get("directory") or ".")).resolve()
    mounts = _mount_roots(doc, task_dir)
    commands: list[tuple[str, str]] = list(_iter_hook_commands(doc))
    for index, criterion in enumerate(doc.get("success_criteria") or []):
        if isinstance(criterion, dict) and criterion.get("command"):
            commands.append((f"success_criteria[{index}].command", str(criterion["command"])))
    for where, command in commands:
        for raw in _PY_IN_COMMAND.findall(command):
            yield where, raw, _resolve_script(raw, task_dir, reference, mounts)


def main(argv: list[str]) -> int:
    offenders: list[tuple[Path, int]] = []
    docker_pins: list[Path] = []
    multi_line: list[tuple[Path, int, str]] = []
    staged_skills: list[tuple[Path, str]] = []
    hooks_checked = 0
    hook_variables: list[tuple[Path, str, str, str]] = []  # (path, yaml_path, variable, command)
    hook_commands_scanned = 0
    missing_scripts: list[tuple[Path, str, str, str]] = []  # (path, where, raw, why)
    scripts_checked = 0
    graded: list[tuple[Path, int, str, str]] = []  # (path, index, description, pattern)

    for path in _iter_task_yamls(argv):
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            # Malformed YAML is another gate's problem; don't mask it as a pass
            # but don't crash this check either.
            continue
        if not isinstance(doc, dict):
            continue

        graded.extend((path, i, desc, pat) for i, desc, pat in _iter_graded_patterns(doc))
        for where, variable, command in _hook_variables(doc):
            hook_commands_scanned += 1
            if variable:
                hook_variables.append((path, where, variable, command))
        for where, raw, resolved in _iter_named_scripts(doc, path):
            if resolved is None:
                continue  # the sandbox supplies it, not the repo — see `_resolve_script`
            scripts_checked += 1
            if not resolved.is_file():
                missing_scripts.append((path, where, raw, f"{_rel(resolved)} does not exist"))
            elif not _is_runnable(resolved.read_text(encoding="utf-8", errors="replace")):
                missing_scripts.append(
                    (path, where, raw,
                     f"{_rel(resolved)} runs nothing when executed: no `if __name__ == "
                     f"\"__main__\":` and no top-level work"))

        tags = doc.get("tags")
        if (
            "experiment_id" in doc
            or "variants" in doc
            or (isinstance(tags, list) and "windows" in tags)
        ):
            for yaml_path, command in _iter_hook_commands(doc):
                hooks_checked += 1
                if len(command.strip().splitlines()) > 1:
                    multi_line.append((path, _hook_line_number(path, command), yaml_path))

        sandbox = doc.get("sandbox")
        if not isinstance(sandbox, dict):
            continue
        # The bug is GUIDANCE in the agent's cwd: the skill root, or its
        # references/. A data directory that merely lives inside a skill
        # folder is legitimate staging — uipath-coded-apps stages
        # skills/uipath-coded-apps/assets/fixtures and should keep working.
        for src in sandbox.get("template_sources") or []:
            if not isinstance(src, dict):
                continue
            src_path = str(src.get("path") or "")
            if re.search(r"(^|/)skills/[^/]+(/references(/|$)|/?$)", src_path):
                staged_skills.append((path, src_path))
        driver = sandbox.get("driver")
        if driver == "tempdir":
            offenders.append((path, _driver_line_number(path)))
        elif driver == "docker":
            docker_pins.append(path)

    if docker_pins:
        print(
            f"note: {len(docker_pins)} task(s) pin `sandbox.driver: docker` (redundant with "
            "the Linux default, harmless — not blocked):"
        )
        for p in docker_pins:
            print(f"  {_rel(p)}")
        print()

    rc = 0

    if multi_line:
        rc = 1
        print(f"FAIL — {len(multi_line)} Windows-reachable hook command(s) span multiple lines:\n")
        for path, line, yaml_path in multi_line:
            rel = _rel(path)
            loc = f"{rel}:{line}" if line else rel
            print(f"::error file={rel},line={line}::{yaml_path} spans multiple lines")
            print(f"  {loc}  ({yaml_path})")
        print()
        print(
            "cmd.exe on the Windows split parses only the first line, so the rest is\n"
            "dropped and an unparseable pre_run ERRORs every task (skills #2756/#3116).\n"
            "Collapse it to one line; if it is POSIX sh that must not run on Windows,\n"
            "prefix it with `:; ` too. See tests/experiments/nightly.yaml."
        )
        print()
    elif hooks_checked:
        print(f"OK — {hooks_checked} Windows-reachable hook command(s) are single-line.")

    if staged_skills:
        rc = 1
        print(f"FAIL — {len(staged_skills)} task(s) stage a skill directory into the sandbox:\n")
        for path, src_path in staged_skills:
            rel = _rel(path)
            print(f"::error file={rel}::Task stages a skill directory ({src_path}) via template_sources")
            print(f"  {rel}  ->  {src_path}")
        print()
        print(
            "template_sources is for pre_run/post_run tooling and fixtures. The skill\n"
            "arrives through agent.plugins, which is what selects the generation under\n"
            "test — a copy in the working directory feeds a preview-arm run the shipped\n"
            "v1 guidance. Drop the entry (delete the `sandbox:` block if it becomes\n"
            "empty). See \"Arm neutrality\" in tests/tasks/uipath-maestro-bpmn/README.md."
        )
        print()

    if not staged_skills:
        print("OK — no task stages a skill directory via template_sources.")

    if hook_variables:
        rc = 1
        print(f"FAIL — {len(hook_variables)} pre_run/post_run command(s) read a variable that is "
              f"not set for hooks:\n")
        for path, where, variable, command in hook_variables:
            rel = _rel(path)
            print(f"::error file={rel}::{where} reads ${variable}, which coder_eval sets for "
                  f"success_criteria only")
            print(f"  {rel}  ({where})  ${variable}")
            print(f"    {command}")
        print()
        print(
            "coder_eval expands $REFERENCE_DIR and $TASK_DIR for success_criteria run_command\n"
            "only. A hook runs in the sandbox CWD with neither set, so the path collapses to an\n"
            "absolute one that does not exist — and because hook results are informational, the\n"
            "hook silently never runs. Mount what the hook needs through\n"
            "sandbox.template_sources and name the mount point relatively (`_setup/...`)."
        )
        print()
    elif hook_commands_scanned:
        print(f"OK — none of {hook_commands_scanned} pre_run/post_run command(s) reads "
              f"$REFERENCE_DIR or $TASK_DIR.")

    if missing_scripts:
        rc = 1
        print(f"FAIL — {len(missing_scripts)} command(s) name a .py that cannot be run:\n")
        for path, where, raw, why in missing_scripts:
            rel = _rel(path)
            print(f"::error file={rel}::{where} names {raw}, which {why}")
            print(f"  {rel}  ({where})  {raw} — {why}")
        print()
        print(
            "A criterion whose grader is missing, renamed, or import-only exits non-zero for a\n"
            "reason that is not the agent's, and the harness scores that exactly like a wrong\n"
            "answer — for every run of the task. Point the command at a file that exists, and\n"
            "give it something to do when it is run: an `if __name__ == \"__main__\":` guard,\n"
            "or the top-level statements a straight-line grader already has."
        )
        print()
    elif scripts_checked:
        print(f"OK — all {scripts_checked} .py path(s) named by a criterion or hook resolve and are runnable.")

    rc |= _report_slow_patterns(graded)

    if not offenders:
        print("OK — no task pins `sandbox.driver: tempdir`.")
        return rc

    print(f"FAIL — {len(offenders)} task(s) pin `sandbox.driver: tempdir`:\n")
    for path, line in offenders:
        rel = _rel(path)
        loc = f"{rel}:{line}" if line else rel
        # GitHub Actions annotation (rendered inline on the PR when run in CI).
        print(f"::error file={rel},line={line}::Task pins sandbox.driver: tempdir")
        print(f"  {loc}")
    print()
    print(
        "The sandbox driver is decided by the run environment, not the task.\n"
        "Remove the `driver: tempdir` line (delete the `sandbox:` block if it becomes empty).\n"
        "If the task needs the Windows toolchain, tag it `windows` instead — see the\n"
        "docstring in scripts/check-task-driver.py for the full rationale."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
