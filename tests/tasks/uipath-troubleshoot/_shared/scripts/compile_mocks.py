#!/usr/bin/env python3
"""Pack the mock scripts in `_shared/mock_src/` into the staged template.

Each entry-point `mock_src/<name>.py` becomes
`_shared/mock_template/m/.<name>.bin`: docstrings are stripped from the AST
(comments never survive `ast.unparse`), and the stripped source is encrypted
under `CODE_KEY` with the keystream cipher in `mock_src/_cipher.py`. Output is
binary. The thin loaders at `mock_template/m/uip` and `m/seal` decrypt and
exec the blob in memory, so the staged sandbox copy documents nothing about
the mock system — a blob shows only high-entropy bytes to `cat`/`strings`
(unlike bytecode, which keeps every string literal readable) and runs on ANY
host CPython >= 3.10 (the sources' syntax floor; the sandbox resolves
`python` from the host PATH, so the artifact must not care which minor runs
it).

`mock_src/*.py` whose name starts with `_` are library modules, not entry
points: they get no blob of their own, and their stripped source is prepended
to every entry point's blob. That keeps a single definition of shared code
while leaving each blob self-contained (the sandbox has no importable copy of
`mock_src/`), and keeps `DATA_KEY` — which lives in `_cipher.py` — reachable
only from inside a `CODE_KEY`-encrypted blob.

Deterministic given the same source and packing interpreter: `ast.unparse`
output is stable within a CPython minor, and the cipher is unsalted. The
canonical committed blobs are produced with CPython 3.13 (the version pinned
across the repo's workflows and tests/.venv) so regenerating unchanged
sources is byte-identical and produces no git diff; the script refuses other
minors unless --allow-any-version is passed.

`CODE_KEY` is duplicated as a byte literal in the two loaders, which must
decrypt without importing anything from this repo. Change it in one place and
the round-trip breaks loudly on the next run.

Run after any edit to `mock_src/*.py`:

    uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py
"""

import argparse
import ast
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SHARED_DIR / "mock_src"
OUT_DIR = SHARED_DIR / "mock_template" / "m"
PACKING_VERSION = (3, 13)

# Code-blob key. Mirrored as a byte literal in `mock_template/m/uip` and
# `m/seal`, which is why it is deliberately NOT `_cipher.DATA_KEY`: the
# loaders are plaintext in the sandbox, so anything they hold is readable
# there. See `mock_src/_cipher.py`.
CODE_KEY = bytes.fromhex("a49e38198e6c9bf1a90d8ad12dc121f5c59994f28c85ec6d44ab92adf2d2a116")

# Import the cipher from the sources being packed, so packer and runtime can
# never drift onto different transforms. Late by necessity: SRC_DIR has to be
# on the path first. `dont_write_bytecode` keeps a `__pycache__` out of
# `mock_src/`, which would otherwise show up as untracked repo noise.
sys.dont_write_bytecode = True
sys.path.insert(0, str(SRC_DIR))
from _cipher import xor_stream


def _strip_docstrings(tree: ast.Module) -> ast.Module:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body.pop(0)
            if not body:
                body.append(ast.Pass())
    return tree


def _stripped_source(path: Path) -> str:
    return ast.unparse(_strip_docstrings(ast.parse(path.read_text(encoding="utf-8"))))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--allow-any-version",
        action="store_true",
        help="pack with the running interpreter even if it is not the canonical 3.13",
    )
    args = parser.parse_args()

    if sys.version_info[:2] != PACKING_VERSION and not args.allow_any_version:
        return (
            f"compile_mocks: pack with CPython {'.'.join(map(str, PACKING_VERSION))} for "
            f"byte-stable output (running {sys.version.split()[0]}); e.g. "
            "`uv run --python 3.13 ...`, or pass --allow-any-version."
        )

    sources = sorted(SRC_DIR.glob("*.py"))
    if not sources:
        return f"compile_mocks: no sources found under {SRC_DIR}"

    libs = [s for s in sources if s.stem.startswith("_")]
    entries = [s for s in sources if not s.stem.startswith("_")]
    if not entries:
        return f"compile_mocks: no entry points found under {SRC_DIR}"

    prelude = [_stripped_source(s) for s in libs]
    for src in entries:
        stripped = "\n".join(prelude + [_stripped_source(src)])
        blob = xor_stream(stripped.encode("utf-8"), CODE_KEY)
        out = OUT_DIR / f".{src.stem}.bin"
        out.write_bytes(blob)
        inlined = f" (+{', '.join(s.name for s in libs)})" if libs else ""
        print(f"packed {src.name}{inlined} -> {out.relative_to(SHARED_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
