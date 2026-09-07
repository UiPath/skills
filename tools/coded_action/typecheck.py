"""Compile one job against a stub of the Coded Functions SDK.

The stub, not the real package: the check is about the job's own types, and requiring an install
would make the gate depend on whether someone had run npm. R extends the declared output type is
what keeps the op-widening trap detectable -- an inline edit literal widens 'UPDATE' to string,
and only a compiler notices.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


SDK_MODULE = "@uipath/coded-functions-js-sdk"


TSC_FLAGS = (
    "--noEmit",
    "--strict",
    "--target",
    "ES2022",
    "--module",
    "ESNext",
    "--moduleResolution",
    "bundler",
    "--skipLibCheck",
)
# The stub keeps handler-satisfies-Output. The handler's return type is its own parameter
# constrained by O rather than plain O: typed as plain O, inference widens O to whatever the
# handler happens to return and the DeclaredEdit op-widening trap compiles clean.


SDK_STUB = """export declare function type<T>(): T;
export declare function defineFunction<I, O, R extends O>(config: {
  name: string;
  description?: string;
  method?: string;
  path?: string;
  input: I;
  output: O;
  handler: (input: I) => R | Promise<R>;
}): unknown;
"""


def find_tsc(workdir: Path) -> tuple[list[str] | None, str]:
    candidates: list[list[str]] = []
    override = os.environ.get("CODED_ACTION_TSC")
    if override:
        candidates.append([override])
    on_path = shutil.which("tsc")
    if on_path:
        candidates.append([on_path])
    for parent in [workdir.resolve(), *workdir.resolve().parents]:
        local = parent / "node_modules" / ".bin" / "tsc"
        if local.is_file():
            candidates.append([str(local)])
    candidates.append(["npx", "--no-install", "tsc"])
    for command in candidates:
        try:
            proc = subprocess.run(command + ["--version"], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError):
            continue
        # The npm package literally named `tsc` is not the compiler and answers --version happily,
        # so the banner is checked rather than the exit code.
        if re.search(r"Version \d+\.\d+", proc.stdout):
            return command, ""
    return None, "no TypeScript compiler found (tried CODED_ACTION_TSC, PATH, node_modules/.bin, npx --no-install)"


def typecheck_job(job: Path, workdir: Path) -> tuple[str, str]:
    """('passed'|'failed'|'skipped', detail) for one TypeScript job, compiled against an SDK stub.

    The job imports nothing but the SDK, and the SDK is stubbed here, so nothing needs installing
    for this to run.
    """
    command, reason = find_tsc(workdir)
    if command is None:
        return "skipped", reason
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stub = root / "node_modules" / SDK_MODULE
        stub.mkdir(parents=True)
        (stub / "index.d.ts").write_text(SDK_STUB, encoding="utf-8")
        (stub / "package.json").write_text(
            json.dumps({"name": SDK_MODULE, "version": "0.0.0", "types": "index.d.ts"}), encoding="utf-8"
        )
        copy = root / job.name
        copy.write_text(job.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            proc = subprocess.run(
                command + list(TSC_FLAGS) + [copy.name], capture_output=True, text=True, timeout=300, cwd=root
            )
        except (OSError, subprocess.SubprocessError) as error:
            return "skipped", f"could not run the compiler: {error}"
        if proc.returncode == 0:
            return "passed", ""
        lines = [line.strip() for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
        return "failed", "; ".join(lines[:3]) or f"tsc exited {proc.returncode} with no output"
