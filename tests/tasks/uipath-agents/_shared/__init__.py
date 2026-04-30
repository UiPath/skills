"""Shared helpers for uipath-agents tests.

Used by check scripts under sibling directories of `_shared/` (e.g.
`simple_echo/check_simple_echo.py`). Each check script imports from
this package via:

    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from _shared.bindings_assertions import (  # noqa: E402
        load_bindings,
        find_resource,
    )
    from _shared.coded_project_factory import write_minimal_project  # noqa: E402
    from _shared.ast_lazy_init_check import (  # noqa: E402
        find_module_level_llm_clients,
    )

Coded-agent helpers are minimal: they mirror the on-disk shape that
`uip codedagent init` would produce, the bindings.json schema documented
in `references/coded/lifecycle/bindings-reference.md`, and the lazy-LLM
init invariant called out in `references/coded/quickstart.md`.
Inline-flow helpers (`inline_wiring.py`) cover the low-code agent-in-flow
shape — see that module's docstring.
"""
