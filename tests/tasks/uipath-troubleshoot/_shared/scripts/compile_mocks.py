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

Before importing anything but `sys`, each loader deletes `sys.path[0]` and then
keeps only the entries under `sys.base_prefix` / `sys.base_exec_prefix`. That is
load-bearing. `sys.path[0]` is the script's own directory for a script
invocation, and `""` or the cwd under `-c` / `-m`; the sandbox can write to the
mock directory, and `PYTHONPATH` entries sit immediately behind that first entry
in the search order. Without the filter a module planted under a standard-library
name is imported in preference to the real one — by the loader, and by the blob
it execs — which hands the sandbox the mock's own behaviour: `hashlib` is the
sharpest case, since the loader hashes the decrypted source and a wrapper would
see it whole, and a planted `json` or `pathlib` sits between the dispatcher and
the fixtures it serves.

State what the filter drops accurately: every entry outside the interpreter's own
base prefixes — the script directory, the cwd, per-user site, and `PYTHONPATH`
*except* an entry nested inside a base prefix, which is retained like any other
path under it. It does NOT drop `PYTHONPATH` unconditionally. The venv prefixes
are deliberately not in the comparison: a `sys.prefix` / `sys.exec_prefix` tree is
agent-writable, so including them retains anything planted under a venv, and the
mock needs nothing from a venv's `site-packages` — it imports only the standard
library.

Three details of the comparison each carry weight:

- **Component-anchored, not a bare string prefix.** Each prefix is compared with
  a trailing separator against the candidate plus one, so `C:\\Py311` does not
  admit a sibling `C:\\Py311-evil`.
- **Never fail open.** One empty prefix value would make a bare `startswith` true
  for every entry and silently reduce the filter to a no-op, so the tuple is
  built from truthy values only and an empty tuple exits.
- **Case-folded only where the filesystem folds.** The loaders mirror
  `os.path.normcase` — lowercase plus a `\\`→`/` rewrite on `win32`, identity
  elsewhere — but select that from `sys.platform` instead of importing `os`,
  which is as shadowable as anything else before the filter has run. Folding
  unconditionally would equate two distinct paths on a case-sensitive filesystem.

Verified on CPython 3.10-3.14, Windows and Linux, inside and outside a virtualenv,
to leave the stdlib zip and `DLLs`/`Lib` (`lib-dynload` / `dist-packages` on
Linux) in place — plus the base install's own `site-packages`, while a venv's
`site-packages` is dropped along with the rest of the venv tree.

The filter is about import integrity, not key confidentiality, and it does not
make `DATA_KEY` unreachable. `mock_src/_cipher.py` states the measured ceiling:
`CODE_KEY` is a byte literal in every loader, and the plaintext a loader decrypts
to defines `DATA_KEY` in its first three lines, so reading a staged loader is
already enough. Read that section before adding any claim about what these layers
withhold.

These lines carry no comment on purpose: they are staged into the sandbox
verbatim, and prose explaining what they defend against is prose describing what
to attack. Do not "tidy" them away, and do not add an import above them.

`mock_src/*.py` whose name starts with `_` are library modules, not entry
points: they get no blob of their own, and their stripped source is prepended
to every entry point's blob. That keeps a single definition of shared code
while leaving each blob self-contained (the sandbox has no importable copy of
`mock_src/`), and keeps `DATA_KEY` — which lives in `_cipher.py` — out of
every *plaintext* file staged into a sandbox. Out of the plaintext only: the
prelude leads every blob, so `DATA_KEY` is among the first lines of what a blob
decrypts to. See `mock_src/_cipher.py` for what that does and does not buy.

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

Every value a loader has to agree with this packer about is duplicated in the
loader as a literal, because a loader must decrypt without importing anything
from this repo. That duplication cannot detect itself: `_pack` and `_unpack` both
read the packer's own constants, so a packer that disagrees with a loader still
packs and round-trips cleanly at exit 0, and the mismatch surfaces only when the
mock runs — as the loader's "runtime data missing" guard, far from the edit that
caused it. Three values must therefore be checked against the loader before
packing, all read in one AST pass (`_loader_literals`):

- **`CODE_KEY`** — among the loader's 32-byte `bytes` literals.
- **The blob's own name** (`code_seed(CODE_KEY, src.stem)` binds each keystream
  to it) — among the loader's short `bytes` literals. Checking the key alone is
  not enough: a new entry point whose loader keeps `b"uip"` derives the wrong
  keystream and decrypts to garbage, which is a runtime failure the round-trip
  here cannot see, because the packer round-trips against its OWN seed.
- **`.<name>.bin`** — among the loader's `str` literals, so a loader that
  decrypts correctly but reads another blob's file is caught too.

Any of the three missing is a refusal, not a warning.

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


def _loader_literals(loader: Path) -> tuple[list[bytes], set[bytes], set[str]]:
    """Return the loader's 32-byte `bytes` constants, its short `bytes`
    constants, and its `str` constants.

    Three things the packer has to agree with the loader about, all readable
    from one AST pass: the key (32 bytes), the keystream seed's name suffix (a
    short `bytes` literal), and the blob filename (a `str`).

    Membership, not position: `ast.walk` yields breadth-first rather than in
    source order, so "the first 32-byte constant" is not a thing a caller can
    rely on, and any other 32-byte literal in the file would outrank the key and
    be reported as a key mismatch. Asking whether `CODE_KEY` is present has no
    ordering dependency and still catches drift — a flipped literal means the
    key is absent from the list. It does not catch a key spelled as anything
    other than a `bytes` literal (`bytes.fromhex(...)`, say), which is why an
    empty list is reported as its own failure rather than as a mismatch. The
    same holds for the other two: a name or filename assembled by expression
    rather than written as a literal reads as absent, and is reported as drift.

    Adjacent literals are already joined by the parser, so the key spelled as
    two 16-byte literals arrives here as one 32-byte constant and no 16-byte
    fragment is ever collected as a "short" one.
    """
    keys: list[bytes] = []
    names: set[bytes] = set()
    texts: set[str] = set()
    for node in ast.walk(ast.parse(loader.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, bytes):
            if len(node.value) == 32:
                keys.append(node.value)
            elif len(node.value) < 32:
                names.add(node.value)
        elif isinstance(node.value, str):
            texts.add(node.value)
    return keys, names, texts


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
        keys, names, texts = _loader_literals(loader)
        if not keys:
            return (
                f"compile_mocks: {loader.relative_to(SHARED_DIR)} holds no 32-byte bytes literal, so "
                "its key cannot be read. The loader must spell CODE_KEY as escaped bytes for this "
                "check to compare it against the packer's."
            )
        if CODE_KEY not in keys:
            return (
                f"compile_mocks: {loader.relative_to(SHARED_DIR)} decrypts with a different key "
                "than this packer's CODE_KEY. Blobs packed now would fail that loader's integrity "
                "check at mock runtime; align the two before packing."
            )
        if src.stem.encode("utf-8") not in names:
            return (
                f"compile_mocks: {loader.relative_to(SHARED_DIR)} does not seed its keystream with "
                f"{src.stem!r}, so it derives a different keystream than this packer does for "
                f"{src.name}. Its decrypt would produce garbage and fail the integrity header at "
                "mock runtime; align the two before packing."
            )
        if f".{src.stem}.bin" not in texts:
            return (
                f"compile_mocks: {loader.relative_to(SHARED_DIR)} names no '.{src.stem}.bin', so it "
                f"does not read the blob this packer writes for {src.name}; align the two before "
                "packing."
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
