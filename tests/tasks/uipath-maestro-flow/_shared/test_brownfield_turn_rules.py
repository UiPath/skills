"""Safety wording for editing an existing Flow, pinned on the shipped text.

Pins wording, not agent behavior.

- `--force` appears only as `never pass --force`, inside a quoted CLI message,
  or on `registry pull` / `codedagent setup`.
- SKILL.md skips the decompile only for a supplied source, and writes
  `-o <Name>.flow` only in the new-flow Lifecycle block.
- Every brownfield loop clears an earlier turn's artifacts and agent sidecars
  before it writes new ones.
- The supplied-source loop never decompiles and ends in `merge --original`.
- The debug, overwrite and guessed-connection rules keep their exact clauses.
- bindings.md holds the connection-pick rule; the others point to it.

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

PIPELINE_ARTIFACTS = ("'{n}.baseline'", "'{n}.edited'", "'{n}.merged.flow'", "'*-*-*-*-*'")
CLEAR_WORK = 'rm -rf "${WORK:?}"'
FLAVORS = ("default", "studioweb")
ALLOWED_FORCE = re.compile(r"never pass `--force`|registry pull --force|codedagent setup --force")
BINDINGS_RULE = "bindings.md#where-both-values-come-from"

INIT_RULE = (
    '`init` answering "already exists and is not empty. Use --force to overwrite" means it exists: '
    "never pass `--force`; edit it."
)
SKIP_DECOMPILE_EXEMPTION = (
    "A supplied source skips the decompile ([brownfield.md](references/brownfield.md#a-supplied-source))."
)

PINNED = {
    ("default", "SKILL.md"): [
        INIT_RULE,
        "When `<Solution>/<Name>/` existed before this turn, skip `init`",
        f"What `prepare` binds or refuses: [bindings.md](references/{BINDINGS_RULE}).",
        "# Stated runtime claim; ask per references/operate.md",
        "`flow debug` is a REAL run, not a validation step: ask first, as it says.",
    ],
    ("studioweb", "SKILL.md"): [
        "`uip maestro flow debug \"<Project>\"` is a real run: ask per references/operate.md.",
        "`flow debug` is a REAL run, not a validation step: ask first, as it says.",
    ],
    ("default", "references/operate.md"): [
        "ask once before the first run, even when the request is for a flow that works; "
        "that yes covers the fix-and-re-run loop on the flow the user asked to get working this turn.",
        "run it when the request is for a flow that works, unless a connection was guessed",
        "for a solution not scaffolded this turn, debug only on a yes to a question that names that "
        "overwrite, and headless, never debug it.",
    ],
    ("studioweb", "references/operate.md"): [
        "ask before each run, even when the request is for a flow that works.",
        "run it when the request is for a flow that works, unless a connection was guessed",
    ],
    ("default", "references/bindings.md"): [
        "When it refuses with several candidates, ask a user who can answer.",
        "Headless, pass `--connection-folder` for the folder the request names.",
        "With no folder named, or when that refuses (no match or several), pass the first candidate line's "
        "`--connection-id`: that connection is guessed. Do not debug on it, report the flow unverified, and "
        "list the pick under Open questions as **[REQUIRED]**",
    ],
    ("default", "references/author.md"): [
        "`uip is connections list <connector-key> --all-folders --output json`",
        f"A guessed connection ([bindings.md]({BINDINGS_RULE})) also goes under Open questions as **[REQUIRED]**.",
    ],
    ("default", "references/connector-params.md"): [
        f"choose as [bindings.md]({BINDINGS_RULE}) says",
    ],
}

_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.S | re.M)
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_QUOTED = re.compile(r'"[^"\n]*"')
_TRAILING_COMMENT = re.compile(r"\s+#.*$")
_SUBSHELL = re.compile(r'^\(\s*cd\s+"[^"]*"\s*&&\s*(.*?)\s*\)$')
_NAME_FLOW_TARGET = re.compile(r"\bcompile\b.*\s-o\s+\"?<Name>\.flow\b")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _composed(flavor: str, rel: str) -> str:
    text = _read(os.path.join(_CANONICAL, rel))
    override = os.path.join(_STUDIOWEB, rel)
    if flavor == "default" or not os.path.exists(override):
        return shipped(text)

    return compose(text, _read(override))


def _flat(text: str) -> str:
    return " ".join(text.split())


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


def _removes(command: str, names: list[str]) -> bool:
    return ("rm -rf" in command) and all(name in command for name in names)


def test_pinned_safety_wording():
    missing = []
    for (flavor, rel), phrases in PINNED.items():
        text = _flat(_composed(flavor, rel))
        missing += [f"{flavor} {rel}: {phrase}" for phrase in phrases if _flat(phrase) not in text]

    assert not missing, "pinned safety wording changed:\n" + "\n".join(missing)


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
    skill = _composed("default", "SKILL.md")
    offenders = []
    for sentence in _sentences(skill):
        if re.search(r"\bskip\w*\b[^.]*\bdecompile", sentence) and sentence != SKIP_DECOMPILE_EXEMPTION:
            offenders.append(sentence)
        if re.search(r"\bexist", sentence) and "compile -o" in sentence:
            offenders.append(sentence)

    targets = [c for c in _commands(skill) if _NAME_FLOW_TARGET.search(c)]
    lifecycle = _commands(_section(skill, "Lifecycle"))
    if len(targets) != 1 or targets != lifecycle[:1]:
        offenders += targets

    assert not offenders, "an existing .flow goes through Editing, not compile -o:\n" + "\n".join(offenders)


def test_editing_loop_clears_pipeline_artifacts_first():
    commands = _commands(_section(_composed("default", "SKILL.md"), "Editing an existing flow"))
    decompile = next((i for i, c in enumerate(commands) if "flow decompile" in c), None)
    assert decompile is not None, "## Editing an existing flow has no decompile command"

    wanted = [p.format(n="<Name>") for p in PIPELINE_ARTIFACTS]
    cleaned = any(_removes(c, wanted) for c in commands[:decompile])
    assert cleaned, f"## Editing an existing flow must remove {wanted} before `decompile`"


def test_generated_pipeline_names_the_artifacts():
    pipeline = _section(_composed("default", "references/brownfield.md"), "The generated pipeline")
    wanted = [p.format(n="Deployed") for p in PIPELINE_ARTIFACTS]
    units = _commands(pipeline) + _paragraphs(pipeline)
    assert any(_removes(u, wanted) for u in units), (
        f"brownfield.md generated pipeline must remove {wanted} before a later turn's decompile"
    )


def test_supplied_source_never_decompiles():
    commands = _commands(_section(_composed("default", "references/brownfield.md"), "A supplied source"))
    assert commands, "brownfield.md ## A supplied source has no commands"
    assert not any("decompile" in c for c in commands), "the supplied-source loop must not decompile"
    assert commands[-1].startswith("uip maestro flow merge ") and "--original" in commands[-1], (
        "the supplied-source loop must end in `merge --original`"
    )


def test_work_loops_clear_work_first():
    brownfield = _composed("default", "references/brownfield.md")
    stale = []
    for block in _FENCE.findall(brownfield):
        commands = _commands("```\n" + block + "```\n")
        writes = next((i for i, c in enumerate(commands) if '"$WORK/candidate' in c and "-o" in c), None)
        if writes is None:
            continue

        if not any(c.startswith(CLEAR_WORK) for c in commands[:writes]):
            stale.append(commands[writes])

    assert not stale, f"a loop that writes $WORK/candidate must `{CLEAR_WORK}` first:\n" + "\n".join(stale)
