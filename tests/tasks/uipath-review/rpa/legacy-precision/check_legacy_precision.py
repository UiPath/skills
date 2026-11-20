#!/usr/bin/env python3
"""NEGATIVE grader: reward precision on a clean Windows-Legacy project.

The project is a valid Windows-Legacy process with no genuine Critical defect.
A good review must:
  * NOT flag the Windows-Legacy targetFramework itself as Critical, AND
  * NOT fabricate Workflow Analyzer rule IDs (any cited ST/UI/TA/RT code must
    appear in the skill's RPA checklists), AND
  * offer tailored migration guidance that names >=1 concrete trade-off.

FAIL an over-eager reviewer; PASS a precise one. Exit 0 on PASS.
"""
import os
import re
import sys
from pathlib import Path

REPORT = Path(os.getcwd()) / "_review_report.md"
MIN_REPORT_BYTES = 500

LEGACY_TERMS = (
    "windows-legacy", "windows legacy", "legacy framework", "legacy target",
    "targetframework", ".net framework", "net framework 4", "framework 4.6",
    ".net 4",
)
# Phrases that genuinely say the framework is NOT a critical problem / IS
# supported. Deliberately narrow: anti-legacy wording ("avoid", "not
# recommended", "should be migrated", bare "not"/"no") must NOT suppress the
# failure — those are exactly the over-eager Critical framing this eval catches.
BENIGN = (
    "not a critical", "not critical", "no critical", "isn't a critical",
    "is not critical", "not a defect", "is supported", "fully supported",
    "supported indefinit", "still supported", "is fine", "acceptable",
    "valid reason", "not an issue", "no issue", "not a blocker",
)
# Targeted "should NOT be treated/classified/flagged as critical" phrasing —
# a correct reviewer explicitly declining to rate Legacy as Critical. Narrow
# regex so it does NOT reintroduce broad "not"/"avoid" suppression.
BENIGN_RE = re.compile(
    r"not\s+(?:be\s+)?(?:treated|classified|flagged|considered|marked|raised|"
    r"reported|listed|categori[sz]ed|rated|deemed)\s+(?:as\s+)?(?:a\s+)?critical"
)
# Negation that directly governs "critical": "never a Critical finding",
# "neither a Critical issue nor ...", "not inherently a Critical issue", "not
# itself a Critical finding". Only filler words may sit between the negator and
# "critical", so "not recommended ... Critical" still fails. Observed false
# FAILs on correct reviews: runs 2026-11-17_04-23-38, 2026-11-18_04-18-55,
# 2026-11-18_04-25-00, 2026-11-19_04-22-41, 2026-11-20_04-22-52.
NEGATED_CRITICAL_RE = re.compile(
    r"\b(?:not|never|neither|nor|isn't|aren't)\b"
    r"(?:\s+(?:a|an|the|be|as|is|are|in|by|of|on|its|own|itself|themselves|inherently|"
    r"necessarily|automatically|per|se|being|treated|classified|flagged|considered|marked|"
    r"raised|reported|listed|categori[sz]ed|rated|deemed))*\s+critical"
)
# "Neither <the Legacy framework> nor <X> is classified as a Critical ..." —
# the subject list sits between the negator and "critical"; sentence-scoped.
NEITHER_NOR_RE = re.compile(r"\bnor\b[^.\n]{0,120}\bcritical")
TRADEOFFS = (
    "unified target", "object repository", "coded test", "coded workflow",
    "healing agent", "autopilot", "screenplay", "modern .net", "modern dotnet",
    "cross-platform", "cross platform", "data manager", "maestro", "agent",
    ".net 6", ".net 8", "modern project",
)
# The fixture's own trade-off: the SOAP client needs System.ServiceModel / WCF,
# which only the .NET Framework (Legacy) runtime provides. Tying the migration
# advice to that dependency is the most tailored guidance there is. These terms
# also appear in any description of the project, so they count only in a
# sentence that is about migrating. Observed false FAILs on reviews that did
# exactly that: runs adhoc-2026-11-09_06-21-12, adhoc-2026-11-14_04-16-48.
DEPENDENCY_TERMS = ("servicemodel", "wcf", "soap")
MIGRATION_WORDS = ("migrat", "upgrad", "convert", "moderni", "recreate", "port ")


