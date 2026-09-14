#!/usr/bin/env python3
"""Grade Anti-pattern #1 precisely: no SERVICE-CLASS import from the SDK package root.

`@uipath/uipath-typescript` exports its service classes ONLY from subpaths
(`@uipath/uipath-typescript/jobs` → `Jobs`, `/entities` → `Entities`, ...). A
root import of one of them fails at build time. The package root DOES export
the `UiPath` class, helpers (`getAppBase`, `loadFromMetaTags`), enums, error
classes and every type — importing those from the root is legitimate, and
`import type { ... }` erases at build regardless of where it points.

The old per-task grep flagged every root import except `{ UiPath }`, which
failed correct code twice in one day (`import type { PaginationCursor }`,
`import { loadFromMetaTags }`). This script grades the property that actually
matters: every value specifier imported from the package root must be
something the root exports.

Usage:
  python3 check_root_imports.py <file-or-dir> [<file-or-dir> ...] [--sdk <dir>]

  <file-or-dir>  .ts/.tsx files to check; directories are walked (node_modules/
                 and dist/ skipped).
  --sdk          path to the installed @uipath/uipath-typescript package.
                 Default: the first node_modules/@uipath/uipath-typescript found
                 under the current directory. When no installed package can be
                 found, falls back to a conservative allowlist (UiPath,
                 getAppBase, loadFromMetaTags) so the check still runs offline.

Exit 0 = no service-class root import. Exit 1 = violation(s), listed on stdout.
"""
import argparse
import os
import re
import sys

PKG = "@uipath/uipath-typescript"
OFFLINE_ALLOWLIST = {"UiPath", "getAppBase", "loadFromMetaTags"}

# Whole `import ... from '<pkg>'` statements whose source is exactly the package root.
IMPORT_RE = re.compile(
    r"""import\s+(?P<type>type\s+)?(?P<clause>[^;'"]*?)\s*from\s*['"]""" + re.escape(PKG) + r"""['"]""",
    re.S,
)
NAMED_RE = re.compile(r"\{(?P<names>[^}]*)\}", re.S)


def strip_comments(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(^|[^:])//.*$", r"\1", src, flags=re.M)


def root_exports(sdk_dir: str):
    """Names exported from dist/index.d.ts, or None when the package is not installed."""
    path = os.path.join(sdk_dir, "dist", "index.d.ts")
    if not os.path.isfile(path):
        return None
    s = open(path, encoding="utf-8").read()
    names = set()
    for blk in re.findall(r"export\s*(?:type\s*)?\{([^}]*)\}", s):
        for part in blk.split(","):
            part = re.sub(r"^\s*type\s+", "", part.strip())
            if not part:
                continue
            m = re.match(r"(\S+)\s+as\s+(\S+)", part)
            names.add(m.group(2) if m else part)
    for m in re.finditer(
        r"^export\s+(?:declare\s+)?(?:abstract\s+)?(?:class|function|const|let|var|enum|interface|type|namespace)\s+([A-Za-z_$][\w$]*)",
        s,
        re.M,
    ):
        names.add(m.group(1))
    return names


def find_sdk(start: str):
    for root, dirs, _files in os.walk(start):
        # Do not descend into nested node_modules of node_modules; the first
        # top-level install is the one the app compiles against.
        if os.path.basename(root) == "node_modules" and root.count("node_modules") > 1:
            dirs[:] = []
            continue
        cand = os.path.join(root, "node_modules", "@uipath", "uipath-typescript")
        if os.path.isfile(os.path.join(cand, "dist", "index.d.ts")):
            return cand
    return None


def value_specifiers(clause: str):
    """Value (non-type) specifiers of a root import clause. Type-only entries are dropped."""
    names = []
    for m in NAMED_RE.finditer(clause):
        for part in m.group("names").split(","):
            part = part.strip()
            if not part or part.startswith("type "):
                continue
            names.append(re.split(r"\s+as\s+", part)[0].strip())
    # `import X from` / `import * as X from` the root: not service-class imports.
    return names


def check_file(path: str, exports):
    src = strip_comments(open(path, encoding="utf-8", errors="replace").read())
    bad = []
    for m in IMPORT_RE.finditer(src):
        if m.group("type"):
            continue  # import type { ... } — erased at build
        for name in value_specifiers(m.group("clause")):
            allowed = (name in exports) if exports is not None else (name in OFFLINE_ALLOWLIST)
            if not allowed:
                bad.append(name)
    return bad


def iter_targets(targets):
    for t in targets:
        if os.path.isdir(t):
            for root, dirs, files in os.walk(t):
                dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".git")]
                for f in files:
                    if f.endswith((".ts", ".tsx")) and not f.endswith(".d.ts"):
                        yield os.path.join(root, f)
        elif os.path.isfile(t):
            yield t
        else:
            print(f"MISSING: {t}")
            yield None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--sdk", default=None)
    args = ap.parse_args(argv)

    sdk = args.sdk or find_sdk(".")
    exports = root_exports(sdk) if sdk else None
    mode = f"root exports of {sdk} ({len(exports)} names)" if exports else "offline allowlist (SDK not installed)"

    failed = False
    for path in iter_targets(args.targets):
        if path is None:
            failed = True
            continue
        bad = check_file(path, exports)
        if bad:
            failed = True
            print(f"VIOLATION {path}: root import of non-root export(s) {sorted(set(bad))} — service classes live on subpaths ({PKG}/<service>)")
    print(f"{'FAIL' if failed else 'OK'}: checked against {mode}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
