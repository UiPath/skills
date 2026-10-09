"""Grade the pack-only task from the artifacts on disk.

Passes when the sandbox holds a solution package (the zip `uip solution pack`
writes: packageInfo.json plus files/<projectId>/<name>.nupkg) whose case
.nupkg carries the compiled plan sidecar, and the plan itself is unchanged
from the fixture (packing must not edit the case).
"""

import io
import json
import os
import sys
import zipfile

ROOT = "."
PLAN = os.path.join("PackReadyCase", "PackReadyCase", "caseplan.json")
FIXTURE = os.path.join(os.environ.get("REFERENCE_DIR", "."), "fixtures", PLAN)
SKIP_DIRS = {"node_modules", ".venv", ".git", "_setup"}


def solution_zips():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".zip"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with zipfile.ZipFile(path) as z:
                    names = z.namelist()
            except zipfile.BadZipFile:
                continue
            if "packageInfo.json" in names and any(n.startswith("files/") and n.endswith(".nupkg") for n in names):
                yield path


def case_sidecar(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if not (name.startswith("files/") and name.endswith(".nupkg")):
                continue
            with zipfile.ZipFile(io.BytesIO(z.read(name))) as nupkg:
                for inner in nupkg.namelist():
                    if inner.startswith("content/caseplan.") and inner.endswith(".bpmn"):
                        return name, inner
    return None


def main():
    zips = list(solution_zips())
    if not zips:
        sys.exit("FAIL: no solution package (zip with packageInfo.json and files/*/*.nupkg) in the sandbox")
    hits = [(z, case_sidecar(z)) for z in zips]
    good = [(z, h) for z, h in hits if h]
    if not good:
        sys.exit(f"FAIL: solution package(s) {zips} hold no case .nupkg with a compiled content/caseplan.*.bpmn")
    if not os.path.isfile(PLAN):
        sys.exit(f"FAIL: {PLAN} is gone")
    if json.load(open(PLAN)) != json.load(open(FIXTURE)):
        sys.exit(f"FAIL: {PLAN} was changed; packing must not edit the case")
    zip_path, (nupkg, sidecar) = good[0]
    print(f"PASS: {zip_path} -> {nupkg} carries {sidecar}; plan unchanged")


if __name__ == "__main__":
    main()
