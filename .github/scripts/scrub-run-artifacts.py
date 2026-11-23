#!/usr/bin/env python3
"""Fail-closed scrub of a coder-eval run directory before anything is published.

Allow-list, not deny-list: only clean text is published. A file survives only if
it is strict UTF-8 (or BOM-marked UTF-16) with no NUL bytes and no archive magic;
symlinks, binaries, archives and compressed files are withheld (a token inside a
ZIP or gzip member survives a byte replace). In the kept files every secret this
job forwarded, plus every UiPath token issued during the run (the mounted .auth
only holds the latest), is replaced as raw bytes in its UTF-8, UTF-16-LE and
base64 (three alignments) forms; JWT characters need no JSON or URL escaping.
A final verify pass re-reads every file.
On any error the whole run directory is wiped, a fixed message is printed and the
exit code is 1, so the workflow's publishing steps (gated on this step's success)
publish nothing. Usage: scrub-run-artifacts.py <run_dir>
"""

from __future__ import annotations

import base64
import html
import json
import os
import pathlib
import shutil
import sys
import urllib.parse

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


def _is_text(data: bytes) -> bool:
    """Clean text only: no archive magic, no NUL, strict UTF-8 or BOM UTF-16."""
    if data.startswith(_MAGIC) or data[257:262] == b"ustar":
        return False
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            data.decode("utf-16")
            return True
        except UnicodeDecodeError:
            return False
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _needles(values: list[str]) -> list[bytes]:
    out: list[bytes] = []
    for v in values:
        raw = v.encode("utf-8")
        out += [raw, v.encode("utf-16-le")]
        for skew in range(3):  # base64 of the value at each alignment
            enc = base64.b64encode(b"x" * skew + raw).decode()
            lead = (4 * skew + 2) // 3  # chars that depend on the skew bytes
            tail = enc.rstrip("=")
            out.append(tail[lead:-1].encode() if len(tail) - lead > 12 else tail.encode())
    for v in values:  # secrets with markup-significant characters (token chars need no escaping)
        for form in (json.dumps(v)[1:-1], html.escape(v), urllib.parse.quote(v), urllib.parse.quote_plus(v)):
            if form != v:
                out.append(form.encode("utf-8"))
    return sorted(set(out), key=len, reverse=True)  # longest first: no fragment survives


def _values(env: dict[str, str], auth_file: pathlib.Path, issued: pathlib.Path) -> list[str]:
    values = [env[n] for n in SECRET_ENV if len(env.get(n, "")) >= 8]
    for source, prefixes in ((auth_file, ("UIPATH_ACCESS_TOKEN=", "UIPATH_REFRESH_TOKEN=")), (issued, ())):
        if source.is_file():
            for line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if prefixes:
                    # Tokens only: redacting org/tenant slugs would garble reports.
                    line = next((line.split("=", 1)[1] for p in prefixes if line.startswith(p)), "")
                if len(line) > MIN_TOKEN:
                    values.append(line)
    return values


def scrub(root: pathlib.Path, values: list[str]) -> int:
    """Scrub `root` in place; returns the number of withheld (deleted) files."""
    needles = _needles(values)
    withheld = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            path.unlink()
            withheld += 1
            continue
        if not path.is_file():
            continue
        data = path.read_bytes()
        if not _is_text(data):
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
        issued = pathlib.Path(os.environ.get("RUNNER_TEMP", "")) / "issued-tokens"
        if os.environ.get("GITHUB_ACTIONS") and (not issued.is_file() or issued.stat().st_size == 0):
            raise RuntimeError("no issued-tokens record")
        if not values:
            return 0
        withheld = scrub(root, values)
    except Exception:  # fixed message only: never echo a value or a path
        for child in root.iterdir() if root.is_dir() else ():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        print("::error::scrub failed; run files withheld from publication")
        return 1
    if withheld:
        print(f"::warning::{withheld} non-text/symlink file(s) withheld from publication")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
