#!/usr/bin/env python3
"""
Verify that `uip` verb literals referenced in coder-eval task YAMLs actually
exist in the CLI catalog.

For every `command_executed` criterion in each task YAML, extract literal verb
tokens that follow the `uip` prefix in `command_pattern`, enumerate the
alternation paths, and check each path against `assets/uip-catalog-snapshot.json`
and `.claude/rules/cli-renames.md`.

Findings:
  - High   — pattern does not match any verb in the catalog. The success
             criterion can never fire; the task scores zero on a passing run.
  - Medium — pattern matches only retired verbs listed in cli-renames.md.
             Suggest the canonical replacement.
  - Info   — pattern is too dynamic to analyse (contains `.`, `[`, `\\w`, etc).
             Skipped — no claim made about it.

Output formats:
  - Default: human-readable, one finding per line.
  - --json:  newline-delimited JSON, suitable for piping into /lint-task.

Usage:
    python3 scripts/check-cli-verbs.py tests/tasks/uipath-rpa/smoke/build.yaml ...
    python3 scripts/check-cli-verbs.py --json tests/tasks/**/*.yaml
"""

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import sre_parse  # noqa: E402 — sre_parse is the only practical way to walk the regex AST

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "assets" / "uip-catalog-snapshot.json"
RENAMES_PATH = REPO_ROOT / ".claude" / "rules" / "cli-renames.md"

# Tokens in a regex AST we refuse to enumerate — anything that could match
# arbitrary text means we cannot pin a verb literal.
DYNAMIC_TOKENS = {
    sre_parse.ANY,
    sre_parse.IN,
    sre_parse.CATEGORY,
    sre_parse.MAX_REPEAT,
    sre_parse.MIN_REPEAT,
    sre_parse.POSSESSIVE_REPEAT,
}


def load_catalog():
    if not CATALOG_PATH.exists():
        sys.exit(f"Catalog not found at {CATALOG_PATH}. "
                 "Run scripts/build-uip-catalog.py first.")
    data = json.loads(CATALOG_PATH.read_text())
    return set(data["verbs"]), data.get("cli_version", "unknown")


def load_renames():
    """
    Parse `.claude/rules/cli-renames.md`. Expected format: a markdown table
    with at least two columns — Retired and Canonical. Lines that look like
    `| retired-verb | canonical-verb | ...` are picked up.
    """
    renames = {}
    if not RENAMES_PATH.exists():
        return renames
    for line in RENAMES_PATH.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        retired, canonical = cells[0], cells[1]
        if not retired or retired.lower() in ("retired", "---", ":---"):
            continue
        if "-" in retired and set(retired) <= set("-: "):
            continue
        renames[retired] = canonical
    return renames


def enumerate_paths(parsed, allow_partial=True):
    """
    Walk a parsed regex AST and return a list of literal strings that the
    pattern can match.

    With ``allow_partial=True`` (default), the walker stops at the first
    dynamic element (`.*`, character class, unbounded quantifier) and returns
    whatever literal prefix it has accumulated. This lets us still verify the
    verb portion of patterns like `uip\\s+tm\\s+execution\\s+list\\s+.*--flag`.

    With ``allow_partial=False``, any dynamic element causes the walker to
    return ``None`` — useful for callers that need a complete match.
    """
    paths = [""]
    for op, args in parsed:
        if op == sre_parse.LITERAL:
            paths = [p + chr(args) for p in paths]
        elif op == sre_parse.NOT_LITERAL:
            return paths if allow_partial else None
        elif op == sre_parse.SUBPATTERN:
            sub = args[3]
            sub_paths = enumerate_paths(sub, allow_partial=False)
            if sub_paths is None:
                return paths if allow_partial else None
            paths = [p + s for p in paths for s in sub_paths]
        elif op == sre_parse.BRANCH:
            branches = args[1]
            branch_paths = []
            bail = False
            for branch in branches:
                b_paths = enumerate_paths(branch, allow_partial=False)
                if b_paths is None:
                    bail = True
                    break
                branch_paths.extend(b_paths)
            if bail:
                return paths if allow_partial else None
            paths = [p + b for p in paths for b in branch_paths]
        elif op in (sre_parse.MAX_REPEAT, sre_parse.MIN_REPEAT,
                    sre_parse.POSSESSIVE_REPEAT):
            mn, mx, sub = args
            sub_paths = enumerate_paths(sub, allow_partial=False)
            if sub_paths is not None and mn == 0 and mx == 1:
                paths = [p + s for p in paths for s in ([""] + sub_paths)]
            elif sub_paths is not None and mn == 1 and mx == 1:
                paths = [p + s for p in paths for s in sub_paths]
            else:
                # Whitespace tolerance: `\s+` collapses to a single space.
                if len(sub) == 1 and sub[0][0] == sre_parse.IN:
                    inner = sub[0][1]
                    if any(t == sre_parse.CATEGORY and a == sre_parse.CATEGORY_SPACE
                           for t, a in inner):
                        paths = [p + " " for p in paths]
                        continue
                return paths if allow_partial else None
        elif op == sre_parse.AT:
            continue
        elif op == sre_parse.IN:
            inner = args
            if any(t == sre_parse.CATEGORY and a == sre_parse.CATEGORY_SPACE
                   for t, a in inner):
                paths = [p + " " for p in paths]
            else:
                return paths if allow_partial else None
        else:
            return paths if allow_partial else None
    return paths


