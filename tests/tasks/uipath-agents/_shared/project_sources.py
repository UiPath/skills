"""Locate a coded agent's own Python sources for check scripts.

Agents do not always keep a whole agent in `main.py`. A tool or helper
often lives in a sibling module (`order_tools.py`, `tools/orders.py`)
that the graph module imports. Checkers that read only `main.py` /
`graph.py` then report a correct project as missing its tool.

This module resolves:

  * the entry module — the file `langgraph.json` (`graphs`) or
    `uipath.json` (`functions`) registers, falling back to `main.py`
    then `graph.py`;
  * the agent modules — the entry module plus every project file it
    imports, transitively (absolute imports resolved against the
    project root, relative imports against the importing file).

Only the import closure counts. Stray scripts the agent wrote to probe
the tenant (`verify.py`, `_setup/`), virtualenvs and tests are never
graded: they are not part of the agent, so they can neither satisfy a
check nor trip the lazy-init rule.

Usage:

    from _shared.project_sources import agent_modules, find_entry_module

    entry = find_entry_module(ROOT)
    modules = agent_modules(ROOT, entry)
    text = read_sources(modules)
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_SKIPPED_DIR_NAMES = frozenset({
    "__pycache__",
    "_setup",
    "evaluations",
    "node_modules",
    "site-packages",
    "tests",
    "venv",
})


def _registered_targets(root: Path) -> list[str]:
    """`<file>:<symbol>` targets from langgraph.json, then uipath.json."""
    targets: list[str] = []
    for name, key in (("langgraph.json", "graphs"), ("uipath.json", "functions")):
        path = root / name
        if not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        mapping = doc.get(key) if isinstance(doc, dict) else None
        if isinstance(mapping, dict):
            targets.extend(v for v in mapping.values() if isinstance(v, str))
    return targets


def find_entry_module(root: Path) -> Path:
    """Return the graph/entry module, or exit with a FAIL diagnostic."""
    for target in _registered_targets(root):
        file_part = target.split(":", 1)[0]
        path = (root / file_part).resolve()
        if path.suffix == ".py" and path.is_file():
            return path
    for candidate in ("main.py", "graph.py"):
        path = root / candidate
        if path.is_file():
            return path.resolve()
    sys.exit(
        f"FAIL: no entry module under {root} — langgraph.json / uipath.json "
        "register no existing .py file, and neither main.py nor graph.py exists"
    )


def _is_project_file(root: Path, path: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    return not any(
        part.startswith(".") or part in _SKIPPED_DIR_NAMES for part in rel.parts[:-1]
    )


def _module_file(base: Path, dotted: str) -> Path | None:
    """`a.b` under `base` → `a/b.py` or `a/b/__init__.py`."""
    stem = base.joinpath(*dotted.split(".")) if dotted else base
    for candidate in (stem.with_suffix(".py"), stem / "__init__.py"):
        if candidate.is_file():
            return candidate.resolve()
    return None


def _imported_files(root: Path, path: Path, tree: ast.Module) -> list[Path]:
    search_roots = [root, root / "src", path.parent]
    found: list[Path] = []

    def add(base_dirs: list[Path], dotted: str) -> None:
        for base in base_dirs:
            hit = _module_file(base, dotted)
            if hit is not None:
                found.append(hit)
                return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(search_roots, alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = path.parent
                for _ in range(node.level - 1):
                    base = base.parent
                bases = [base]
            else:
                bases = search_roots
            module = node.module or ""
            add(bases, module)
            # `from pkg import submodule` imports a module, not a symbol.
            for alias in node.names:
                add(bases, f"{module}.{alias.name}" if module else alias.name)
    return found


def agent_modules(root: Path, entry: Path) -> list[Path]:
    """The entry module plus every project module it imports, transitively."""
    root = root.resolve()
    ordered: list[Path] = []
    pending = [entry.resolve()]
    while pending:
        path = pending.pop(0)
        if path in ordered:
            continue
        ordered.append(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for dep in _imported_files(root, path, tree):
            if dep not in ordered and _is_project_file(root, dep):
                pending.append(dep)
    return ordered


def read_sources(modules: list[Path]) -> str:
    """Concatenate module sources for project-wide regex checks."""
    return "\n\n".join(p.read_text(encoding="utf-8") for p in modules)


def parse_modules(modules: list[Path]) -> list[tuple[Path, ast.Module]]:
    """Parse each module, exiting with a FAIL diagnostic on a syntax error."""
    parsed: list[tuple[Path, ast.Module]] = []
    for path in modules:
        try:
            parsed.append(
                (path, ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
            )
        except SyntaxError as exc:
            sys.exit(f"FAIL: {path.name} has a syntax error: {exc}")
    return parsed


def describe(modules: list[Path], root: Path) -> str:
    """`main.py, order_tools.py` — for OK/FAIL messages."""
    root = root.resolve()
    names = []
    for p in modules:
        try:
            names.append(p.relative_to(root).as_posix())
        except ValueError:
            names.append(p.name)
    return ", ".join(names)
