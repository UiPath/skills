"""Guard: the case lane's documented `uip is connections list` carries `--all-folders`.

The default Integration Service scope returns an EMPTY list on tenants that hold
hundreds of connections — measured 0 vs 251 on one tenant — so an agent following a
reference that omits the flag buckets every connector as `Empty` instead of
`Ambiguous`. Those two buckets offer the user different options at the resolution
gate ("create during build" vs "pick a match"), so the omission silently changes
what the user is asked.

Scope note: the same un-scoped invocation is documented in several other skills
(`uipath-rpa`, `uipath-api-workflow`, `uipath-platform/agent-workflow.md`, and parts
of `uipath-troubleshoot`). Those are owned by other teams and are NOT enforced here;
they are a known follow-up. This guard covers the case design lane and the case build
skill, where the mis-bucketing changes a user-facing gate.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[4]
SKILLS = REPO / "skills"

# Surfaces this guard enforces.
ENFORCED = (
    "uipath-planner/references/case",
    "uipath-maestro-case",
)

# An invocation is correctly scoped if it names all folders OR targets one
# connection / folder explicitly.
EXPLICIT_SCOPE = ("--all-folders", "--connection-id", "--folder-key", "--folder ")

INVOCATION = re.compile(r"uip\s+is\s+connections\s+list([^\n`]*)")


def enforced_markdown() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for rel in ENFORCED:
        out.extend(sorted((SKILLS / rel).rglob("*.md")))
    return out


def test_repo_layout_is_what_this_test_assumes():
    """Fail loudly if the path math is wrong rather than passing vacuously."""
    assert SKILLS.is_dir(), f"expected skills/ under {REPO}"
    assert enforced_markdown(), f"no markdown under {ENFORCED} — the glob is wrong"


def test_case_lane_connection_list_is_scoped():
    offenders: list[str] = []
    for md in enforced_markdown():
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in INVOCATION.finditer(text):
            tail = m.group(1)
            if any(flag in tail for flag in EXPLICIT_SCOPE):
                continue
            # Prose that names the flag as the fix nearby is documentation, not a recipe.
            start = text.rfind("\n\n", 0, m.start())
            para = text[start if start != -1 else 0 : m.end() + 400]
            if "--all-folders" in para:
                continue
            line = text[: m.start()].count("\n") + 1
            offenders.append(f"{md.relative_to(REPO)}:{line}: {m.group(0).strip()}")

    assert not offenders, (
        "`uip is connections list` documented without an explicit scope:\n  "
        + "\n  ".join(offenders)
        + "\n\nThe default scope returns [] on tenants that have connections. Pass "
        "--all-folders (or target --connection-id / --folder-key). See "
        "skills/uipath-planner/references/case/grounding.md."
    )


def test_all_folders_response_shape_is_documented():
    """The two scopes are not schema-compatible: `--all-folders` returns PascalCase.
    A reference that tells the agent to read connections must say so."""
    grounding = SKILLS / "uipath-planner/references/case/grounding.md"
    assert grounding.is_file(), f"missing {grounding}"
    text = grounding.read_text(encoding="utf-8")
    missing = [k for k in ("Id", "Name", "ConnectorKey", "State") if f"`{k}`" not in text]
    assert not missing, (
        f"grounding.md documents the connection lookup but not these response keys: {missing}. "
        "An agent parsing camelCase against a PascalCase payload reads every field as absent."
    )
