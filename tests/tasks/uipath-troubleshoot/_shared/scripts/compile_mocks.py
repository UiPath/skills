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

Blob layout — a plaintext integrity header followed by the ciphertext:

    bytes 0:4    plaintext length, big-endian
    bytes 4:12   first 8 bytes of sha256(CODE_KEY + plaintext)
    bytes 12:    keystream-encrypted stripped source

Both loaders check the length and the digest before `compile()` and exit with
their "runtime data missing" guard on mismatch, and reject a blob with no
payload at all. A keystream cipher cannot detect damage on its own — XOR happily
decrypts a truncated or flipped blob into garbage — and a mock that fails
quietly would let a scenario grade against evidence that was never served, so
damage MUST be loud. The header is deliberately outside the ciphertext: the
loader has to know the expected length before it can tell a short read from a
short payload.

The digest covers `CODE_KEY` as well as the plaintext, which is what stops a
header being *forged* rather than merely damaged. Over a plaintext alone the
digest is a public constant, so for a tiny payload a search over the ciphertext
byte walks every possible plaintext while the digest of a chosen one (a newline
— `compile()` accepts it and `exec`s to nothing) stays fixed: 256 tries with no
key knowledge produce a blob that passes both checks and exits 0 with no
output, the exact silent-success shape this header exists to eliminate. Keyed,
the required digest is uncomputable without `CODE_KEY`. Damage detection is
unchanged, and this is still integrity rather than authenticity: anyone holding
the key — which the loaders necessarily carry — can forge at will.

`mock_src/*.py` whose name starts with `_` are library modules, not entry
points: they get no blob of their own, and their stripped source is prepended
to every entry point's blob. That keeps a single definition of shared code
while leaving each blob self-contained (the sandbox has no importable copy of
`mock_src/`), and keeps `DATA_KEY` — which lives in `_cipher.py` — out of
every plaintext file staged into a sandbox.

Two constraints follow from prepending rather than importing:

- **No entry point may use `from __future__ import ...`.** Such an import has
  to be the first statement in a module, and the prelude now sits ahead of it.
  The packer compiles the combined source and fails loudly if this happens,
  rather than letting the SyntaxError surface only in a sandbox.
- **Library modules must not depend on each other at module level.** They are
  concatenated in a fixed order (by lowercased filename) into one namespace,
  with no import machinery to resolve a cycle or a forward reference. Sorting
  is explicitly case-insensitive because bare `sorted()` on `Path` is
  case-insensitive on Windows and case-sensitive on POSIX, which would order a
  second library module differently per platform and break byte-stability.

