import json
import os
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE_SCRIPT = REPO_ROOT / "tests/scripts/stage-preview-sdk-workspace.sh"
REQUIRED_CONNECTOR = "uipath.connector.uipath-uipath-dataservice.query-entity-records"
DEFAULT_PACKAGE = "@uipath/maestro-builder-sdk"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


# The stager reads the package name from FLOW_SDK_PKG_NAME and falls back to the
# post-rename default. Both halves of that knob are covered: the unset case pins
# the default, and the old name proves the value is actually threaded through
# every place the name appears (install probe, devDependency, provenance) rather
# than hard-coded.
@pytest.mark.parametrize(
    ("sdk_package", "set_env"),
    [
        pytest.param(DEFAULT_PACKAGE, False, id="default-when-unset"),
        pytest.param(DEFAULT_PACKAGE, True, id="new-name-explicit"),
        pytest.param("@uipath/flow-sdk", True, id="old-name-via-env"),
    ],
)
def test_stages_credential_free_sdk_workspace(
    tmp_path: Path, sdk_package: str, set_env: bool
) -> None:
    sdk_root = tmp_path / "sdk"
    package_dir = sdk_root / "node_modules" / sdk_package
    package_dir.mkdir(parents=True)
    (package_dir / "package.json").write_text(
        json.dumps(
            {
                "name": sdk_package,
                "version": "3.20.0",
                "gitref": "efd27ce4c90ad76fc7f3c9b67f4920997b2cf0a8",
                "type": "module",
                "exports": "./index.js",
            }
        )
    )
    (package_dir / "index.js").write_text("export {};\n")

    assets_root = tmp_path / "assets"
    library_json = assets_root / "typescript/sdk/lib/library-json"
    library_json.mkdir(parents=True)
    (library_json / "index.json").write_text(
        json.dumps({"entries": [{"nodeType": REQUIRED_CONNECTOR}]})
    )
    registry_root = assets_root / "registry"
    registry_root.mkdir()
    registry_hash = "d34db33f"
    (registry_root / "current.json").write_text(
        json.dumps({"libraryHash": registry_hash})
    )

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_executable(
        bin_dir / "uip",
        "#!/bin/sh\n[ \"$*\" = \"maestro flow compile --help\" ]\n",
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "package.json").write_text(
        json.dumps({"scripts": {"keep": "true"}})
    )
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "PREVIEW_FLOW_SDK_ROOT": str(sdk_root),
        "PREVIEW_FLOW_SDK_ASSETS_ROOT": str(assets_root),
        "UIP_MAESTRO_REGISTRY_HOME": str(registry_root),
        "FLOW_SDK_LIBRARY_JSON": str(library_json),
    }
    env.pop("FLOW_SDK_PKG_NAME", None)
    if set_env:
        env["FLOW_SDK_PKG_NAME"] = sdk_package

    completed = subprocess.run(
        ["bash", str(STAGE_SCRIPT)],
        cwd=workspace,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"{sdk_package}@3.20.0" in completed.stdout
    assert (workspace / "node_modules").is_symlink()
    assert (workspace / "node_modules").resolve() == sdk_root / "node_modules"
    package_json = json.loads((workspace / "package.json").read_text())
    assert package_json["scripts"] == {"keep": "true"}
    assert package_json["devDependencies"] == {sdk_package: "3.20.0"}
    assert "flowSdk" not in package_json
    assert json.loads((workspace / "preview-sdk-provenance.json").read_text()) == {
        "package": sdk_package,
        "version": "3.20.0",
        "gitref": "efd27ce4c90ad76fc7f3c9b67f4920997b2cf0a8",
        "connector_library": True,
        "connector_library_hash": registry_hash,
    }
