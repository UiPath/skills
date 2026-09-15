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


# --- cli_called criteria are in scope for the catalog check -------------------

def _task(tmp_path, body, name="task.yaml"):
    task = tmp_path / name
    task.write_text("success_criteria:\n" + body)
    return task


CLI_CALLED_CATALOG = {"ixp", "ixp projects", "ixp projects list",
                      "ixp projects get", "ixp projects delete"}


def test_cli_called_verb_is_linted_at_all(tmp_path):
    """`cli_called` names its verb in `verb`, not in a `command_pattern`.

    The checker only ever parsed `command_pattern`, so every task migrated from
    `file_matches_regex`/`command_executed` to `cli_called` silently left the
    catalog linter's reach — a stale verb in a migrated task was unreachable by
    any gate in the repo.
    """
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "typo"\n'
                 '    verb: "ixp projects lisst"\n'
                 '    tool: "uip"\n')
    findings = cli.lint_file(task, CLI_CALLED_CATALOG, {})
    assert [f["severity"] for f in findings] == ["High"], (
        f"Expected one High for a verb absent from the catalog, got {findings!r}."
    )
    assert findings[0]["source"] == "cli_called"


def test_cli_called_typoed_leaf_not_rescued_by_group_prefix(tmp_path):
    """`classify`'s longest-prefix fallback must NOT apply to a cli_called verb.

    A `command_pattern` can carry a trailing fragment the regex happened to
    capture, so it needs the fallback. A `cli_called` verb is a complete literal
    chain, and `ixp projects` is itself a catalog entry — so under the fallback
    the typo `ixp projects lisst` matched the parent group and scored reachable,
    which is the exact blind spot this check exists to close.
    """
    verdict, _ = cli.classify(["ixp projects lisst"], CLI_CALLED_CATALOG, {},
                              exact=True)
    assert verdict == "unknown", (
        f"Expected 'unknown' — the leaf is a typo and must not match the "
        f"`ixp projects` group; got {verdict!r}."
    )
    # The prefix fallback is still what `command_pattern` needs.
    verdict_prefix, _ = cli.classify(["ixp projects lisst"],
                                     CLI_CALLED_CATALOG, {})
    assert verdict_prefix == "reachable"


def test_cli_called_deliberately_short_verb_stays_reachable(tmp_path):
    """A group-level verb is legal — `verb` is an ordered PREFIX of the argv, so
    a `max_count: 0` guard on `ixp projects` deliberately fires on every
    subcommand. The catalog holds group entries, so exact matching accepts it.
    """
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "group guard"\n'
                 '    verb: "ixp projects"\n'
                 '    tool: "uip"\n'
                 '    min_count: 0\n'
                 '    max_count: 0\n')
    assert cli.lint_file(task, CLI_CALLED_CATALOG, {}) == []


def test_cli_called_verb_any_of_reachable_if_any_spelling_is(tmp_path):
    """`verb_any_of` entries are alternatives, so they classify as a group —
    the same way a regex alternation's paths do. One reachable spelling means
    the criterion can still fire.
    """
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "channel"\n'
                 '    verb_any_of: ["ixp projects get", "ixp projects list"]\n'
                 '    tool: "uip"\n')
    assert cli.lint_file(task, CLI_CALLED_CATALOG, {}) == []

    both_bad = _task(tmp_path,
                     '  - type: cli_called\n'
                     '    description: "channel"\n'
                     '    verb_any_of: ["ixp projects gett", "ixp projects listt"]\n'
                     '    tool: "uip"\n',
                     name="both_bad.yaml")
    findings = cli.lint_file(both_bad, CLI_CALLED_CATALOG, {})
    assert [f["severity"] for f in findings] == ["High"], (
        f"Expected High when NO spelling is reachable, got {findings!r}."
    )


def test_cli_called_retired_verb_is_medium_with_suggestion(tmp_path):
    """Renames stay prefix-matched under `exact`, so a retired ancestor still
    yields the canonical suggestion rather than a bare High.
    """
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "retired"\n'
                 '    verb: "solution new"\n'
                 '    tool: "uip"\n')
    findings = cli.lint_file(task, {"solution", "solution init"},
                             {"solution new": "solution init"})
    assert [f["severity"] for f in findings] == ["Medium"], (
        f"Expected Medium for a retired verb, got {findings!r}."
    )
    assert "solution init" in findings[0]["message"]


def test_cli_called_non_uip_tool_gets_no_verdict(tmp_path):
    """`record_cli` shims several executables into ONE shared log, and `tool`
    is what separates them. A verb recorded under `curl` is not a uip verb, and
    an ABSENT `tool` matches any executable — neither can be claimed against the
    uip catalog, so both are skipped without a finding.
    """
    other_tool = _task(tmp_path,
                       '  - type: cli_called\n'
                       '    description: "curl guard"\n'
                       '    verb: "not a uip verb"\n'
                       '    tool: "curl"\n'
                       '    min_count: 0\n'
                       '    max_count: 0\n')
    assert cli.lint_file(other_tool, CLI_CALLED_CATALOG, {}) == []

    no_tool = _task(tmp_path,
                    '  - type: cli_called\n'
                    '    description: "tool-less"\n'
                    '    verb: "not a uip verb"\n',
                    name="no_tool.yaml")
    assert cli.lint_file(no_tool, CLI_CALLED_CATALOG, {}) == []


def test_cli_called_verbless_criterion_is_skipped(tmp_path):
    """A flags-only or positional-only `cli_called` is legal and names no verb."""
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "flags only"\n'
                 '    tool: "uip"\n'
                 '    flags:\n'
                 '      force: {present: true}\n'
                 '    min_count: 0\n'
                 '    max_count: 0\n')
    assert cli.lint_file(task, CLI_CALLED_CATALOG, {}) == []


def test_cli_called_verb_whitespace_is_normalised(tmp_path):
    """coder_eval splits the verb on whitespace (`verb.split()`), so irregular
    inner spacing is the same verb and must not read as absent from the catalog.
    """
    task = _task(tmp_path,
                 '  - type: cli_called\n'
                 '    description: "spacing"\n'
                 '    verb: "ixp   projects  list"\n'
                 '    tool: "uip"\n')
    assert cli.lint_file(task, CLI_CALLED_CATALOG, {}) == []
