#!/usr/bin/env python3
"""Smoke check: an inline (uipath.agent.autonomous) agent embedded in a .flow
file meets the production bar — self-contained inputs, not toy defaults.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $TASK_DIR/../_shared/check_inline_agent.py <flow-glob>

  <flow-glob>  Shell-style glob for the .flow file, e.g.
               "EmailTriage/EmailTriage/EmailTriage.flow". Defaults to
               "*/*/*.flow" if omitted.

Grades the `.flow` file as the source of truth (self-contained-flow storage
contract): the sidecar directory is derived and is neither read nor required.
Asserts, on the first `uipath.agent.autonomous` node of the first matching
flow:

  1. Self-contained + real: string prompts (embed trigger), system prompt not
     a placeholder, model set and not the stale scaffold default, lowercase
     UUID `inputs.source`, no never-author artifacts (instance `model` block,
     `contentTokens`, `derivedInputDefinition`).
  2. Prompts use the canvas token namespace — never derived `{{input.*}}` /
     `{{ $agent.* }}` forms.
  3. `agentInputVariables` follows the authoring contract.
  4. `agentOutputVariables` declares at least one typed field beyond a bare
     `content` string.

Exit 0 on pass; exit 1 with a "FAIL: ..." line naming the failing property.
Reads only the .flow file — no tenant calls, no agent self-reports.
"""

from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_inline_wiring import (  # noqa: E402
    load_json,
    find_autonomous_agent_node,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_agent_input_vars,
)


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*/*/*.flow"
    paths = sorted(glob.glob(pattern))
    if not paths:
        print(f"FAIL: no .flow file matched {pattern!r}")
        return 1

    path = paths[0]
    flow = load_json(path)
    node = find_autonomous_agent_node(flow)
    inputs = assert_embedded_agent(node)
    assert_prompt_tokens(node)
    assert_agent_input_vars(node)

    declared = inputs.get("agentOutputVariables")
    if not isinstance(declared, list):
        print(f"FAIL ({path}): inputs.agentOutputVariables is not a list")
        return 1
    typed = [
        v.get("id")
        for v in declared
        if isinstance(v, dict) and v.get("id") and v.get("id") != "content"
    ]
    if not typed:
        print(
            f"FAIL ({path}): agentOutputVariables has no typed field beyond "
            f"'content': {[v.get('id') for v in declared if isinstance(v, dict)]}"
        )
        return 1

    prompt = (inputs.get("systemPrompt") or "").strip()
    print(
        f"OK ({path}): node={node['id']} model={inputs.get('model')} "
        f"promptlen={len(prompt)} outputs={typed}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
