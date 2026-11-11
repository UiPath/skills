"""
Regression tests for scripts/check-sensitive-content.py.

The corpus below is the exact text a customer content-inspection gate flagged
in @uipath/skills 1.202.0 and 1.203.0 (each case names the shipped file).
Block-tier strings must fail the check; warn-tier strings are shapes the
scanner flagged inconsistently and must surface as advisory. The negative
cases are real skill content that must NOT be flagged — each one was a false
positive while tuning the detectors against main.

Run from repo root:
    pytest tests/scripts/test_check_sensitive_content.py
"""

import importlib.util
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-sensitive-content.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_sensitive_content", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # @dataclass resolves annotations through sys.modules
    spec.loader.exec_module(module)
    return module


check = _load()


def _rules(text):
    return {(f.rule, f.severity) for f in check.scan_text("x.md", text)}


# (source of the customer finding, text, expected rule)
BLOCKED = [
    ("maestro-bpmn B.1.0.bpmn: Credit Card (Luhn-valid float fraction)",
     '<dc:Bounds x="209.33333333333334" y="149.18190079662895"/>', "credit-card"),
    ("maestro-bpmn B.1.0.bpmn: Credit Card (13 digits)",
     'y="392.6228456785188"', "credit-card"),
    ("grouped card number", "4111 1111 1111 1111", "credit-card"),
    ("rpa legacy/data-manipulation-guide.md: US SSN",
     "| SSN | `\\d{3}-\\d{2}-\\d{4}` | `123-45-6789` |", "us-ssn"),
    ("rpa legacy/data-manipulation-guide.md: Card Expiration Date",
     'DateTime.ParseExact("01/15/2025", "MM/dd/yyyy", CultureInfo.InvariantCulture)', "card-expiration-date"),
    ("admin pat-management.md: Card Expiration Date",
     'uip admin pat regenerate <TOKEN_ID> --expiration "2028-01-15" --output json', "card-expiration-date"),
    ("admin external-app-management.md: Card Expiration Date",
     '--description "Rotated secret" --expiration "2027-06-01" --output json', "card-expiration-date"),
    ("card expiry MM/YY beside keyword", "Card expires 09/28", "card-expiration-date"),
    ("rpa Word 2.5 coded/examples.md: US Street Address",
     'doc.SetBookmarkContent("Address", "123 Main Street, Suite 100");', "us-street-address"),
    ("E.164 phone", 'callerId: "+15550001111"', "phone-number"),
    ("NANP phone", "Call (555) 123-4567 for support", "phone-number"),
    ("fictional NANP local", 'phone = "+1-555-0123"', "phone-number"),
    ("AWS access key id", "aws_access_key_id = AKIAIOSFODNN7EXAMPLE", "secret-token"),
    ("GitHub PAT", "token: ghp_" + "a" * 36, "secret-token"),
    ("private key", "-----BEGIN RSA PRIVATE KEY-----", "secret-token"),
]

ADVISORY = [
    ("rpa legacy/ThirdParty-SharePoint.md: Phone Number (forum thread ID, 2 releases)",
     "[Forum](https://forum.uipath.com/t/332491): service account must have access", "numeric-identifier"),
    ("troubleshoot foreground-unattended-robot.md: Phone Number",
     "- [Forum: Error #1230](https://forum.uipath.com/t/718082)", "numeric-identifier"),
    ("troubleshoot old slug tail: Phone Number",
     "https://forum.uipath.com/t/foreground-job-requires-robot-1230/718082", "numeric-identifier"),
    ("rpa Terminal TerminalSession.md: Phone Number",
     "**Raise to 3000–5000 ms for TLS hosts**", "numeric-identifier"),
    ("rpa legacy/testing-guide.md: US SSN",
     '| `"INV-99999999999"` | False | Number too long |', "numeric-identifier"),
    ("rpa AzureWVD coded/examples.md: GUID with all-digit group",
     '"ffffffff-1111-2222-3333-444444444444"', "numeric-identifier"),
    ("admin audit-workflow-guide.md: Card Expiration Date (ISO date, no keyword)",
     "  --from-date 2026-01-01 \\", "date-shaped-value"),
    ("admin audit-commands.md: Card Expiration Date (compact timestamp)",
     '"Path": "audit_<from>_<to>_20260617T112630"', "date-shaped-value"),
    ("platform vendor-docs-registry.json: Secret AWS Secret KEY (40-char shape)",
     "sha: bde2c5964a3cfbc9b839aef9aa2a2764829d5497", "aws-secret-shape"),
    ("coded-apps SKILL.md 1.203.0: Insecure credential handling",
     'uip login --client-id "<CLIENT_ID>" --client-secret "<CLIENT_SECRET>" --tenant "<TENANT>"', "secret-cli-argument"),
    ("literal password argument", 'uip admin smtp set --password "smtp-pass"', "secret-cli-argument"),
]

