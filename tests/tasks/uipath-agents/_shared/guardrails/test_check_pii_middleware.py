"""Unit tests for the coded PII middleware checker: it judges what the middleware sends, not how it is spelled."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from string import Template

import pytest

CHECKER = Path(__file__).with_name("check_pii_middleware.py")

GRAPH = Template(
    textwrap.dedent(
        '''
        from langchain.agents import create_agent
        from langchain_core.messages import HumanMessage
        from langchain_core.tools import tool
        from pydantic import BaseModel
        from uipath.core.guardrails import GuardrailScope
        from uipath.platform.attachments import Attachment
        from uipath_langchain.guardrails import (
            DetectionScope,
            GuardrailExecutionStage,
            LogAction,
            PIIDetectionEntity,
            PIIDetectionEntityType,
            UiPathPIIDetectionMiddleware,
            render_attachments_block,
        )
        $module

        class Input(BaseModel):
            question: str
            statement: Attachment | None = None


        @tool
        def lookup_account_info(customer_id: str) -> str:
            """Look up an account."""
            return customer_id


        def build_agent(llm$params):
        $local
            return create_agent(model=llm, tools=[lookup_account_info], middleware=[*$agent, *$tool])


        async def support_node(state: Input):
            content = state.question
            if state.statement is not None:
                content += render_attachments_block([state.statement.model_dump(mode="json", exclude_none=True)])
            return [HumanMessage(content=content)]
        '''
    )
)
EMAIL_AND_PHONE = (
    "[PIIDetectionEntity(PIIDetectionEntityType.EMAIL, 0.5), PIIDetectionEntity(PIIDetectionEntityType.PHONE_NUMBER, 0.5)]"
)


def graph(
    *,
    entities: str = EMAIL_AND_PHONE,
    module: str = "",
    params: str = "",
    local: str = "",
    agent: str = "",
    tool: str = "",
) -> str:
    agent = agent or (
        "UiPathPIIDetectionMiddleware(scopes=[GuardrailScope.AGENT], action=LogAction(), "
        f"entities={entities}, detection_scope=DetectionScope.BOTH)"
    )
    tool = tool or (
        "UiPathPIIDetectionMiddleware(scopes=[GuardrailScope.TOOL], tools=[lookup_account_info], "
        f"action=LogAction(), entities={entities})"
    )
    return GRAPH.substitute(module=module, params=params, local=local, agent=agent, tool=tool)


def run_checker(tmp_path: Path, source: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "graph.py").write_text(source)
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False, timeout=30
    )


EMAIL_TYPE = "PIIDetectionEntityType.EMAIL"
PHONE_TYPE = "PIIDetectionEntityType.PHONE_NUMBER"
EMAIL = f"PIIDetectionEntity({EMAIL_TYPE})"
PHONE = f"PIIDetectionEntity({PHONE_TYPE})"


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(graph(), id="inline-list"),
        pytest.param(graph(module=f"ENTITIES = {EMAIL_AND_PHONE}", entities="ENTITIES"), id="top-level-list"),
        pytest.param(graph(local=f"    pii_entities = {EMAIL_AND_PHONE}", entities="pii_entities"), id="function-local-list"),
        pytest.param(graph(entities='[PIIDetectionEntity("Email"), PIIDetectionEntity("PhoneNumber")]'), id="value-strings"),
        pytest.param(
            graph(
                entities='[PIIDetectionEntity(PIIDetectionEntityType("Email")), '
                'PIIDetectionEntity(name=PIIDetectionEntityType("PhoneNumber"))]'
            ),
            id="enum-by-value",
        ),
        pytest.param(
            graph(
                module="from uipath_langchain.guardrails import PIIDetectionEntityType as EntityType",
                entities="[PIIDetectionEntity(EntityType.EMAIL), PIIDetectionEntity(EntityType.PHONE_NUMBER)]",
            ),
            id="import-alias",
        ),
        pytest.param(
            graph(
                local="    email = [PIIDetectionEntity(PIIDetectionEntityType.EMAIL)]",
                entities="[*email, PIIDetectionEntity(PIIDetectionEntityType.PHONE_NUMBER)]",
            ),
            id="spread-of-local-list",
        ),
        pytest.param(
            graph(
                local="    agent_scopes = [GuardrailScope.AGENT]",
                agent="UiPathPIIDetectionMiddleware(scopes=agent_scopes, action=LogAction(), "
                f"entities={EMAIL_AND_PHONE}, detection_scope=DetectionScope.BOTH)",
            ),
            id="function-local-scopes",
        ),
        pytest.param(
            graph(
                agent=f"UiPathPIIDetectionMiddleware([GuardrailScope.AGENT], LogAction(), {EMAIL_AND_PHONE}, "
                'detection_scope="Both")',
                tool=f"UiPathPIIDetectionMiddleware([GuardrailScope.TOOL], LogAction(), {EMAIL_AND_PHONE}, "
                'tools=["lookup_account_info"])',
            ),
            id="positional-arguments-and-tool-name",
        ),
        pytest.param(graph(local=f"    pii = [{EMAIL}]\n    pii = pii + [{PHONE}]", entities="pii"), id="list-reassigned-from-itself"),
        pytest.param(graph(local=f"    pii = [{EMAIL}]\n    pii += [{PHONE}]", entities="pii"), id="list-augmented"),
        pytest.param(graph(local=f"    pii = [{EMAIL}]\n    pii.append({PHONE})", entities="pii"), id="list-appended"),
        pytest.param(graph(entities=f"[PIIDetectionEntity(x, threshold=0.5) for x in ({EMAIL_TYPE}, {PHONE_TYPE})]"), id="list-comprehension"),
        pytest.param(
            graph(module=f"WANTED = [{EMAIL_TYPE}, {PHONE_TYPE}]", entities="[PIIDetectionEntity(x) for x in WANTED]"),
            id="comprehension-over-a-named-list",
        ),
        pytest.param(graph(entities=f"list(PIIDetectionEntity(x) for x in ({EMAIL_TYPE}, {PHONE_TYPE}))"), id="generator"),
        pytest.param(
            graph(module="def entity(kind):\n    return PIIDetectionEntity(kind, 0.5)", entities=f"[entity({EMAIL_TYPE}), entity({PHONE_TYPE})]"),
            id="helper-call",
        ),
    ],
)
def test_accepts_every_spelling_that_sends_email_and_phone(tmp_path: Path, source: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode == 0, result.stderr
    assert "OK: PII middleware guardrail correctly added to graph.py" in result.stdout


@pytest.mark.parametrize(
    ("source", "message"),
    [
        pytest.param(
            graph(
                module=f"ENTITIES = {EMAIL_AND_PHONE}",
                local="    ENTITIES = [PIIDetectionEntity(PIIDetectionEntityType.PERSON)]",
                entities="ENTITIES",
            ),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities (found: ['Person'])",
            id="local-list-shadows-top-level-list",
        ),
        pytest.param(
            graph(entities="[PIIDetectionEntity(PIIDetectionEntityType.PHONE_NUMBER)]"),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities",
            id="email-missing",
        ),
        pytest.param(
            graph(entities=f"[PIIDetectionEntity(x) for x in (PIIDetectionEntityType.PERSON, {PHONE_TYPE})]"),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities (found: ['Person', 'PhoneNumber'])",
            id="comprehension-without-email",
        ),
        pytest.param(
            graph(entities=f"[PIIDetectionEntity(x) for x in (PIIDetectionEntityType.PERSON, {PHONE_TYPE}) if x != {EMAIL_TYPE}]"),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities (found: ['Person', 'PhoneNumber'])",
            id="email-only-in-a-comprehension-filter",
        ),
        pytest.param(
            graph(entities=f"[PIIDetectionEntity(x) for x in (PIIDetectionEntityType.PERSON, {PHONE_TYPE})] if {EMAIL_TYPE} else []"),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities (found: ['Person', 'PhoneNumber'])",
            id="email-only-in-a-condition",
        ),
        pytest.param(
            graph(entities='[PIIDetectionEntity("email"), PIIDetectionEntity("PhoneNumber")]'),
            "PIIDetectionEntityType.EMAIL is not in the middleware entities",
            id="wrong-case-value",
        ),
        pytest.param(
            graph(
                agent="UiPathPIIDetectionMiddleware(scopes=[GuardrailScope.AGENT], action=LogAction(), "
                f"entities={EMAIL_AND_PHONE}, stage=GuardrailExecutionStage.POST, detection_scope=DetectionScope.BOTH)"
            ),
            "runs at POST only",
            id="agent-scope-post-only",
        ),
        pytest.param(
            graph(
                tool="UiPathPIIDetectionMiddleware(scopes=[GuardrailScope.TOOL], tools=[], "
                f"action=LogAction(), entities={EMAIL_AND_PHONE})"
            ),
            "GuardrailScope.TOOL in scopes and tools=[lookup_account_info]",
            id="tool-not-listed",
        ),
        pytest.param(
            graph(module=f"ENTITIES = [{EMAIL}, {PHONE}]", params=", ENTITIES", entities="ENTITIES")
            + "\n\nAGENT = build_agent(None, [PIIDetectionEntity(PIIDetectionEntityType.PERSON)])\n",
            "PIIDetectionEntityType.EMAIL is not in the middleware entities (found: [])",
            id="parameter-shadows-top-level-list",
        ),
        pytest.param(
            graph(
                module="from uipath_langchain.guardrails import GuardrailExecutionStage as Stage\n\n\n"
                "def unrelated():\n    from enum import Enum as Stage\n    return Stage\n",
                agent="UiPathPIIDetectionMiddleware(scopes=[GuardrailScope.AGENT], action=LogAction(), "
                f"entities={EMAIL_AND_PHONE}, stage=Stage.POST, detection_scope=DetectionScope.BOTH)",
            ),
            "runs at POST only",
            id="alias-reused-in-another-scope",
        ),
    ],
)
def test_rejects_what_does_not_send_the_requested_guardrail(tmp_path: Path, source: str, message: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode != 0, result.stdout
    assert message in result.stderr
