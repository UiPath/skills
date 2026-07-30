#!/usr/bin/env python3
"""Compile the mock scripts in `_shared/mock_src/` into the staged template.

Each `mock_src/<name>.py` is compiled per supported interpreter to
`_shared/mock_template/m/.<name>.<maj><min>.bin` (pyc-format bytecode under
neutral filenames — `__pycache__/` and `*.pyc` are stripped by the sandbox
template copy's default ignore patterns AND by this repo's .gitignore, so
the idiomatic names can neither be committed nor staged) with:

    - `optimize=2` — docstrings dropped (comments never reach bytecode), so
      the staged sandbox copy documents nothing about the mock system.
    - `invalidation_mode=UNCHECKED_HASH` — the header embeds the source hash
      instead of an mtime, so output is deterministic: recompiling unchanged
      sources is byte-identical and produces no git diff.
    - `dfile=<name>` — bare name in tracebacks, no contributor paths.

CPython bytecode loads only on the minor version that compiled it, and the
sandbox resolves `python` from the host PATH — so the template ships one
`.bin` per supported version (3.10–3.14; the floor is the sources' syntax,
`dict | None` signature annotations). The thin loaders at
`mock_template/m/uip` and `m/seal` pick the `.bin` matching the running
interpreter via `SourcelessFileLoader` (accepts pyc-format bytecode under
any filename; rejects a magic mismatch) and exit 1 with a clear error
outside the range. When a new CPython minor ships, add it to
SUPPORTED_VERSIONS here and in the loaders' error text, then recompile.

Run after any edit to `mock_src/*.py` (uv fetches missing interpreters):

    python tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py --all

Or compile just the running interpreter's slice: run without flags on any
supported version.
"""

import argparse
import py_compile
import subprocess
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SHARED_DIR / "mock_src"
OUT_DIR = SHARED_DIR / "mock_template" / "m"
SUPPORTED_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


def compile_for_running_interpreter() -> int:
    running = f"{sys.version_info[0]}.{sys.version_info[1]}"
    sources = sorted(SRC_DIR.glob("*.py"))
    if not sources:
        return f"compile_mocks: no sources found under {SRC_DIR}"
    for src in sources:
        out = OUT_DIR / f".{src.stem}.{running.replace('.', '')}.bin"
        py_compile.compile(
            str(src),
            cfile=str(out),
            dfile=src.stem,
            doraise=True,
            optimize=2,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        print(f"compiled {src.name} -> {out.relative_to(SHARED_DIR)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--all",
        action="store_true",
        help="compile every supported version via `uv run --python <ver>`",
    )
    parser.add_argument(
        "--allow-any-version",
        action="store_true",
        help="compile for the running interpreter even outside the supported range",
    )
    args = parser.parse_args()

    if args.all:
        for version in SUPPORTED_VERSIONS:
            subprocess.run(
                ["uv", "run", "--no-project", "--python", version, __file__],
                check=True,
            )
        return 0

    running = f"{sys.version_info[0]}.{sys.version_info[1]}"
    if running not in SUPPORTED_VERSIONS and not args.allow_any_version:
        return (
            f"compile_mocks: Python {sys.version.split()[0]} is outside the supported "
            f"range ({', '.join(SUPPORTED_VERSIONS)}); shipping its bytecode would break "
            "the sandboxes. Use --allow-any-version to override."
        )
    return compile_for_running_interpreter()


if __name__ == "__main__":
    sys.exit(main())
