"""Keystream cipher shared by the mock scripts and their packer.

Two independent keys, with different blast radii:

`CODE_KEY` (in `scripts/compile_mocks.py` and, as a byte literal, in the
`mock_template/m/uip` + `m/seal` loaders) covers the packed code blobs
`m/.uip.bin` / `m/.seal.bin`. The loaders must run unaided in the sandbox, so
this key is necessarily present there in plaintext.

`DATA_KEY` below covers the runtime data files the mock writes beside itself
(`.store`, `.log`, `_cache`). It is defined only in `mock_src/`, which reaches
the sandbox exclusively inside the `CODE_KEY`-encrypted blobs, so no plaintext
file staged into a sandbox carries it.

Keys are unrelated values; neither is derivable from the other.

The transform is a chained-SHA-256 keystream XORed over the payload: the key
is hashed repeatedly, each digest supplying the next 32 keystream bytes.
Standard library only (`hashlib`, `zlib`) — the sandbox guarantees no
third-party packages. Symmetric, so the same call both seals and opens.
Deterministic: no salt, no nonce, no timestamp, so repacking or re-sealing
identical input yields identical bytes.

Not a confidentiality boundary — a reader who has the key can reverse it.
It exists to make the staged artifacts opaque to casual inspection.

The transform provides no integrity of its own: XOR decrypts damaged input
into garbage just as willingly as intact input. Anything that stores a
keystream-encrypted payload MUST carry its own length + digest header and
refuse a payload that fails it, so corruption is loud instead of silently
yielding empty or partial data. `scripts/compile_mocks.py` documents the
header the code blobs use.
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


def data_seal(raw: bytes) -> bytes:
    """Compress and encrypt `raw` under `DATA_KEY`. Output is binary."""
    return xor_stream(zlib.compress(raw, 9), DATA_KEY)


def data_open(blob: bytes) -> bytes:
    """Inverse of `data_seal`."""
    return zlib.decompress(xor_stream(blob, DATA_KEY))


def line_seal(text: str) -> str:
    """`data_seal` for one line of a line-oriented file: hex, no newlines."""
    return data_seal(text.encode("utf-8")).hex()


def line_open(line: str) -> str:
    """Inverse of `line_seal`."""
    return data_open(bytes.fromhex(line.strip())).decode("utf-8")