_EMPTY_SECTION_RE = re.compile(r"(?:none\b|no\s+critical|n/a\b|nothing\b)")


def _is_empty_section_heading(lower: str, pos: int) -> bool:
    """True if `pos` sits in a Markdown heading whose section body opens with
    "None" (prose, or the first data cell of a table). An empty "### Critical
    Findings" section flags nothing, whatever the sentence after "None" says
    (run 2026-11-18_04-25-00: "None identified. Neither the Windows-Legacy
    target framework nor ... is classified as a Critical deployment blocker")."""
    line_start = lower.rfind("\n", 0, pos) + 1
    if not lower[line_start:pos].lstrip().startswith("#"):
        return False
    line_end = lower.find("\n", pos)
    if line_end == -1:
        return False
    for line in lower[line_end:].split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cells = [c for c in cells if c and not re.fullmatch(r"[-:—–\s]+", c)]
        if not cells:
            continue  # blank line, table separator, or a row of dash placeholders
        if line.lstrip().startswith("#"):
            return False  # next heading: section had no body at all
        if all(re.fullmatch(r"[a-z /&]+", c) for c in cells) and "|" in line and not \
                _EMPTY_SECTION_RE.match(cells[0]):
            continue  # table header row (ID | Rule | Recommendation)
        return bool(_EMPTY_SECTION_RE.match(cells[0]))
    return False


def flags_legacy_as_critical(text: str) -> bool:
    """True if a Critical claim is made ABOUT the legacy framework."""
    lower = text.lower()
    for m in re.finditer(r"critical", lower):
        if _is_empty_section_heading(lower, m.start()):
            continue
        start = max(0, m.start() - 90)
        end = min(len(lower), m.end() + 90)
        window = lower[start:end]
        if any(t in window for t in LEGACY_TERMS):
            if (not any(n in window for n in BENIGN) and not BENIGN_RE.search(window)
                    and not NEGATED_CRITICAL_RE.search(window)
                    and not NEITHER_NOR_RE.search(window)):
                return True
    return False


# Real UiPath Workflow Analyzer rule IDs (Studio core ST-*, UI Automation UI-*,
# Test Automation TA-*, Runtime RT-*). A cited code outside this set AND not
# referenced anywhere in the skill docs is a fabrication — the task contract
# forbids fabricating rule IDs, so it fails regardless of how plausible the
# number looks (e.g. ST-SEC-029, UI-ANA-029).
_REAL_RULE_IDS = frozenset("""
ST-NMG-001 ST-NMG-002 ST-NMG-004 ST-NMG-005 ST-NMG-006 ST-NMG-009 ST-NMG-010 ST-NMG-011
ST-DBP-002 ST-DBP-003 ST-DBP-006 ST-DBP-007 ST-DBP-008 ST-DBP-009 ST-DBP-020 ST-DBP-021
ST-DBP-022 ST-DBP-023 ST-DBP-024 ST-DBP-025 ST-DBP-026 ST-DBP-027 ST-DBP-028 ST-DBP-029 ST-DBP-030
ST-MRD-001 ST-MRD-002 ST-MRD-004 ST-MRD-005 ST-MRD-007 ST-MRD-008 ST-MRD-009 ST-MRD-010 ST-MRD-011
ST-USG-005 ST-USG-006 ST-USG-009 ST-USG-010 ST-USG-011 ST-USG-012 ST-USG-014 ST-USG-020 ST-USG-024 ST-USG-027
ST-REL-006 ST-PRR-004 ST-AMG-001
ST-SEC-004 ST-SEC-005 ST-SEC-007 ST-SEC-008 ST-SEC-009 ST-SEC-010
ST-ANA-001 ST-ANA-002 ST-ANA-003 ST-ANA-004 ST-ANA-005 ST-ANA-006 ST-ANA-007 ST-ANA-008 ST-ANA-009 ST-ANA-018
UI-ANA-016 UI-ANA-017 UI-ANA-018 UI-REL-001 UI-DBP-006 UI-DBP-013 UI-DBP-030
UI-PRR-001 UI-PRR-002 UI-PRR-003 UI-PRR-004 UI-USG-011 UI-SEC-004 UI-SEC-010 UI-SEC-014
TA-DBP-001 TA-DBP-002 TA-DBP-005 TA-DBP-006 TA-NMG-001 TA-NMG-002
RT-UIA-001 RT-OUT-001
""".split())


