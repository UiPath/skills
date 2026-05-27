#!/usr/bin/env python3
"""Scaffold a coded FUNCTION agent and inject ENV_FILE_TRACKED.

git-inits CodedAgent and stages a `.env` file containing a secret.
Detected by `git -C CodedAgent ls-files .env` returning non-empty.
`git add` (without commit) is enough — ls-files shows the index.
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from coded_scaffold import write_baseline_function_agent  # noqa: E402

ROOT = Path("CodedAgent")


def _git(*args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )


def main() -> None:
    write_baseline_function_agent(ROOT)

    # .env with a secret — the thing that must never be committed.
    (ROOT / ".env").write_text(
        "API_KEY=sk-livesecretdonotcommit0123456789\n", encoding="utf-8"
    )

    _git("init")
    # Local identity so any future commit wouldn't fail; `add` alone
    # doesn't need it, but set it to keep git quiet across versions.
    _git("config", "user.email", "test@fixture.local")
    _git("config", "user.name", "Test Fixture")
    _git("add", ".env")

    # Confirm the file is tracked (mirrors the rule's detection).
    out = subprocess.run(
        ["git", "ls-files", ".env"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if ".env" not in out:
        raise SystemExit(
            f"Pre-condition failed: git ls-files .env returned {out!r}"
        )
    print("Scaffolded CodedAgent + git-tracked .env (ENV_FILE_TRACKED)")


if __name__ == "__main__":
    main()