Deterministic given the same source and packing interpreter: `ast.unparse`
output is stable within a CPython minor, and the cipher is unsalted. The
canonical committed blobs are produced with CPython 3.13 (the version pinned
across the repo's workflows and tests/.venv) so regenerating unchanged
sources is byte-identical and produces no git diff; the script refuses other
minors unless --allow-any-version is passed.

`CODE_KEY` is duplicated as a byte literal in the two loaders, which must
decrypt without importing anything from this repo. That duplication cannot
detect itself: `_pack` and `_unpack` both read the constant below, so a packer
that disagrees with a loader still packs and round-trips cleanly at exit 0, and
the mismatch surfaces only when the mock runs — as the loader's "runtime data
missing" guard, far from the edit that caused it. So the packer reads the
32-byte literal out of each entry point's loader and refuses to pack when it
differs from `CODE_KEY`.

Run after any edit to `mock_src/*.py`:

    uv run --python 3.13 tests/tasks/uipath-troubleshoot/_shared/scripts/compile_mocks.py
"""

import argparse
import ast
import hashlib
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
from _cipher import code_seed, xor_stream


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


HEADER_LEN = 12


def _pack(stripped: str, name: str) -> bytes:
    """Encrypt `stripped` and prefix the integrity header. See module docstring."""
    plain = stripped.encode("utf-8")
    header = len(plain).to_bytes(4, "big") + hashlib.sha256(CODE_KEY + plain).digest()[:8]
    return header + xor_stream(plain, code_seed(CODE_KEY, name))


def _unpack(blob: bytes, name: str) -> bytes | None:
    """Reverse `_pack`, or None if the header does not match — mirrors the loaders."""
    if len(blob) <= HEADER_LEN:
        return None
    plain = xor_stream(blob[HEADER_LEN:], code_seed(CODE_KEY, name))
    if len(plain) != int.from_bytes(blob[:4], "big"):
        return None
    if hashlib.sha256(CODE_KEY + plain).digest()[:8] != blob[4:HEADER_LEN]:
        return None
    return plain


def _loader_key(loader: Path) -> bytes | None:
    """Return the 32-byte key literal the loader at `loader` decrypts with.

    The loaders spell the key as adjacent escaped byte literals, which the
    parser folds into one constant, so the first 32-byte `bytes` constant in the
    file is it. None when the file has no such constant.
    """
    for node in ast.walk(ast.parse(loader.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Constant) and isinstance(node.value, bytes) and len(node.value) == 32:
            return node.value
    return None


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

    # Sort on the lowercased filename, not on Path: Path ordering is
    # case-insensitive on Windows and case-sensitive on POSIX, so a second
    # library module could be prepended in a different order per platform and
    # silently produce different blob bytes on each.
    sources = sorted(SRC_DIR.glob("*.py"), key=lambda s: s.name.lower())
    if not sources:
        return f"compile_mocks: no sources found under {SRC_DIR}"

    libs = [s for s in sources if s.stem.startswith("_")]
    entries = [s for s in sources if not s.stem.startswith("_")]
    if not entries:
        return f"compile_mocks: no entry points found under {SRC_DIR}"

    prelude = [_stripped_source(s) for s in libs]

    # Build every blob first, write nothing until all of them pass. The blobs
    # are a matched set — `m/seal` writes the runtime data files that `m/uip`
    # reads — so writing one and then failing on the next would leave a stale
    # blob paired with a fresh one behind an "it failed" exit code.
    outputs: list[tuple[Path, bytes, str]] = []
    for src in entries:
        loader = OUT_DIR / src.stem
        if not loader.is_file():
            return f"compile_mocks: {src.name} has no loader at {loader.relative_to(SHARED_DIR)}."
        if _loader_key(loader) != CODE_KEY:
            return (
                f"compile_mocks: {loader.relative_to(SHARED_DIR)} decrypts with a different key "
                "than this packer's CODE_KEY. Blobs packed now would fail that loader's integrity "
                "check at mock runtime; align the two before packing."
            )

        entry = _stripped_source(src)
        if not entry:
            return f"compile_mocks: {src.name} strips to nothing; there is no entry point to pack."
        stripped = "\n".join(prelude + [entry])

        # The combined source is what the sandbox executes, and a blob that
        # cannot compile only fails there. Prepending the prelude can break an
        # entry point that compiles fine on its own — a `from __future__`
        # import, which must be the first statement in a module, is the case
        # that bites. Catch it here instead.
        try:
            compile(stripped, src.name, "exec")
        except SyntaxError as exc:
            return (
                f"compile_mocks: {src.name} does not compile once the prelude is "
                f"prepended: {exc.msg} (line {exc.lineno}). A `from __future__ import ...` "
                "in an entry point cannot survive the prepend - remove it, or move the "
                "code needing it into a library module."
            )

        blob = _pack(stripped, src.stem)
        if _unpack(blob, src.stem) != stripped.encode("utf-8"):
            return f"compile_mocks: {src.name} failed its own round-trip; refusing to write."
        outputs.append((OUT_DIR / f".{src.stem}.bin", blob, src.name))

    inlined = f" (+{', '.join(s.name for s in libs)})" if libs else ""
    for out, blob, name in outputs:
        out.write_bytes(blob)
        print(f"packed {name}{inlined} -> {out.relative_to(SHARED_DIR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
