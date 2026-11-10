"""Unit tests for the simple-echo grader's typed-I/O check.

The regression these lock in (UiPath/skills#4585): the grader required the
literal strings `class Input` and `class Output`, but SKILL.md rule 4 only
asks for typed I/O and never names the classes. An agent that wrote
`@dataclass class EchoIn` / `class EchoOut` with
`def main(input: EchoIn) -> EchoOut` followed the skill and still failed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _shared.check_simple_echo import typed_io_problems  # noqa: E402

PYDANTIC_INPUT_OUTPUT = """
from pydantic import BaseModel

class Input(BaseModel):
    message: str
    repeat: int = 1

class Output(BaseModel):
    echoed: str
    length: int

def main(input: Input) -> Output:
    return Output(echoed=input.message, length=1)
"""

# The exact main.py from the failing smoke run (42699662892).
DATACLASS_ECHO_NAMES = """
from dataclasses import dataclass


@dataclass
class EchoIn:
    message: str
    repeat: int = 1


@dataclass
class EchoOut:
    echoed: str
    length: int


def main(input: EchoIn) -> EchoOut:
    echoed = input.message * input.repeat
    return EchoOut(echoed=echoed, length=len(echoed))
"""


@pytest.mark.parametrize(
    "source, entry",
    [
        pytest.param(PYDANTIC_INPUT_OUTPUT, "main", id="pydantic-Input-Output"),
        pytest.param(DATACLASS_ECHO_NAMES, "main", id="dataclass-EchoIn-EchoOut"),
        pytest.param(
            "import pydantic\n"
            "@pydantic.dataclasses.dataclass\nclass A:\n    message: str\n"
            "class B:\n    echoed: str\n    length: int\n"
            "async def run(a: 'A') -> B:\n    ...\n",
            "run",
            id="pydantic-dataclass-thin-class-async-string-annotation",
        ),
        pytest.param(
            "from models import EchoIn, EchoOut\n"
            "def main(input: EchoIn) -> EchoOut:\n    ...\n",
            "main",
            id="imported-models",
        ),
        pytest.param(
            "from pydantic import BaseModel\n"
            "class Shared(BaseModel):\n    trace_id: str = ''\n"
            "class Input(Shared):\n    pass\n"
            "class Output(Shared):\n    pass\n"
            "def main(input: Input) -> Output:\n    ...\n",
            "main",
            id="inherited-local-base",
        ),
        pytest.param(
            "from base_models import Shared\n"
            "class Input(Shared):\n    pass\n"
            "class Output(Shared):\n    pass\n"
            "def main(input: Input) -> Output:\n    ...\n",
            "main",
            id="inherited-imported-base",
        ),
        pytest.param(
            "from pydantic import BaseModel\n"
            "class Input(BaseModel):\n    message: str\n"
            "class Output(BaseModel):\n    echoed: str\n"
            "def main(*, input: Input) -> Output:\n    ...\n",
            "main",
            id="keyword-only-input",
        ),
    ],
)
def test_typed_io_passes_whatever_the_class_names(source: str, entry: str) -> None:
    assert typed_io_problems(source, entry) == []


@pytest.mark.parametrize(
    "source, expected",
    [
        pytest.param(
            "def main(input):\n    return {'echoed': input['message']}\n",
            "input has no type annotation",
            id="missing-annotations",
        ),
        pytest.param(
            "from pydantic import BaseModel\n"
            "class Input(BaseModel):\n    message: str\n"
            "def main(input: Input):\n    ...\n",
            "return has no type annotation",
            id="missing-return-annotation",
        ),
        pytest.param(
            "def main(input: dict) -> dict:\n    ...\n",
            "annotated `dict`, which is not typed I/O",
            id="dict-is-not-typed-io",
        ),
        pytest.param(
            "class Input:\n    pass\n"
            "class Output:\n    pass\n"
            "def main(input: Input) -> Output:\n    ...\n",
            "is not a BaseModel, a dataclass, or a class with annotated fields",
            id="untyped-class",
        ),
        pytest.param(
            "def main(input: EchoIn) -> EchoOut:\n    ...\n",
            "neither defined nor imported",
            id="undefined-type",
        ),
        pytest.param(
            "def other(input: int) -> int:\n    ...\n",
            "does not define `def main`",
            id="entry-function-missing",
        ),
        pytest.param(
            "from typing import Optional\n"
            "from pydantic import BaseModel\n"
            "class Input(BaseModel):\n    message: str\n"
            "class Output(BaseModel):\n    echoed: str\n"
            "def main(input: Optional[Input]) -> Output:\n    ...\n",
            "unsupported annotation `Optional[Input]`",
            id="optional-is-unsupported-not-missing",
        ),
        pytest.param(
            "from typing import TypedDict\n"
            "class Input(TypedDict):\n    message: str\n"
            "class Output(TypedDict):\n    echoed: str\n"
            "def main(input: Input) -> Output:\n    ...\n",
            "is not a BaseModel, a dataclass, or a class with annotated fields",
            id="typeddict-subclass-fails",
        ),
    ],
)
def test_untyped_io_fails(source: str, expected: str) -> None:
    problems = typed_io_problems(source, "main")
    assert problems, "expected a typed-I/O failure"
    assert any(expected in p for p in problems), problems
