"""Editing an existing Flow on a later turn must keep the user's work.

- No instruction pairs `init` with `--force` except to forbid it: `--force`
  resets `<Name>.flow`, `project.uiproj` and `operate.json`.
- The editing loop removes the generated pipeline's artifacts before its fresh
  decompile: the pipeline keeps a baseline that exists, and a stale one makes
  merge drop an edit that matches it. The names are the pipeline's own
  (`BASELINE`, `EDITED`, `MERGED` in a generated `<Name>.pipeline.mjs`).
- `flow debug` is a real run: every shipped debug rule says when to ask first.
- The completion output reports the connection `prepare` bound, and the
  connector loops point to it.

Checked on the shipped text of the default package and the Studio Web flavor.
Regex, not PyYAML: CI installs only pytest.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flavor_markers import compose, shipped  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", "..", "..", ".."))
_CANONICAL = os.path.join(_REPO, "skills", "uipath-maestro-flow")
_STUDIOWEB = os.path.join(_REPO, "skill-flavors", "studioweb", "uipath-maestro-flow")

PIPELINE_ARTIFACTS = (".flow-sdk/{n}.baseline", ".flow-sdk/{n}.edited", ".flow-sdk/{n}.merged.flow")
FLAVORS = ("default", "studioweb")
COMPLETION_OUTPUT = "author.md#completion-output"

_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.S | re.M)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_QUOTED = re.compile(r'"[^"]*"')
_TRAILING_COMMENT = re.compile(r"\s+#.*$")
_SUBSHELL = re.compile(r'^\(\s*cd\s+"[^"]*"\s*&&\s*(.*?)\s*\)$')


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _composed(flavor: str, rel: str) -> str:
    text = _read(os.path.join(_CANONICAL, rel))
    override = os.path.join(_STUDIOWEB, rel)
    if flavor == "default" or not os.path.exists(override):
        return shipped(text)

    return compose(text, _read(override))


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##+ {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match, f"missing section: {heading}"
    return match.group(1)


def _paragraphs(text: str) -> list[str]:
    prose = _FENCE.sub("\n\n", text)
    return [" ".join(line.strip() for line in p.splitlines()) for p in re.split(r"\n\s*\n", prose)]


def _sentences(paragraph: str) -> list[str]:
    return [s for s in _SENTENCE_END.split(_QUOTED.sub('""', paragraph)) if s]


def _commands(text: str) -> list[str]:
    commands = []
    for block in _FENCE.findall(text):
        joined = re.sub(r"\\\n\s*", " ", block)
        for line in joined.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            line = _TRAILING_COMMENT.sub("", line)
            inner = _SUBSHELL.match(line)
            commands.append(inner.group(1) if inner else line)
    return commands


def test_init_never_paired_with_force():
    offenders = []
    for flavor in FLAVORS:
        for rel in ("SKILL.md", "references/brownfield.md", "references/author.md", "references/CLI-LOOP.md"):
            text = _composed(flavor, rel)
            for paragraph in _paragraphs(text):
                for sentence in _sentences(paragraph):
                    pairs = re.search(r"\binit\b", sentence) and "--force" in sentence
                    if pairs and not re.search(r"\bnever\b[^.]*?--force", sentence):
                        offenders.append(f"{flavor} {rel}: {sentence}")

            for command in _commands(text):
                if re.search(r"\bflow init\b", command) and "--force" in command:
                    offenders.append(f"{flavor} {rel}: {command}")

    assert not offenders, "init with --force resets an existing project:\n" + "\n".join(offenders)


def test_editing_loop_clears_pipeline_artifacts_first():
    editing = _section(_composed("default", "SKILL.md"), "Editing an existing flow")
    commands = _commands(editing)
    decompile = next((i for i, c in enumerate(commands) if "flow decompile" in c), None)
    assert decompile is not None, "## Editing an existing flow has no decompile command"

    wanted = [p.format(n="<Name>") for p in PIPELINE_ARTIFACTS]
    cleaned = any(
        c.startswith("rm -rf ") and all(path in c.split() for path in wanted)
        for c in commands[:decompile]
    )
    assert cleaned, f"## Editing an existing flow must run `rm -rf {' '.join(wanted)}` before `decompile`"


def test_generated_pipeline_names_the_artifacts():
    pipeline = _section(_composed("default", "references/brownfield.md"), "The generated pipeline")
    commands = _commands(pipeline) + [p for p in _paragraphs(pipeline) if "rm -rf" in p]
    wanted = [p.format(n="Deployed") for p in PIPELINE_ARTIFACTS]
    assert any("rm -rf" in c and all(path in c for path in wanted) for c in commands), (
        f"brownfield.md generated pipeline must remove {wanted} before a later turn's decompile"
    )


def test_every_debug_rule_says_when_to_ask():
    missing = []
    for flavor in FLAVORS:
        lifecycle = _section(_composed(flavor, "SKILL.md"), "Lifecycle")
        if not re.search(r"\bask\b[^\n]*\bunless\b", lifecycle):
            missing.append(f"{flavor} SKILL.md ## Lifecycle")

        operate = _composed(flavor, "references/operate.md")
        rule = next((s for s in re.split(r"\n\s*\n", operate) if "`flow debug` executes the flow for real" in s), "")
        if not re.search(r"\bask (once )?before\b", rule):
            missing.append(f"{flavor} references/operate.md debug rule")

    assert not missing, "debug without an ask-first rule:\n" + "\n".join(missing)


def test_connection_report_has_one_home():
    problems = []
    for flavor in FLAVORS:
        author = _composed(flavor, "references/author.md")
        item = re.search(r"^5\. \*\*Connections\*\*.*?(?=^\d+\. \*\*)", author, re.S | re.M)
        body = " ".join(item.group(0).split()) if item else ""
        for needed in ("connection: <Name> (<id>)", "folder", "[REQUIRED]"):
            if needed not in body:
                problems.append(f"{flavor} author.md completion item 5 lacks {needed!r}")

        if COMPLETION_OUTPUT not in _composed(flavor, "SKILL.md"):
            problems.append(f"{flavor} SKILL.md connector loop does not point to {COMPLETION_OUTPUT}")

    assert not problems, "\n".join(problems)
