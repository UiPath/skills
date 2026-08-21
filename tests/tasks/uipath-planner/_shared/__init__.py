"""Cross-suite `_shared` package bridge.

Two eval suites (uipath-maestro-case, uipath-planner) each carry a `_shared`
checker package under the same importable name. In a combined pytest run the
first-imported package lands in sys.modules and would shadow the other, so a
checker's `from _shared.<module> import ...` breaks depending on collection
order. Extending __path__ over BOTH suite directories (own directory first)
makes submodule resolution order-independent.
"""

from pathlib import Path as _Path

_here = _Path(__file__).resolve().parent
_tasks_root = _here.parents[1]
__path__ = [str(_here)] + [
    str(_d)
    for _d in (
        _tasks_root / "uipath-maestro-case" / "_shared",
        _tasks_root / "uipath-planner" / "_shared",
    )
    if _d.is_dir() and _d != _here
]