UIP_TOKENS = {"uip", "$uip"}


def extract_verb_paths(pattern):
    """
    Parse `command_pattern`, strip the `uip` (or `(uip|$UIP)`) prefix, and
    enumerate the literal verb sequences that follow. Returns either a list
    of normalised verb-path strings, or None if the pattern is too dynamic.
    """
    try:
        parsed = sre_parse.parse(pattern)
    except re.error:
        return None
    candidates = enumerate_paths(list(parsed))
    if candidates is None:
        return None
    verb_paths = []
    for c in candidates:
        # Drop everything after the first flag marker (`--foo`, `-f`).
        c = re.split(r"\s+--?[a-zA-Z]", c, maxsplit=1)[0]
        tokens = c.strip().split()
        if not tokens or tokens[0].lower() not in UIP_TOKENS:
            continue
        verb = " ".join(tokens[1:])
        if verb:
            verb_paths.append(verb)
    return verb_paths or None


def classify(verb_paths, catalog, renames):
    """Return ('reachable'|'retired'|'unknown', details)."""
    if not verb_paths:
        return "unknown", {}

    # Try progressively shorter prefixes — `solution project add --foo` should
    # match the catalog entry `solution project add` even when the regex
    # captured a trailing flag fragment.
    def best_match(verb, lookup):
        parts = verb.split()
        for i in range(len(parts), 0, -1):
            candidate = " ".join(parts[:i])
            if candidate in lookup:
                return candidate
        return None

    reachable = []
    retired = []
    for v in verb_paths:
        if best_match(v, catalog):
            reachable.append(v)
        elif best_match(v, renames):
            retired.append(v)
    if reachable:
        return "reachable", {"reachable": reachable, "retired": retired}
    if retired:
        return "retired", {"retired": retired,
                           "suggestions": {v: renames[best_match(v, renames)]
                                           for v in retired}}
    return "unknown", {"unmatched": verb_paths}


def iter_command_patterns(spec, path):
    for idx, crit in enumerate(spec.get("success_criteria") or []):
        if not isinstance(crit, dict):
            continue
        if crit.get("type") != "command_executed":
            continue
        if crit.get("tool_name", "Bash") != "Bash":
            continue
        pattern = crit.get("command_pattern")
        if not isinstance(pattern, str):
            continue
        yield idx, pattern, crit.get("description", "")


def lint_file(path, catalog, renames):
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML is required. Install with: pip install pyyaml")
    text = path.read_text()
    try:
        spec = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [{
            "path": str(path), "severity": "Info",
            "axis": "cli-verb-reachability",
            "message": f"YAML parse error: {exc}",
        }]
    if not isinstance(spec, dict):
        return []
    findings = []
    for idx, pattern, desc in iter_command_patterns(spec, path):
        verbs = extract_verb_paths(pattern)
        if verbs is None:
            findings.append({
                "path": str(path), "severity": "Info",
                "axis": "cli-verb-reachability",
                "criterion_index": idx,
                "command_pattern": pattern,
                "message": "Pattern too dynamic to verify (wildcard / character "
                           "class / quantifier). Skipped.",
            })
            continue
        verdict, details = classify(verbs, catalog, renames)
        if verdict == "reachable":
            continue
        if verdict == "retired":
            sugg = details["suggestions"]
            findings.append({
                "path": str(path), "severity": "Medium",
                "axis": "cli-verb-reachability",
                "criterion_index": idx,
                "command_pattern": pattern,
                "description": desc,
                "message": "Pattern matches only retired verbs: "
                           + ", ".join(f"`{r}` → `{sugg[r]}`"
                                       for r in details["retired"]),
            })
        else:
            findings.append({
                "path": str(path), "severity": "High",
                "axis": "cli-verb-reachability",
                "criterion_index": idx,
                "command_pattern": pattern,
                "description": desc,
                "message": "No verb in pattern matches uip catalog "
                           f"(unmatched: {details['unmatched']}).",
            })
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path,
                        help="Task YAML files to lint")
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as newline-delimited JSON")
    args = parser.parse_args()

    catalog, version = load_catalog()
    renames = load_renames()

    all_findings = []
    for p in args.paths:
        if not p.exists():
            print(f"skip: {p} (not found)", file=sys.stderr)
            continue
        all_findings.extend(lint_file(p, catalog, renames))

    if args.json:
        for f in all_findings:
            print(json.dumps(f))
    else:
        if not all_findings:
            print(f"OK — no CLI-verb issues (catalog: uip {version}, "
                  f"{len(catalog)} verbs).")
            return
        sev_order = {"High": 0, "Medium": 1, "Info": 2, "Low": 3}
        all_findings.sort(key=lambda f: (sev_order.get(f["severity"], 9),
                                         f["path"]))
        for f in all_findings:
            print(f"[{f['severity']}] {f['path']}: {f['message']}")
            if f.get("command_pattern"):
                print(f"           pattern: {f['command_pattern']}")
        high = sum(1 for f in all_findings if f["severity"] == "High")
        med = sum(1 for f in all_findings if f["severity"] == "Medium")
        info = sum(1 for f in all_findings if f["severity"] == "Info")
        print(f"\n{high} High, {med} Medium, {info} Info "
              f"(catalog: uip {version})")
    return 1 if any(f["severity"] in ("High", "Medium") for f in all_findings) else 0


if __name__ == "__main__":
    sys.exit(main() or 0)
