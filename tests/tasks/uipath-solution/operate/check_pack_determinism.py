#!/usr/bin/env python3
"""Guard: `uip solution pack` is structurally deterministic.

Fingerprints the two packages the AGENT packed into the working directory and
asserts they are the same once per-pack volatile values are normalized away.
Every pack regenerates fresh GUIDs (packageVersionKey, resource keys, the
files/<guid>/ path segment) and stamps fresh zip timestamps — those are
expected. Anything else that differs is real build nondeterminism that could
mask regressions in other tests, so it fails.

Deliberately does NOT re-run `uip solution pack` here: the grading subprocess
resolves the CLI's tool packages from its own environment, not the agent's, so
a grade-time pack can fail for tool-resolution reasons unrelated to determinism
(nightly 2026-07-10: sandbox had no @uipath/solution-tool next to the CLI; the
agent self-installed into its npm prefix, invisible to this subprocess). The
companion `command_executed` criterion in the task YAML guarantees the agent
really packed twice rather than copying one package.

Comparison, after replacing GUIDs -> <GUID> and ISO timestamps -> <TS>:
  - the set of entry paths must match across all packages, and
  - the text of every JSON entry must match.
Binary entries (the nested project .nupkg) are compared by normalized path only —
their bytes carry zip timestamps and are not a determinism signal on their own."""

import json
import re
import sys
import zipfile
from pathlib import Path

GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
TS = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?")


def normalize(text: str) -> str:
    return TS.sub("<TS>", GUID.sub("<GUID>", text))


def is_solution_package(zip_path: Path) -> bool:
    """True only for real `uip solution pack` output: it always carries the
    solution metadata, the package manifest, and the bundled project payload
    under files/ — a zipped source tree or hand-rolled archive doesn't."""
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
    except (zipfile.BadZipFile, OSError):
        return False
    return (
        "solutionMetadata.json" in names
        and "packageInfo.json" in names
        and any(n.startswith("files/") for n in names)
    )


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


# Cwd is the sandbox working directory the agent packed into. Skip hidden dirs
# (.git, .local investigation state) — packages land in plain output folders.
packages = sorted(
    p for p in Path(".").rglob("*.zip")
    if not any(part.startswith(".") for part in p.parts) and is_solution_package(p)
)
if len(packages) < 2:
    sys.exit(
        f"FAIL: expected at least 2 packed solution packages (*.zip containing "
        f"solutionMetadata.json) under the working directory, found "
        f"{[str(p) for p in packages]} — the agent must pack the fixture twice "
        f"into two separate output folders"
    )

base_paths, base_json = fingerprint(packages[0])

for other in packages[1:]:
    o_paths, o_json = fingerprint(other)
    if base_paths != o_paths:
        only_a = sorted(set(base_paths) - set(o_paths))
        only_b = sorted(set(o_paths) - set(base_paths))
        sys.exit(
            f"FAIL: package entry lists differ between {packages[0]} and {other} "
            f"(after id/timestamp normalization). only-in-first={only_a} only-in-other={only_b}"
        )
    for name in base_json:
        if base_json[name] != o_json.get(name):
            sys.exit(
                f"FAIL: JSON entry {name!r} differs between {packages[0]} and {other} "
                f"after id/timestamp normalization — real nondeterminism"
            )

print(
    f"OK: pack is deterministic — {len(packages)} packages "
    f"({', '.join(str(p) for p in packages)}), {len(base_paths)} entries each, "
    f"all JSON matches (GUIDs/timestamps normalized)"
)
