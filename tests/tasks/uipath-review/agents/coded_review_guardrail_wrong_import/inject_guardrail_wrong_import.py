#!/usr/bin/env python3
"""Scaffold a LangChain coded agent whose guardrails are imported from the wrong module.

Flips the baseline's `from uipath_langchain.guardrails import …` to
`from uipath.platform.guardrails import …` and leaves no other
`uipath_langchain.guardrails` import — so the LangChain adapter never registers as
an import side effect and the `@guardrail`-decorated factory returns the LLM
unwrapped (silent no-op). `uip codedagent review` (Step 2.5a) emits
`CODED_GUARDRAIL_WRONG_IMPORT` for this deterministically and **offline** (no
catalog / auth needed), which the reviewer must carry into the report.
"""

import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from coded_scaffold import (  # noqa: E402
    BASELINE_LANGCHAIN_GRAPH,
    write_baseline_langchain_agent,
)

PROJECT = Path("CodedAgent")


def main() -> None:
    wrong = BASELINE_LANGCHAIN_GRAPH.replace(
        "from uipath_langchain.guardrails import",
        "from uipath.platform.guardrails import",
    )
    if "uipath_langchain.guardrails import" in wrong:
        sys.exit("FAIL: a uipath_langchain.guardrails import still remains")
    write_baseline_langchain_agent(PROJECT, graph_py=wrong)
    print("Scaffolded LangChain agent importing guardrails from uipath.platform.guardrails")


if __name__ == "__main__":
    main()
