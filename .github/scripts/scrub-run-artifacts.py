#!/usr/bin/env python3
"""Publish only an allow-listed set of result files from a coder-eval run dir.

Runs carry a live UiPath login, so the run dir is reduced before anything is
published (GitHub artifact, evalboard blob, job summary):

* Everything outside ALLOWED is deleted: agent artifact dirs, transcripts,
  workspace copies, binaries, archives, symlinks. Nothing about their contents
  is trusted or inspected.
* Allowed files must be strict UTF-8 text without NUL bytes, else they are
  deleted too. In the kept files every secret this job forwarded and every
  UiPath token issued during the run (the mounted .auth only holds the latest)
  is replaced verbatim. A verify pass re-reads every kept file.
* On any error the whole run dir is wiped, a fixed message is printed and the
  exit code is 1; the workflow's publishing steps require this step's success,
  so they publish nothing. Under GITHUB_ACTIONS a missing or empty issued-tokens
  record is also an error.

Usage: scrub-run-artifacts.py <run_dir>
"""

from __future__ import annotations

import os
import pathlib
import shutil
import sys

SECRET_ENV = (
    "AWS_BEARER_TOKEN_BEDROCK",
    "CODEX_API_KEY",
    "GEMINI_API_KEY",
    "E2E_PROCESS_KEY",
    "E2E_LONG_PROCESS_KEY",
    "UIPATH_ROPC_CLIENT_SECRET",
    "UIPATH_BOT_PASSWORD",
    "UIPATH_CLI_AUTH_TOKEN",
)
# Report files at <run_dir>, <run_dir>/<variant>/ and per-task dirs below it.
TOP_LEVEL = frozenset({"run.json", "run.md", "experiment.json", "experiment.md", "experiment.html", "experiment.log"})
VARIANT_LEVEL = frozenset({"variant.json", "variant.md", "variant.html"})
TASK_LEVEL = frozenset({"task.json", "task.log", "task.html"})
MIN_TOKEN = 28


def allowed(rel: pathlib.PurePosixPath) -> bool:
    parts = rel.parts
    if "artifacts" in parts[:-1]:
        return False
    if len(parts) == 1:
        return parts[0] in TOP_LEVEL
    if len(parts) == 2 and parts[1] in VARIANT_LEVEL:
        return True
    return len(parts) >= 3 and parts[-1] in TASK_LEVEL


def _is_text(data: bytes) -> bool:
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _values(env: dict[str, str], auth_file: pathlib.Path, issued: pathlib.Path) -> list[bytes]:
    values = [env[n] for n in SECRET_ENV if len(env.get(n, "")) >= 8]
    for source, prefixes in ((auth_file, ("UIPATH_ACCESS_TOKEN=", "UIPATH_REFRESH_TOKEN=")), (issued, ())):
        if source.is_file():
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if prefixes:  # tokens only: org/tenant slugs would garble reports
                    line = next((line.split("=", 1)[1] for p in prefixes if line.startswith(p)), "")
                if len(line) > MIN_TOKEN:
                    values.append(line)
    return sorted({v.encode("utf-8") for v in values}, key=len, reverse=True)


def scrub(root: pathlib.Path, needles: list[bytes]) -> int:
    """Reduce `root` in place; returns the number of withheld files."""
    withheld = 0
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():  # links, FIFOs, sockets, devices: never opened
            path.unlink()
            withheld += 1
            continue
        data = path.read_bytes()
        if not allowed(pathlib.PurePosixPath(path.relative_to(root).as_posix())) or not _is_text(data):
            path.unlink()
            withheld += 1
            continue
        out = data
        for needle in needles:
            out = out.replace(needle, b"***")
        if out != data:
            path.write_bytes(out)
    for path in root.rglob("*"):  # verify
        if path.is_file() and any(n in path.read_bytes() for n in needles):
            raise RuntimeError("secret survived the scrub")
    return withheld


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1])
    try:
        issued = pathlib.Path(os.environ.get("RUNNER_TEMP", "")) / "issued-tokens"
        if os.environ.get("GITHUB_ACTIONS") and (not issued.is_file() or issued.stat().st_size == 0):
            raise RuntimeError("no issued-tokens record")
        needles = _values(dict(os.environ), pathlib.Path(os.path.expanduser("~/.uipath/.auth")), issued)
        withheld = scrub(root, needles)
    except Exception:  # fixed message only: never echo a value or a path
        for child in root.iterdir() if root.is_dir() else ():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        print("::error::scrub failed; run files withheld from publication")
        return 1
    print(f"::notice::{withheld} file(s) outside the publication allow-list withheld")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