CLEAN = [
    ("CLI reads secret from env (the #3714 fix)", "uip login --client-secret env.UIPATH_CLIENT_SECRET \\"),
    ("shell variable secret", 'uip login --client-secret "$CLIENT_SECRET"'),
    ("placeholder date", '--expiration "<EXPIRATION_DATE>"'),
    ("masked SSN", "| SSN | `\\d{3}-\\d{2}-\\d{4}` | `NNN-NN-NNNN` |"),
    ("placeholder address", 'doc.SetBookmarkContent("Address", "<STREET_ADDRESS>");'),
    ("Windows 10/11 is not MM/YY", "Supported on Windows 10/11 machines."),
    ("version numbers", "Requires uip 1.203.0 and Node 22.11.0"),
    ("numeric range is not a phone", "batch size 600-1200 rows"),
    ("decimal score delta is not E.164", "| recall | +0.370 |"),
    ("zero GUID placeholder", '"00000000-0000-0000-0000-000000000000"'),
    ("IP address", "10.20.30.40"),
    ("short error code", "Orchestrator error code `#1230`"),
    # PR #3798 review: ordinary prose that ends in an ambiguous street suffix.
    ("Drive is a product, not a street", "Upload 5 Google Drive files"),
    ("step number before a product", "Step 2 Google Drive"),
    ("Way in prose", "then 10 Second Way"),
    ("Square in prose", "Step 2 Town Square"),
]

# Repo-wide false positives the first cut of the block tier hit. Some still
# surface as advisory (a 12-digit GUID tail is a numeric-identifier); none may block.
NOT_BLOCKED = [
    ("digits inside a hex expression id", '"expressionId":"id7ca932f7092040649018223c7de7ba78"'),
    ("GUID segments", '"JobKey": "11aa1111-2222-3333-4444-555566667777"'),
    ("GUID segments with Luhn-valid groups", '"Key": "aabb1088-3344-5566-7788-99aabbccdd33"'),
    ("epoch milliseconds", "--started-after 1751328000000 --started-before 1751673600000"),
    ("repeated-digit run", "INV-0000000000000"),
    ("regex quantifier before epoch seconds", r"--since[\s=]+1788000000\b"),
    ("DD.MM.YYYY sample with no expiry keyword", "Example: '16.05.2017'"),
    ("dated build path in a stack trace that later says expired",
     r"at Http.Send() in C:\\Apiary\\2023-06-26.09-20-33\\Src\\Http.cs:line 12 -- token expired"),
    ("space-separated number triple", "| 100 200 3000 |"),
    ("short signed numbers", "delta +5 10 20"),
    ("unassignable SSN area", "build 900-12-3456"),
]


# Shapes the revision kept blocking, in forms the first cut did not cover.
BLOCKED_REVISED = [
    ("expiry keyword a few words before the date", 'pat create --expiration-date "2027-01-15"', "card-expiration-date"),
    ("DD.MM.YYYY beside a keyword", "Card valid thru 31.12.2027", "card-expiration-date"),
    ("NANP with dots", "Call 555.234.5678", "phone-number"),
    ("international E.164 with spaces", "Phone: +44 20 7946 0958", "phone-number"),
    ("street abbreviation", "Ship to 100 Market St, Suite 4", "us-street-address"),
    ("standalone Mastercard test number", "5555555555554444", "credit-card"),
    ("Mastercard 2-series", "2223000048400011", "credit-card"),
]


@pytest.mark.parametrize("source,text,rule", BLOCKED_REVISED, ids=[c[0] for c in BLOCKED_REVISED])
def test_blocks_revised_shapes(source, text, rule):
    assert (rule, check.BLOCK) in _rules(text), source


def test_expiry_keyword_far_from_date_does_not_block():
    line = "The token expired. " + "x" * 120 + " Created 2026-01-01."
    assert ("card-expiration-date", check.BLOCK) not in _rules(line)
    assert ("date-shaped-value", check.WARN) in _rules(line)


@pytest.mark.parametrize("source,text,rule", BLOCKED, ids=[c[0] for c in BLOCKED])
def test_blocks_customer_flagged_shapes(source, text, rule):
    assert (rule, check.BLOCK) in _rules(text), source


