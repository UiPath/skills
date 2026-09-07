"""The bridge to tools/entry_points.py, the shared contract deriver.

type<T>() is inert at runtime, so the JSON Schema the platform validates against is derived from
the job's interfaces at stage time. Running that same deriver here is what makes input-strictness a
real check rather than an assumption: it fails on exactly the contracts that could not produce a
manifest, at authoring time instead of at pack time.

The deriver is loaded by path rather than imported, because it is also path-loaded by the deploy
skill's staging step from a different tree, and a module loaded that way has no package context.
The parent walk matches the one that step uses, so the two agree about where tools/ is.
"""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path


def foreign_idiom(src: str) -> str | None:
    """The Standard Schema library a job declares its contract with, or None for type<T>().

    Only used to name the reason in a diagnostic. Such a contract carries its own schema and so
    cannot be lowered into the manifest this pipeline stages, which is what makes it undeployable
    here rather than merely unusual.
    """
    for module in ("zod", "arktype", "valibot"):
        if re.search(r"from\s+['\"]%s['\"]" % module, src):
            return module
    return None


_DERIVER_CACHE: list = []


def load_deriver():
    """The deriver module, or None when tools/entry_points.py cannot be found."""
    if _DERIVER_CACHE:
        return _DERIVER_CACHE[0]
    override = os.environ.get("ENTRY_POINTS_TOOL")
    candidates = [Path(override)] if override else [
        parent / "tools" / "entry_points.py" for parent in Path(__file__).resolve().parents
    ]
    found = next((c for c in candidates if c.is_file()), None)
    module = None
    if found:
        spec = importlib.util.spec_from_file_location("ontology_entry_points", found)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    _DERIVER_CACHE.append(module)
    return module
