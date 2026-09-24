"""The preview Flow skill must not teach an inline-agent prompt that asks for JSON text.

Why this gate exists (skill-flow-devcon-billing-resolution-writer, 2026-09-23):
the v2 agent read ``references/inline-agent.md`` (``systemPrompt: 'Return JSON
with category.'``) and ``examples/PostcardCaption.flow.ts`` ("return ONLY a JSON
object with keys ..."), and wrote "Return ONLY a JSON object with exactly two
string keys: subject and body" next to ``returns: { subject, body }``. The
platform already returns ``returns`` as a typed object (agent.json
``outputSchema``, filled by the runtime's structured final call), so the model
packed its whole answer into ``body``: '{"subject":...,"body":"Dear ..."}' in 3 of
3 debug runs.

The SDK now refuses that prompt at ``check`` (INLINE_AGENT_PROMPT_JSON_TEXT,
UiPath/flow-builder-sdk). This test keeps the preview docs from teaching it: it
reads every ``inlineAgent(...)`` call in the preview skill's ``.ts`` files and
``ts`` code fences, folds each ``systemPrompt`` / ``userPrompt`` string (``'a ' +
'b'`` concatenation included), and fails on any phrase the SDK matcher would
refuse. Prose, ``--output json`` CLI text and checker code are never read.

``json_text_directive`` is a port of the SDK's ``jsonTextDirective``
(``typescript/sdk/src/check.ts``). Both repos run it against the same vectors:
``inline_agent_prompt_vectors.json`` here is a byte-identical copy of the SDK's
``typescript/tests/fixtures/inline-agent-prompt-vectors.json``. When the SDK
matcher changes, copy the fixture and port the table change in the same PR.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
PREVIEW = REPO / "preview" / "skills" / "uipath-maestro-flow"

# ── the SDK matcher, ported ───────────────────────────────────────────────────
# Three shapes, each skipping a negation earlier in the same clause or inside the gap:
#  DIRECT  verb + closed qualifier words + json   ("Return ONLY a JSON object")
#  VIA     verb + <=2 words + as/in/with + qualifiers + json   ("Format your answer as JSON")
#  BRACE   a quoted-key brace spelling a returns key   ('Return ONLY {"category"}')
_VERBS = "return|respond|reply|output|answer|produce|emit|format|give|provide"
_QUALIFIERS = [
    "only", "just", "exactly", "strictly", "solely", "simply", "a", "an", "one", "single", "the",
    "your", "its", "this", "that", "valid", "raw", "pure", "plain", "strict", "compact", "minified",
    "well-formed", "properly", "formatted", "typed", "declared", "structured", "following", "same",
    "final", "back", "proper", "correct", "machine-readable", "parseable", "parsable",
]
_NEGATIONS = {"not", "never", "no", "dont", "without", "rather", "instead", "avoid"}
_WORD = r"[A-Za-z][\w'’-]*"
_SEP = r"[ \t]*,?[ \t]+"
_QUAL = "(?:" + "|".join(re.escape(w) for w in sorted(_QUALIFIERS, key=len, reverse=True)) + r")\b"
_TAIL = (
    r"json\b(?!\.\w)(?!-(?:ld|rpc)\b)(?![ \t]+(?:below|above|provided|given|you"
    r"|keys?|data|records?|examples?|inputs?"
    r"|schemas?|patch|path|pointer|lines|rpc|web[ \t]+tokens?)\b)"
)
_VERB = rf"(?<![-\w])(?:{_VERBS})\b"
# re.ASCII: the JS patterns carry no `u` flag, so their `\w` and `\b` are ASCII-only.
_DIRECT = re.compile(rf"{_VERB}((?:{_SEP}{_QUAL}){{0,5}}){_SEP}{_TAIL}", re.I | re.A)
_VIA = re.compile(
    rf"{_VERB}((?:{_SEP}{_WORD}){{0,2}}?){_SEP}(?:as|in|with)((?:{_SEP}{_QUAL}){{0,4}}){_SEP}{_TAIL}",
    re.I | re.A,
)


def _is_negation(word: str) -> bool:
    return word in _NEGATIONS or word.endswith("n't") or word.endswith("n’t")


def _words(text: str) -> list[str]:
    return [w.lower() for w in re.findall(_WORD, text, re.A)]


def json_text_directive(text: str, return_keys: list[str] | None = None) -> str | None:
    """The phrase that tells a model to answer in JSON text, or ``None``.

    With ``return_keys`` the brace form counts only a brace spelling one of them;
    without, any quoted identifier key counts (the SDK behaves the same way)."""
    if not isinstance(text, str) or not text:
        return None
    t = re.sub(r"\{\{\s*input\.[^}]*\}\}", " · ", text)
    t = re.sub(r"[`\"'“”](json)[`\"'“”]", r" \1 ", t, flags=re.I)
    keys = "|".join(re.escape(k) for k in return_keys) if return_keys else r"[A-Za-z_]\w*"
    brace = re.compile(rf"\{{[ \t]*[\"'](?:{keys})[\"'][ \t]*[,:}}]", re.A)
    for rule in (_DIRECT, _VIA, brace):
        for m in rule.finditer(t):
            if any(_is_negation(w) for g in m.groups() for w in _words(g or "")):
                continue
            clause = re.split(r"[.;:!?\n,]", t[: m.start()])[-1]
            if any(_is_negation(w) for w in _words(clause)):
                continue
            return m.group(0).strip()
    return None


# ── reading the inlineAgent calls out of the preview tree ────────────────────
_STRING = re.compile(r"'((?:[^'\\\n]|\\.)*)'|\"((?:[^\"\\\n]|\\.)*)\"|`((?:[^`\\]|\\.)*)`")
_PROP = re.compile(r"\b(systemPrompt|userPrompt)\s*:\s*")


def _unescape(raw: str) -> str:
    return re.sub(r"\\(.)", lambda m: "\n" if m.group(1) == "n" else m.group(1), raw)


def _call_body(code: str, open_paren: int) -> str:
    """The text inside ``inlineAgent( ... )``, skipping parens inside strings."""
    depth, i = 0, open_paren
    while i < len(code):
        m = _STRING.match(code, i)
        if m:
            i = m.end()
            continue
        ch = code[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return code[open_paren + 1 : i]
        i += 1
    return code[open_paren + 1 :]


def _prompt_value(body: str, start: int) -> tuple[str, list[tuple[int, int]]]:
    """Fold the ``'a' + 'b'`` literals after a prop key. Returns the text and,
    per literal, (offset in the folded text, offset in ``body``)."""
    text, spans, i = "", [], start
    while True:
        m = _STRING.match(body, i)
        if not m:
            break
        spans.append((len(text), m.start()))
        text += _unescape(next(g for g in m.groups() if g is not None))
        j = m.end()
        plus = re.match(r"\s*\+\s*", body[j:])
        if not plus:
            break
        i = j + plus.end()
    return text, spans


def _code_regions(path: Path) -> list[tuple[str, int]]:
    """(code, 1-based line of its first character) — a whole ``.ts`` file, or
    each ``ts`` fence of a Markdown page."""
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".ts":
        return [(source, 1)]
    regions = []
    for m in re.finditer(r"^```(?:ts|typescript)[^\n]*\n(.*?)^```", source, re.S | re.M):
        regions.append((m.group(1), source.count("\n", 0, m.start(1)) + 1))
    return regions


def directive_hits(root: Path = PREVIEW) -> list[str]:
    """``file:line: phrase`` for every JSON-text directive in an inlineAgent prompt."""
    hits = []
    for path in sorted(p for p in root.rglob("*") if p.suffix in {".md", ".ts"} and p.is_file()):
        for code, first_line in _code_regions(path):
            for call in re.finditer(r"\binlineAgent\s*\(", code):
                open_paren = call.end() - 1
                body = _call_body(code, open_paren)
                body_offset = open_paren + 1
                returns = re.search(r"\breturns\s*:\s*\{([^}]*)\}", body)
                keys = re.findall(r"['\"]?([A-Za-z_]\w*)['\"]?\s*:", returns.group(1)) if returns else []
                for prop in _PROP.finditer(body):
                    text, spans = _prompt_value(body, prop.end())
                    phrase = json_text_directive(text, keys or None)
                    if phrase is None:
                        continue
                    at = text.find(phrase)
                    literal_start = max((b for a, b in spans if a <= at), default=prop.start())
                    line = first_line + code.count("\n", 0, body_offset + literal_start)
                    shown = path.relative_to(REPO) if REPO in path.parents else path
                    hits.append(f"{shown}:{line}: {prop.group(1)} {phrase!r}")
    return hits


def test_preview_skill_has_no_json_text_inline_agent_prompt():
    hits = directive_hits()
    assert not hits, (
        "An inlineAgent prompt in the preview Flow skill asks for JSON text. `returns` is "
        "already the answer's shape; describe each field instead: 'Return a result "
        "conforming to the output schema. <field>: <how to fill it>.'\n  " + "\n  ".join(hits)
    )


@pytest.mark.parametrize(
    "rel", ["SKILL.md", "references/inline-agent.md", "examples/PostcardCaption.flow.ts"]
)
def test_the_gate_reads_the_preview_inline_agent_snippets(rel):
    """Guard against a vacuous pass: each page that shows an inline agent is read."""
    regions = _code_regions(PREVIEW / rel)
    assert any(re.search(r"\binlineAgent\s*\(", code) for code, _ in regions), rel


def test_every_preview_prompt_is_a_literal_the_gate_can_read():
    """Guard against a silent skip: the gate folds only string literals, so a prompt
    written as a variable (``systemPrompt: PROMPT``) would never be checked."""
    unread = []
    for path in sorted(p for p in PREVIEW.rglob("*") if p.suffix in {".md", ".ts"} and p.is_file()):
        for code, _ in _code_regions(path):
            for call in re.finditer(r"\binlineAgent\s*\(", code):
                body = _call_body(code, call.end() - 1)
                for prop in _PROP.finditer(body):
                    text, _spans = _prompt_value(body, prop.end())
                    if not text:
                        unread.append(f"{path.relative_to(REPO)}: {prop.group(1)}")
    assert not unread, "write these prompts as string literals so the gate reads them: " + ", ".join(unread)


# The SDK's vectors, byte for byte (see the module docstring).
VECTORS = json.loads((Path(__file__).parent / "inline_agent_prompt_vectors.json").read_text(encoding="utf-8"))
FIRES = VECTORS["fire"]
SKIPS = VECTORS["skip"]


@pytest.mark.parametrize("prompt", FIRES)
def test_matcher_fires_like_the_sdk(prompt):
    assert json_text_directive(prompt)


@pytest.mark.parametrize("prompt", SKIPS)
def test_matcher_skips_like_the_sdk(prompt):
    assert json_text_directive(prompt) is None


def test_vector_file_is_the_sdk_shape():
    """A vacuous-pass guard: the copied fixture still carries both lists and its notes."""
    assert len(FIRES) >= 20 and len(SKIPS) >= 40
    assert set(VECTORS["notes"]) <= set(FIRES) | set(SKIPS)


def test_brace_form_counts_only_the_steps_own_returns_keys():
    assert json_text_directive('Return ONLY {"category","priority"}.', ["category", "priority"]) == '{"category",'
    assert json_text_directive('Input record: {"ticketId": "T-1"}', ["category", "priority"]) is None


def test_preview_skill_never_restates_the_retired_fil_run_contract():
    """The SDK's old TSDoc said "the engine's own live path appends a 'return ONLY a
    JSON object' directive". Only the retired fil-run runner did that; the platform
    fills agent.json ``outputSchema`` through a structured final call. A copied doc
    must not bring the sentence back."""
    stale = re.compile(r"live path appends|engine'?s own live path", re.I)
    hits = [
        f"{p.relative_to(REPO)}:{n}"
        for p in sorted(PREVIEW.rglob("*"))
        if p.is_file() and p.suffix in {".md", ".ts"}
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
        if stale.search(line)
    ]
    assert not hits, hits


def test_folds_concatenated_literals_and_reports_the_literal_line(tmp_path):
    src = tmp_path / "Example.flow.ts"
    src.write_text(
        "export default flow('x')\n"
        "  .step('write', inlineAgent({\n"
        "    model: 'gpt-5.4',\n"
        "    systemPrompt:\n"
        "      'You write captions. Given a place, return ONLY a JSON '\n"
        "      + 'object with keys \"caption\".',\n"
        "    userPrompt: 'Place: {{input.place}}',\n"
        "    returns: { caption: 'string' },\n"
        "  }))\n"
        "  .step('say', script({ code: 'run with --output json' }))\n",
        encoding="utf-8",
    )
    hits = directive_hits(tmp_path)
    assert len(hits) == 1, hits
    assert ":5: systemPrompt 'return ONLY a JSON'" in hits[0]
