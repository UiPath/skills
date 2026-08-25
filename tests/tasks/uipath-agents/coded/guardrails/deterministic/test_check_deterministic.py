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


def test_accepts_positional_inline_lambda_rule(tmp_path: Path) -> None:
    """Codex gpt-5.6-terra's actual output, rep 0 of a 2026-08-06 x5 validation run:
    `rule` passed positionally to CustomValidator instead of as `rule=...`. It's a
    regular positional-or-keyword constructor parameter, so both bind identically."""
    result = run_checker(
        tmp_path,
        """
        @guardrail(
            validator=CustomValidator(
                lambda args: "secret" in str(args.get("customer_id", "")).lower()
            ),
            action=BlockAction(detail="blocked"),
        )
        @tool
        def lookup_account_info(customer_id: str) -> str:
            return customer_id
        """,
    )

    assert result.returncode == 0, result.stderr


def test_accepts_positional_named_rule(tmp_path: Path) -> None:
    """Same gap, named-function form (rep 1 of the same validation run)."""
    result = run_checker(
        tmp_path,
        """
        def contains_secret_customer_id(data: dict) -> bool:
            return "secret" in data.get("customer_id", "").lower()

        @guardrail(
            validator=CustomValidator(contains_secret_customer_id),
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


def test_accepts_regex_based_rule(tmp_path: Path) -> None:
    """Codex gpt-5.6-terra's actual output (2026-08-04 rerun): a named function using
    `re.search` with a word-boundary pattern instead of a plain `in` membership check."""
    result = run_checker(
        tmp_path,
        """
        import re

        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def contains_secret_customer_id(tool_input: dict) -> bool:
            \"\"\"Return whether a tool input has the standalone word 'secret' in its ID.\"\"\"
            return bool(
                re.search(
                    r"\bsecret\b",
                    str(tool_input.get("customer_id", "")),
                    flags=re.IGNORECASE,
                )
            )

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


def test_rejects_regex_rule_checking_wrong_field(tmp_path: Path) -> None:
    result = run_checker(
        tmp_path,
        """
        import re

        def lookup_account_info(customer_id: str) -> str:
            return customer_id

        def checks_account_name(data: dict) -> bool:
            return bool(re.search(r"secret", data.get("account_name", "")))

        middleware = [
            *UiPathDeterministicGuardrailMiddleware(
                tools=[lookup_account_info],
                rules=[checks_account_name],
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
