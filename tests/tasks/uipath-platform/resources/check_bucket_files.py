#!/usr/bin/env python3
"""Verify bucket round-trip: sha256 byte-equality, file listed in bucket, sizes match."""

import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name: str) -> dict:
    p = Path(name)
    if not p.is_file():
        sys.exit(f"FAIL: {name} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {name} is not valid JSON: {e}")


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


for f in ("source.bin", "downloaded.bin"):
    if not Path(f).is_file():
        sys.exit(f"FAIL: {f} not found")

src_sha = sha256_of("source.bin")
dl_sha = sha256_of("downloaded.bin")
if src_sha != dl_sha:
    sys.exit(f"FAIL: sha256 mismatch — source={src_sha} downloaded={dl_sha}")

src_size = os.path.getsize("source.bin")
dl_size = os.path.getsize("downloaded.bin")
if src_size != dl_size:
    sys.exit(f"FAIL: size mismatch — source={src_size} downloaded={dl_size}")

# Verify list contained the uploaded file
lst = load("list.json")
if lst.get("Result") != "Success":
    sys.exit(f"FAIL: list.json Result={lst.get('Result')!r}")
data = lst.get("Data")
if isinstance(data, dict):
    items = _pick(data, "Items", "Value", "Results", "Files") or []
elif isinstance(data, list):
    items = data
else:
    items = []
names = [_pick(it, "FullPath", "Path", "Name") for it in items if isinstance(it, dict)]
if not any(name and "probe.bin" in name for name in names):
    sys.exit(f"FAIL: list.json does not contain probe.bin — saw: {names}")

print(f"OK: sha256 match ({src_sha[:12]}…), size={src_size}B, file 'probe.bin' present in bucket listing")
