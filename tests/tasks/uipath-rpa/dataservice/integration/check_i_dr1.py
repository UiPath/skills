#!/usr/bin/env python3
"""I-DR1 — DeleteEntityRecord basic; no read-mode/write-mode bleed."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import (  # noqa: E402
    assert_attr_or_default,
    assert_child_absent,
    get_activity,
    load,
)

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    root = load(xaml)
    activity = get_activity(
        root, "DeleteEntityRecord", type_arg="local:CodingAgentsEvalEntity"
    )

    # ScopeValue defaults to "Tenant" when omitted from XAML — accept either
    # absent (default) or explicit "Tenant"; reject explicit non-Tenant values.
    assert_attr_or_default(activity, "ScopeValue", "Tenant")

    # DeleteEntityRecord must not carry any read-mode or write-mode props
    for forbidden in (
        "DynamicEntityField",
        "InputEntityInFieldView",
    ):
        assert_child_absent(activity, forbidden)

    print(f"PASS: {xaml} — DeleteEntityRecord matches I-DR1 spec")
