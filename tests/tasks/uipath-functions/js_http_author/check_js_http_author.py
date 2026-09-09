#!/usr/bin/env python3
"""JS/TS coded-function authoring-shape check.

Verifies the artifacts the `quote` HTTP function task MUST produce:

  1. `quote-fns/functions/quote.ts` exists, default-exports `defineFunction`,
     declares `method: "POST"` + `path: "/quote"`, and builds both contracts
     with `defineSchema<...>()` (schema-first — no zod/arktype/valibot).
  2. Error semantics: `FunctionError` imported from the SDK and thrown with
     status 422 for the over-limit rejection; no `errors` array in the output
     contract (success-only output — errors are thrown).
  3. Any relative import in quote.ts carries the `.ts` extension.
  4. `quote-fns/uipath.json` still parses, keeps the seeded `health` entry,
     and maps `quote` to `functions/quote.ts:default`.
  5. `quote-fns/package.json`: the SDK stays in devDependencies and was not
     moved/duplicated into dependencies; no schema-validator runtime dep
     (zod/arktype/valibot) was added.

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def find_project_root(name: str) -> Path:
    cwd = Path.cwd()
    direct = cwd / name
    if (direct / "uipath.json").is_file():
        return direct
    for candidate in cwd.rglob(name):
        if candidate.is_dir() and (candidate / "uipath.json").is_file():
            return candidate
    sys.exit(f"FAIL: could not locate project directory {name!r} under {cwd}")


ROOT = find_project_root("quote-fns")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_quote_ts() -> None:
    src = _read_text(ROOT / "functions" / "quote.ts")

    if not re.search(r"export\s+default\s+defineFunction\s*\(", src):
        sys.exit("FAIL: quote.ts must default-export defineFunction(...)")
    if not re.search(r'from\s+["\']@uipath/coded-functions-js-sdk["\']', src):
        sys.exit("FAIL: quote.ts must import from @uipath/coded-functions-js-sdk")
    if not re.search(r'method\s*:\s*["\']POST["\']', src):
        sys.exit('FAIL: quote.ts must declare method: "POST"')
    if not re.search(r'path\s*:\s*["\']/quote["\']', src):
        sys.exit('FAIL: quote.ts must declare path: "/quote"')

    if len(re.findall(r"defineSchema\s*<", src)) < 2:
        sys.exit("FAIL: input and output must both be declared with defineSchema<...>()")
    for lib in ("zod", "arktype", "valibot"):
        if re.search(rf'from\s+["\']{lib}', src):
            sys.exit(f"FAIL: schema-first contract required — {lib} import found")

    if "FunctionError" not in src:
        sys.exit("FAIL: over-limit rejection must throw FunctionError")
    # Accept FunctionError("...", 422) and subclass/variable forms that carry 422.
    if not re.search(r"FunctionError\s*\([^)]*422", src, re.DOTALL) and not re.search(
        r"\b422\b", src
    ):
        sys.exit("FAIL: rejection must carry HTTP status 422")

    for m in re.finditer(r'from\s+["\'](\.[^"\']+)["\']', src):
        target = m.group(1)
        if not target.endswith(".ts"):
            sys.exit(f"FAIL: relative import {target!r} must carry the .ts extension")


def check_uipath_json() -> None:
    manifest = _load_json(ROOT / "uipath.json")
    functions = manifest.get("functions")
    if not isinstance(functions, dict):
        sys.exit("FAIL: uipath.json must keep a functions map")
    if functions.get("health") != "functions/health.ts:default":
        sys.exit("FAIL: seeded health entry must be preserved in uipath.json")
    if functions.get("quote") != "functions/quote.ts:default":
        sys.exit(
            "FAIL: uipath.json functions map must register quote -> functions/quote.ts:default"
        )


def check_package_json() -> None:
    pkg = _load_json(ROOT / "package.json")
    dev = pkg.get("devDependencies") or {}
    deps = pkg.get("dependencies") or {}
    if "@uipath/coded-functions-js-sdk" not in dev:
        sys.exit("FAIL: @uipath/coded-functions-js-sdk must stay in devDependencies")
    if "@uipath/coded-functions-js-sdk" in deps:
        sys.exit("FAIL: the SDK must not be moved/duplicated into dependencies")
    for lib in ("zod", "arktype", "valibot"):
        if lib in deps or lib in dev:
            sys.exit(f"FAIL: no schema-validator dependency allowed — found {lib}")


def main() -> None:
    check_quote_ts()
    check_uipath_json()
    check_package_json()
    print("PASS")


if __name__ == "__main__":
    main()
