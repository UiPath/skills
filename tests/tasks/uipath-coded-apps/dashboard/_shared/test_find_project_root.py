#!/usr/bin/env python3
"""Unit test for find_project_root() in check_dashboard.py.

Regression guard for a real CI failure: a partial starter-kit extract left an
abandoned scaffold husk beside the real project at the SAME depth (both had
package.json + src/). The old selector broke that tie on `set` iteration order,
which Python randomizes per process — so the same artifacts graded PASS or FAIL
at roughly 50/50 depending on the hash seed.

Selection must be a pure function of the tree: completeness first, then depth,
then path string. Run under several PYTHONHASHSEED values to prove it.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_dashboard import find_project_root  # noqa: E402

SEEDS = ["0", "1", "2", "3", "5", "7"]  # 1/2/5/7 selected the husk before the fix


def mk(root: Path, rel: str, files=(), dirs=()) -> Path:
    """Create a candidate project: package.json + src/, plus any extras."""
    d = root / rel
    for f in ("package.json",) + tuple(files):
        (d / f).parent.mkdir(parents=True, exist_ok=True)
        (d / f).write_text("{}")
    for x in ("src",) + tuple(dirs):
        (d / x).mkdir(parents=True, exist_ok=True)
    return d


def main() -> int:
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got}, want {want}")

    with tempfile.TemporaryDirectory() as t:
        r = Path(t)

        proj = mk(r / "one", "proj", ("intent.json",))
        check("single project one level down", find_project_root(r / "one"), proj)
        check("cwd is the project itself", find_project_root(proj), proj)

        # The CI case: husk and real project, same depth, both valid candidates.
        two = r / "two"
        mk(two, "agent-perf-k7m4")
        real = mk(two, "agent-perf-p9v2", ("intent.json",), ("metrics",))
        check("complete project beats husk", find_project_root(two), real)

        # Husk sorts FIRST lexically — completeness must still win.
        three = r / "three"
        mk(three, "aaa-husk")
        rich = mk(three, "zzz-real", ("intent.json",), ("metrics",))
        check("completeness outranks lexical order", find_project_root(three), rich)

        # No candidates: fall back to start so the caller emits
        # "package.json not found" rather than wandering up the tree.
        empty = r / "empty"
        empty.mkdir()
        check("no candidates falls back to start", find_project_root(empty), empty)

        # Two indistinguishable husks: still deterministic, via path string.
        four = r / "four"
        mk(four, "zzz")
        first = mk(four, "aaa")
        check("bare tie breaks lexically", find_project_root(four), first)

        # The actual regression: identical answer under every hash seed.
        probe = (
            "import sys; sys.path.insert(0, %r)\n"
            "from pathlib import Path\n"
            "from check_dashboard import find_project_root\n"
            "print(find_project_root(Path(%r)).name)\n"
            % (os.path.dirname(os.path.abspath(__file__)), str(two))
        )
        seen = set()
        for seed in SEEDS:
            env = dict(os.environ, PYTHONHASHSEED=seed)
            out = subprocess.run(
                [sys.executable, "-c", probe],
                capture_output=True, text=True, timeout=30, env=env,
            )
            if out.returncode != 0:
                failures.append(f"seed {seed}: probe crashed: {out.stderr.strip()}")
            seen.add(out.stdout.strip())
        if len(seen) != 1:
            failures.append(f"hash-seed dependent selection: {sorted(seen)}")
        elif seen != {real.name}:
            failures.append(f"seeds agreed on the wrong project: {seen.pop()}")

    for f in failures:
        print(f"FAIL: {f}")
    if failures:
        return 1
    print(f"PASS: find_project_root deterministic across {len(SEEDS)} hash seeds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
