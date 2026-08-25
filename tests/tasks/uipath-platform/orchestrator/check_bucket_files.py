#!/usr/bin/env python3
"""Query tenant: bucket exists with the expected file; local source==downloaded."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def uip_json(*args: str) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} no stdout")
    return json.loads(r.stdout)


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
folder_path = seed.get("folder_a_path")
if not (uuid8 and folder_path):
    sys.exit("FAIL: seed.json missing uuid8 or folder_a_path")

expected_bucket = f"e2e-bucket-{uuid8}"

# 1) Local sha256 round-trip (file existence + byte equality)
for f in ("source.bin", "downloaded.bin"):
    if not Path(f).is_file():
        sys.exit(f"FAIL: {f} not present in sandbox")
src_sha = sha256_of("source.bin")
dl_sha = sha256_of("downloaded.bin")
if src_sha != dl_sha:
    sys.exit(f"FAIL: sha256 mismatch — source={src_sha[:12]}… downloaded={dl_sha[:12]}…")

# 2) Tenant: bucket exists in folder
env = uip_json("or", "buckets", "list", "--folder-path", folder_path)
if env.get("Result") != "Success":
    sys.exit(f"FAIL: buckets list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
match = next((b for b in items if _pick(b, "Name") == expected_bucket), None)
if not match:
    sys.exit(f"FAIL: bucket {expected_bucket!r} not in folder {folder_path!r}")
# Bucket envelopes expose `identifier` (GUID string), NOT a Key — and `id` is numeric.
bucket_key = _pick(match, "Identifier") or _pick(match, "Key")

# 3) Tenant: bucket contains ≥1 file
flist = uip_json("or", "bucket-files", "list", bucket_key, "--folder-path", folder_path)
if flist.get("Result") != "Success":
    sys.exit(f"FAIL: bucket-files list Result={flist.get('Result')!r}")
fdata = flist.get("Data") or []
if isinstance(fdata, dict):
    fdata = _pick(fdata, "Items", "Value", "Results", "Files") or []
if not fdata:
    sys.exit(f"FAIL: bucket {expected_bucket!r} contains no files")

print(f"OK: bucket {expected_bucket!r} exists with {len(fdata)} file(s); sha256 round-trip verified ({src_sha[:12]}…)")