def classify_rule_ids(text: str):
    """Return (fabricated, uncataloged). A cited ST/UI/TA/RT code is fabricated
    unless it is a real Workflow Analyzer rule (``_REAL_RULE_IDS``) or is
    referenced somewhere in the skill docs."""
    cited = set(re.findall(r"\b((?:ST|UI|TA|RT)-[A-Z]{3}-\d{3})\b", text))
    if not cited:
        return [], []
    known = ""
    skills_repo = os.environ.get("SKILLS_REPO_PATH")
    if skills_repo:
        refs = Path(skills_repo) / "skills" / "uipath-review" / "references"
        if refs.is_dir():
            known = "".join(f.read_text(encoding="utf-8", errors="replace")
                            for f in refs.rglob("*.md"))
    fabricated = sorted(c for c in cited if c not in _REAL_RULE_IDS and c not in known)
    return fabricated, []


def has_migration_guidance(text: str) -> bool:
    lower = text.lower()
    return "migrat" in lower or "upgrade" in lower or "convert" in lower or "modern project" in lower


def names_tradeoff(text: str) -> bool:
    lower = text.lower()
    if any(t in lower for t in TRADEOFFS):
        return True
    for sentence in re.split(r"(?<=[.;!?])\s+|\n", lower):
        if (any(d in sentence for d in DEPENDENCY_TERMS)
                and any(m in sentence for m in MIGRATION_WORDS)):
            return True
    return False


def _fixture_intact() -> bool:
    p = Path(os.getcwd()) / "LegacyBot" / "project.json"
    try:
        return p.is_file() and '"targetFramework": "Legacy"' in p.read_text(errors="replace")
    except Exception:
        return False


def main() -> None:
    if not REPORT.is_file():
        sys.exit(f"FAIL: {REPORT} not found")
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    if len(text) < MIN_REPORT_BYTES:
        sys.exit(f"FAIL: {REPORT} is suspiciously short ({len(text)} bytes).")
    if not _fixture_intact():
        sys.exit("FAIL: LegacyBot/project.json no longer declares targetFramework 'Legacy' "
                 "(fixture appears mutated).")

    if flags_legacy_as_critical(text):
        sys.exit(
            "FAIL: report flags the Windows-Legacy framework itself as Critical. "
            "Legacy is supported indefinitely in Studio LTS — this is a "
            "false-positive the skill's anti-patterns forbid."
        )
    print("OK: does not flag Legacy framework as Critical")

    # Contract: the reviewer must NOT fabricate Workflow Analyzer rule IDs.
    # An implausibly-numbered code (e.g. ST-SEC-999) is fabricated -> FAIL. A
    # low-numbered code the repo just doesn't enumerate could be a real rule ->
    # only warn, so a correct review is not false-failed.
    fabricated, uncataloged = classify_rule_ids(text)
    if fabricated:
        sys.exit(f"FAIL: report cites fabricated Workflow Analyzer rule ID(s): {fabricated}. "
                 "The task contract forbids fabricating rule IDs.")
    if uncataloged:
        print(f"WARN: rule code(s) not enumerated in the skill docs (may be real WFA codes): {uncataloged}")
    else:
        print("OK: no fabricated rule IDs")

    if not has_migration_guidance(text):
        sys.exit("FAIL: report gives no migration guidance (expected migrate/upgrade advice).")
    if not names_tradeoff(text):
        sys.exit(
            "FAIL: migration guidance is not tailored — expected >=1 named "
            "trade-off (Unified Target, Object Repository, coded tests, Healing "
            "Agent, modern .NET, cross-platform, etc.)."
        )
    print("OK: tailored migration guidance with a named trade-off")
    print("PASS")


if __name__ == "__main__":
    main()
