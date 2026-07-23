"""
Shared validation script for dashboard skill tests (compiler/metric-module arch).
Run from the generated project directory (tempdir sandbox).

Architecture validated here:
  - intent.json is PURE METADATA (schemaVersion 2, no fnBody strings)
  - each metric is a real TS module under a metrics/ folder exporting fetchData
  - widgets are generated under src/dashboard/widgets/
  - SDK calls live in the metric modules (src/metrics/*.ts), NOT in widgets

Usage:
  python3 check_dashboard.py
      [--min-metrics N] [--min-widgets N]
      [--require-substr S ...] [--forbid-substr S ...]
      [--require-starttime] [--require-state] [--tsc]

Exit 0 = all checks pass. Exit 1 = failure with details on stdout.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Config contract: a normal build writes uipath.json with these keys. The
# uipathCodedApps() Vite plugin reads them and injects <meta name="uipath:*">
# tags; the SDK (new UiPath()) reads its config from those tags. There is no
# .env.local / VITE_* anymore. (clientId may be "" when no OAuth app is
# provisioned in a sandbox — the KEY must be present, not necessarily a value.)
REQUIRED_UIPATH_JSON_KEYS = [
    "scope",
    "orgName",
    "tenantName",
    "baseUrl",
    "clientId",
]

STARTTIME_CONSTANTS = [
    "ONE_DAY_AGO", "SEVEN_DAYS_AGO", "THIRTY_DAYS_AGO",
    "SIXTY_DAYS_AGO", "NINETY_DAYS_AGO",
]

UUID_RE = re.compile(
    r'["\']([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})["\']'
)


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", flush=True)
    sys.exit(1)


def check(condition: bool, msg: str) -> None:
    if not condition:
        fail(msg)


def find_project_root(start: Path) -> Path:
    """Locate the generated dashboard project root.

    The skill scaffolds into a <routingName> subdirectory (e.g. agent-health-x7k2),
    so the project may be at cwd OR one level (or more) below it. The root is the
    shallowest directory containing package.json AND (intent.json OR a src/ dir).
    Falls back to ``start`` when nothing matches (so structural checks emit a clear
    'package.json not found' failure).
    """
    candidates = []
    if (start / "package.json").exists():
        candidates.append(start)
    for pkg in start.rglob("package.json"):
        parts = set(pkg.parts)
        if "node_modules" in parts or "dist" in parts or ".vite" in parts:
            continue
        d = pkg.parent
        if (d / "intent.json").exists() or (d / "src").is_dir():
            candidates.append(d)
    if not candidates:
        return start
    # Shallowest (fewest path parts) wins.
    return sorted(set(candidates), key=lambda p: len(p.parts))[0]


def find_files(root: Path, suffix: str, path_contains: str = "") -> list:
    """Recursively find files by suffix, optionally requiring a substring in the path.
    Skips node_modules and dist."""
    out = []
    for p in root.rglob(f"*{suffix}"):
        parts = set(p.parts)
        if "node_modules" in parts or "dist" in parts:
            continue
        rel = p.as_posix()
        if path_contains and path_contains not in rel:
            continue
        out.append(p)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-metrics", type=int, default=1,
                        help="Minimum number of metric modules (.ts under a metrics/ folder, exporting fetchData)")
    parser.add_argument("--min-widgets", type=int, default=1,
                        help="Minimum number of generated widget files under src/dashboard/widgets/")
    parser.add_argument("--require-substr", action="append", default=[],
                        help="Substring that MUST appear across metric modules / generated code (repeatable)")
    parser.add_argument("--forbid-substr", action="append", default=[],
                        help="Substring that must NOT appear across metric modules / generated code (repeatable)")
    parser.add_argument("--require-starttime", action="store_true",
                        help="A named time constant must appear in metric modules (not inline Date arithmetic)")
    parser.add_argument("--require-state", action="store_true",
                        help=".dashboard/state.json must exist with schemaVersion 2")
    parser.add_argument("--require-rowlink", action="store_true",
                        help="A generated widget must wire a non-empty ROW_LINK_KEY and an onRowClick handler")
    parser.add_argument("--require-detailview", action="store_true",
                        help="A *DetailView.tsx must be generated under src/dashboard/views/")
    parser.add_argument("--tsc", action="store_true",
                        help="Run npx tsc --noEmit and require exit 0 (gold gate; skipped if node_modules absent)")
    args = parser.parse_args()

    # The skill scaffolds into a <routingName> subdir, so resolve the real
    # project root (cwd or a descendant) before any path-relative checks.
    cwd = find_project_root(Path.cwd())

    # 1. Project structure
    check((cwd / "package.json").exists(), "package.json not found — scaffold did not run")
    check((cwd / "uipath.json").exists(), "uipath.json not found — config not written")
    check((cwd / "src").is_dir(), "src/ directory missing")
    check((cwd / "vite.config.ts").exists(), "vite.config.ts missing")
    # The Vite plugin that injects config meta tags must be wired in.
    vite_cfg = (cwd / "vite.config.ts").read_text(encoding="utf-8", errors="ignore")
    check("uipathCodedApps" in vite_cfg,
          "vite.config.ts does not wire the uipathCodedApps() config-injection plugin")

    # 2. Config contract: uipath.json carries the SDK config (the plugin → meta tags)
    try:
        uipath_cfg = json.loads((cwd / "uipath.json").read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError as e:
        fail(f"uipath.json is not valid JSON: {e}")
    for key in REQUIRED_UIPATH_JSON_KEYS:
        check(key in uipath_cfg, f"uipath.json missing key: {key}")

    # 3. intent.json — pure metadata, schemaVersion 2, no fnBody.
    # Search from the sandbox root (not just the resolved project dir): the agent
    # may author intent.json beside the project dir (it runs the build with a
    # projectDir field pointing at the <routingName> subdir) rather than inside it.
    # Exact-name filter so the glob does NOT also match `edit-intent.json` (which
    # has no schemaVersion and would fail the v2 assertion below).
    intent_files = [f for f in find_files(Path.cwd(), "intent.json") if f.name == "intent.json"]
    check(len(intent_files) >= 1, "intent.json not found — build did not author intent metadata")
    for f in intent_files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        check("fnBody" not in raw,
              f"{f.as_posix()} contains an fnBody string - reverted to the old embedded-code model")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            fail(f"{f.as_posix()} is not valid JSON: {e}")
        check(data.get("schemaVersion") == 2,
              f"{f.as_posix()} must declare \"schemaVersion\": 2 (found {data.get('schemaVersion')!r})")

    # 4. Metric modules — .ts under a metrics/ folder, each exporting fetchData
    metric_files = [p for p in find_files(cwd, ".ts") if "/metrics/" in p.as_posix()]
    check(len(metric_files) >= args.min_metrics,
          f"Expected >= {args.min_metrics} metric module(s) under a metrics/ folder, found {len(metric_files)}")
    for p in metric_files:
        body = p.read_text(encoding="utf-8", errors="ignore")
        check("fetchData" in body,
              f"Metric module {p.as_posix()} does not export fetchData")

    # 5. Generated widgets under src/dashboard/widgets/
    widgets_dir = cwd / "src" / "dashboard" / "widgets"
    widget_files = []
    if widgets_dir.is_dir():
        widget_files = [f for f in widgets_dir.iterdir()
                        if f.suffix == ".tsx"]
    check(len(widget_files) >= args.min_widgets,
          f"Expected >= {args.min_widgets} widget(s) under src/dashboard/widgets/, found {len(widget_files)}")

    # Concatenated code surface for substring checks: metric modules + generated dashboard code.
    scan_files = list(metric_files)
    dash_dir = cwd / "src" / "dashboard"
    if dash_dir.is_dir():
        scan_files += [p for p in dash_dir.rglob("*.tsx")]
        scan_files += [p for p in dash_dir.rglob("*.ts")]
    code_surface = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in scan_files)
    metric_surface = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in metric_files)

    # 6. require-substr / forbid-substr
    for s in args.require_substr:
        check(s in code_surface,
              f"Required substring not found in metric modules / generated code: {s!r}")
    for s in args.forbid_substr:
        check(s not in code_surface,
              f"Forbidden substring present in metric modules / generated code: {s!r}")

    # 7. startTime constants in metric modules
    if args.require_starttime:
        has_constant = any(c in metric_surface for c in STARTTIME_CONSTANTS)
        check(has_constant,
              "No named time constant (e.g. SEVEN_DAYS_AGO) found in metric modules — "
              "expected a constant from @/lib/time, not inline Date arithmetic")

    # 8. state.json
    if args.require_state:
        state_path = cwd / ".dashboard" / "state.json"
        check(state_path.exists(), ".dashboard/state.json missing — incremental + deploy depend on it")
        try:
            state = json.loads(state_path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError as e:
            fail(f".dashboard/state.json is not valid JSON: {e}")
        check(state.get("schemaVersion") == 2,
              f".dashboard/state.json must have schemaVersion 2 (found {state.get('schemaVersion')!r})")

    # 9. Row-click wiring on a generated widget (rowLink default fix)
    if args.require_rowlink:
        rowlink_re = re.compile(r"ROW_LINK_KEY\s*=\s*'[^']+'")
        clickable = any(
            rowlink_re.search(w.read_text(encoding="utf-8", errors="ignore"))
            and "onRowClick" in w.read_text(encoding="utf-8", errors="ignore")
            for w in widget_files
        )
        check(clickable,
              "No generated widget has a non-empty ROW_LINK_KEY with an onRowClick handler "
              "(rowLink default did not wire the click handler)")

    # 9b. Generated detail view
    if args.require_detailview:
        views_dir = cwd / "src" / "dashboard" / "views"
        detail_views = list(views_dir.glob("*DetailView.tsx")) if views_dir.is_dir() else []
        check(len(detail_views) >= 1,
              "No *DetailView.tsx generated under src/dashboard/views/")

    # 10. No hardcoded UUID in metric modules
    m = UUID_RE.search(metric_surface)
    check(m is None, f"Hardcoded UUID found in a metric module: {m.group(1) if m else ''}")

    # 10. TypeScript compilation (gold gate)
    if args.tsc:
        if (cwd / "node_modules").is_dir():
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True, text=True, cwd=str(cwd)
            )
            if result.returncode != 0:
                fail(f"tsc --noEmit failed:\n{result.stdout}\n{result.stderr}")
        else:
            print("SKIP: node_modules not present, skipping tsc check", flush=True)

    metric_names = [p.stem for p in metric_files]
    print(f"PASS: {len(metric_files)} metric module(s), {len(widget_files)} widget(s): "
          f"{', '.join(metric_names)}", flush=True)


if __name__ == "__main__":
    main()
