#!/usr/bin/env python3
"""Compare files under two roots (repo vs. installed plugin cache).

Reports three categories by relative path + SHA-256:
  - missing-in-cache: present in repo, absent in cache
  - extra-in-cache:   present in cache, absent in repo
  - content-differs:  present in both, bytes differ

Exit code 0 if identical, 1 if any differences.
"""

import argparse
import difflib
import hashlib
import sys
from pathlib import Path


def walk_files(root: Path) -> dict[str, Path]:
    """Return {relative_posix_path: absolute_path} for every file under root."""
    files = {}
    for p in root.rglob("*"):
        if p.is_file():
            files[p.relative_to(root).as_posix()] = p
    return files


def sha256(path: Path, normalize_newlines: bool) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        data = f.read()
    if normalize_newlines:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    h.update(data)
    return h.hexdigest()


def unified_diff(a: Path, b: Path, rel: str) -> str:
    try:
        a_lines = a.read_text(encoding="utf-8").splitlines(keepends=True)
        b_lines = b.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return f"    <binary file, {a.stat().st_size} vs {b.stat().st_size} bytes>\n"
    return "".join(difflib.unified_diff(a_lines, b_lines, fromfile=f"repo/{rel}", tofile=f"cache/{rel}"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", type=Path, help="repo root (source of truth)")
    ap.add_argument("cache", type=Path, help="installed plugin cache root")
    ap.add_argument("--subpath", default="", help="narrow comparison to this relative subpath (e.g. 'skills/uipath-rpa/references')")
    ap.add_argument("--diff", action="store_true", help="print unified diff for each content mismatch")
    ap.add_argument("--raw", action="store_true", help="hash raw bytes (default: normalize CRLF/CR to LF before hashing)")
    args = ap.parse_args()
    normalize = not args.raw

    repo_base = (args.repo / args.subpath).resolve()
    cache_base = (args.cache / args.subpath).resolve()

    for label, base in [("repo", repo_base), ("cache", cache_base)]:
        if not base.is_dir():
            print(f"error: {label} path not a directory: {base}", file=sys.stderr)
            return 2

    repo_files = walk_files(repo_base)
    cache_files = walk_files(cache_base)

    repo_keys = set(repo_files)
    cache_keys = set(cache_files)

    missing_in_cache = sorted(repo_keys - cache_keys)
    extra_in_cache = sorted(cache_keys - repo_keys)

    differs = []
    for rel in sorted(repo_keys & cache_keys):
        if sha256(repo_files[rel], normalize) != sha256(cache_files[rel], normalize):
            differs.append(rel)

    print(f"repo:  {repo_base}")
    print(f"cache: {cache_base}")
    print(f"scanned: {len(repo_keys)} repo file(s), {len(cache_keys)} cache file(s)")
    print()

    def section(title: str, items: list[str]) -> None:
        print(f"{title} ({len(items)}):")
        for rel in items:
            print(f"  {rel}")
        if not items:
            print("  (none)")
        print()

    section("missing-in-cache (repo has, cache does not)", missing_in_cache)
    section("extra-in-cache (cache has, repo does not)", extra_in_cache)
    section("content-differs", differs)

    if args.diff and differs:
        print("--- unified diffs ---")
        for rel in differs:
            print()
            print(f"### {rel}")
            diff_text = unified_diff(repo_files[rel], cache_files[rel], rel)
            print(diff_text if diff_text else "    <no textual diff>")

    return 0 if not (missing_in_cache or extra_in_cache or differs) else 1


if __name__ == "__main__":
    sys.exit(main())
