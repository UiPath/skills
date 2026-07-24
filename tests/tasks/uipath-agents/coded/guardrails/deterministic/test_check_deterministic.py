"""Unit tests for the deterministic coded-agent guardrail checker."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

CHECKER = Path(__file__).with_name("check_deterministic.py")


def run_checker(tmp_path: Path, source: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "graph.py").write_text(textwrap.dedent(source))
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_accepts_inline_lambda_rule(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[lookup_account_info],
                rules=[
                    lambda data: "secret"
                    in data.get("customer_id", "").lower()
                ],
                action=BlockAction(detail="blocked"),
            ),
        ]
        """,
    )

    assert result.returncode == 0, result.stderr


def test_accepts_named_rule_with_docstring(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def contains_secret_customer_id(data: dict) -> bool:
            \"\"\"Return whether a tool call includes a forbidden customer ID.\"\"\"
            return "secret" in data.get("customer_id", "").lower()

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[lookup_account_info],
                rules=[contains_secret_customer_id],
                action=BlockAction(detail="blocked"),
            ),
        ]
        """,
    )

    assert result.returncode == 0, result.stderr


def test_accepts_decorator_rule_with_docstring(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        def contains_secret_customer_id(data: dict) -> bool:
            \"\"\"Return whether a tool call includes a forbidden customer ID.\"\"\"
            return "secret" in data.get("customer_id", "").lower()

        @guardrail(
            validator=CustomValidator(rule=contains_secret_customer_id),
            action=BlockAction(detail="blocked"),
        )
        @tool
        def lookup_account_info(customer_id: str) -> str:
            return customer_id
        """,
    )

    assert result.returncode == 0, result.stderr


def test_rejects_secret_function_not_wired_as_rule(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def mentions_secret(data: dict) -> bool:
            return "secret" in data.get("customer_id", "").lower()

        def allow_everything(data: dict) -> bool:
            return True

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[lookup_account_info],
                rules=[allow_everything],
                action=BlockAction(detail="blocked"),
            ),
        ]
        """,
    )

    assert result.returncode != 0
    assert "callable rule checking customer_id for 'secret'" in result.stderr


def test_rejects_variable_named_secret_without_secret_literal(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        secret = "public"

        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def misleading_rule(data: dict) -> bool:
            return secret in data.get("customer_id", "").lower()

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[lookup_account_info],
                rules=[misleading_rule],
                action=BlockAction(detail="blocked"),
            ),
        ]
        """,
    )

    assert result.returncode != 0
    assert "callable rule checking customer_id for 'secret'" in result.stderr


def test_rejects_middleware_targeting_another_tool(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def another_tool(customer_id: str) -> str:
            return customer_id

        def contains_secret_customer_id(data: dict) -> bool:
            return "secret" in data.get("customer_id", "").lower()

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[another_tool],
                rules=[contains_secret_customer_id],
                action=BlockAction(detail="blocked"),
            ),
        ]
        """,
    )

    assert result.returncode != 0
    assert "lookup_account_info" in result.stderr
