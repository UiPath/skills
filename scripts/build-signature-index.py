#!/usr/bin/env python3
"""
Build and validate the uipath-troubleshoot signature index from playbook
frontmatter (the canonical source).

Every playbook under skills/uipath-troubleshoot/references/**/playbooks/*.md
declares its routable error signatures in YAML frontmatter:

    ---
    confidence: high
    signatures:
      - kind: exception
        value: "UiPath.UIAutomationNext.Exceptions.VerifyActivityExecutionException"
      - kind: message-key
        value: "ExceptionCheckActivity"
        note: "generic assertion failure — this playbook's main target"
    exclusions:
      - "ExceptionCheckActivityTypeInto* → verify-execution-typeinto.md"
    ---

Playbooks with no crisp machine-matchable signature declare `silent: true`
instead of `signatures:` — they are reachable only via the no-signature
routing table (hand-maintained section of the index).

Checks (default mode):
  1. Frontmatter parses and declares a legal confidence (high|medium|low).
  2. Every playbook has >=1 signature OR `silent: true` (not both).
  3. Every signature has a legal kind and a non-empty value.
  4. A (kind, value) pair claimed by 2+ playbooks requires a `note`
     (discriminator) on every claiming row.
  5. Playbook files referenced from `exclusions` entries exist.

Index generation:
  --write-index  regenerate the table between the markers
                 `<!-- BEGIN GENERATED SIGNATURES -->` / `<!-- END ... -->`
                 in references/signature-index.md.
  --check-index  fail if the generated table is out of date (CI uses this).

Usage:
    python3 scripts/build-signature-index.py
    python3 scripts/build-signature-index.py --write-index
    python3 scripts/build-signature-index.py --check-index
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFS_DIR = REPO_ROOT / "skills" / "uipath-troubleshoot" / "references"
INDEX_PATH = REFS_DIR / "signature-index.md"

CONFIDENCES = {"high", "medium", "low"}
KINDS = {
    "exception",        # exception class FQN or leaf (e.g. NodeNotFoundException)
    "message",          # verbatim message fragment
    "message-key",      # localization resource key (e.g. ExceptionCheckActivity)
    "error-code",       # exact error code (e.g. DAP-GE-3000, 170002)
    "error-code-prefix",# error code family prefix (e.g. DAP-GE-)
    "http-status",      # HTTP status relevant to the failure surface
    "state",            # entity state / status field value (e.g. Pending + PendingReasons code)
}

BEGIN_MARKER = "<!-- BEGIN GENERATED SIGNATURES -->"
END_MARKER = "<!-- END GENERATED SIGNATURES -->"
BLOCK_RE = re.compile(
    re.escape(BEGIN_MARKER) + r"(.*?)" + re.escape(END_MARKER), re.DOTALL
)
EXCLUSION_FILE_RE = re.compile(r"([a-z0-9][a-z0-9-]*\.md)")


def split_frontmatter(text):
    """Return frontmatter text between the --- fences, or None if absent."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Parse the restricted frontmatter subset used by playbooks.

    Supports scalar keys (confidence, silent), a list of mappings
    (signatures), and a list of strings (exclusions). Returns a dict;
    raises ValueError on lines that fit none of those shapes.
    """
    data = {"confidence": None, "silent": False, "signatures": [], "exclusions": []}
    current_list = None
    current_item = None

    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()

        if indent == 0:
            current_item = None
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"unparseable frontmatter line: {line!r}")
            key, value = key.strip(), value.strip()
            if key in ("signatures", "exclusions") and not value:
                current_list = key
            else:
                current_list = None
                if key == "confidence":
                    data["confidence"] = unquote(value)
                elif key == "silent":
                    data["silent"] = value.lower() == "true"
                else:
                    data.setdefault("extra_keys", []).append(key)
        elif line.startswith("- "):
            if current_list is None:
                raise ValueError(f"list item outside a list: {line!r}")
            item = line[2:].strip()
            if current_list == "exclusions":
                data["exclusions"].append(unquote(item))
                current_item = None
            else:
                current_item = {}
                data["signatures"].append(current_item)
                if item:
                    key, sep, value = item.partition(":")
                    if not sep:
                        raise ValueError(f"unparseable signature field: {item!r}")
                    current_item[key.strip()] = unquote(value)
        else:
            if current_item is None:
                raise ValueError(f"unexpected continuation line: {line!r}")
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError(f"unparseable signature field: {line!r}")
            current_item[key.strip()] = unquote(value)

    return data


def discover_playbooks():
    return sorted(
        p for p in REFS_DIR.rglob("*.md")
        if p.parent.name == "playbooks"
    )


def rel(path):
    return path.relative_to(REFS_DIR).as_posix()


def load_all():
    """Return (entries, findings). entries: list of (relpath, parsed dict)."""
    entries = []
    findings = []
    playbooks = discover_playbooks()
    playbook_names = {p.name for p in playbooks}

    def flag(path, error):
        findings.append({"playbook": rel(path), "error": error})

    for path in playbooks:
        fm_text = split_frontmatter(path.read_text(encoding="utf-8"))
        if fm_text is None:
            flag(path, "missing frontmatter")
            continue
        try:
            data = parse_frontmatter(fm_text)
        except ValueError as e:
            flag(path, f"frontmatter parse error: {e}")
            continue

        if data["confidence"] not in CONFIDENCES:
            flag(path, f"invalid confidence {data['confidence']!r} "
                       f"(expected one of {sorted(CONFIDENCES)})")
        if data["silent"] and data["signatures"]:
            flag(path, "declares both silent: true and signatures")
        if not data["silent"] and not data["signatures"]:
            flag(path, "no signatures and not silent: true — unroutable")
        for sig in data["signatures"]:
            kind = sig.get("kind")
            if kind not in KINDS:
                flag(path, f"invalid signature kind {kind!r} "
                           f"(expected one of {sorted(KINDS)})")
            if not sig.get("value", "").strip():
                flag(path, f"signature with empty value (kind={kind!r})")
        for exc in data["exclusions"]:
            for name in EXCLUSION_FILE_RE.findall(exc):
                if name not in playbook_names:
                    flag(path, f"exclusion references missing playbook {name!r}")

        entries.append((rel(path), data))

    # Duplicate (kind, value) pairs across playbooks need discriminating notes.
    claims = {}
    for relpath, data in entries:
        for sig in data["signatures"]:
            key = (sig.get("kind"), sig.get("value"))
            claims.setdefault(key, []).append((relpath, sig))
    for (kind, value), rows in claims.items():
        if len(rows) > 1:
            for relpath, sig in rows:
                if not sig.get("note", "").strip():
                    findings.append({
                        "playbook": relpath,
                        "error": f"signature ({kind}, {value!r}) is claimed by "
                                 f"{len(rows)} playbooks and needs a discriminating "
                                 "note on every claim",
                    })

    return entries, findings


def cell(text):
    return text.replace("|", "\\|")


def build_table(entries):
    lines = ["| signature | kind | playbook | confidence | note |",
             "|---|---|---|---|---|"]
    rows = []
    for relpath, data in entries:
        for sig in data["signatures"]:
            rows.append((sig.get("value", ""), sig.get("kind", ""), relpath,
                         data["confidence"] or "", sig.get("note", "")))
    rows.sort(key=lambda r: (r[0].lower(), r[2]))
    for value, kind, relpath, confidence, note in rows:
        lines.append(f"| {cell(value)} | {kind} | {relpath} | {confidence} | {cell(note)} |")

    disambiguations = [(relpath, exc) for relpath, data in entries
                       for exc in data["exclusions"]]
    if disambiguations:
        lines.append("")
        lines.append("### Disambiguations")
        lines.append("")
        for relpath, exc in sorted(disambiguations):
            lines.append(f"- `{relpath}`: NOT for {cell(exc)}")

    silent = sorted(relpath for relpath, data in entries if data["silent"])
    if silent:
        lines.append("")
        lines.append("### Silent playbooks (no greppable signature — route via the no-signature table below)")
        lines.append("")
        for relpath in silent:
            lines.append(f"- {relpath}")

    return "\n".join(lines)


def render_region(entries):
    return "\n" + build_table(entries) + "\n"


def write_index(entries):
    if not INDEX_PATH.exists():
        sys.exit(f"Index not found at {INDEX_PATH}. Create it once with the "
                 f"marker pair:\n{BEGIN_MARKER}\n{END_MARKER}")
    text = INDEX_PATH.read_text(encoding="utf-8")
    if not BLOCK_RE.search(text):
        sys.exit(f"Marker pair not found in {INDEX_PATH}. Add this block once:\n"
                 f"{BEGIN_MARKER}\n{END_MARKER}")
    new_text = BLOCK_RE.sub(
        lambda m: BEGIN_MARKER + render_region(entries) + END_MARKER, text
    )
    if new_text != text:
        INDEX_PATH.write_text(new_text, encoding="utf-8")
        print(f"Updated signature table in {INDEX_PATH.name}.")
    else:
        print(f"{INDEX_PATH.name} signature table already current.")
    return 0


def check_index(entries):
    if not INDEX_PATH.exists():
        print(f"FAIL — {INDEX_PATH} does not exist.", file=sys.stderr)
        return 1
    match = BLOCK_RE.search(INDEX_PATH.read_text(encoding="utf-8"))
    if not match:
        print(f"FAIL — marker pair not found in {INDEX_PATH.name}. "
              f"Add {BEGIN_MARKER} / {END_MARKER}.", file=sys.stderr)
        return 1
    if match.group(1) != render_region(entries):
        print(f"FAIL — signature table in {INDEX_PATH.name} is out of date. "
              "Run: python3 scripts/build-signature-index.py --write-index",
              file=sys.stderr)
        return 1
    print(f"OK — {INDEX_PATH.name} signature table is current.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-index", action="store_true",
                        help="Regenerate the signature table in place")
    parser.add_argument("--check-index", action="store_true",
                        help="Fail if the signature table is out of date")
    args = parser.parse_args()

    entries, findings = load_all()

    if findings:
        print(f"{len(findings)} finding(s):\n")
        for f in findings:
            print(f"  {f['playbook']}: {f['error']}")
        return 1

    if args.write_index:
        return write_index(entries)
    if args.check_index:
        return check_index(entries)

    total_sigs = sum(len(d["signatures"]) for _, d in entries)
    total_silent = sum(1 for _, d in entries if d["silent"])
    print(f"OK — {len(entries)} playbooks, {total_sigs} signatures, "
          f"{total_silent} silent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
