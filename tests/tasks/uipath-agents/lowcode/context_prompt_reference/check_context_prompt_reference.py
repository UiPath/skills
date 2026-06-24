#!/usr/bin/env python3
"""Context prompt-reference check.

Validates that the agent referenced an attachments context in the user
prompt via the Studio expression syntax `@{contexts.Knowledge}` and kept
`content` and `contentTokens` in sync:

  1. The Knowledge resource is a context (`$resourceType: "context"`) with
     `contextType: "attachments"` (lowercase — Anti-pattern 12).
  2. The user message content contains `@{contexts.Knowledge}`.
  3. contentTokens contains a matching `{type: "expression",
     rawString: "contexts.Knowledge"}` token (Critical Rule 6 — the `@{ }`
     expression family, not a `variable`).
  4. content and contentTokens reconstruct to each other (the sync check
     `uip agent validate` enforces), across simpleText/variable/expression.
  5. `Knowledge` is NOT declared as an inputSchema property — a context is a
     runtime-resolved resource, not an input field.
  6. inputSchema/outputSchema stay in sync with entry-points.json
     (Critical Rule 4).
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocSol" / "DocAssistant"
AGENT = ROOT / "agent.json"
ENTRY = ROOT / "entry-points.json"
RESOURCE = ROOT / "resources" / "Knowledge" / "resource.json"

CONTEXT_NAME = "Knowledge"
EXPR_RAW = f"contexts.{CONTEXT_NAME}"          # token rawString, prefix included
EXPR_LITERAL = "@{" + EXPR_RAW + "}"           # how it appears in content

EXPR_RE = re.compile(r"@\{([^}]*)\}")


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def reconstruct(tokens: list) -> str:
    """Rebuild the content string from contentTokens, mirroring how
    `uip agent validate` tokenizes: simpleText verbatim, variable -> {{ }},
    expression -> @{ }."""
    out = []
    for i, t in enumerate(tokens):
        if not isinstance(t, dict):
            sys.exit(f"FAIL: contentTokens[{i}] is not an object: {t!r}")
        ttype = t.get("type")
        raw = t.get("rawString", "")
        if ttype == "simpleText":
            out.append(raw)
        elif ttype == "variable":
            out.append("{{" + raw + "}}")
        elif ttype == "expression":
            out.append("@{" + raw + "}")
        else:
            sys.exit(
                f"FAIL: contentTokens[{i}].type is {ttype!r}; expected one of "
                "'simpleText', 'variable', 'expression'"
            )
    return "".join(out)


def assert_context_resource() -> None:
    res = load(RESOURCE)
    if res.get("$resourceType") != "context":
        sys.exit(
            f"FAIL: {RESOURCE} $resourceType is {res.get('$resourceType')!r}, "
            "expected 'context'"
        )
    ctype = res.get("contextType")
    if ctype != "attachments":
        sys.exit(
            f"FAIL: Knowledge contextType is {ctype!r}, expected 'attachments' "
            "(lowercase — Anti-pattern 12)"
        )
    print("OK: Knowledge is an attachments context resource")


def assert_user_prompt_references_context(agent: dict) -> None:
    messages = agent.get("messages")
    if not isinstance(messages, list):
        sys.exit(f"FAIL: agent.json.messages is not a list: {messages!r}")
    user_messages = [
        m for m in messages if isinstance(m, dict) and m.get("role") == "user"
    ]
    if not user_messages:
        sys.exit("FAIL: agent.json.messages has no entry with role == 'user'")
    user = user_messages[0]
    content = user.get("content", "")
    tokens = user.get("contentTokens")
    if not isinstance(tokens, list):
        sys.exit(f"FAIL: user message contentTokens is not a list: {tokens!r}")

    # 2. content references the context with @{ } expression syntax
    inners = [m.group(1).strip() for m in EXPR_RE.finditer(content)]
    if EXPR_RAW not in inners:
        sys.exit(
            f"FAIL: user message content does not reference {EXPR_LITERAL} "
            f"(found @{{ }} expressions: {inners!r}); content={content!r}"
        )

    # 3. a matching expression token exists (not a variable token)
    expr_tokens = [
        t for t in tokens
        if isinstance(t, dict) and t.get("type") == "expression"
        and t.get("rawString", "").strip() == EXPR_RAW
    ]
    if not expr_tokens:
        sys.exit(
            "FAIL: contentTokens has no expression token with rawString "
            f"{EXPR_RAW!r} (Critical Rule 6 — context refs are `expression` "
            f"tokens, not `variable`)\n  got tokens: {json.dumps(tokens, indent=2)}"
        )
    # The context must NOT be modeled as an input variable token.
    if any(
        isinstance(t, dict) and t.get("type") == "variable"
        and CONTEXT_NAME in t.get("rawString", "")
        for t in tokens
    ):
        sys.exit(
            f"FAIL: {CONTEXT_NAME} appears as a `variable` token — a context is "
            "an `expression` (@{ }) reference, not an input variable ({{ }})"
        )

    # 4. content <-> contentTokens sync (what validate enforces)
    rebuilt = reconstruct(tokens)
    if rebuilt != content:
        sys.exit(
            "FAIL: contentTokens do not reconstruct content (sync broken — "
            f"Critical Rule 6)\n  content : {content!r}\n  rebuilt : {rebuilt!r}"
        )
    print("OK: user prompt references @{contexts.Knowledge} with a synced expression token")


def assert_context_not_an_input(agent: dict) -> None:
    in_schema = agent.get("inputSchema")
    props = in_schema.get("properties") if isinstance(in_schema, dict) else None
    if isinstance(props, dict) and CONTEXT_NAME in props:
        sys.exit(
            f"FAIL: inputSchema.properties declares {CONTEXT_NAME!r} — a context "
            "is a runtime-resolved resource, not an inputSchema field"
        )
    print("OK: Knowledge is not declared as an inputSchema field")


def assert_schema_sync(agent: dict, entry: dict) -> None:
    entry_points = entry.get("entryPoints")
    if not isinstance(entry_points, list) or not entry_points:
        sys.exit("FAIL: entry-points.json has no entryPoints[0]")
    ep = entry_points[0]
    if agent.get("inputSchema") != ep.get("input"):
        sys.exit(
            "FAIL: agent.json.inputSchema != entry-points.json entryPoints[0].input "
            "(Critical Rule 4)"
        )
    if agent.get("outputSchema") != ep.get("output"):
        sys.exit(
            "FAIL: agent.json.outputSchema != entry-points.json entryPoints[0].output "
            "(Critical Rule 4)"
        )
    print("OK: inputSchema and outputSchema are in sync with entry-points.json")


def main() -> None:
    agent = load(AGENT)
    entry = load(ENTRY)
    assert_context_resource()
    assert_user_prompt_references_context(agent)
    assert_context_not_an_input(agent)
    assert_schema_sync(agent, entry)


if __name__ == "__main__":
    main()
