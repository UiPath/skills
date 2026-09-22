#!/usr/bin/env python3
"""Coded App <-> JS/TS function backend layout check.

Verifies the artifacts the `quote-backend` task MUST produce, per the
uipath-functions coded-app wiring guide:

  1. `quote-backend/` is a SIBLING of `quote-app/` (same parent, neither
     nested in the other) with its own `package.json` (name `quote-backend`,
     SDK in devDependencies only) and `uipath.json` functions map registering
     `quote -> functions/quote.ts:default`.
  2. `quote-backend/functions/quote.ts` default-exports `defineFunction`,
     declares `method: "POST"` + `path: "/quote"`, builds both contracts with
     `defineSchema<...>()` (no zod/arktype/valibot), `.ts` on relative imports.
  3. The app project was NOT turned into a function project: no `functions`
     key in `quote-app/uipath.json`, no `@uipath/coded-functions-js-sdk` in its
     package.json, no `quote-app/functions/` dir, no `defineFunction` under
     `quote-app/src`.
  4. `quote-app/uipath.json` `scope` carries the `OR.Default` token.
  5. `quote-app/src/api/quote.ts` calls the deployed function through the SDK
     `Functions` service (`@uipath/uipath-typescript/functions`, `new
     Functions(`, `.invoke`); executable code never hand-builds a trigger URL
     (`orchestrator_/t/`) nor names the portal domain `cloud.uipath.com`. A
     `fetch` to `http://localhost:7070` (the local serve loop) is allowed.
  6. `quote-app/vite.config.ts` gained no `proxy`.

Run as `check_js_app_backend_layout.py layout` (checks 1 minus the backend
package shape, 3-6) or `... backend` (backend package.json, functions map and
quote.ts shape); no argument runs everything. Exits 0 on PASS, with a
`FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "dist", ".uipath"}


def _candidates(name: str) -> list[Path]:
    cwd = Path.cwd()
    found = []
    direct = cwd / name
    if direct.is_dir():
        found.append(direct)
    for candidate in cwd.rglob(name):
        if candidate.is_dir() and candidate not in found and not (SKIP_DIRS & set(candidate.parts)):
            found.append(candidate)
    return found


def find_project_root(name: str, marker: str) -> Path:
    for candidate in _candidates(name):
        if (candidate / marker).is_file():
            return candidate
    sys.exit(f"FAIL: could not locate project directory {name!r} (with {marker}) under {Path.cwd()}")


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


def _strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    # Only `//` at line start or after whitespace — `https://...` inside a string literal is not a comment.
    return re.sub(r"(?m)(?:^|(?<=\s))//[^\n]*$", "", src)


APP = find_project_root("quote-app", "uipath.json")
BACKEND = find_project_root("quote-backend", "uipath.json")
SDK = "@uipath/coded-functions-js-sdk"


def check_sibling_layout() -> None:
    if BACKEND.resolve().parent != APP.resolve().parent:
        sys.exit(f"FAIL: quote-backend must sit next to quote-app, not at {BACKEND}")
    if APP.resolve() in BACKEND.resolve().parents or BACKEND.resolve() in APP.resolve().parents:
        sys.exit("FAIL: the app and the backend must be separate projects, not nested")
    print("OK: quote-backend is a sibling project of quote-app")


def check_backend_package() -> None:
    pkg = _load_json(BACKEND / "package.json")
    if pkg.get("name") != "quote-backend":
        sys.exit(f"FAIL: backend package.json name must be 'quote-backend' (its package id), got {pkg.get('name')!r}")
    dev = pkg.get("devDependencies") or {}
    deps = pkg.get("dependencies") or {}
    if SDK not in dev:
        sys.exit(f"FAIL: {SDK} must be in the backend's devDependencies")
    if SDK in deps:
        sys.exit(f"FAIL: {SDK} must not be in the backend's dependencies")
    for lib in ("zod", "arktype", "valibot"):
        if lib in deps or lib in dev:
            sys.exit(f"FAIL: no schema-validator dependency allowed — found {lib}")
    print("OK: backend package.json has its own package id and SDK placement")


def check_backend_manifest() -> None:
    manifest = _load_json(BACKEND / "uipath.json")
    functions = manifest.get("functions")
    if not isinstance(functions, dict):
        sys.exit("FAIL: backend uipath.json must carry a functions map")
    if functions.get("quote") != "functions/quote.ts:default":
        sys.exit("FAIL: backend uipath.json must register quote -> functions/quote.ts:default")
    print("OK: backend uipath.json functions map registers quote")


def check_quote_ts() -> None:
    src = _read_text(BACKEND / "functions" / "quote.ts")
    if not re.search(r"export\s+default\s+defineFunction\s*\(", src):
        sys.exit("FAIL: quote.ts must default-export defineFunction(...)")
    if not re.search(rf'from\s+["\']{re.escape(SDK)}["\']', src):
        sys.exit(f"FAIL: quote.ts must import from {SDK}")
    if not re.search(r'method\s*:\s*["\']POST["\']', src):
        sys.exit('FAIL: quote.ts must declare method: "POST"')
    if not re.search(r'path\s*:\s*["\']/quote["\']', src):
        sys.exit('FAIL: quote.ts must declare path: "/quote"')
    if len(re.findall(r"defineSchema\s*<", src)) < 2:
        sys.exit("FAIL: input and output must both be declared with defineSchema<...>()")
    for lib in ("zod", "arktype", "valibot"):
        if re.search(rf'from\s+["\']{lib}', src):
            sys.exit(f"FAIL: schema-first contract required — {lib} import found")
    for m in re.finditer(r'from\s+["\'](\.[^"\']+)["\']', src):
        if not m.group(1).endswith(".ts"):
            sys.exit(f"FAIL: relative import {m.group(1)!r} must carry the .ts extension")
    print("OK: quote.ts has the defineFunction/defineSchema shape")


def check_app_not_a_function_project() -> None:
    manifest = _load_json(APP / "uipath.json")
    if "functions" in manifest:
        sys.exit("FAIL: the app's uipath.json must not gain a functions map — the backend is a separate project")
    pkg = _load_json(APP / "package.json")
    for section in ("dependencies", "devDependencies"):
        if SDK in (pkg.get(section) or {}):
            sys.exit(f"FAIL: {SDK} must not be added to the app's {section}")
    if (APP / "functions").exists():
        sys.exit("FAIL: the app project must not contain a functions/ directory")
    for path in (APP / "src").rglob("*.ts*"):
        text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        if SDK in text or re.search(r"\bdefineFunction\s*\(", text):
            sys.exit(f"FAIL: function code found inside the app project: {path.relative_to(APP)}")
    print("OK: the app project was not turned into a function project")


def check_app_scope() -> None:
    manifest = _load_json(APP / "uipath.json")
    scope = str(manifest.get("scope", ""))
    if "OR.Default" not in scope.split():
        sys.exit(f"FAIL: app uipath.json scope must include OR.Default to call the function trigger; got {scope!r}")
    for kept in ("clientId", "orgName", "tenantName", "baseUrl", "redirectUri"):
        if kept not in manifest:
            sys.exit(f"FAIL: app uipath.json lost its {kept} entry")
    print("OK: app scope includes OR.Default")


def check_app_wiring() -> None:
    raw = _read_text(APP / "src" / "api" / "quote.ts")
    src = _strip_comments(raw)
    uses_sdk = (
        re.search(r'from\s+["\']@uipath/uipath-typescript/functions["\']', src)
        and re.search(r"new\s+Functions\s*\(", src)
        and re.search(r"\.invoke\s*(<.*?>)?\s*\(", src, re.DOTALL)
    )
    if not uses_sdk:
        sys.exit(
            "FAIL: quote-app/src/api/quote.ts must call the deployed function through the SDK Functions service "
            "(@uipath/uipath-typescript/functions, new Functions(sdk).invoke(...)) — not a hand-built trigger URL"
        )
    if re.search(r"orchestrator_/t/", src):
        sys.exit("FAIL: hand-built trigger URL found — deployed calls go through Functions.invoke; only http://localhost:7070 (local serve) may be fetched")
    if re.search(r"cloud\.uipath\.com", src):
        sys.exit("FAIL: browser calls must target the api.* host — cloud.uipath.com found in executable code")
    if not re.search(r"export\s+(default\s+)?(async\s+)?(function\s+|const\s+|let\s+)?requestQuote\b|export\s*\{[^}]*\brequestQuote\b", src):
        sys.exit("FAIL: quote-app/src/api/quote.ts must export requestQuote")
    print("OK: app calls the function via the SDK Functions service")


def check_no_vite_proxy() -> None:
    src = _strip_comments(_read_text(APP / "vite.config.ts"))
    if re.search(r"\bproxy\s*:", src):
        sys.exit("FAIL: vite.config.ts must not add server.proxy — it breaks the app's OAuth callback")
    if not re.search(r"base\s*:\s*['\"]\./['\"]", src):
        sys.exit("FAIL: vite.config.ts must keep base: './'")
    print("OK: vite.config.ts unchanged (no proxy, base './')")


LAYOUT_CHECKS = (
    check_sibling_layout,
    check_app_not_a_function_project,
    check_app_scope,
    check_app_wiring,
    check_no_vite_proxy,
)
BACKEND_CHECKS = (check_backend_package, check_backend_manifest, check_quote_ts)


def main() -> None:
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    groups = {"layout": LAYOUT_CHECKS, "backend": BACKEND_CHECKS, "all": LAYOUT_CHECKS + BACKEND_CHECKS}
    if part not in groups:
        sys.exit(f"FAIL: unknown check group {part!r} (layout | backend | all)")
    for check in groups[part]:
        check()
    print("PASS")


if __name__ == "__main__":
    main()
