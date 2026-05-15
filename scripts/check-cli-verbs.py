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
import collections
import datetime as dt
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


def _trim_to_word_boundary(paths):
    """Trim each path to the last whitespace if it ends mid-word.

    Called when the walker bails on a partial match — we must not return a
    literal that ends inside a token, because the downstream extractor would
    treat the truncated chunk as a complete verb (e.g. `uip\\s+solution\\w+`
    accumulates `"uip solution"` and would yield verb `"solution"` even
    though the regex never matches that literal alone).
    """
    out = []
    for p in paths:
        if p and not p[-1].isspace():
            idx = p.rfind(" ")
            if idx == -1:
                continue
            p = p[:idx]
        out.append(p)
    return out


def enumerate_paths(parsed, allow_partial=True):
    """
    Walk a parsed regex AST and return a list of literal strings that the
    pattern can match.

    With ``allow_partial=True`` (default), the walker stops at the first
    dynamic element (`.*`, character class, unbounded quantifier) and returns
    whatever literal prefix it has accumulated, trimmed back to the last
    whitespace so we never return a mid-token literal. This lets us still
    verify the verb portion of patterns like
    `uip\\s+tm\\s+execution\\s+list\\s+.*--flag`.

    With ``allow_partial=False``, any dynamic element causes the walker to
    return ``None`` — useful for callers that need a complete match.
    """
    paths = [""]
    for op, args in parsed:
        if op == sre_parse.LITERAL:
            paths = [p + chr(args) for p in paths]
        elif op == sre_parse.NOT_LITERAL:
            return _trim_to_word_boundary(paths) if allow_partial else None
        elif op == sre_parse.SUBPATTERN:
            sub = args[3]
            sub_paths = enumerate_paths(sub, allow_partial=False)
            if sub_paths is None:
                return _trim_to_word_boundary(paths) if allow_partial else None
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
                return _trim_to_word_boundary(paths) if allow_partial else None
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
                return _trim_to_word_boundary(paths) if allow_partial else None
        elif op == sre_parse.AT:
            continue
        elif op == sre_parse.IN:
            inner = args
            if any(t == sre_parse.CATEGORY and a == sre_parse.CATEGORY_SPACE
                   for t, a in inner):
                paths = [p + " " for p in paths]
            else:
                return _trim_to_word_boundary(paths) if allow_partial else None
        else:
            return _trim_to_word_boundary(paths) if allow_partial else None
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
    # Dedup while preserving order — alternations like `(uip|$UIP)` produce
    # duplicate downstream paths that would otherwise inflate report counts.
    verb_paths = list(dict.fromkeys(verb_paths))
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


def write_report(findings, catalog_size, version, output_path):
    """Render findings to a markdown audit report."""
    by_sev = collections.Counter(f["severity"] for f in findings)
    files_with = {sev: sorted({f["path"] for f in findings
                               if f["severity"] == sev})
                  for sev in ("High", "Medium", "Info")}
    unmatched = collections.Counter()
    for f in findings:
        if f["severity"] != "High":
            continue
        m = re.search(r"unmatched: \[(.+?)\]", f["message"])
        if m:
            for v in m.group(1).split(","):
                unmatched[v.strip().strip("'\"")] += 1
    by_skill_high = collections.Counter()
    for f in findings:
        if f["severity"] != "High":
            continue
        parts = Path(f["path"]).parts
        if len(parts) >= 3 and parts[0] == "tests" and parts[1] == "tasks":
            by_skill_high[parts[2]] += 1

    now = dt.datetime.now(dt.timezone.utc).isoformat(
        timespec="seconds").replace("+00:00", "Z")
    out = [
        "# CLI Verb Reachability Audit\n",
        f"*Generated: {now}*  ",
        f"*Catalog: uip {version} — {catalog_size} reachable verbs*\n",
        "Generated by `scripts/check-cli-verbs.py --report` against task "
        "YAMLs under `tests/tasks/`.\n",
        "## Summary\n",
        "| Severity | Findings | Files affected |",
        "|---|---|---|",
        f"| **High** (verb not in catalog) | {by_sev.get('High', 0)} | "
        f"{len(files_with['High'])} |",
        f"| **Medium** (verb retired per `cli-renames.md`) | "
        f"{by_sev.get('Medium', 0)} | {len(files_with['Medium'])} |",
        f"| **Info** (pattern too dynamic to verify) | "
        f"{by_sev.get('Info', 0)} | {len(files_with['Info'])} |\n",
    ]
    if unmatched:
        out.append("## High findings — verbs not in catalog\n")
        out.append("| Count | Verb path |\n|---|---|")
        for verb, n in unmatched.most_common(40):
            out.append(f"| {n} | `{verb}` |")
        out.append("")
    if by_skill_high:
        out.append("### High findings by skill\n")
        out.append("| Skill | High findings |\n|---|---|")
        for skill, n in sorted(by_skill_high.items(), key=lambda x: -x[1]):
            out.append(f"| `{skill}` | {n} |")
        out.append("")
    if by_sev.get("High", 0):
        out.append("### All High findings\n")
        for f in sorted([x for x in findings if x["severity"] == "High"],
                        key=lambda x: x["path"]):
            out.append(f"- **`{f['path']}`** (criterion "
                       f"{f['criterion_index']})  ")
            out.append(f"  pattern: `{f['command_pattern']}`  ")
            out.append(f"  {f['message']}")
        out.append("")
    out.append("## Info findings — patterns skipped\n")
    out.append(f"{by_sev.get('Info', 0)} patterns could not be statically "
               "enumerated (contain `.*`, character classes, or unbounded "
               "quantifiers). Skipped without a verdict.\n")
    out.append("## Reproducing\n")
    out.append("```bash\nfind tests/tasks -name '*.yaml' "
               "-not -path '*/activation/*' -not -path '*/_shared/*' \\\n  "
               "| xargs python3 scripts/check-cli-verbs.py "
               f"--report {output_path}\n```\n")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path,
                        help="Task YAML files to lint")
    parser.add_argument("--json", action="store_true",
                        help="Emit findings as newline-delimited JSON")
    parser.add_argument("--report", type=Path, metavar="PATH",
                        help="Write a markdown audit report to PATH "
                             "(suppresses stdout text output)")
    args = parser.parse_args()

    catalog, version = load_catalog()
    renames = load_renames()

    all_findings = []
    for p in args.paths:
        if not p.exists():
            print(f"skip: {p} (not found)", file=sys.stderr)
            continue
        all_findings.extend(lint_file(p, catalog, renames))

    if args.report:
        write_report(all_findings, len(catalog), version, args.report)
        print(f"wrote {args.report} "
              f"({sum(1 for f in all_findings if f['severity']=='High')} High, "
              f"{sum(1 for f in all_findings if f['severity']=='Medium')} Medium, "
              f"{sum(1 for f in all_findings if f['severity']=='Info')} Info)")
        return 1 if any(f["severity"] in ("High", "Medium")
                        for f in all_findings) else 0

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
