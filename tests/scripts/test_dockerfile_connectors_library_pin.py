"""The eval image's CONNECTORS_LIBRARY_VERSION pin, run as the Dockerfile runs it.

On 2026-09-22 the stable connectors-library alias was overwritten with a
2-connector build and the image followed it. The pin maps a build number to
that build's immutable copy; these tests lift the block out of the Dockerfile
and run it under /bin/sh (dash in the base image), so they test the text that
ships.
"""

import re
import subprocess
from pathlib import Path

import pytest

DOCKERFILE = Path(__file__).resolve().parents[1] / "docker" / "Dockerfile"
TEXT = DOCKERFILE.read_text()
VERSIONS = "https://download.uipath.com/maestro/registry/versions"


def _pin_block() -> str:
    start = TEXT.index('    connectors_library_version="${CONNECTORS_LIBRARY_VERSION:-latest}"')
    end = TEXT.index('    if [ "$sdk_status" = available ]; then', start)
    # Dockerfile line continuations → one shell script.
    return re.sub(r"\\\n", "\n", TEXT[start:end]).rstrip().removesuffix("&&")


def _resolve(version: str | None) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin"}
    if version is not None:
        env["CONNECTORS_LIBRARY_VERSION"] = version
    script = f'set -eu\n{_pin_block()}\nprintf "URL=%s\\n" "$connectors_library_url"'
    return subprocess.run(["sh", "-c", script], env=env, capture_output=True, text=True)


def test_arg_defaults_to_latest_and_is_persisted_as_env():
    assert "ARG CONNECTORS_LIBRARY_VERSION=latest" in TEXT
    assert "ENV CONNECTORS_LIBRARY_VERSION=${CONNECTORS_LIBRARY_VERSION}" in TEXT
    assert 'uip maestro registry pull --force ${connectors_library_url:+--url "$connectors_library_url"}' in TEXT
    assert "requestedVersion: $connectorsLibraryVersion" in TEXT


@pytest.mark.parametrize("version", [None, "latest"])
def test_latest_uses_the_stable_alias(version):
    run = _resolve(version)
    assert run.returncode == 0, run.stderr
    assert "URL=\n" in run.stdout


@pytest.mark.parametrize("version", ["2026.09.9", "connectors-library-2026.09.9"])
def test_build_number_pins_the_immutable_copy(version):
    run = _resolve(version)
    assert run.returncode == 0, run.stderr
    assert f"URL={VERSIONS}/connectors-library-2026.09.9/library-json.zip" in run.stdout


@pytest.mark.parametrize("version", ["v9", "2026.9.9", "Latest", "2026.09.9; rm -rf /", "../x"])
def test_anything_else_fails_the_build(version):
    run = _resolve(version)
    assert run.returncode == 1
    assert "CONNECTORS_LIBRARY_VERSION must be 'latest' or a build number" in run.stderr
