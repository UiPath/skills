#!/usr/bin/env bash
#
# Launches a `uip rpa debug start` session in the background and waits until it
# suspends (breakpoint / unhandled exception) or finishes. `debug start` holds the
# session open on a suspend and never returns, so it MUST be backgrounded and polled
# — a foreground call blocks, a plain background call never notifies.
#
# Leaves the session active on a suspend; drive it afterwards with
# `uip rpa debug continue` / `continue-ignore` / `step-*` / `execution cancel`.
# Read debug.out for the streamed state (the exception is in a `[Debug] Exception:` line,
# not the returned envelope).
#
# Usage (after copying into the project dir): bash debug-run.sh <file-path> [extra uip args, e.g. --input-arguments '<json>']

set -u
out="debug.out"; : > "$out"
uip rpa debug start --file-path "$1" "${@:2}" --output json > "$out" 2>&1 &
pid=$!
until grep -qE '\[Debug\] Suspended|"hasErrors"' "$out" 2>/dev/null; do
  kill -0 "$pid" 2>/dev/null || break   # process exited (completed or hard-failed)
  sleep 1
done
tail -n 40 "$out"
