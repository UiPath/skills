#!/usr/bin/env python3
"""NameToAge: an API-workflow node executes and the output holds a plausible age."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_node_types,
    assert_output_int_in_range,
    run_debug,
)


def main():
    payload = run_debug(timeout=240)
    # Low-code API-workflow invocation node has extensionType "api-workflow".
    assert_node_types(payload, ["api-workflow"])
    age = assert_output_int_in_range(payload, 1, 150)
    print(f"OK: API workflow executed; age = {age}")


if __name__ == "__main__":
    main()
