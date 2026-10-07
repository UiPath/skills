#!/usr/bin/env python3
"""
Scan shipped skill content for values a customer content-inspection gate
rejects: cardholder data, PII-shaped numbers, credentials, and secrets passed
as CLI arguments.

Why: customers run the published @uipath/skills package through DLP-style
scanners before allowing it. Those scanners match on SHAPE, not meaning — an
ISO date reads as a "Card Expiration Date", the 14-digit fraction of a BPMN
diagram coordinate passes Luhn and reads as a "Credit Card", a 6-digit forum
thread ID reads as a "Phone Number". One hit rejects the whole skill upload.
The 1.202/1.203 scans failed on exactly these shapes (cleared by hand in
#3714); this check keeps them from coming back. Every detector below is
calibrated on a string the customer scanner actually flagged — see
tests/scripts/test_check_sensitive_content.py.

Rules (id -> customer scanner label):
  credit-card            Credit Card            13-19 digit run (or 4-4-4-4 / 4-6-5 groups) that passes Luhn
  us-ssn                 US SSN                 NNN-NN-NNNN
  phone-number           Phone Number           NANP (555-123-4567, 555-0123) and E.164 (+15550001111) formats
  card-expiration-date   Card Expiration Date   MM/DD/YYYY always; MM/YY, MM/YYYY, YYYY-MM-DD beside an expiry keyword
  us-street-address      US Street Address      "<number> <Name> Street|Ave|Road|..."
  secret-token           Secret                 AWS access key IDs, GitHub/Slack/OpenAI/Google tokens, private keys, JWTs

Warn-tier rules (advisory; --strict makes them fail too). The customer scanner
has flagged each of these shapes, but not consistently:
  date-shaped-value      YYYY-MM-DD / YYYYMMDDTHHMMSS with no expiry keyword
  numeric-identifier     6-12 digit runs (forum thread IDs, error codes), NNNN-NNNN pairs
  aws-secret-shape       40-char base64 token (also matches git SHAs)
  secret-cli-argument    --client-secret/--password/... given a literal or <PLACEHOLDER> instead of env.<NAME> / $VAR

Fix a finding by replacing the value with a letter-only placeholder
(<EXPIRATION_DATE>, <PHONE_NUMBER>, NNN-NN-NNNN, <THREAD_ID>) — see
.claude/rules/content-quality.md § CLI Command Documentation. When a match is
genuinely required content that the customer scanner does NOT flag, add it to
scripts/sensitive-content-allowlist.json with a reason (it lives outside the
packaged `files` so the allowlisted values never ship).

Usage:
  python3 scripts/check-sensitive-content.py [PATH ...]           # default: every shipped source tree
  python3 scripts/check-sensitive-content.py package.tgz          # scan a packed npm tarball
  python3 scripts/check-sensitive-content.py --baseline-ref origin/main
  python3 scripts/check-sensitive-content.py --output json

--baseline-ref reports findings that already exist at the baseline as
pre-existing warnings; only findings this change introduces exit 1. Publish
runs omit it so every finding blocks.

Exit codes: 0 = clean (or only pre-existing findings), 1 = new findings,
2 = usage / IO error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST = REPO_ROOT / "scripts" / "sensitive-content-allowlist.json"

TEXT_SUFFIXES = {
    ".md", ".mdx", ".txt", ".json", ".jsonc", ".yaml", ".yml", ".toml", ".xml",
    ".xaml", ".bpmn", ".flow", ".cs", ".vb", ".py", ".js", ".mjs", ".cjs", ".ts",
    ".tsx", ".jsx", ".sh", ".ps1", ".html", ".css", ".csv", ".ini", ".cfg",
    ".env", ".sql", ".graphql", ".template",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist"}
MAX_BYTES = 5 * 1024 * 1024
# Source trees that land in the npm package (package.json `files`), scanned when no PATH is given.
SHIPPED_PATHS = ["skills", "skill-flavors", "commands", "hooks", "assets", ".claude-plugin", ".cursor-plugin", "README.md"]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    column: int
    rule: str
    label: str
    severity: str
    match: str
    pre_existing: bool = False

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.path, self.rule, self.match)


# ---------------------------------------------------------------- detectors

def _luhn(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_CARD_RUN = re.compile(r"(?<!\d)\d{13,19}(?!\d)")
_CARD_GROUPED = re.compile(
    r"(?<![\d-])(?:\d{4}([ -])\d{4}\1\d{4}\1\d{1,7}|\d{4}([ -])\d{6}\2\d{5})(?![\d])"
)


def detect_credit_card(line: str):
    for m in _CARD_RUN.finditer(line):
        if _luhn(m.group()):
            yield m
    for m in _CARD_GROUPED.finditer(line):
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn(digits):
            yield m


def _iter_simple(patterns, line):
    for pattern in patterns:
        yield from pattern.finditer(line)


_SSN = re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])")

# Block tier: formats the customer scanner rejects on sight.
_PHONE_PATTERNS = [
    # NANP: (555) 123-4567, 555-123-4567, 555.123.4567, +1 555 123 4567
    re.compile(r"(?<![\w.-])(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w-])"),
    # E.164 / international: +15550001111, +44 20 7946 0958, +1-555-0123
    re.compile(r"(?<![\w+])\+[1-9]\d{0,2}(?:[ -]?\(?\d{2,4}\)?){1,4}[ -]?\d{4}(?![\w.-])"),
    # Fictional NANP local: 555-0123 (plain NNN-NNNN is too often a range like 600-1200)
    re.compile(r"(?<![\w.-])555-\d{4}(?![\w-])"),
]

# Warn tier: digit shapes the scanner has flagged at least once (forum thread
# IDs "/t/332491" and "/t/718082" on two consecutive releases, old slug
# "1230/718082", "3000–5000 ms", "INV-99999999999") but that also appear in
# content that passed. Runs of one repeated 0 are GUID
# placeholders and are skipped.
_NUMERIC_ID_PATTERNS = [
    re.compile(r"(?<![\w./-])\d{4}[-–/]\d{4}(?![\w./-])"),
    re.compile(r"(?<![\w.])\d{3,4}/\d{6,7}(?![\w.])"),
    re.compile(r"(?<![\w.])(?!0+(?!\d))\d{6,12}(?![\w.])"),
]

_EXPIRY_KEYWORD = re.compile(r"expir|valid\s+(?:thru|through|until)|\bexp\b|good\s+thru", re.I)

# Always block: MM/DD/YYYY and DD.MM.YYYY ("01/15/2025" was flagged with no
# keyword nearby).
_FULL_DATE_PATTERNS = [
    re.compile(r"(?<![\w./-])(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/(?:19|20)\d{2}(?![\d/])"),
    re.compile(r"(?<![\w./-])(?:0?[1-9]|[12]\d|3[01])[./](?:0?[1-9]|1[0-2])[./](?:19|20)\d{2}(?![\d./])"),
]
# Block only beside an expiry keyword: MM/YY, MM/YYYY, MM/DD/YY, and ISO dates
# (`--expiration "2027-01-15"`). Without a keyword "Windows 10/11" is not a card expiry.
_SHORT_EXPIRY_PATTERNS = [
    re.compile(r"(?<![\w./-])(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/\d{2}(?![\d/])"),
    re.compile(r"(?<![\w./-])(?:0[1-9]|1[0-2])/(?:\d{2}|20\d{2})(?![\d/])"),
]
_ISO_DATE_PATTERNS = [
    re.compile(r"(?<![\w.-])(?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])(?!\d)"),
    re.compile(r"(?<!\d)(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])T\d{4,6}(?!\d)"),
]


def detect_expiration_date(line: str):
    yield from _iter_simple(_FULL_DATE_PATTERNS, line)
    if _EXPIRY_KEYWORD.search(line):
        yield from _iter_simple(_SHORT_EXPIRY_PATTERNS, line)
        yield from _iter_simple(_ISO_DATE_PATTERNS, line)


def detect_date_shape(line: str):
    if not _EXPIRY_KEYWORD.search(line):
        yield from _iter_simple(_ISO_DATE_PATTERNS, line)


_STREET_SUFFIX = (
    r"Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|"
    r"Way|Place|Pl|Terrace|Parkway|Pkwy|Highway|Hwy|Circle|Cir|Square|Sq"
)
_STREET = re.compile(
    rf"(?<![\w.])\d{{1,6}}\s+(?:[NSEW]\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+){{0,3}}\s+(?:{_STREET_SUFFIX})\b\.?"
)

_SECRET_PATTERNS = [
    re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA|AGPA|AIDA|AROA)[A-Z0-9]{16}(?![A-Z0-9])"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
]

# AWS secret access key shape: exactly 40 base64 chars, mixed letters and
# digits. Warn only — a 40-hex git SHA has the same shape.
_AWS_SECRET_SHAPE = re.compile(
    r"(?<![A-Za-z0-9/+=])(?=[A-Za-z0-9/+]*\d)(?=[A-Za-z0-9/+]*[A-Za-z])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+=])"
)

# A secret-bearing flag must read the value from the environment (`env.NAME`,
# `$NAME`, `${NAME}`, `${{ secrets.NAME }}`) — never a literal, and never a
# <PLACEHOLDER> that tells the agent to paste the secret into the command.
_SECRET_FLAG = re.compile(
    r"(?<![\w-])--(?:client-secret|password|passwd|secret|api-key|apikey|access-token|"
    r"auth-token|token|pat|private-key|connection-string)(?:[ =]+)"
    r"(?!env\.|\"?\$|'?\$|\"?env\.)(?P<value>\"[^\"]*\"|'[^']*'|<[^>\s]+>|[^\s`|)\\]+)"
)


BLOCK, WARN = "block", "warn"

# Order matters: an earlier rule claims a span, so a block-tier hit is never
# re-reported as a warning.
RULES = [
    ("credit-card", "Credit Card", BLOCK, detect_credit_card),
    ("us-ssn", "US SSN", BLOCK, lambda line: _SSN.finditer(line)),
    ("card-expiration-date", "Card Expiration Date", BLOCK, detect_expiration_date),
    ("phone-number", "Phone Number", BLOCK, lambda line: _iter_simple(_PHONE_PATTERNS, line)),
    ("us-street-address", "US Street Address", BLOCK, lambda line: _STREET.finditer(line)),
    ("secret-token", "Secret / access key", BLOCK, lambda line: _iter_simple(_SECRET_PATTERNS, line)),
    ("date-shaped-value", "Card Expiration Date (possible)", WARN, detect_date_shape),
    ("numeric-identifier", "Phone Number / SSN (possible)", WARN, lambda line: _iter_simple(_NUMERIC_ID_PATTERNS, line)),
    ("aws-secret-shape", "Secret AWS Secret KEY (possible)", WARN, lambda line: _AWS_SECRET_SHAPE.finditer(line)),
    ("secret-cli-argument", "Insecure credential handling", WARN, lambda line: _SECRET_FLAG.finditer(line)),
]


def scan_text(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        claimed: list[tuple[int, int]] = []
        for rule, label, severity, detect in RULES:
            for m in detect(line):
                start, end = m.span()
                # One finding per span: an SSN-shaped value is not also a phone number.
                if any(start < c_end and c_start < end for c_start, c_end in claimed):
                    continue
                claimed.append((start, end))
                findings.append(Finding(path, lineno, start + 1, rule, label, severity, m.group()))
    return findings


# ---------------------------------------------------------------- inputs

def _is_text_candidate(name: str) -> bool:
    p = Path(name)
    return p.suffix.lower() in TEXT_SUFFIXES or p.name in {"SKILL.md", "LICENSE", "CODEOWNERS"}


def _decode(data: bytes) -> str | None:
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def iter_files(target: Path):
    """Yield (display_path, repo_relative_path_or_None, text)."""
    if target.is_file() and target.name.endswith((".tgz", ".tar.gz")):
        with tarfile.open(target, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile() or member.size > MAX_BYTES or not _is_text_candidate(member.name):
                    continue
                fh = tar.extractfile(member)
                text = _decode(fh.read()) if fh else None
                if text is not None:
                    yield f"{target.name}!{member.name}", None, text
        return
    files = [target] if target.is_file() else sorted(
        p for p in target.rglob("*")
        if p.is_file() and not (SKIP_DIRS & set(p.relative_to(target).parts))
    )
    for f in files:
        if not _is_text_candidate(f.name) or f.stat().st_size > MAX_BYTES:
            continue
        text = _decode(f.read_bytes())
        if text is None:
            continue
        try:
            rel = f.resolve().relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = None
        yield (rel or f.as_posix()), rel, text


def load_allowlist(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    for i, entry in enumerate(entries):
        missing = {"path", "rule", "match", "reason"} - entry.keys()
        if missing:
            raise ValueError(f"{path}: entry {i} missing {sorted(missing)}")
    return entries


def is_allowed(finding: Finding, allowlist: list[dict]) -> bool:
    path = finding.path.split("!", 1)[-1]
    # Packed tarball members are prefixed `package/`; allowlist paths are repo-relative.
    path = path[len("package/"):] if path.startswith("package/") else path
    return any(
        e["rule"] == finding.rule and e["match"] == finding.match and path.endswith(e["path"])
        for e in allowlist
    )


def baseline_keys(ref: str, rel_paths: list[str]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for rel in rel_paths:
        proc = subprocess.run(
            ["git", "show", f"{ref}:{rel}"], cwd=REPO_ROOT, capture_output=True
        )
        if proc.returncode != 0:
            continue  # file is new in this change
        text = _decode(proc.stdout)
        if text is not None:
            keys.update(f.key for f in scan_text(rel, text))
    return keys


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", help="files, directories, or .tgz packages (default: shipped source trees)")
    parser.add_argument("--baseline-ref", help="git ref; findings already present there do not fail the run")
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="warn-tier findings also fail the run")
    args = parser.parse_args(argv)

    try:
        allowlist = load_allowlist(args.allowlist)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    rel_paths: list[str] = []
    paths = args.paths or [p for p in SHIPPED_PATHS if (REPO_ROOT / p).exists()]
    for raw in paths:
        target = Path(raw)
        if not target.is_absolute():
            target = (Path.cwd() if args.paths else REPO_ROOT) / target
        if not target.exists():
            print(f"error: {raw} does not exist", file=sys.stderr)
            return 2
        for display, rel, text in iter_files(target):
            if rel:
                rel_paths.append(rel)
            findings.extend(f for f in scan_text(display, text) if not is_allowed(f, allowlist))

    if args.baseline_ref:
        # Only files with findings need a baseline read — one `git show` each.
        known = baseline_keys(args.baseline_ref, sorted({f.path for f in findings} & set(rel_paths)))
        findings = [Finding(**{**asdict(f), "pre_existing": f.key in known}) for f in findings]

    fail_on = {BLOCK, WARN} if args.strict else {BLOCK}
    blocking = [f for f in findings if not f.pre_existing and f.severity in fail_on]
    advisory = [f for f in findings if f not in blocking]

    if args.output == "json":
        json.dump(
            {"blocking": [asdict(f) for f in blocking], "advisory": [asdict(f) for f in advisory]},
            sys.stdout,
            indent=2,
        )
        print()
        return 1 if blocking else 0

    annotate = os.environ.get("GITHUB_ACTIONS") == "true"
    for f in blocking:
        print(f"{f.path}:{f.line}:{f.column}: error [{f.rule}] {f.label}: {f.match!r}")
        if annotate:
            print(f"::error file={f.path},line={f.line},col={f.column},title={f.label}::[{f.rule}] {f.match}")
    for f in advisory:
        tag = "pre-existing" if f.pre_existing else f.severity
        print(f"{f.path}:{f.line}:{f.column}: {tag} [{f.rule}] {f.label}: {f.match!r}")
        if annotate and not f.pre_existing:
            print(f"::warning file={f.path},line={f.line},col={f.column},title={f.label}::[{f.rule}] {f.match}")
    if blocking:
        print(
            f"\n{len(blocking)} finding(s) a customer content-inspection gate will reject. Replace each value "
            "with a letter-only placeholder (<EXPIRATION_DATE>, <PHONE_NUMBER>, NNN-NN-NNNN, <THREAD_ID>) and "
            "pass secrets as env.<NAME>. See .claude/rules/content-quality.md § CLI Command Documentation.",
            file=sys.stderr,
        )
    else:
        print(f"OK — no blocking sensitive-content findings ({len(advisory)} advisory).")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
