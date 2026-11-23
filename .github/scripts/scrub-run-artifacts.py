#!/usr/bin/env python3
"""Fail-closed scrub of a coder-eval run directory before anything is published.

Every secret this job forwarded, plus every UiPath token issued during the run
(the mounted .auth only holds the latest), is replaced in EVERY file as raw
bytes (UTF-8 and UTF-16-LE). Anything that cannot be inspected is deleted, not
published: symlinks and archives or compressed files (a token inside a ZIP or
gzip member survives a byte replace). A final verify pass re-reads every file.
On any error the whole run directory is wiped, a fixed message is printed and the
exit code is 1, so the workflow's publishing steps (gated on this step's success)
publish nothing. Usage: scrub-run-artifacts.py <run_dir>
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
# Compressed or archive containers: contents are invisible to a byte replace.
_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08", b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00",
          b"7z\xbc\xaf\x27\x1c", b"\x28\xb5\x2f\xfd", b"\x04\x22\x4d\x18", b"Rar!", b"\x1f\x9d", b"\x1f\xa0")
MIN_TOKEN = 28


def _is_archive(head: bytes) -> bool:
    return head.startswith(_MAGIC) or head[257:262] == b"ustar"


def _values(env: dict[str, str], auth_file: pathlib.Path, issued: pathlib.Path) -> list[str]:
    values = [env[n] for n in SECRET_ENV if len(env.get(n, "")) >= 8]
    for source, prefix in ((auth_file, "UIPATH_ACCESS_TOKEN="), (issued, "")):
        if source.is_file():
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if prefix:
                    # Token only: redacting org/tenant slugs would garble reports.
                    line = line.split("=", 1)[1] if line.startswith(prefix) else ""
                if len(line) > MIN_TOKEN:
                    values.append(line)
    return values


def scrub(root: pathlib.Path, values: list[str]) -> int:
    """Scrub `root` in place; returns the number of withheld (deleted) files."""
    needles = [v.encode("utf-8") for v in values] + [v.encode("utf-16-le") for v in values]
    withheld = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            path.unlink()
            withheld += 1
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if _is_archive(data[:300]):
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
        values = _values(
            dict(os.environ),
            pathlib.Path(os.path.expanduser("~/.uipath/.auth")),
            pathlib.Path(os.environ.get("RUNNER_TEMP", "")) / "issued-tokens",
        )
        if not values:
            return 0
        withheld = scrub(root, values)
    except Exception:  # fixed message only: never echo a value or a path
        for child in root.iterdir() if root.is_dir() else ():
            shutil.rmtree(child, ignore_errors=True) if child.is_dir() else child.unlink(missing_ok=True)
        print("::error::scrub failed; run files withheld from publication")
        return 1
    if withheld:
        print(f"::warning::{withheld} archive/symlink file(s) withheld from publication")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
