"""Locate and invoke the XAML runner (`../_runner`), the CoreWF host that loads and executes a workflow."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parent.parent / "_runner"
CANDIDATES = (Path("/opt/xaml-runner/XamlRunner.dll"), RUNNER_DIR / ".build" / "XamlRunner.dll")


class RunnerMissingError(RuntimeError):
    pass


def locate() -> list[str]:
    """The argv prefix that starts the runner, or RunnerMissingError.

    `XAML_RUNNER` wins, then the image's install, then a local `_runner/install.sh` build.
    """
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        raise RunnerMissingError("dotnet not on PATH")
    override = os.environ.get("XAML_RUNNER")
    paths = [Path(override)] if override else list(CANDIDATES)
    for dll in paths:
        if dll.exists():
            return [dotnet, str(dll)]
    raise RunnerMissingError(f"no runner build at {', '.join(str(p) for p in paths)}; run _runner/install.sh")


def _invoke(argv: list[str], timeout: float, inputs: dict | None = None) -> dict:
    # The input and result files live outside the scenario's working directory, so a
    # workflow that lists or reads its directory sees only what the scenario staged.
    with tempfile.TemporaryDirectory(prefix="xaml-runner-") as tmp:
        out = Path(tmp) / "result.json"
        if inputs is not None:
            args_file = Path(tmp) / "input.json"
            args_file.write_text(json.dumps(inputs), encoding="utf-8")
            argv = [*argv, "--input-file", str(args_file)]
        # Fixed argv, no shell.
        proc = subprocess.run(
            [*locate(), *argv, "--out", str(out)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0 or not out.exists():
            tail = (proc.stderr or proc.stdout).strip().splitlines()[-5:]
            raise RuntimeError(f"runner exited {proc.returncode}: {' | '.join(tail)}")
        return json.loads(out.read_text(encoding="utf-8"))


def inspect(xaml: Path) -> dict:
    return _invoke(["inspect", str(xaml)], timeout=120)


def run(xaml: Path, inputs: dict, cwd: Path, timeout: float = 30) -> dict:
    return _invoke(["run", str(xaml), "--cwd", str(cwd), "--timeout", str(timeout)], timeout + 60, inputs)