@pytest.mark.parametrize("source,text,rule", ADVISORY, ids=[c[0] for c in ADVISORY])
def test_reports_inconsistently_flagged_shapes_as_advisory(source, text, rule):
    rules = _rules(text)
    assert (rule, check.WARN) in rules, source
    assert not any(sev == check.BLOCK for _, sev in rules), f"{source} must not block: {rules}"


@pytest.mark.parametrize("source,text", CLEAN, ids=[c[0] for c in CLEAN])
def test_does_not_flag_safe_content(source, text):
    assert _rules(text) == set(), source


@pytest.mark.parametrize("source,text", NOT_BLOCKED, ids=[c[0] for c in NOT_BLOCKED])
def test_does_not_block_repo_false_positives(source, text):
    rules = _rules(text)
    assert not any(sev == check.BLOCK for _, sev in rules), f"{source}: {rules}"


def test_non_luhn_digit_run_is_not_a_card():
    assert ("credit-card", check.BLOCK) not in _rules('x="209.33333333333334"')


def test_one_finding_per_span():
    findings = check.scan_text("x.md", "123-45-6789")
    assert [f.rule for f in findings] == ["us-ssn"]


def _run(*args, cwd=REPO_ROOT):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True
    )


def test_cli_exit_codes(tmp_path):
    (tmp_path / "bad.md").write_text("Expires 2027-01-15\n", encoding="utf-8")
    (tmp_path / "warn.md").write_text("Error code 170002\n", encoding="utf-8")
    assert _run(str(tmp_path / "bad.md")).returncode == 1
    assert _run(str(tmp_path / "warn.md")).returncode == 0
    assert _run("--strict", str(tmp_path / "warn.md")).returncode == 1
    assert _run(str(tmp_path / "missing.md")).returncode == 2


def test_scans_packed_tarball_members(tmp_path):
    tgz = tmp_path / "uipath-skills-0.0.0.tgz"
    data = b'callerId: "+15550001111"\n'
    with tarfile.open(tgz, "w:gz") as tar:
        info = tarfile.TarInfo("package/skills/uipath-x/SKILL.md")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    proc = _run("--output", "json", str(tgz))
    assert proc.returncode == 1
    blocking = json.loads(proc.stdout)["blocking"]
    assert blocking[0]["path"].endswith("!package/skills/uipath-x/SKILL.md")
    assert blocking[0]["rule"] == "phone-number"


def test_scans_files_of_any_extension(tmp_path):
    # PR #3798 review: an extension allowlist let `*.canonical` ship unscanned.
    (tmp_path / "flow.canonical").write_text("SSN 123-45-6789\n", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\0\0\0 123-45-6789")
    proc = _run("--output", "json", str(tmp_path))
    paths = [f["path"] for f in json.loads(proc.stdout)["blocking"]]
    assert proc.returncode == 1
    assert len(paths) == 1 and paths[0].endswith("flow.canonical")


def test_reports_oversized_files_as_not_scanned(tmp_path, monkeypatch):
    big = tmp_path / "big.md"
    big.write_text("x" * 32, encoding="utf-8")
    monkeypatch.setattr(check, "MAX_BYTES", 16)
    skipped = []
    assert list(check.iter_files(tmp_path, skipped)) == []
    assert skipped == [big.as_posix()]


def test_allowlist_suppresses_exact_match(tmp_path):
    target = tmp_path / "doc.md"
    target.write_text('callerId: "+15550001111"\n', encoding="utf-8")
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"entries": [
        {"path": "doc.md", "rule": "phone-number", "match": "+15550001111", "reason": "test"}
    ]}), encoding="utf-8")
    assert _run("--allowlist", str(allow), str(target)).returncode == 0


def test_allowlist_entry_requires_reason(tmp_path):
    allow = tmp_path / "allow.json"
    allow.write_text(json.dumps({"entries": [{"path": "a", "rule": "b", "match": "c"}]}), encoding="utf-8")
    assert _run("--allowlist", str(allow), str(SCRIPT)).returncode == 2


def test_baseline_ref_demotes_pre_existing_findings():
    # HEAD always exists; every finding in a file unchanged since HEAD is pre-existing.
    tracked = subprocess.run(
        ["git", "ls-files", "skills/uipath-ixp/references/label-documents-guide.md"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    ).stdout.strip()
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", tracked], cwd=REPO_ROOT).returncode
    if not tracked or dirty:
        pytest.skip("fixture file missing or locally modified")
    proc = _run("--baseline-ref", "HEAD", "--output", "json", tracked)
    report = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert report["blocking"] == []
