#!/usr/bin/env python3
"""Unit tests for check_root_imports.py — the Anti-pattern #1 grader.

Uses a synthetic installed SDK (a dist/index.d.ts with a known export list) so
no npm install is needed. Covers: service-class root import fails; root helper,
enum, `import type`, inline `type` specifiers and `UiPath` pass; subpath
imports are ignored; comments are ignored; offline allowlist fallback.
"""
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(__file__), "check_root_imports.py")

FAKE_INDEX_DTS = """
export { UiPath, getAppBase, loadFromMetaTags, FeedbackRating, AuthenticationError } from './core';
export type { PaginationCursor, PaginatedResponse } from './core';
export declare function getAsset(): void;
"""


def run(src: str, install_sdk: bool = True):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "src"))
        with open(os.path.join(d, "src", "x.ts"), "w") as f:
            f.write(src)
        if install_sdk:
            sdk = os.path.join(d, "node_modules", "@uipath", "uipath-typescript", "dist")
            os.makedirs(sdk)
            with open(os.path.join(sdk, "index.d.ts"), "w") as f:
                f.write(FAKE_INDEX_DTS)
        return subprocess.run([sys.executable, SCRIPT, "src/x.ts"], cwd=d, capture_output=True, text=True)


def test_service_class_root_import_fails():
    r = run("import { Assets } from '@uipath/uipath-typescript';\n")
    assert r.returncode == 1, r.stdout
    assert "Assets" in r.stdout


def test_mixed_root_import_names_only_the_bad_specifier():
    r = run("import { UiPath, Jobs } from '@uipath/uipath-typescript';\n")
    assert r.returncode == 1
    assert "['Jobs']" in r.stdout


def test_root_helpers_enums_and_uipath_pass():
    r = run(
        "import { UiPath } from '@uipath/uipath-typescript';\n"
        "import { getAppBase, loadFromMetaTags } from '@uipath/uipath-typescript';\n"
        "import { FeedbackRating } from '@uipath/uipath-typescript';\n"
        "import { Assets } from '@uipath/uipath-typescript/assets';\n"
    )
    assert r.returncode == 0, r.stdout


def test_type_only_imports_pass():
    r = run(
        "import type { PaginationCursor } from '@uipath/uipath-typescript';\n"
        "  import type { Jobs } from \"@uipath/uipath-typescript\";\n"
        "import { type PaginatedResponse, UiPath } from '@uipath/uipath-typescript';\n"
    )
    assert r.returncode == 0, r.stdout


def test_multiline_import_and_alias():
    r = run("import {\n  Entities as EntitySvc,\n  UiPath,\n} from '@uipath/uipath-typescript';\n")
    assert r.returncode == 1
    assert "Entities" in r.stdout


def test_commented_out_import_is_ignored():
    r = run(
        "// import { Assets } from '@uipath/uipath-typescript';\n"
        "/* import { Jobs } from '@uipath/uipath-typescript'; */\n"
        "import { Assets } from '@uipath/uipath-typescript/assets';\n"
    )
    assert r.returncode == 0, r.stdout


def test_offline_allowlist_when_sdk_missing():
    ok = run("import { UiPath, getAppBase } from '@uipath/uipath-typescript';\n", install_sdk=False)
    assert ok.returncode == 0, ok.stdout
    assert "offline allowlist" in ok.stdout
    bad = run("import { Assets } from '@uipath/uipath-typescript';\n", install_sdk=False)
    assert bad.returncode == 1


def test_directory_walk_skips_node_modules_and_dist():
    with tempfile.TemporaryDirectory() as d:
        for sub, body in [
            ("src", "import { UiPath } from '@uipath/uipath-typescript';\n"),
            ("dist", "import { Assets } from '@uipath/uipath-typescript';\n"),
            (os.path.join("node_modules", "x"), "import { Assets } from '@uipath/uipath-typescript';\n"),
        ]:
            os.makedirs(os.path.join(d, sub), exist_ok=True)
            with open(os.path.join(d, sub, "a.ts"), "w") as f:
                f.write(body)
        r = subprocess.run([sys.executable, SCRIPT, "."], cwd=d, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout
