"""Background fixture HTTP server. Pre-run: `start <port>`; post-run: `stop`.

PID file bridges pre_run and post_run (separate shell invocations).
"""

import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# PID file lives in the system temp dir — keeps the source-controlled
# fixture tree clean. Fixed name so the separate pre_run / post_run
# shells can both find it.
PID_FILE = Path(tempfile.gettempdir()) / "uia-cryptocom-serve.pid"
# Serve files from the cryptocom resource dir alongside this script.
SERVE_ROOT = HERE / "resources" / "cryptocom"


def _wait(port: int, timeout_s: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1).close()
            return True
        except Exception:
            time.sleep(0.2)
    return False


def start(port: int) -> int:
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=str(SERVE_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=flags,
    )
    PID_FILE.write_text(str(proc.pid))
    return 0 if _wait(port) else 1


def stop() -> int:
    if not PID_FILE.exists():
        return 0
    try:
        pid = int(PID_FILE.read_text().strip())
    except ValueError:
        PID_FILE.unlink(missing_ok=True)
        return 0
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    PID_FILE.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "start":
        sys.exit(start(int(sys.argv[2])))
    if cmd == "stop":
        sys.exit(stop())
    print("usage: serve.py {start <port> | stop}", file=sys.stderr)
    sys.exit(2)
