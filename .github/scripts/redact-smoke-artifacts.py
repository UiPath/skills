#!/usr/bin/env python3
"""Replace smoke credentials in every smoke artifact without changing result fields.

Credentials are the forwarded secrets plus the UiPath tokens the ROPC mint writes
to ~/.uipath/.auth, which smoke.yaml mounts read-write into every agent sandbox.
The uip CLI rewrites that file when it refreshes, so the minted tokens come from
a runner-owned snapshot taken before any sandbox starts (UIPATH_AUTH_SNAPSHOT),
and the scrub covers the union of the snapshot and the file after the run.

Scan bytes, not selected text extensions: agent artifacts can have any suffix or
contain non-UTF-8 bytes. This covers verbatim secrets, not encoded/compressed ones.
Any unreadable path, symlink, special file or surviving secret blocks publication.
"""

import os
from pathlib import Path
import stat
import sys


SECRET_ENV = ("CODEX_API_KEY", "AWS_BEARER_TOKEN_BEDROCK")
AUTH_TOKENS = ("UIPATH_ACCESS_TOKEN", "UIPATH_REFRESH_TOKEN")


class Blocked(ValueError):
    """A failure whose message holds no secret and can be printed."""


def auth_tokens(path: Path, label: str) -> list[str]:
    # KEY=value lines: refresh-auth.sh writes them, and the uip CLI keeps the
    # format when it rewrites ~/.uipath/.auth on a refresh.
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        raise Blocked(f"{label} missing or unreadable") from None
    tokens = {}
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key in AUTH_TOKENS:
            tokens[key] = value.strip()
    if len(tokens.get("UIPATH_ACCESS_TOKEN", "")) < 8:
        raise Blocked(f"{label} has no access token")
    # The refresh token is optional, and "null" when the mint got none.
    return [value for value in tokens.values() if len(value) >= 8]


def auth_secrets() -> list[str]:
    # A token an agent printed before a mid-run refresh is gone from .auth but
    # still valid, so the minted snapshot must be readable, not best-effort.
    snapshot = os.environ.get("UIPATH_AUTH_SNAPSHOT")
    if not snapshot:
        raise Blocked("UiPath token snapshot missing or unreadable")
    return (auth_tokens(Path(snapshot), "UiPath token snapshot")
            + auth_tokens(Path.home() / ".uipath/.auth", "UiPath auth file ~/.uipath/.auth"))


def redact(root: Path, secrets: list[bytes]) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("missing run directory")

    def walk_error(error: OSError) -> None:
        raise error

    files = []
    for directory, dirs, names in os.walk(root, onerror=walk_error, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if any(secret in os.fsencode(path.relative_to(root)) for secret in secrets):
                raise ValueError("secret in artifact name")
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError("unsupported artifact")
            data = path.read_bytes()
            redacted = data
            for secret in secrets:
                redacted = redacted.replace(secret, b"***")
            if redacted != data:
                path.write_bytes(redacted)
            files.append(path)

    for path in files:
        data = path.read_bytes()
        if any(secret in data for secret in secrets):
            raise ValueError("secret survived redaction")


def main(argv: list[str]) -> int:
    try:
        # Smoke always uses Codex. An absent key must not silently skip its scrub.
        if len(os.environ.get("CODEX_API_KEY", "")) < 8:
            raise ValueError("missing Codex key")
        values = {os.environ[name] for name in SECRET_ENV if os.environ.get(name)}
        values.update(auth_secrets())
        secrets = sorted((value.encode() for value in values), key=len, reverse=True)
        redact(Path(argv[1]), secrets)
    except Blocked as error:
        print(f"::error::{error}; upload blocked")
        return 1
    except Exception:
        # Paths and exception details can themselves contain a credential.
        print("::error::Smoke artifact redaction failed; upload blocked")
        return 1
    print("Smoke artifact redaction and verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
