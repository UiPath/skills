"""Per-subprocess `uip` login for graders that need the eval tenant.

The run keeps a live ROPC login in the mounted `.auth` file (a host-side
refresher renews it). It is NOT exported as UIPATH_CLI_* env into the task
environment, so the agent never gets grader env-auth (Delegate / Studio Web
agents still receive their own DELEGATE_AUTH_TOKEN; that is a separate login).
A grader that must reach
the tenant passes `grader_env()` as `env=` to its own `uip` subprocess, which
turns the file into the CLI's env-auth for that one call. A task that never
calls this stays logged out. Only the run's mounted file (or UIPATH_AUTH_FILE) is used,
never a developer's own ~/.uipath login. Without an auth file the environment is returned
unchanged, so offline use is unaffected.
"""

from __future__ import annotations

import base64
import json
import os
import time
from collections.abc import Callable, Mapping

_FILE_CANDIDATES = (os.environ.get("UIPATH_AUTH_FILE", ""), "/.uipath/.auth")
_MAP = {
    "UIPATH_CLI_AUTH_TOKEN": "UIPATH_ACCESS_TOKEN",
    "UIPATH_CLI_ORGANIZATION_NAME": "UIPATH_ORGANIZATION_NAME",
    "UIPATH_CLI_ORGANIZATION_ID": "UIPATH_ORGANIZATION_ID",
    "UIPATH_CLI_TENANT_NAME": "UIPATH_TENANT_NAME",
    "UIPATH_CLI_TENANT_ID": "UIPATH_TENANT_ID",
}
EXPIRY_MARGIN_S = 300


class AuthExpired(RuntimeError):
    """The shared login is expired and was not renewed within the wait."""


def _read(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            key, sep, value = line.strip().partition("=")
            if sep:
                values[key] = value
    return values


def _expires_soon(token: str, margin: int = EXPIRY_MARGIN_S) -> bool:
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return float(claims["exp"]) < time.time() + margin
    except (IndexError, KeyError, ValueError, TypeError):
        return False


def _auth_file(candidates: tuple[str, ...]) -> str | None:
    return next((c for c in candidates if c and os.path.exists(c)), None)


def grader_env(
    base: Mapping[str, str] | None = None,
    *,
    candidates: tuple[str, ...] | None = None,
    attempts: int = 4,
    wait: float = 15.0,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, str]:
    """`base` (default: this process's env) plus env-auth read fresh from the login file.

    Re-reads up to `attempts` times while the token is expired or expiring, or the
    file is mid-swap by the refresher; raises AuthExpired if it never recovers.
    """
    env = dict(os.environ if base is None else base)
    path = _auth_file(_FILE_CANDIDATES if candidates is None else candidates)
    if path is None:
        return env
    problem = "no usable token"
    for attempt in range(attempts):
        if attempt:
            sleep(wait)
        try:
            login = _read(path)
        except OSError as exc:
            problem = f"unreadable ({type(exc).__name__})"
            continue
        token = login.get("UIPATH_ACCESS_TOKEN", "")
        if not token:
            problem = "no access token in file"
        elif _expires_soon(token):
            problem = "token expired or expiring"
        elif missing := [k for k in _MAP.values() if not login.get(k)]:
            problem = f"incomplete login, missing {', '.join(missing)}"
        else:
            for env_key, file_key in _MAP.items():
                env[env_key] = login[file_key]
            if login.get("UIPATH_URL"):
                env.setdefault("UIPATH_URL", login["UIPATH_URL"])
            env["UIPATH_CLI_ENABLE_ENV_AUTH"] = "true"
            return env
    raise AuthExpired(
        f"shared UiPath login in {path}: {problem} after {attempts} reads; this is an "
        "ENVIRONMENT failure (token refresh), not an agent failure"
    )
