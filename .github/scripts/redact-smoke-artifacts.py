#!/usr/bin/env python3
"""Replace forwarded secrets in every smoke artifact without changing result fields.

Scan bytes, not selected text extensions: agent artifacts can have any suffix or
contain non-UTF-8 bytes. This covers verbatim secrets, not encoded/compressed ones.
Any unreadable path, symlink, special file or surviving secret blocks publication.
"""

import os
from pathlib import Path
import stat
import sys


SECRET_ENV = ("CODEX_API_KEY", "AWS_BEARER_TOKEN_BEDROCK", "UIPATH_CLI_AUTH_TOKEN")


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
        secrets = sorted(
            {os.environ[name].encode() for name in SECRET_ENV if os.environ.get(name)},
            key=len, reverse=True,
        )
        redact(Path(argv[1]), secrets)
    except Exception:
        # Paths and exception details can themselves contain a credential.
        print("::error::Smoke artifact redaction failed; upload blocked")
        return 1
    print("Smoke artifact redaction and verification passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
