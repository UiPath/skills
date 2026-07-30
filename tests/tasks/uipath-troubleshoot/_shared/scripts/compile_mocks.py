#!/usr/bin/env python3
"""Pack the mock scripts in `_shared/mock_src/` into the staged template.

Each `mock_src/<name>.py` becomes `_shared/mock_template/m/.<name>.bin`:
docstrings are stripped from the AST (comments never survive
`ast.unparse`), the stripped source is zlib-compressed and base64-encoded.
The thin loaders at `mock_template/m/uip` and `m/seal` decode and exec the
blob in memory, so the staged sandbox copy documents nothing about the mock
system — a blob shows a single base64 run to `cat`/`strings` (unlike
bytecode, which keeps every string literal readable) and runs on ANY host
CPython >= 3.10 (the sources' syntax floor; the sandbox resolves `python`
from the host PATH, so the artifact must not care which minor runs it).

Deterministic given the same source and packing interpreter: `ast.unparse`
output is stable within a CPython minor, zlib level 9 and base64 are
deterministic. The canonical committed blobs are produced with CPython
3.13 (the version pinned across the repo's workflows and tests/.venv) so
regenerating unchanged sources is byte-identical and produces no git diff;
the script refuses other minors unless --allow-any-version is passed.

Run after any edit to `mock_src/*.py`:

    uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py
"""

import argparse
import ast
import base64
import sys
import zlib
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = SHARED_DIR / "mock_src"
OUT_DIR = SHARED_DIR / "mock_template" / "m"
PACKING_VERSION = (3, 13)


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

    for src in sources:
        tree = _strip_docstrings(ast.parse(src.read_text(encoding="utf-8")))
        stripped = ast.unparse(tree)
        blob = base64.b64encode(zlib.compress(stripped.encode("utf-8"), 9))
        out = OUT_DIR / f".{src.stem}.bin"
        out.write_bytes(blob)
        print(f"packed {src.name} -> {out.relative_to(SHARED_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
