#!/usr/bin/env python3
"""Compile the mock scripts in `_shared/mock_src/` into the staged template.

Each `mock_src/<name>.py` is compiled to `_shared/mock_template/m/.<name>.bin`
(pyc-format bytecode under a neutral filename — `__pycache__/` and `*.pyc`
are stripped by the sandbox template copy's default ignore patterns AND by
this repo's .gitignore, so the idiomatic names can neither be committed nor
staged) with:

    - `optimize=2` — docstrings dropped (comments never reach bytecode), so
      the staged sandbox copy documents nothing about the mock system.
    - `invalidation_mode=UNCHECKED_HASH` — the header embeds the source hash
      instead of an mtime, so output is deterministic: recompiling unchanged
      sources is byte-identical and produces no git diff.
    - `dfile=<name>` — bare name in tracebacks, no contributor paths.

The thin loaders at `mock_template/m/uip` and `m/seal` run the matching
`.bin` via `SourcelessFileLoader`, which accepts pyc-format bytecode under
any filename and rejects a magic-number mismatch — that rejection is the
version guard. The committed bytecode is pinned to CPython 3.13, the
interpreter every executing environment runs (the coder-eval-agent image is
python:3.13-slim; tests/.venv and the CI workflows pin 3.13). On any other
interpreter the loaders exit 1 with a clear error. This script refuses other
versions too, so a stray local run cannot commit bytecode the sandboxes
cannot load; pass --allow-any-version only when deliberately targeting a
different interpreter.

Run after any edit to `mock_src/*.py`:

    uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py
"""

import argparse
import py_compile
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SHARED_DIR / "mock_src"
OUT_DIR = SHARED_DIR / "mock_template" / "m"
REQUIRED_VERSION = (3, 13)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--allow-any-version", action="store_true")
    args = parser.parse_args()

    running = sys.version_info[:2]
    if running != REQUIRED_VERSION and not args.allow_any_version:
        return (
            f"compile_mocks: requires Python {'.'.join(map(str, REQUIRED_VERSION))} "
            f"(running {sys.version.split()[0]}); use --allow-any-version to override"
        )

    sources = sorted(SRC_DIR.glob("*.py"))
    if not sources:
        return f"compile_mocks: no sources found under {SRC_DIR}"

    for src in sources:
        out = OUT_DIR / f".{src.stem}.bin"
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


if __name__ == "__main__":
    sys.exit(main())
