"""Round-trip diff: what a Studio Web load + save did to a case project (MST-15831).

Compares two copies of one case project directory, before (as uploaded) and after (as
pulled back), file by file. JSON files are compared leaf by leaf: a path present only
after is ADDED, only before is DROPPED, and on both with a different value is REWRITTEN.
Non-JSON files are compared by bytes. Paths are written with object keys and list
indices; list elements that carry an `id` are keyed by it, so a reorder is not reported
as every element rewritten.

Each divergence is then matched against the committed prediction (PREDICTION.json):
a rule names a file, a path pattern (fnmatch over the dotted path) and the change it
expects. A divergence no rule predicts is a SURPRISE; a predicted change that did not
happen is a MISS. Both are findings: the prediction is scored both ways.

Run: python3 roundtrip_diff.py <before_dir> <after_dir> [--prediction PREDICTION.json] [--json]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys

MISSING = object()


def leaves(node, path=""):
    if isinstance(node, dict):
        if not node:
            yield path, {}
        for key, value in node.items():
            yield from leaves(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        if not node:
            yield path, []
        keyed = all(isinstance(v, dict) and "id" in v for v in node) and len({v["id"] for v in node}) == len(node)
        for i, value in enumerate(node):
            yield from leaves(value, f"{path}[{value['id'] if keyed else i}]")
    else:
        yield path, node


def files(root: str) -> dict[str, str]:
    out = {}
    for dirpath, _, names in os.walk(root):
        for name in names:
            full = os.path.join(dirpath, name)
            out[os.path.relpath(full, root)] = full
    return out


def load(path: str):
    with open(path, "rb") as fh:
        raw = fh.read()
    if path.endswith((".json", ".uiproj", ".uipx")):
        try:
            return json.loads(raw.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError):
            pass
    return raw


def diff(before_dir: str, after_dir: str) -> list[dict]:
    a, b = files(before_dir), files(after_dir)
    out = []
    for rel in sorted(set(a) | set(b)):
        if rel not in b:
            out.append({"file": rel, "path": "", "change": "file-dropped"})
            continue
        if rel not in a:
            out.append({"file": rel, "path": "", "change": "file-added"})
            continue
        x, y = load(a[rel]), load(b[rel])
        if isinstance(x, bytes) or isinstance(y, bytes):
            if x != y:
                out.append({"file": rel, "path": "", "change": "bytes-rewritten"})
            continue
        lx, ly = dict(leaves(x)), dict(leaves(y))
        for path in sorted(set(lx) | set(ly)):
            before, after = lx.get(path, MISSING), ly.get(path, MISSING)
            if before is MISSING:
                out.append({"file": rel, "path": path, "change": "added", "after": after})
            elif after is MISSING:
                out.append({"file": rel, "path": path, "change": "dropped", "before": before})
            elif before != after:
                out.append({"file": rel, "path": path, "change": "rewritten", "before": before, "after": after})
    return out


def path_matches(path: str, pattern: str) -> bool:
    """`*` is any run of characters; `[*]` is any one list index or id. Unlike fnmatch,
    brackets are literal, since every list step in a path is written in brackets."""
    rx = re.escape(pattern).replace(r"\[\*\]", r"\[[^\]]*\]").replace(r"\*", ".*")
    return re.fullmatch(rx, path) is not None


def score(divergences: list[dict], rules: list[dict]) -> tuple[dict, list, list, list]:
    """Each divergence goes to the first rule that matches it; unmatched ones are surprises.
    A rule with `expect: "change"` that matched nothing is a miss; a rule with
    `expect: "survive"` that matched anything is violated (its matches are surprises)."""
    hits = {i: [] for i in range(len(rules))}
    surprises = []
    for d in divergences:
        for i, r in enumerate(rules):
            if fnmatch.fnmatch(d["file"], r["file"]) and path_matches(d["path"], r.get("path", "*")) \
                    and d["change"] in r.get("changes", [d["change"]]):
                hits[i].append(d)
                break
        else:
            surprises.append(d)
    misses = [r for i, r in enumerate(rules) if r["expect"] == "change" and not hits[i]]
    violated = [(r, hits[i]) for i, r in enumerate(rules) if r["expect"] == "survive" and hits[i]]
    return hits, misses, violated, surprises


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--prediction")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    divergences = diff(args.before, args.after)
    if not args.prediction:
        if args.json:
            json.dump(divergences, sys.stdout, indent=1, default=str)
        else:
            for d in divergences:
                print(d["change"], d["file"], d["path"], d.get("before", ""), "->", d.get("after", ""))
        return 0
    with open(args.prediction, encoding="utf-8") as fh:
        rules = json.load(fh)["rules"]
    hits, misses, violated, surprises = score(divergences, rules)
    report = {
        "divergences": len(divergences),
        "predicted": [{"rule": r["id"], "expect": r["expect"], "matched": len(hits[i])} for i, r in enumerate(rules)],
        "misses": [r["id"] for r in misses],
        "violated": [{"rule": r["id"], "examples": h[:5]} for r, h in violated],
        "surprises": surprises,
    }
    json.dump(report, sys.stdout, indent=1, default=str)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
