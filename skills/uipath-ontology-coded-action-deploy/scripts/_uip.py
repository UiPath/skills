"""The uip CLI boundary, and the stdout/stderr contract every script here keeps.

Two rules live in this file. Errors go to stderr and data to stdout, so a caller parsing stdout
never reads a failure as a result. And every command is an argv list: no shell, no interpolation.

uip_json and uip_plain are separate deliberately. Some commands interleave a {solutionKey} log
line with their JSON, which breaks a strict parse, so the plain variant exists for those.
"""

import json
import os
import subprocess
import sys

UIP = os.environ.get("UIP_CLI", "uip")


def die(message, **extra):
    """Errors go to stderr, never stdout: a caller parsing stdout must not see a failure as data."""
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload), file=sys.stderr)
    raise SystemExit(1)


def emit(payload):
    print(json.dumps(payload, indent=2))


def uip_json(argv, allow_fail=False):
    """Run a uip command and parse its stdout as JSON.

    Capture stdout ONLY. `uip` writes a long INFO log to stderr even at --log-level error, and one
    of those lines contains a literal "{solutionKey}"; folding stderr in makes the first brace in
    the stream a log line, so the JSON parse silently yields nothing.
    """
    proc = subprocess.run([UIP] + argv + ["--output", "json", "--log-level", "error"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        if allow_fail:
            return None
        tail = " ".join((proc.stderr or "").strip().splitlines()[-5:])
        die("uip %s failed" % " ".join(argv), detail=tail)
    try:
        return json.loads(proc.stdout)
    except ValueError:
        if allow_fail:
            return None
        die("uip %s returned unparseable JSON" % " ".join(argv), stdout=proc.stdout[:400])


def uip_plain(argv, cwd):
    """Run a uip command whose output is human text, not JSON (e.g. `uip functions pack`)."""
    proc = subprocess.run([UIP] + argv, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        tail = " ".join((proc.stderr or proc.stdout or "").strip().splitlines()[-5:])
        die("uip %s failed in %s" % (" ".join(argv), cwd), detail=tail)
    return proc.stdout


def described(describe):
    """True when the caller asked for this script's contract instead of running it.

    Answered before argparse, so a script with required positionals can still be interrogated.
    The skill's Scripts table is generated from these, and a test asserts the two agree.
    """
    if "--describe" not in sys.argv[1:]:
        return False
    print(json.dumps(describe, indent=2, sort_keys=True))
    return True
