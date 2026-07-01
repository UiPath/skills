#!/usr/bin/env python3
"""Guard: `uip solution pack` is structurally deterministic.

Packs the fixture solution twice (into isolated temp dirs, so the source is
never mutated) and asserts the two packages are the same once per-pack volatile
values are normalized away. Every pack regenerates fresh GUIDs (packageVersionKey,
resource keys, the files/<guid>/ path segment) and stamps fresh zip timestamps —
those are expected. Anything else that differs is real build nondeterminism that
could mask regressions in other tests, so it fails.

Comparison, after replacing GUIDs -> <GUID> and ISO timestamps -> <TS>:
  - the set of entry paths must match, and
  - the text of every JSON entry must match.
Binary entries (the nested project .nupkg) are compared by normalized path only —
their bytes carry zip timestamps and are not a determinism signal on their own."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")


def normalize(text: str) -> str:
    return TS.sub("<TS>", GUID.sub("<GUID>", text))


repo = os.environ.get("SKILLS_REPO_PATH") or str(Path(__file__).resolve().parents[4])
solution = Path(repo) / "tests" / "fixtures" / "solutions" / "e2e-stub-solution"
if not (solution / "e2e-stub-solution.uipx").is_file():
    sys.exit(f"FAIL: solution fixture not found at {solution}")


def pack_once(tag: str) -> Path:
    work = Path(tempfile.mkdtemp(prefix=f"packdet-{tag}-"))
    src = work / "solution"
    shutil.copytree(solution, src)
    out = work / "out"
    r = subprocess.run(
        ["uip", "solution", "pack", str(src), str(out), "--output", "json"],
        capture_output=True, text=True, timeout=180,
    )
    zips = list(out.glob("*.zip")) if out.is_dir() else []
    if not zips:
        sys.exit(f"FAIL: pack ({tag}) produced no package (exit={r.returncode}, stderr={r.stderr[-300:]})")
    return zips[0]


def fingerprint(zip_path: Path) -> tuple[list[str], dict]:
    """(sorted normalized paths, {normalized json path -> normalized json text})."""
    paths, jsons = [], {}
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            npath = normalize(name)
            paths.append(npath)
            if name.endswith(".json"):
                try:
                    doc = json.loads(z.read(name))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                jsons[npath] = normalize(json.dumps(doc, sort_keys=True, indent=2))
    return sorted(paths), jsons


a_paths, a_json = fingerprint(pack_once("a"))
b_paths, b_json = fingerprint(pack_once("b"))

if a_paths != b_paths:
    only_a = sorted(set(a_paths) - set(b_paths))
    only_b = sorted(set(b_paths) - set(a_paths))
    sys.exit(f"FAIL: package entry lists differ (after id/timestamp normalization). only-in-a={only_a} only-in-b={only_b}")

for name in a_json:
    if a_json[name] != b_json.get(name):
        sys.exit(f"FAIL: JSON entry {name!r} differs between packs after id/timestamp normalization — real nondeterminism")

print(f"OK: pack is deterministic — {len(a_paths)} entries and all JSON match (GUIDs/timestamps normalized)")
