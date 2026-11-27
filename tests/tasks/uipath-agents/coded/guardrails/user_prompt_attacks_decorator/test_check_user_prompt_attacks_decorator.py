"""Unit tests for the coded user-prompt-attacks decorator checker: stage, action and validator resolve as Python does."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from string import Template

import pytest

CHECKER = Path(__file__).with_name("check_user_prompt_attacks_decorator.py")

GRAPH = Template(
    textwrap.dedent(
        """
        from langchain.agents import create_agent
        from langchain_core.messages import HumanMessage
        from pydantic import BaseModel
        from uipath.platform.attachments import Attachment
        from uipath_langchain.chat import UiPathChat
        from uipath_langchain.guardrails import (
            BlockAction,
            DetectionScope,
            GuardrailExecutionStage,
            LogAction,
            UserPromptAttacksValidator,
            guardrail,
            render_attachments_block,
        )
        $module

        class Input(BaseModel):
            question: str
            document: Attachment | None = None


        @guardrail(validator=$validator, action=$action, stage=$stage, detection_scope=DetectionScope.BOTH)
        def create_llm():
            return UiPathChat(model="gpt-4.1-mini-2025-04-14")


        agent = create_agent(model=create_llm(), tools=[])


        async def support_node(state: Input):
            content = state.question
            if state.document is not None:
                content += render_attachments_block([state.document.model_dump(mode="json", exclude_none=True)])
            return [HumanMessage(content=content)]
        """
    )
)


def graph(
    *,
    module: str = "",
    validator: str = "UserPromptAttacksValidator()",
    action: str = "BlockAction()",
    stage: str = "GuardrailExecutionStage.PRE",
) -> str:
    return GRAPH.substitute(module=module, validator=validator, action=action, stage=stage)


def run_checker(tmp_path: Path, source: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "graph.py").write_text(source)
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False, timeout=30
    )


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(graph(), id="enum-member"),
        pytest.param(
            graph(
                module="from uipath_langchain.guardrails import GuardrailExecutionStage as Stage",
                stage="Stage.PRE",
            ),
            id="import-alias",
        ),
        pytest.param(graph(stage='"pre"'), id="value-string"),
        pytest.param(
            graph(
                module="VALIDATOR = UserPromptAttacksValidator()\nBLOCK = BlockAction()\nSTAGE = GuardrailExecutionStage.PRE",
                validator="VALIDATOR",
                action="BLOCK",
                stage="STAGE",
            ),
            id="top-level-names",
        ),
    ],
)
def test_accepts_every_spelling_of_a_pre_stage_block(tmp_path: Path, source: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode == 0, result.stderr
    assert "OK: User prompt attacks decorator guardrail correctly added to graph.py" in result.stdout


@pytest.mark.parametrize(
    ("source", "message"),
    [
        pytest.param(graph(stage="GuardrailExecutionStage.PRE_AND_POST"), "stage must be GuardrailExecutionStage.PRE", id="pre-and-post"),
        pytest.param(graph(stage='"PRE"'), "stage must be GuardrailExecutionStage.PRE", id="member-name-as-string"),
        pytest.param(graph(action="LogAction()"), "action must be BlockAction(...)", id="log-action"),
        pytest.param(
            graph(module="VALIDATOR = UserPromptAttacksValidator()", validator="LogAction()"),
            "no @guardrail(validator=UserPromptAttacksValidator(...))",
            id="other-validator",
        ),
    ],
)
def test_rejects_a_decorator_that_does_not_block_at_pre(tmp_path: Path, source: str, message: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode != 0, result.stdout
    assert message in result.stderr
