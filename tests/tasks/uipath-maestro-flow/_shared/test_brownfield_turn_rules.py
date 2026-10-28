"""Rules for editing an existing Flow on a later turn, on the shipped text.

- `--force` appears only as `never pass --force`, inside a quoted CLI message,
  or on `registry pull` / `codedagent setup`.
- SKILL.md never tells an agent to skip the decompile (except for a supplied
  source) or `compile -o` over an existing flow.
- The editing loop removes the generated pipeline's artifacts before decompile.
- Every shipped debug rule asks first, and none negates the ask.
- Completion output item 5 holds the connection rule; SKILL.md points to it.

Regex, not PyYAML: CI installs only pytest.
"""
from __future__ import annotations

import glob
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
ALLOWED_FORCE = re.compile(r"never pass `--force`|registry pull --force|codedagent setup --force")

_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.S | re.M)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_QUOTED = re.compile(r'"[^"\n]*"')
_TRAILING_COMMENT = re.compile(r"\s+#.*$")
_SUBSHELL = re.compile(r'^\(\s*cd\s+"[^"]*"\s*&&\s*(.*?)\s*\)$')
_ASK = re.compile(r"\bask\b")
_NEGATED_ASK = re.compile(r"\b(?:do not|don't|never|no need to)\s+ask\b", re.I)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _composed(flavor: str, rel: str) -> str:
    text = _read(os.path.join(_CANONICAL, rel))
    override = os.path.join(_STUDIOWEB, rel)
    if flavor == "default" or not os.path.exists(override):
        return shipped(text)

    return compose(text, _read(override))


def _files() -> list[str]:
    refs = sorted(glob.glob(os.path.join(_CANONICAL, "references", "**", "*.md"), recursive=True))
    return ["SKILL.md"] + [os.path.relpath(p, _CANONICAL) for p in refs]


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##+ {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match, f"missing section: {heading}"
    return match.group(1)


def _paragraphs(text: str) -> list[str]:
    prose = _FENCE.sub("\n\n", text)
    return [" ".join(line.strip() for line in p.splitlines()) for p in re.split(r"\n\s*\n", prose)]


def _sentences(text: str) -> list[str]:
    return [s for p in _paragraphs(text) for s in _SENTENCE_END.split(_QUOTED.sub('""', p)) if s]


def _commands(text: str) -> list[str]:
    commands = []
    for block in _FENCE.findall(text):
        for line in re.sub(r"\\\n\s*", " ", block).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            line = _TRAILING_COMMENT.sub("", line)
            inner = _SUBSHELL.match(line)
            commands.append(inner.group(1) if inner else line)
    return commands


def _positive_ask(text: str) -> bool:
    return bool(_ASK.search(_NEGATED_ASK.sub("", text))) and not _NEGATED_ASK.search(text)


def test_force_only_where_safe():
    offenders = []
    for flavor in FLAVORS:
        for rel in _files():
            text = _composed(flavor, rel)
            for unit in _sentences(text) + _commands(text):
                if "--force" in ALLOWED_FORCE.sub("", unit):
                    offenders.append(f"{flavor} {rel}: {unit}")

    assert not offenders, "--force outside `never pass --force` (it resets a project):\n" + "\n".join(offenders)


def test_existing_flow_is_never_recompiled_over():
    offenders = []
    for sentence in _sentences(_composed("default", "SKILL.md")):
        if re.search(r"\bskip\w*\b[^.]*\bdecompile", sentence) and "supplied" not in sentence:
            offenders.append(sentence)
        if re.search(r"\bexist", sentence) and "compile -o" in sentence:
            offenders.append(sentence)

    assert not offenders, "an existing .flow goes through Editing, not compile -o:\n" + "\n".join(offenders)


def test_editing_loop_clears_pipeline_artifacts_first():
    commands = _commands(_section(_composed("default", "SKILL.md"), "Editing an existing flow"))
    decompile = next((i for i, c in enumerate(commands) if "flow decompile" in c), None)
    assert decompile is not None, "## Editing an existing flow has no decompile command"

    wanted = [p.format(n="<Name>") for p in PIPELINE_ARTIFACTS]
    cleaned = any(c.startswith("rm -rf ") and all(p in c.split() for p in wanted) for c in commands[:decompile])
    assert cleaned, f"## Editing an existing flow must run `rm -rf {' '.join(wanted)}` before `decompile`"


def test_generated_pipeline_names_the_artifacts():
    pipeline = _section(_composed("default", "references/brownfield.md"), "The generated pipeline")
    wanted = [p.format(n="Deployed") for p in PIPELINE_ARTIFACTS]
    units = _commands(pipeline) + _paragraphs(pipeline)
    assert any("rm -rf" in u and all(p in u for p in wanted) for u in units), (
        f"brownfield.md generated pipeline must remove {wanted} before a later turn's decompile"
    )


def test_every_debug_rule_asks_first():
    missing = []
    for flavor in FLAVORS:
        skill = _composed(flavor, "SKILL.md")
        for heading in ("Lifecycle", "Operating a deployed flow"):
            debug = [u for u in _sentences(_section(skill, heading)) if "debug" in u]
            debug += [line for line in _section(skill, heading).splitlines() if line.lstrip().startswith("#")]
            if not any(_positive_ask(u) for u in debug) or any(_NEGATED_ASK.search(u) for u in debug):
                missing.append(f"{flavor} SKILL.md ## {heading}")

        operate = _composed(flavor, "references/operate.md")
        rule = next((p for p in _paragraphs(operate) if "`flow debug` executes the flow for real" in p), "")
        if not re.search(r"\bask (?:once )?before\b", rule) or _NEGATED_ASK.search(rule):
            missing.append(f"{flavor} references/operate.md debug rule")

    assert not missing, "debug without an ask-first rule:\n" + "\n".join(missing)


def test_connection_report_has_one_home():
    problems = []
    for flavor in FLAVORS:
        author = _composed(flavor, "references/author.md")
        item = re.search(r"^5\. \*\*Connections\*\*.*?(?=^\d+\. \*\*)", author, re.S | re.M)
        body = " ".join(item.group(0).split()) if item else ""
        for needed in ("connection: <Name> (<id>)", "folder", "do not debug on that guess", "[REQUIRED]"):
            if needed not in body:
                problems.append(f"{flavor} author.md completion item 5 lacks {needed!r}")

        if COMPLETION_OUTPUT not in _composed(flavor, "SKILL.md"):
            problems.append(f"{flavor} SKILL.md does not point to {COMPLETION_OUTPUT}")

    assert not problems, "\n".join(problems)
