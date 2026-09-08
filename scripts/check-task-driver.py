#!/usr/bin/env python3
"""Two static gates over the coder-eval task/experiment corpus.

Gate 1 — no task YAML pins ``sandbox.driver: tempdir``
------------------------------------------------------

The sandbox driver is decided by the run environment, NOT by the task:

  - The Linux nightly slice runs every non-windows task under ``driver: docker``
    (the ``skills-image`` bakes the full ``uip`` CLI + all tool plugins). The
    experiment config (``tests/experiments/nightly.yaml``) sets that default.
  - The Windows slice selects tasks by the ``windows`` tag and forces
    ``--driver tempdir`` on the CLI (which wins over any YAML). Windows tasks
    therefore do NOT need -- and must not rely on -- a YAML driver override.

A task that pins ``driver: tempdir`` opts out of the docker image and runs on
the bare host, where the tool plugins are NOT installed. Any task that then
calls a tool-backed command (e.g. ``uip maestro flow validate`` needs
``@uipath/maestro-tool``) fails with "No compatible version found", scoring
zero on an otherwise-correct run. This gate blocks that footgun.

If a task genuinely needs the Windows toolchain, tag it ``windows`` -- do not
pin the driver.

Gate 2 — every Windows-reachable shell command is cmd.exe-safe
--------------------------------------------------------------

coder_eval hands three kinds of string straight to a shell:

  - ``pre_run[].command``  -> ``asyncio.create_subprocess_shell``
  - ``post_run[].command`` -> same call site
  - ``run_command`` criteria -> ``subprocess.run(shell=True)``

On Windows all three resolve to ``%COMSPEC% /c`` -- that is **cmd.exe**, not sh,
not PowerShell, not Git Bash. cmd cannot parse POSIX sh, and the three surfaces
fail with very different volumes:

  - a bad ``pre_run`` aborts the task (``fail_on_error`` defaults true)
  - a bad ``post_run`` only warn-logs, so artifacts leak silently
  - a bad ``run_command`` criterion **scores zero**, which in the report is
    indistinguishable from the agent having written bad code

That last one is why this gate exists. On 2026-09-04 a multi-line POSIX ``sh``
``pre_run`` hook landed in ``nightly.yaml`` and took the entire Windows nightly
split to ``7/7 status=ERROR`` at setup. Nothing connected "this experiment can
run on Windows" to "therefore its commands must be cmd-safe". This gate is that
missing link.

A command clears the gate if any of these holds:

  1. it starts with ``:`` followed by ``;`` or whitespace. cmd reads a leading
     ``:`` as a label, skips the line, and exits 0; sh reads ``:`` as the no-op
     builtin and runs the rest unchanged. This is the sanctioned way to make a
     POSIX command inert on Windows -- see ``tests/experiments/nightly.yaml``.
  2. it is a single self-contained ``pwsh``/``powershell`` invocation, which cmd
     can dispatch verbatim (this is what ``coder_eval_uipath``'s
     ``prepare_windows_experiment.py`` overlay generates).
  3. it contains none of the POSIX-only constructs in ``_CMD_UNSAFE``.

Every command must also be a **single line**: cmd parses only the first line of
the string it is given, so a YAML ``|-`` block scalar silently drops or
misparses everything after line 1.

Scope of gate 2:

  - ``run_command`` criteria and hooks on tasks tagged ``windows``
  - hooks on any experiment classified ``windows-reachable`` in
    ``_EXPERIMENT_PLATFORM``

That table is **fail-closed**: an experiment file that is not listed fails the
gate until someone classifies it. Adding an experiment therefore forces an
explicit decision about Windows reachability, which is the whole point.

Not covered: the ``uipath_eval`` criterion builds its command with
``shlex.quote`` (POSIX single-quote escaping, which cmd does not honour). That
is latent and only fires when a resolved eval-set path contains a space; it
belongs in coder_eval, not here.

Usage:
    python3 scripts/check-task-driver.py                              # tests/tasks
    python3 scripts/check-task-driver.py tests/tasks tests/experiments  # both gates

Exit codes:
    0 — both gates pass
    1 — one or more violations (paths printed, with GitHub annotations)
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "tests" / "tasks"

_DRIVER_LINE = re.compile(r"^\s*driver:\s*tempdir\s*$")

# Every experiment file must appear here. An unlisted file FAILS gate 2, which
# forces the author of a new experiment to decide whether its hooks can reach a
# Windows runner. Same fail-closed shape as the `len(matches) != 1` assertion in
# coder_eval_uipath's prepare_windows_experiment.py.
_EXPERIMENT_PLATFORM: dict[str, str] = {
    # Overlaid onto a Windows-private copy by coder_eval_uipath's
    # .azure-pipelines/scripts/prepare_windows_experiment.py, then run by
    # eval_runner/scripts/ci/daily-windows.ps1 with TAGS=windows.
    "nightly.yaml": "windows-reachable",
    # smoke-rpa-skills.yml and run-coder-eval.yml both drive this one on
    # `runs-on: uipath-windows-latest`. Not overlaid: what is in this file is
    # what cmd.exe receives.
    "smoke-windows.yaml": "windows-reachable",
    # Linux-only: no workflow or runner script pairs these with a Windows agent.
    "activation.yaml": "linux-only",
    "default.yaml": "linux-only",
    "flow-v2-preview.yaml": "linux-only",
    "same-ground-headtohead.yaml": "linux-only",
    "sherif-skill-comparison.yaml": "linux-only",
    "skill-comparison-template.yaml": "linux-only",
    "smoke.yaml": "linux-only",
}

# (experiment filename, yaml path) -> the exact POSIX command that
# coder_eval_uipath's .azure-pipelines/scripts/prepare_windows_experiment.py
# rewrites into a PowerShell equivalent before the Windows slice ever sees the
# file. Exempt here because cmd.exe never receives this string.
#
# Exact-match on purpose. If the command drifts, this gate fails AND the
# overlay's own `if len(matches) != 1: raise ValueError(...)` fails, so the two
# checks pincer the change instead of one of them silently going stale. Do not
# relax this to a prefix or regex match.
_OVERLAY_TRANSLATED: dict[tuple[str, str], str] = {
    ("nightly.yaml", "defaults.post_run[0].command"): (
        "find . -maxdepth 5 -type d \\( -name node_modules -o -name .npm-prefix "
        "-o -name .venv \\) -prune -exec rm -rf {} +"
    ),
}

# POSIX-sh constructs cmd.exe cannot parse or cannot resolve. `&&` and `||` are
# deliberately absent: cmd supports both.
_CMD_UNSAFE: tuple[tuple[str, re.Pattern[str]], ...] = (
    # No sh coreutils on the Windows image PATH unless Git Bash happens to be
    # there. `bash` is in this list deliberately: on the ADO Windows image it
    # resolves to the WSL launcher, which exits 1 with "no installed
    # distributions" -- the exact reason coder_eval_uipath PR #115's PowerShell
    # translation of the nightly hook could not work.
    ("posix-tool", re.compile(
        r"(?<![\w./-])(bash|sh|grep|sed|awk|printf|chmod|touch|wc|cut|tr|xargs|basename|dirname"
        r"|rm|mkdir|cp|mv|ls|cat|head|tail|sort|uniq|find)\b"
    )),
    # cmd has `if`, but no `test` and no `[`.
    ("test-or-bracket", re.compile(r"(?<![\w./-])test\s+-|\[\s")),
    # cmd's equivalent is `for /f`; there is no $(...) or backtick form.
    ("command-substitution", re.compile(r"\$\(|`")),
    # cmd uses %VAR% and has no ${VAR:-default} form; ${...} is literal text.
    ("sh-variable", re.compile(r"\$\{|\$[A-Za-z_]")),
    # cmd has no then/fi/elif/esac/done.
    ("sh-keyword", re.compile(r"(?<![\w-])(then|fi|elif|esac|done)(?![\w-])")),
    # sh separates statements with `;`; cmd uses `&` and treats `;` as a token
    # delimiter, so a `;`-joined command silently runs as one mangled argv.
    ("semicolon-separator", re.compile(r";")),
    # cmd's null sink is NUL.
    ("dev-null", re.compile(r"/dev/null")),
    # cmd only recognises `"`. A `'` is a literal character, so it is passed
    # through into the argument (e.g. python -c 'print(1)' becomes a SyntaxError).
    ("single-quote", re.compile(r"'")),
    # No `export`/`source`/`set -e` in cmd.
    ("sh-builtin", re.compile(r"(?<![\w-])(export|source|set\s+-[eu])(?![\w-])")),
)

# cmd reads a leading `:` as a label and skips the line; sh reads it as the
# no-op builtin. This is the sanctioned way to neutralise a POSIX command on
# Windows (skills #3116).
_CMD_INERT_PREFIX = re.compile(r"^:(?:;|\s)")

# A self-contained PowerShell invocation is a single command cmd can dispatch
# verbatim, whatever the payload inside the quotes.
_NATIVE_SHELL = re.compile(r"^\s*(pwsh|powershell)(\.exe)?\s")


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


def _cmd_unquoted(command: str) -> str:
    """The parts of ``command`` cmd.exe does NOT treat as literal text.

    cmd has exactly one quote character, ``"``, with no escape for it: each one
    toggles quoting. Inside a quoted run, ``;`` ``'`` ``&`` ``|`` ``<`` ``>``
    and ``$`` are all literal, so a payload like

        python -c "import sys; sys.exit(0 if open('f').read() else 1)"

    is perfectly cmd-safe despite being full of sh metacharacters. Only the
    unquoted remainder is worth scanning. (``%VAR%`` *is* still expanded inside
    quotes, but ``%`` is not a construct this gate cares about.)
    """
    return "".join(part for n, part in enumerate(command.split('"')) if n % 2 == 0)


def cmd_safety_problems(command: str) -> list[str]:
    """Names of the reasons ``command`` would break under cmd.exe. Empty == safe.

    Order matters. Multi-line is checked first and unconditionally: cmd parses
    only the first line it is handed, so a `|-` block scalar is broken even if
    every individual line would otherwise pass.
    """
    if not isinstance(command, str) or not command.strip():
        return []
    if "\n" in command.strip():
        return ["multi-line (cmd parses the first line only)"]
    stripped = command.lstrip()
    if _CMD_INERT_PREFIX.match(stripped):
        return []
    if _NATIVE_SHELL.match(stripped):
        return []
    unquoted = _cmd_unquoted(command)
    return [label for label, pattern in _CMD_UNSAFE if pattern.search(unquoted)]


def _iter_shell_commands(node: object, path: str = "") -> Iterator[tuple[str, str]]:
    """Yield ``(yaml_path, command)`` for every string a shell will receive.

    Shape-agnostic on purpose: hooks and criteria can sit at the document root,
    under ``defaults``, or inside a ``variants`` entry, and a task can carry its
    own ``post_run`` alongside the experiment's.
    """
    if isinstance(node, dict):
        if node.get("type") == "run_command" and isinstance(node.get("command"), str):
            yield f"{path}.command" if path else "command", node["command"]
        for key, value in node.items():
            child = f"{path}.{key}" if path else key
            if key in ("pre_run", "post_run") and isinstance(value, list):
                for n, step in enumerate(value):
                    if isinstance(step, dict) and isinstance(step.get("command"), str):
                        yield f"{child}[{n}].command", step["command"]
            else:
                yield from _iter_shell_commands(value, child)
    elif isinstance(node, list):
        for n, item in enumerate(node):
            yield from _iter_shell_commands(item, f"{path}[{n}]")


def _command_line_number(path: Path, command: str) -> int:
    """1-indexed line where ``command`` starts in the raw file (0 if not found)."""
    first = command.strip().splitlines()[0].strip() if command.strip() else ""
    # The raw YAML may double a backslash that yaml.safe_load collapsed, so fall
    # back to progressively less exact needles rather than giving up on line 0.
    needles = [first, first.split("\\")[0], first[:32]]
    lines = path.read_text(errors="ignore").splitlines()
    for needle in needles:
        needle = needle.strip()
        if len(needle) < 8:
            continue
        for n, line in enumerate(lines, start=1):
            if needle in line:
                return n
    return 0


def _load(path: Path) -> object | None:
    try:
        return yaml.safe_load(path.read_text())
    except yaml.YAMLError:
        # Malformed YAML is another gate's problem; don't mask it as a pass but
        # don't crash this check either.
        return None


def _gate_driver(paths: list[Path], docs: dict[Path, object]) -> int:
    """Gate 1: no task pins ``sandbox.driver: tempdir``."""
    offenders: list[tuple[Path, int]] = []
    docker_pins: list[Path] = []

    for path in paths:
        doc = docs.get(path)
        if not isinstance(doc, dict):
            continue
        sandbox = doc.get("sandbox")
        if not isinstance(sandbox, dict):
            continue
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

    if not offenders:
        print("OK — no task pins `sandbox.driver: tempdir`.")
        return 0

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


def _gate_cmd_safety(paths: list[Path], docs: dict[Path, object]) -> int:
    """Gate 2: every shell command reachable from a Windows runner is cmd-safe."""
    offenders: list[tuple[Path, int, str, list[str]]] = []
    unclassified: list[Path] = []
    checked_files = 0
    checked_commands = 0
    exempted = 0

    for path in paths:
        doc = docs.get(path)
        if not isinstance(doc, dict):
            continue

        is_experiment = "experiment_id" in doc or "variants" in doc
        if is_experiment:
            platform = _EXPERIMENT_PLATFORM.get(path.name)
            if platform is None:
                unclassified.append(path)
                continue
            if platform != "windows-reachable":
                continue
        elif "windows" not in (doc.get("tags") or []):
            continue

        checked_files += 1
        for yaml_path, command in _iter_shell_commands(doc):
            checked_commands += 1
            if _OVERLAY_TRANSLATED.get((path.name, yaml_path)) == command:
                exempted += 1
                continue
            problems = cmd_safety_problems(command)
            if problems:
                offenders.append((path, _command_line_number(path, command), yaml_path, problems))

    if unclassified:
        print(
            f"FAIL — {len(unclassified)} experiment(s) are not classified in "
            "`_EXPERIMENT_PLATFORM`:\n"
        )
        for path in unclassified:
            rel = _rel(path)
            print(f"::error file={rel},line=1::Experiment not classified in _EXPERIMENT_PLATFORM")
            print(f"  {rel}")
        print()
        print(
            "Add it to `_EXPERIMENT_PLATFORM` in scripts/check-task-driver.py as either\n"
            "`windows-reachable` (some workflow or runner script pairs it with a Windows\n"
            "agent, so its hooks must be cmd.exe-safe) or `linux-only`, with a comment\n"
            "saying which. This gate is fail-closed by design: an unclassified experiment\n"
            "is how the 2026-09-04 Windows nightly outage happened."
        )

    if not offenders:
        if not unclassified:
            suffix = f" ({exempted} translated by the Windows overlay)" if exempted else ""
            print(
                f"OK — {checked_commands} Windows-reachable shell command(s) across "
                f"{checked_files} file(s) are cmd.exe-safe{suffix}."
            )
            return 0
        return 1

    print(f"FAIL — {len(offenders)} Windows-reachable shell command(s) are not cmd.exe-safe:\n")
    for path, line, yaml_path, problems in offenders:
        rel = _rel(path)
        loc = f"{rel}:{line}" if line else rel
        detail = ", ".join(problems)
        print(f"::error file={rel},line={line}::{yaml_path} is not cmd.exe-safe: {detail}")
        print(f"  {loc}  ({yaml_path})")
        print(f"    {detail}")
    print()
    print(
        "On Windows these strings go to cmd.exe (%COMSPEC% /c), not sh: pre_run and\n"
        "post_run via asyncio.create_subprocess_shell, run_command criteria via\n"
        "subprocess.run(shell=True). A pre_run that cmd cannot parse ERRORs the task; a\n"
        "run_command criterion silently scores 0, which reads as a model regression.\n"
        "\n"
        "Fix by one of:\n"
        "  - prefix the single-line command with `:; ` so cmd skips it as a label and sh\n"
        "    still runs it (see tests/experiments/nightly.yaml)\n"
        "  - rewrite it as one self-contained `pwsh -NoLogo -NoProfile -NonInteractive\n"
        "    -Command \"...\"` invocation\n"
        "  - use only portable constructs (`&&` and `||` are fine in cmd)\n"
        "\n"
        "Note a command must also be a SINGLE line: cmd parses only the first line, so a\n"
        "YAML `|-` block scalar drops the rest. See the docstring for the full rationale."
    )
    return 1


def main(argv: list[str]) -> int:
    paths = _iter_task_yamls(argv)
    docs = {path: _load(path) for path in paths}
    rc = _gate_driver(paths, docs)
    print()
    rc |= _gate_cmd_safety(paths, docs)
    return 1 if rc else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
