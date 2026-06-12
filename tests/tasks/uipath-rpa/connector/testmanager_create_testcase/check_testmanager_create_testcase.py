#!/usr/bin/env python3
"""Shape check for the Test Manager RPA (coded) connector task.

SKELETON: `shape` mode is implemented (connector-agnostic) — it asserts the
produced project references the Test Manager Integration Service connector and
uses the IS connector activity package. `tenant` mode is a TODO that needs the
live-confirmed create operation + connection UUID.

Usage: check_testmanager_create_testcase.py [shape|tenant]
"""
import glob
import os
import sys

CONNECTOR_KEY = "uipath-uipath-testmanager"
IS_PACKAGE = "UiPath.IntegrationService.Activities"
TC_NAME = "Connector Eval - RPA TC"


def _project_text():
    """Concatenate the project's authored sources + manifests for substring checks."""
    globs = ["**/*.cs", "**/*.csproj", "**/project.json", "**/*.xaml"]
    blobs = []
    for g in globs:
        for path in glob.glob(g, recursive=True):
            if any(seg in path for seg in ("/obj/", "/bin/", "node_modules")):
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    blobs.append((path, fh.read()))
            except OSError:
                pass
    return blobs


def check_shape():
    blobs = _project_text()
    if not blobs:
        print("FAIL: no project sources (.cs/.csproj/project.json) found")
        sys.exit(1)
    joined = "\n".join(text for _p, text in blobs)
    problems = []
    if CONNECTOR_KEY not in joined:
        problems.append(f"connectorKey {CONNECTOR_KEY!r} not referenced in the project")
    if IS_PACKAGE not in joined:
        problems.append(f"{IS_PACKAGE} not referenced (expected the IS connector activity package)")
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        sys.exit(1)
    print(f"OK: project references {CONNECTOR_KEY} via {IS_PACKAGE}")


def check_tenant():
    # TODO(operation): after `uip is resources describe uipath-uipath-testmanager --output json`,
    # confirm the create + get/list operations, then verify the test case named
    # TC_NAME exists via `uip is resources run ...` and assert it is present.
    print("SKIP: tenant-state check not yet implemented (needs live-confirmed operation slug)")
    sys.exit(0)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "shape"
    (check_tenant if mode == "tenant" else check_shape)()
