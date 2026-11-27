"""Unit tests for the coded file-tool LLM-as-judge checker: it judges what the guardrail does, not how it is spelled."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path
from string import Template

import pytest

CHECKER = Path(__file__).with_name("check_file_tool_judge.py")

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
            BlockAction,
            DetectionScope,
            GuardrailExecutionStage,
            LLMAsJudgeValidator,
            UiPathLLMAsJudgeMiddleware,
            guardrail,
            render_attachments_block,
        )
        $module

        class Input(BaseModel):
            question: str
            contract: Attachment | None = None


        $decorator
        @tool
        def review_contract(contract: dict) -> str:
            """Review a contract."""
            return "reviewed"


        def build_agent(llm):
        $local
            return create_agent(model=llm, tools=[review_contract], middleware=[$middleware])


        async def review_node(state: Input):
            content = state.question
            if state.contract is not None:
                content += render_attachments_block([state.contract.model_dump(mode="json", exclude_none=True)])
            return [HumanMessage(content=content)]
        '''
    )
)
RULE = '"Fail when the non-compete lasts more than 12 months."'
MODEL = '"gpt-4.1-mini-2025-04-14"'
DETAIL = '"Non-compete exceeds 12 months."'
JUDGE = (
    "UiPathLLMAsJudgeMiddleware(scopes=[GuardrailScope.TOOL], tools=[review_contract], "
    f"action=BlockAction(detail={DETAIL}), guardrail_text={RULE}, model={MODEL}, "
    "stage=GuardrailExecutionStage.PRE, detection_scope=DetectionScope.FILES)"
)
DECORATOR = (
    f"@guardrail(validator=LLMAsJudgeValidator({RULE}, {MODEL}), action=BlockAction(None, {DETAIL}), "
    "stage=GuardrailExecutionStage.PRE, detection_scope=DetectionScope.FILES)"
)


def graph(*, judge: str = JUDGE, decorator: str = "", module: str = "", local: str = "") -> str:
    middleware = "" if decorator else f"*{judge}"
    return GRAPH.substitute(module=module, decorator=decorator, local=local, middleware=middleware)


def run_checker(tmp_path: Path, source: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "graph.py").write_text(source)
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False, timeout=30
    )


@pytest.mark.parametrize(
    ("source", "flavor"),
    [
        pytest.param(graph(), "middleware", id="middleware-keywords"),
        pytest.param(
            graph(
                judge=f"UiPathLLMAsJudgeMiddleware([GuardrailScope.TOOL], BlockAction(detail={DETAIL}), {RULE}, {MODEL}, "
                "tools=[review_contract], stage=GuardrailExecutionStage.PRE, detection_scope=DetectionScope.FILES)"
            ),
            "middleware",
            id="middleware-positional",
        ),
        pytest.param(
            graph(
                local=textwrap.indent(
                    f"rule = {RULE}\njudge_model = {MODEL}\njudge_scopes = [GuardrailScope.TOOL]\n"
                    f"judged_tools = [review_contract]\nblock = BlockAction(detail={DETAIL})\n"
                    "stage = GuardrailExecutionStage.PRE_AND_POST",
                    "    ",
                ),
                judge="UiPathLLMAsJudgeMiddleware(scopes=judge_scopes, tools=judged_tools, action=block, "
                'guardrail_text=rule, model=judge_model, stage=stage, detection_scope="Files")',
            ),
            "middleware",
            id="middleware-function-local-names",
        ),
        pytest.param(graph(decorator=DECORATOR), "decorator", id="decorator-positional"),
        pytest.param(
            graph(
                module=f"RULE = {RULE}\nMODEL = {MODEL}\nJUDGE = LLMAsJudgeValidator(guardrail_text=RULE, model=MODEL)",
                decorator=f"@guardrail(validator=JUDGE, action=BlockAction(detail={DETAIL}), "
                'stage="pre", detection_scope=DetectionScope.FILES)',
            ),
            "decorator",
            id="decorator-top-level-names-and-stage-value",
        ),
    ],
)
def test_accepts_every_spelling_of_the_file_judge(tmp_path: Path, source: str, flavor: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode == 0, result.stderr
    assert f"OK: LLM-as-judge guardrail on review_contract ({flavor})" in result.stdout


@pytest.mark.parametrize(
    ("source", "message"),
    [
        pytest.param(
            graph(judge=JUDGE.replace(f"BlockAction(detail={DETAIL})", f"BlockAction({DETAIL})")),
            "BlockAction(detail=...) must carry",
            id="message-in-title-not-detail",
        ),
        pytest.param(
            graph(judge=JUDGE.replace("GuardrailExecutionStage.PRE", "GuardrailExecutionStage.POST")),
            "the guardrail must run before the tool reads the file",
            id="post-only",
        ),
        pytest.param(
            graph(judge=JUDGE.replace("GuardrailScope.TOOL", "GuardrailScope.AGENT")),
            "no LLM-as-judge guardrail targets review_contract",
            id="agent-scope-only",
        ),
        pytest.param(
            graph(judge=JUDGE.replace(RULE, '"Fail when the contract is unfair."')),
            "guardrail_text must state the non-compete rule",
            id="rule-without-limit",
        ),
        pytest.param(
            graph(module="import config", decorator=DECORATOR.replace(f"LLMAsJudgeValidator({RULE}, {MODEL})", "config.JUDGE")),
            "no LLM-as-judge guardrail targets review_contract",
            id="validator-not-a-call",
        ),
    ],
)
def test_rejects_a_judge_that_does_not_do_what_was_asked(tmp_path: Path, source: str, message: str) -> None:
    result = run_checker(tmp_path, source)

    assert result.returncode != 0, result.stdout
    assert message in result.stderr
    assert "Traceback" not in result.stderr
