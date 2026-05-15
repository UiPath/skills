#!/usr/bin/env python3
"""
Scan skill markdown files for `uip <verb>` references and verify each one
against the CLI catalog at assets/uip-catalog-snapshot.json.

How it works:
  1. For each .md file under skills/, find every line containing `uip ` and
     extract the token sequence that follows.
  2. Walk tokens until hitting a flag (`-x`, `--xxx`), shell operator, or
     end-of-line. Placeholder tokens (`<arg>`, `[arg]`, `$VAR`, `...`) are
     treated as wildcards — they break the verb path but don't disqualify
     the prefix before them.
  3. Match the leading literal-token prefix against the catalog. The longest
     prefix that is a real verb wins. If no literal token matches, the
     reference is reported as a finding.

Outputs:
  - Default: one finding per line, human-readable.
  - --json : newline-delimited JSON for downstream tooling.

Usage:
    python3 scripts/check-skill-verbs.py skills/
    python3 scripts/check-skill-verbs.py --json skills/uipath-rpa/SKILL.md ...
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "assets" / "uip-catalog-snapshot.json"

# `uip` followed by at least one space, then the rest of the line up to a
# code-block end backtick or newline.
UIP_LINE = re.compile(r"\buip(\s+[^\n`]*)?")

# Tokens that look like placeholders or non-verb content.
PLACEHOLDER = re.compile(r"^(<.+?>|\[.+?\]|\$\{?[A-Za-z_]\w*\}?|\.\.\.|\*+)$")
# Tokens that start a flag — stop verb extraction here.
FLAG = re.compile(r"^-{1,2}[A-Za-z]")
# Shell operators / control characters that end a command segment.
SHELL_STOP = {"|", "||", "&&", ";", ">", ">>", "<", "2>", "2>&1"}
# Strip trailing punctuation that markdown formatting can leave behind.
TRAILING_PUNCT = re.compile(r"[`,.;:)\]\"'\\]+$")
LEADING_PUNCT = re.compile(r"^[`(\[\"']+")


def load_catalog():
    if not CATALOG_PATH.exists():
        sys.exit(f"Catalog not found at {CATALOG_PATH}. "
                 "Run scripts/build-uip-catalog.py first.")
    data = json.loads(CATALOG_PATH.read_text())
    return (
        set(data["verbs"]),
        set(data.get("unwalkable_groups", [])),
        data.get("cli_version", "unknown"),
    )


def clean_token(tok):
    tok = TRAILING_PUNCT.sub("", tok)
    tok = LEADING_PUNCT.sub("", tok)
    return tok


def extract_verb_tokens(tail):
    """
    Given the text after `uip`, return the list of literal verb tokens
    leading up to the first flag/placeholder/shell-stop, or [] if the line
    has no usable verb path.
    """
    tail = tail.strip()
    if not tail:
        return []
    # Cut at obvious end-of-statement markers.
    for stop in ["\\\n", "\n"]:
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    raw_tokens = tail.split()
    verb = []
    for raw in raw_tokens:
        tok = clean_token(raw)
        if not tok:
            break
        if FLAG.match(tok):
            break
        if tok in SHELL_STOP:
            break
        if PLACEHOLDER.match(tok):
            # Placeholder — stop here. Whatever came before is the verb.
            break
        # Reject things that clearly aren't verbs: paths, JSON snippets,
        # filenames, quoted strings.
        if any(ch in tok for ch in "/={}\"'"):
            break
        # Stop if the token starts looking like a value (digits-only).
        if tok.replace("-", "").replace("_", "").isdigit():
            break
        verb.append(tok)
    return verb


def best_prefix(tokens, catalog):
    """Return the longest token prefix that exists in the catalog, or None."""
    for n in range(len(tokens), 0, -1):
        prefix = " ".join(tokens[:n])
        if prefix in catalog:
            return prefix
    return None


def scan_file(path, catalog, unwalkable):
    """Yield findings with severity (Stale|Uncertain)."""
    findings = []
    try:
        text = path.read_text()
    except (UnicodeDecodeError, OSError):
        return findings
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in UIP_LINE.finditer(line):
            tail = match.group(1) or ""
            tokens = extract_verb_tokens(tail)
            if not tokens:
                continue
            verb_path = " ".join(tokens)
            match_str = best_prefix(tokens, catalog)
            if match_str == verb_path:
                continue  # exact catalog hit
            if match_str is None and len(tokens) == 1 and tokens[0] in ("CLI", "is", "a", "the"):
                continue  # noise like "the uip CLI ..."
            # Severity: if any catalog prefix sits under an unwalkable group,
            # we cannot verify the rest of the path — call it Uncertain.
            severity = "Stale"
            for n in range(len(tokens), 0, -1):
                prefix = " ".join(tokens[:n])
                if prefix in unwalkable or tokens[0] in unwalkable:
                    severity = "Uncertain"
                    break
            findings.append({
                "line": lineno,
                "verb_path": verb_path,
                "matched_prefix": match_str,
                "severity": severity,
                "context": line.strip(),
            })
    return findings


def iter_markdown(roots):
    for root in roots:
        root = Path(root)
        if root.is_file() and root.suffix == ".md":
            yield root
            continue
        if root.is_dir():
            for p in sorted(root.rglob("*.md")):
                yield p


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path,
                        help="Files or directories to scan (e.g. skills/)")
    parser.add_argument("--json", action="store_true",
                        help="Emit newline-delimited JSON instead of text")
    args = parser.parse_args()

    catalog, unwalkable, version = load_catalog()

    all_findings = []
    for path in iter_markdown(args.paths):
        for f in scan_file(path, catalog, unwalkable):
            f["path"] = str(path)
            all_findings.append(f)

    if args.json:
        for f in all_findings:
            print(json.dumps(f))
        return 0

    stale = [f for f in all_findings if f["severity"] == "Stale"]
    uncertain = [f for f in all_findings if f["severity"] == "Uncertain"]

    if not stale and not uncertain:
        print(f"OK — no stale uip verbs found (catalog: uip {version}, "
              f"{len(catalog)} verbs).")
        return 0

    print(f"{len(stale)} Stale, {len(uncertain)} Uncertain findings "
          f"(catalog: uip {version}, {len(catalog)} verbs, "
          f"{len(unwalkable)} unwalkable groups)\n")
    if stale:
        by_verb = collections.Counter(f["verb_path"] for f in stale)
        by_file = collections.Counter(f["path"] for f in stale)
        print("Top stale verb paths:")
        for verb, n in by_verb.most_common(20):
            print(f"  {n:3d}  {verb}")
        print("\nFiles with most stale findings:")
        for path, n in by_file.most_common(15):
            print(f"  {n:3d}  {path}")
    if uncertain:
        print(f"\n{len(uncertain)} Uncertain findings under unwalkable groups "
              f"({', '.join(sorted(unwalkable))}) — not counted as stale.")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
