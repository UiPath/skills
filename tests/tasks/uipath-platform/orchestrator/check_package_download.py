#!/usr/bin/env python3
"""Verify pkg.nupkg exists locally with PK\\x03\\x04 magic bytes."""

import sys
from pathlib import Path


p = Path("pkg.nupkg")
if not p.is_file():
    sys.exit("FAIL: pkg.nupkg not present in sandbox")

size = p.stat().st_size
if size <= 4:
    sys.exit(f"FAIL: pkg.nupkg size={size}, too small to be a real package")

with open(p, "rb") as f:
    magic = f.read(4)
if magic != b"PK\x03\x04":
    sys.exit(f"FAIL: pkg.nupkg first bytes = {magic!r}, expected b'PK\\x03\\x04' (zip magic)")

print(f"OK: pkg.nupkg present ({size} bytes), valid zip magic")
