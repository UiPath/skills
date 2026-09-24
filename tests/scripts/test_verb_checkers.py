"""
Regression tests for scripts/check-cli-verbs.py and scripts/check-skill-verbs.py.
Each test reproduces a specific bug surfaced by code review.

Run from repo root:
    pytest tests/scripts/test_verb_checkers.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = _load("check_cli_verbs", REPO_ROOT / "scripts" / "check-cli-verbs.py")
skill = _load("check_skill_verbs", REPO_ROOT / "scripts" / "check-skill-verbs.py")
build = _load("build_uip_catalog", REPO_ROOT / "scripts" / "build-uip-catalog.py")


# --- Issue 1 (High): mid-token partial truncation ---------------------------

def test_extract_verb_paths_rejects_mid_token_dynamic():
    """`uip\\s+solution\\w+\\s+list` must not produce verb `"solution"`.

    The regex matches things like `uip solutionFoo list`, which is not a real
    verb. The AST walker stops at `\\w+` and currently returns the literal
    prefix `"uip solution"`, so the extractor yields the verb `solution` and
    the classifier matches it (since `solution` is a catalog group). That's a
    false-positive reachable verdict.
    """
    paths = cli.extract_verb_paths(r"uip\s+solution\w+\s+list")
    # The pattern is dynamic mid-verb; the extractor should signal that by
    # returning None (treated as Info) rather than a concrete partial.
    assert paths is None, (
        f"Expected None for mid-token dynamic, got {paths!r}. "
        "This would produce a false 'reachable' verdict for a pattern that "
        "matches no real verb."
    )


def test_extract_verb_paths_rejects_dynamic_after_uip():
    """`uip\\s+\\w+\\s+list` is purely dynamic; must return None."""
    paths = cli.extract_verb_paths(r"uip\s+\w+\s+list")
    assert paths is None


# --- Issue 2 (High): duplicate verb paths ----------------------------------

def test_extract_verb_paths_deduplicates_alternations():
    """`(uip|$UIP)\\s+(maestro\\s+)?flow\\s+init` must yield each verb once."""
    paths = cli.extract_verb_paths(r"(uip|\$UIP)\s+(maestro\s+)?flow\s+init")
    assert paths is not None
    assert len(paths) == len(set(paths)), (
        f"Duplicate verb paths in extraction: {paths!r}. "
        "Inflates 'Top unmatched verbs' counts in the audit report."
    )
    assert set(paths) == {"flow init", "maestro flow init"}


# --- Issue 6 (Medium): redundant OR-clause in severity classification ------

def test_scan_classifies_unwalkable_via_prefix_loop():
    """An unwalkable group should classify a multi-token reference as
    Uncertain via the prefix-iteration loop alone, without needing the
    redundant `tokens[0] in unwalkable` short-circuit."""
    md = REPO_ROOT / "tests" / "scripts" / "_fixture_unwalkable.md"
    md.write_text("Run `uip codedagent init <name>` then deploy.\n")
    try:
        catalog = set()  # empty; we only care about Uncertain via unwalkable
        unwalkable = {"codedagent"}
        findings = skill.scan_file(md, catalog, unwalkable)
        # Exactly one finding for `codedagent init`, classified Uncertain.
        relevant = [f for f in findings if f["verb_path"] == "codedagent init"]
        assert len(relevant) == 1, f"Expected 1 finding, got {findings!r}"
        assert relevant[0]["severity"] == "Uncertain"
    finally:
        md.unlink(missing_ok=True)


# --- Issue 5 (Medium): missing uip → graceful failure ----------------------

def test_run_uip_handles_missing_binary(tmp_path, monkeypatch):
    """When `uip` is not on PATH, run_uip should not crash with
    FileNotFoundError; it should exit with a helpful message."""
    monkeypatch.setenv("PATH", str(tmp_path))  # empty PATH
    # The current implementation raises FileNotFoundError unhandled.
    # After the fix, it should sys.exit with a message.
    with pytest.raises(SystemExit):
        build.run_uip(["--help"])


# --- Issue 7 (High): noise filter is dead code ------------------------------

def test_scan_suppresses_prose_noise(tmp_path):
    """`the uip CLI works` and `uip is great` must NOT produce findings.

    Current bug: the noise filter at check-skill-verbs.py:134 only fires when
    `len(tokens) == 1`, but `"the uip CLI works"` extracts tokens
    `["CLI", "works"]` (length 2), so the filter never matches and prose
    becomes a Stale finding.
    """
    md = tmp_path / "noise.md"
    md.write_text(
        "The uip CLI works well.\n"
        "Then uip is great for automation.\n"
        "Also `uip a tool` is sometimes seen in prose.\n"
    )
    catalog = {"orchestrator", "flow"}
    findings = skill.scan_file(md, catalog, set())
    assert findings == [], (
        f"Expected no findings on prose noise, got {findings!r}. "
        "The noise filter must match these lines."
    )


# --- Issue 9 (Medium): word-boundary anchors must not pass silently --------

def test_extract_verb_paths_treats_word_boundary_as_dynamic():
    r"""`\b` and `\B` constrain matches in ways the literal walker cannot
    model — the surrounding context decides whether the match fires. Treat
    them like other dynamic tokens (return None for purely-dynamic patterns,
    or trim back to the last whitespace for partial matches)."""
    # Pattern is fully dynamic once the boundary appears mid-verb.
    paths = cli.extract_verb_paths(r"uip\s+\bfoo\b")
    # The walker should bail at `\b`, leaving only "uip " and returning no verb.
    assert paths is None, (
        f"Expected None for `\\b` anchor mid-verb, got {paths!r}. "
        "Boundary anchors can prevent a match the literal-walker would assume."
    )


# --- Issue 8 (Medium): --report exit code contract --------------------------

def test_report_exit_zero_when_only_medium(tmp_path, monkeypatch):
    """`audit-verbs.md` documents 'exit 0 if no Stale/High findings'.
    A Medium-only run (retired verbs) must therefore exit 0, not 1.
    """
    # Stub the catalog so 'foo bar' is recognised as RETIRED, not unknown.
    monkeypatch.setattr(cli, "load_catalog", lambda: ({"baz"}, "test"))
    monkeypatch.setattr(cli, "load_renames", lambda: {"foo bar": "baz"})

    task = tmp_path / "task.yaml"
    task.write_text(
        "success_criteria:\n"
        "  - type: command_executed\n"
        "    command_pattern: 'uip\\s+foo\\s+bar'\n"
    )
    report = tmp_path / "report.md"
    monkeypatch.setattr(sys, "argv",
                        ["check-cli-verbs.py", "--report", str(report),
                         str(task)])
    rc = cli.main()
    # Confirm we actually produced a Medium-only finding.
    body = report.read_text()
    assert "Medium" in body
    assert "**High**" in body  # the summary table mentions High even if zero
    assert rc == 0, f"Expected exit 0 for Medium-only run, got {rc}"


# --- Issue 10: placeholder with file extension --------------------------------

def test_placeholder_with_extension_does_not_extend_verb(tmp_path):
    """`uip maestro flow validate <ProjectName>.flow` must stop at the
    placeholder. The trailing `.flow` extension would otherwise sneak the
    token past the bare-placeholder regex and get treated as a verb part.
    """
    md = tmp_path / "doc.md"
    md.write_text("Run `uip maestro flow validate <ProjectName>.flow` to check.\n")
    catalog = {"maestro flow validate"}
    findings = skill.scan_file(md, catalog, set())
    assert findings == [], (
        f"Expected no findings — `<ProjectName>.flow` is a placeholder, "
        f"got {findings!r}."
    )


# --- Issue 11: inline shell comment must not extend the verb path -------------

def test_inline_shell_comment_stops_verb_extraction(tmp_path):
    """`uip foo bar # refresh local cache` — the `#` starts a shell comment;
    the prose after must not be treated as verb tokens.
    """
    md = tmp_path / "doc.md"
    md.write_text("Run `uip maestro flow registry pull # refresh local cache`.\n")
    catalog = {"maestro flow registry pull"}
    findings = skill.scan_file(md, catalog, set())
    assert findings == [], (
        f"Expected no findings — `#` starts a comment, "
        f"got {findings!r}."
    )


# --- Issue 14: per-line `<!-- uip-check-skip -->` suppression -----------------

def test_skip_marker_suppresses_line(tmp_path):
    """The marker `<!-- uip-check-skip -->` on a line must suppress all
    findings for that line. Used by intentional historical references — CLI
    version-comparison tables that document removed prefixes, fallback-prefix
    sentences. Without honoring the marker, the gate hard-fails on lines
    that explicitly opted out (regression flagged in PR #833 review).
    """
    md = tmp_path / "doc.md"
    md.write_text(
        "Run `uip flow init MyProject` — modern form.\n"
        "| **< 0.3.4** | `uip flow` | `uip flow init MyProject` <!-- uip-check-skip --> |\n"
    )
    catalog = {"maestro flow init", "maestro flow"}
    findings = skill.scan_file(md, catalog, set())
    lines = sorted({f["line"] for f in findings})
    assert lines == [1], (
        f"Expected findings only on line 1 (no skip marker); the line-2 "
        f"version-comparison row must be suppressed by `<!-- uip-check-skip -->`. "
        f"Got findings on lines: {lines!r}."
    )


# --- Issue 13: renames entry shadows shallower catalog prefix -----------------

def test_renames_entry_shadows_shallower_catalog_prefix():
    """When a subcommand is retired but its parent group is still in the
    catalog, classify must mark the path as retired — not reachable via the
    parent prefix. Example: `solution new` was removed in uip 1.2.0, but
    `solution` (the group) is still a catalog verb. Without preferring the
    more-specific renames entry, the longest-prefix walker would match the
    parent and report the retired verb as reachable, swallowing the rename.
    """
    catalog = {"solution", "solution init"}
    renames = {"solution new": "solution init"}
    verdict, details = cli.classify(["solution new"], catalog, renames)
    assert verdict == "retired", (
        f"Expected 'retired' (renames shadows shallower catalog prefix), "
        f"got {verdict!r} with details {details!r}."
    )
    assert details["suggestions"]["solution new"] == "solution init"


def test_backticked_rename_cells_strip_to_bare_verbs(tmp_path, monkeypatch):
    """The markdown table in cli-renames.md formats verb cells with backticks
    for readability (`| `solution new` | `solution init` | ...`). The loader
    must strip those so classify gets bare verb strings — otherwise the
    renames dict looks like `{'`solution new`': '`solution init`'}` and no
    extracted verb ever matches.
    """
    rename_file = tmp_path / "cli-renames.md"
    rename_file.write_text(
        "| Retired           | Canonical            | Retired at |\n"
        "|-------------------|----------------------|------------|\n"
        "| `solution new`    | `solution init`      | uip 1.2.0  |\n"
    )
    monkeypatch.setattr(cli, "RENAMES_PATH", rename_file)
    renames = cli.load_renames()
    assert renames == {"solution new": "solution init"}, (
        f"Expected stripped keys/values, got {renames!r}."
    )


# --- Issue 15 (High): `\b` after a complete token discarded the leaf verb -----

def test_word_boundary_after_complete_token_keeps_leaf():
    r"""`uip\s+pm\s+apps\s+data-model\s+add-table\b.*--file\b` must yield the
    FULL verb path, not just the group `pm apps data-model`.

    `\b` following a literal word character confirms the token ended — the
    opposite of a partial match. Trimming it dropped the leaf verb from every
    `uip <group> <leaf>\b` pattern, which is the repo's standard shape, so the
    checker only ever verified the command group.
    """
    paths = cli.extract_verb_paths(
        r"uip\s+pm\s+apps\s+data-model\s+add-table\b.*--file\b")
    assert paths == ["pm apps data-model add-table"], (
        f"Expected the leaf verb to survive `\\b`, got {paths!r}."
    )


def test_bogus_leaf_under_real_group_is_unknown():
    """`pm apps model add-table` must NOT pass via the parent group.

    `pm apps model` is a real group (`fields`/`get`/`update`), but it has no
    `add-table` child — that verb is `pm apps data-model add-table`. Longest-
    prefix matching silently reported the bogus leaf as reachable, so the
    criterion could never fire and the task lost its weight on a correct run.
    """
    catalog = {"pm apps model", "pm apps model fields", "pm apps model get",
               "pm apps data-model", "pm apps data-model add-table"}
    verdict, _ = cli.classify(["pm apps model add-table"], catalog, {})
    assert verdict == "unknown", (
        f"Expected 'unknown' for a leaf absent under a known group, got {verdict!r}."
    )
    verdict, _ = cli.classify(["pm apps data-model add-table"], catalog, {})
    assert verdict == "reachable"


def test_positional_args_after_leaf_verb_stay_reachable():
    """Trailing positional arguments must not be mistaken for subcommands.

    `is resources run list` is a leaf (no children), so `uipath-testmanager`
    and `GetAssertions` are arguments — flagging them would be a false positive.
    """
    catalog = {"is resources run", "is resources run list"}
    verdict, _ = cli.classify(
        ["is resources run list uipath-testmanager GetAssertions"], catalog, {})
    assert verdict == "reachable"


def test_partial_kebab_token_is_not_reported_missing():
    """A path ending mid-kebab (`create-`) came from a prefix match over real
    verbs (`create-raw`, `create-resource`) — we cannot claim it is missing."""
    catalog = {"agenthub mcp-tools", "agenthub mcp-tools create-raw",
               "agenthub mcp-tools create-resource"}
    verdict, _ = cli.classify(["agenthub mcp-tools create-"], catalog, {})
    assert verdict == "reachable"


def test_unwalkable_group_never_reports_missing_leaf():
    """Children of an unwalkable group are unknown, so absence proves nothing."""
    catalog = {"codedagent", "codedagent init"}
    verdict, _ = cli.classify(["codedagent teleport"], catalog, {},
                              unwalkable={"codedagent"})
    assert verdict == "reachable"


# --- Issue 16 (Medium): negative criteria were never verb-checked -------------

def test_negative_criteria_are_scanned_and_reported_medium(tmp_path, monkeypatch):
    """A `command_not_executed` whose verb does not exist can never fire, so it
    awards its weight unconditionally. Previously such criteria were skipped
    entirely. They are reported at Medium (sometimes the guard is deliberate),
    never High — they do not break the run.
    """
    monkeypatch.setattr(cli, "load_catalog", lambda: ({"pm apps", "pm apps get"}, "test"))
    monkeypatch.setattr(cli, "load_renames", lambda: {})
    monkeypatch.setattr(cli, "load_unwalkable", lambda: set())

    task = tmp_path / "task.yaml"
    task.write_text(
        "success_criteria:\n"
        "  - type: command_not_executed\n"
        "    command_pattern: 'uip\\s+pm\\s+apps\\s+teleport\\b'\n"
    )
    findings = cli.lint_file(task, {"pm apps", "pm apps get"}, {}, set())
    assert len(findings) == 1, f"Expected the negative to be scanned, got {findings!r}"
    assert findings[0]["severity"] == "Medium", findings[0]


def test_zero_bounded_command_executed_counts_as_negative(tmp_path):
    """`command_executed` with `max_count: 0` is the other negative idiom in
    this repo; it must get the same Medium treatment, not High."""
    task = tmp_path / "task.yaml"
    task.write_text(
        "success_criteria:\n"
        "  - type: command_executed\n"
        "    command_pattern: 'uip\\s+pm\\s+apps\\s+teleport\\b'\n"
        "    min_count: 0\n"
        "    max_count: 0\n"
    )
    findings = cli.lint_file(task, {"pm apps", "pm apps get"}, {}, set())
    assert len(findings) == 1
    assert findings[0]["severity"] == "Medium", findings[0]


# --- Issue 12: dot-separated argument values are not verb tokens --------------

def test_dot_separated_argument_value_not_treated_as_verb(tmp_path):
    """`uip maestro flow registry get core.action.script` — the trailing
    `core.action.script` is a registry resource key, not a verb token.
    Catalog verbs never contain dots; dot-separated identifiers are args.
    """
    md = tmp_path / "doc.md"
    md.write_text("Run `uip maestro flow registry get core.action.script`.\n")
    catalog = {"maestro flow registry get"}
    findings = skill.scan_file(md, catalog, set())
    assert findings == [], (
        f"Expected no findings — `core.action.script` is an argument, "
        f"got {findings!r}."
    )
