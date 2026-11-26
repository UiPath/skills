#!/usr/bin/env python3
"""Replace smoke credentials in every smoke artifact without changing result fields.

Credentials are the forwarded secrets plus the UiPath tokens the ROPC mint writes
to ~/.uipath/.auth, which smoke.yaml mounts read-write into every agent sandbox.

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


def auth_secrets() -> list[str]:
    # refresh-auth.sh writes KEY=value lines; the uip CLI rewrites the file in the
    # same format when it refreshes, so read it after the run, not at mint time.
    try:
        lines = (Path.home() / ".uipath/.auth").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        raise Blocked("UiPath auth file ~/.uipath/.auth missing or unreadable") from None
    tokens = {}
    for line in lines:
        key, sep, value = line.partition("=")
        if sep and key in AUTH_TOKENS:
            tokens[key] = value.strip()
    if len(tokens.get("UIPATH_ACCESS_TOKEN", "")) < 8:
        raise Blocked("UiPath auth file ~/.uipath/.auth has no access token")
    # The refresh token is optional, and "null" when the mint got none.
    return [value for value in tokens.values() if len(value) >= 8]


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
