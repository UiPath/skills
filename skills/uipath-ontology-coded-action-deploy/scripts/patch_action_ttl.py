#!/usr/bin/env python3
"""Patch the deployed Orchestrator coordinates into ONE coded-action TTL.

    patch_action_ttl.py <file.ttl> --folder-id <numericId> [--execute]

Generation writes ont:processFolderId "PENDING_DEPLOY"; this replaces it with the numeric folder
id of the deployment that now carries the job. One file per action, one call per file: the
per-action layout is what makes this a substitution rather than surgery on a shared artifact.

ont:process is never touched. A release is matched on Name or ProcessKey and never on version, so
the process name survives a new release; only the folder moves.

Refusals, both of them deliberate:

  ont:processFolderId absent        this is not a coded-action TTL, or generation did not emit
                                    the placeholder. Patching a file that never declared the
                                    predicate would produce a TTL that parses and resolves
                                    nothing at invoke time.
  ont:processFolderId more than     two definitions of one action merge in RDF and the runtime
  once                              sees an arbitrary one. Editing either is guesswork.

Idempotent: a file that already carries the requested value is reported as a no-op, exit 0.

Writes nothing without --execute. The default prints the current and intended values.
"""

import argparse
import json
import pathlib
import re
import sys
from _uip import described

# The predicate, its quoted value, and the separator that follows. Matching the separator keeps
# the rewritten line valid Turtle whichever of ; , . closed the original.
FOLDER_RE = re.compile(r'^(?P<indent>\s*)ont:processFolderId(?P<gap>\s+)"(?P<value>[^"]*)"'
                       r'(?P<tail>\s*)(?P<sep>[;,.])(?P<rest>.*)$')


DESCRIBE = {
    "name": "patch_action_ttl",
    "purpose": "Replace the PENDING_DEPLOY placeholder with the resolved folder id",
    "phase": "5 - patch",
    "inputs": {"env": [], "args": ["ttl", "--folder-id", "--execute"]},
    "outputs": {"patched": "the file written", "folderId": "the id written into it"},
    "mutates": True,
    "exit_codes": {"0": "ok, result on stdout", "1": "refused or failed, reason on stderr"},
}


def die(message, **extra):
    payload = {"ok": False, "error": message}
    payload.update(extra)
    print(json.dumps(payload), file=sys.stderr)
    raise SystemExit(1)


def locate(lines, pattern, predicate, required):
    hits = [(i, m) for i, line in enumerate(lines) for m in [pattern.match(line)] if m]
    if len(hits) > 1:
        die("%s appears %d times in this file; refusing to guess which one binds the action"
            % (predicate, len(hits)), lines=[i + 1 for i, _ in hits])
    if not hits and required:
        die("%s not found; this is not a coded-action TTL, or generation never emitted the "
            "PENDING_DEPLOY placeholder" % predicate)
    return hits[0] if hits else (None, None)


def rewrite(match, value, sep=None):
    return '%sont:processFolderId%s"%s"%s%s%s' % (
        match.group("indent"), match.group("gap"), value,
        match.group("tail"), sep or match.group("sep"), match.group("rest"))


def main():
    if described(DESCRIBE):
        return
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ttl", help="one per-action TTL file")
    ap.add_argument("--folder-id", required=True, help="numeric Orchestrator folder id")
    ap.add_argument("--execute", action="store_true", help="write; default prints the change")
    args = ap.parse_args()

    if not str(args.folder_id).isdigit():
        die("--folder-id must be the numeric Orchestrator folder id, not %r" % args.folder_id)

    path = pathlib.Path(args.ttl).expanduser().resolve()
    if not path.is_file():
        die("no such file: %s" % path)

    lines = path.read_text().splitlines(keepends=True)
    stripped = [line.rstrip("\n") for line in lines]

    idx, match = locate(stripped, FOLDER_RE, "ont:processFolderId", required=True)
    current = match.group("value")

    changes = []
    if current != args.folder_id:
        changes.append({"predicate": "ont:processFolderId", "line": idx + 1,
                        "from": current, "to": args.folder_id})

    if not changes:
        print(json.dumps({"ok": True, "noop": True, "file": str(path),
                          "folderId": current,
                          "reason": "already patched"}, indent=2))
        return

    if not args.execute:
        print(json.dumps({"ok": True, "dryRun": True, "file": str(path),
                          "changes": changes}, indent=2))
        return

    newline = "\n" if lines[idx].endswith("\n") else ""
    lines[idx] = rewrite(match, args.folder_id) + newline

    path.write_text("".join(lines))
    print(json.dumps({"ok": True, "file": str(path), "changes": changes}, indent=2))


if __name__ == "__main__":
    main()
