"""Keystream cipher shared by the mock scripts and their packer.

Two independent keys, with different blast radii:

`CODE_KEY` (in `scripts/compile_mocks.py` and, as a byte literal, in the
`mock_template/m/uip` + `m/seal` loaders) covers the packed code blobs
`m/.uip.bin` / `m/.seal.bin`. The loaders must run unaided in the sandbox, so
this key is necessarily present there in plaintext.

`DATA_KEY` below covers the runtime data files the mock writes beside itself:
the sealed fixture store `.store`, the call log `.log`, and the passthrough
cache `_cache/*.json`. It is defined only in `mock_src/`, which is never
staged, so no plaintext file staged into a sandbox carries it.

Keys are unrelated values; neither is derivable from the other. That is not a
containment claim, and the split does not put `DATA_KEY` behind `CODE_KEY`.
What the two layers actually buy is stated below.

What this protects, measured:

No file staged into a sandbox states its own encoding: the loaders name no
transform, and `grep`-ing the staged tree for `base64` / `zlib` / `compress`
turns up nothing. Recovering the fixture archive is therefore a deliberate
reverse-engineering exercise — read a loader, reproduce its keystream,
decrypt its blob, lift `DATA_KEY` out of the recovered source, then decrypt
`.store` — rather than copying a two-line recipe out of a small plaintext
file. Raising that cost is the entire benefit, and it is worth having.

It is NOT confidentiality, and NOT a boundary. `CODE_KEY` is a byte literal in
each loader (spelled as two adjacent literals, which Python concatenates)
because the loaders must run unaided; the plaintext a loader decrypts to
defines `DATA_KEY` within its first three lines, since the `_cipher.py` prelude
leads every blob. So reproducing the keystream and reaching the data key is
about fifteen lines of standard library over files the sandbox already holds —
no planted module, no `PYTHONPATH`, no `sitecustomize` needed. Anyone who reads
a loader can reach the data key. Treat every key here as recoverable and design
accordingly.

Detection of answer-key reads is the control that actually holds. This layer
only raises cost.

Known residual, stated rather than fixed: a `sitecustomize.py` planted on
`PYTHONPATH` executes at interpreter startup, before a loader's first line, so
no loader-side change can close it — the only levers are outside the loader
(`-E`, or scrubbing the environment). It is left open because it grants nothing
beyond the ceiling above: the keys are already reachable by reading a staged
loader.

The transform is a chained-SHA-256 keystream XORed over the payload: the key
is hashed repeatedly, each digest supplying the next 32 keystream bytes.
Standard library only (`hashlib`, `zlib`) — the sandbox guarantees no
third-party packages. Symmetric, so the same call both seals and opens.
Deterministic: no salt, no nonce, no timestamp, so repacking or re-sealing
identical input yields identical bytes.

Not a confidentiality boundary — a reader who has the key can reverse it.
It exists to make the staged artifacts opaque to inspection that stops short of
reverse-engineering a loader.

The transform provides no integrity of its own: XOR decrypts damaged input
into garbage just as willingly as intact input. Anything that stores a
keystream-encrypted payload MUST therefore be framed so damage is loud rather
than silently yielding empty or partial data. The two layers frame it
differently:

- Data payloads are compressed before encryption, and a zlib stream is its own
  frame — it carries an Adler-32 over the plaintext and refuses an incomplete
  stream — so `data_open` raises on a truncated or flipped payload.
- The code blobs are raw source with no compression (a `zlib` token in a
  loader would hand the sandbox the recipe), so they carry an explicit length +
  digest header instead. `scripts/compile_mocks.py` documents it.

Each purpose gets its own keystream, seeded `sha256(DATA_KEY + purpose)`, so
recovering the keystream of one file kind reveals nothing about another — the
store does not become readable because the call log was cracked. Payloads
sharing a purpose (every record in `.log`, every entry in `_cache`) do share a
keystream; the exposure is bounded to those files' own contents, which the
agent's own invocations largely dictate anyway. This bounds keystream reuse
only. It is not containment: `DATA_KEY` itself derives every purpose's seed, so
whoever recovers the key from a loader gets all of them at once.
"""

import hashlib
import zlib

# Runtime data key (`.store`, `.log`, `_cache`). Never leaves `mock_src/`.
DATA_KEY = bytes.fromhex("1cd3e2ed9ea4329dd0a8771a7bc7a3297b63b6387f7e80314f6ed5e32f6fa3c1")


def keystream(key: bytes, n: int) -> bytes:
    """Return `n` keystream bytes for `key` (chained SHA-256 digests)."""
    out = bytearray()
    block = key
    while len(out) < n:
        block = hashlib.sha256(block).digest()
        out += block
    return bytes(out[:n])


def xor_stream(data: bytes, key: bytes) -> bytes:
    """XOR `data` with `key`'s keystream. Symmetric: seals and opens."""
    return bytes(a ^ b for a, b in zip(data, keystream(key, len(data))))


def code_seed(key: bytes, name: str) -> bytes:
    """Per-blob keystream seed for the code blob named `name`.

    Every code blob starts with the same inlined library prelude. Keying them
    all on `CODE_KEY` alone would therefore give every blob an identical
    ciphertext prefix as long as that prelude, which advertises both that the
    blobs share a plaintext head and how long it is. Binding the seed to the
    blob's own name removes the shared prefix.
    """
    return hashlib.sha256(key + name.encode("utf-8")).digest()


def data_seed(purpose: str) -> bytes:
    """Keystream seed for the data files of one `purpose` (`store`/`log`/`cache`)."""
    return hashlib.sha256(DATA_KEY + purpose.encode("utf-8")).digest()


def data_seal(raw: bytes, purpose: str) -> bytes:
    """Compress and encrypt `raw` for `purpose`. Output is binary."""
    return xor_stream(zlib.compress(raw, 9), data_seed(purpose))


def data_open(blob: bytes, purpose: str) -> bytes:
    """Inverse of `data_seal`. Raises `ValueError` when the zlib frame rejects
    the payload — truncated, flipped, or encrypted for another purpose. Bytes
    appended after a complete frame are ignored rather than reported, so this
    does not raise on every possible alteration.
    """
    try:
        return zlib.decompress(xor_stream(blob, data_seed(purpose)))
    except zlib.error as exc:
        raise ValueError(f"damaged {purpose} payload") from exc


def line_seal(text: str, purpose: str) -> str:
    """`data_seal` for one line of a line-oriented file: hex, no newlines."""
    return data_seal(text.encode("utf-8"), purpose).hex()


def line_open(line: str, purpose: str) -> str:
    """Inverse of `line_seal`. Raises `ValueError` on a damaged line."""
    return data_open(bytes.fromhex(line.strip()), purpose).decode("utf-8")
