#!/usr/bin/env python3
"""Generate the catalog of cloud-tenant resources the coder-eval tasks depend on.

The catalog is derived from ``tests/tasks/`` on every run, never hand-maintained:

* each task is tiered ``hard`` (a pre_run, post_run or grader command calls the
  tenant), ``soft`` (graded locally, but the prompt sends the agent to the tenant)
  or ``local``;
* each dependency the task's own files name — Integration Service connectors and
  pinned connection ids, solution resources (SDD task details, caseplan bindings,
  registry ledgers), Data Fabric entities and tenant-calling setup helpers — is
  recorded with the tasks that reference it;
* each dependency gets a disposition from ``RULES`` below: ``creatable``,
  ``substitutable`` or ``unavailable``, with its reason and the tenant services it
  needs. A dependency no rule covers is ``unclassified``; ``--strict`` fails on it,
  so a dependency added to a task later cannot go unreviewed.

Usage:
  python3 tests/scripts/tenant_catalog.py [--skill uipath-maestro-case] \
      [--format json|md] [--out FILE] [--strict]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]
TASKS_ROOT = REPO / "tests" / "tasks"
SKILLS_ROOT = REPO / "skills"

TEXT_SUFFIXES = {".yaml", ".yml", ".md", ".json", ".py", ".case", ".bpmn", ".flow", ".txt", ".sh"}
MAX_TEXT_BYTES = 2_000_000
GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
GUID_RE = re.compile(GUID)
PLACEHOLDER_RE = re.compile(r"^(?:—|-|–|n/a|none|tbd|\(none\)|<.*>)$", re.IGNORECASE)

# --- Tenant-calling CLI verbs ------------------------------------------------------

UIP_CALL_RE = re.compile(
    r"""\buip\b(?:["'\s,\]\)\[]+(?:--[\w-]+\s+)?)((?:[a-z][a-z-]*["'\s,]+){1,3})""",
)

# Verbs that run without a tenant, per skills/uipath-maestro-case/references/case-commands.md
# and skills/uipath-solution. Every other `uip` verb is treated as tenant-calling.
OFFLINE_VERBS = (
    "maestro case validate",
    "maestro case init",
    "maestro case pack",
    "maestro case splice",
    "maestro case bindings",
    "maestro case sdd",
    "maestro flow validate",
    "maestro flow init",
    "maestro flow compile",
    "maestro bpmn validate",
    "solution init",
    "solution pack",
    "solution project",
    "solution resources remove",
    "solution resources edit",
    "solution resources list",
    "login",
    "tools",
    "update",
    "version",
)

# Tenant services each verb family needs, longest prefix first.
VERB_SERVICES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("maestro case debug", ("Orchestrator", "Maestro", "Studio Web")),
    ("maestro case registry", ("Orchestrator", "Maestro")),
    ("maestro case tasks", ("Orchestrator", "Maestro")),
    ("maestro case spec", ("Integration Service", "Maestro")),
    ("maestro case", ("Orchestrator", "Maestro")),
    ("maestro flow", ("Orchestrator", "Maestro")),
    ("maestro", ("Orchestrator", "Maestro")),
    ("solution upload", ("Studio Web",)),
    ("solution", ("Orchestrator", "Automation Solutions")),
    ("is", ("Integration Service",)),
    ("or", ("Orchestrator",)),
    ("df", ("Data Fabric",)),
    ("ixp", ("IXP",)),
    ("tm", ("Test Manager",)),
    ("agent", ("Agents",)),
)

SOFT_PROMPT_RE = re.compile(
    r"\bauthenticated\b|cloud auth|uip login|registry pull|sdd resolve|target tenant|on the (?:test )?tenant"
    r"|live registry|publish the solution",
    re.IGNORECASE,
)

# --- Dispositions -----------------------------------------------------------------

SAAS_REASON = (
    "third-party SaaS account reached through Integration Service; an Automation Suite tenant "
    "holds the connector, but the eval needs a local stand-in for the external account"
)
FIRST_PARTY_REASON = "first-party UiPath connector with no external account; a script can create the connection"

SAAS_CONNECTORS = {
    "uipath-atlassian-jira",
    "uipath-automattic-woocommerce",
    "uipath-box-box",
    "uipath-citrix-sharefile",
    "uipath-databricks-databricks",
    "uipath-docusign-docusign",
    "uipath-freshworks-freshdesk",
    "uipath-google-drive",
    "uipath-google-gmail",
    "uipath-google-sheets",
    "uipath-google-tasks",
    "uipath-greenhouse-greenhouse",
    "uipath-microsoft-azureactivedirectory",
    "uipath-microsoft-linkedin",
    "uipath-microsoft-onedrive",
    "uipath-microsoft-outlook365",
    "uipath-microsoft-teams",
    "uipath-oracle-netsuite",
    "uipath-salesforce-sfdc",
    "uipath-salesforce-slack",
    "uipath-servicenow-servicenow",
    "uipath-snowflake-cortex",
    "uipath-workday-workday",
    "uipath-zendesk-zendesk",
}
FIRST_PARTY_CONNECTORS = {
    "uipath-http-webhook",
    "uipath-uipath-airdk",
    "uipath-uipath-dataservice",
    "uipath-uipath-http",
    "uipath-uipath-jdbc",
    "uipath-uipath-mcp",
    "uipath-uipath-testmanager",
}
CONNECTOR_SERVICES = {
    "uipath-uipath-dataservice": ("Integration Service", "Data Fabric"),
    "uipath-uipath-testmanager": ("Integration Service", "Test Manager"),
    "uipath-uipath-airdk": ("Integration Service", "LLM Gateway"),
}

# (kind, sub-type) -> (disposition, reason, services). Sub-type None matches any.
RESOURCE_RULES: dict[tuple[str, str | None], tuple[str, str, tuple[str, ...]]] = {
    ("process", "api"): (
        "creatable",
        (
            "API workflow published from a solution zip; Automation Suite has no serverless robots, "
            "so it runs on an unattended robot"
        ),
        ("Orchestrator", "Automation Solutions", "Unattended robot"),
    ),
    ("process", "agent"): (
        "creatable",
        "agent published from a solution zip",
        ("Orchestrator", "Automation Solutions", "Agents", "LLM Gateway"),
    ),
    ("process", "processorchestration"): (
        "creatable",
        "agentic process published from a solution zip",
        ("Orchestrator", "Automation Solutions", "Maestro"),
    ),
    ("process", "casemanagement"): (
        "creatable",
        "case process published from a solution zip",
        ("Orchestrator", "Automation Solutions", "Maestro"),
    ),
    ("process", "flow"): (
        "creatable",
        "flow published from a solution zip",
        ("Orchestrator", "Automation Solutions", "Maestro"),
    ),
    ("process", "function"): (
        "creatable",
        (
            "coded function published from a solution zip; assumed to run on an unattended robot "
            "because Automation Suite has no serverless robots — confirm on an ETE run"
        ),
        ("Orchestrator", "Automation Solutions", "Unattended robot"),
    ),
    ("process", "businessrule"): (
        "creatable",
        "business rule published from a solution zip",
        ("Orchestrator", "Automation Solutions"),
    ),
    ("process", None): (
        "creatable",
        "RPA process published from a package; needs an unattended robot",
        ("Orchestrator", "Unattended robot"),
    ),
    ("app", None): (
        "creatable",
        "action app deployed from a solution zip",
        ("Orchestrator", "Action Center", "Apps"),
    ),
    ("folder", None): (
        "creatable",
        "Orchestrator folder; the provisioning recipe or `uip or folders create` makes it",
        ("Orchestrator",),
    ),
    ("entity", None): (
        "creatable",
        "Data Fabric entity created from a committed schema",
        ("Data Fabric",),
    ),
}

# Tenant capabilities a verb family needs beyond its services, as dependencies of their own.
VERB_DEPENDENCIES = {"ixp projects": "IXP projects"}

SERVICE_RULES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "IXP projects": (
        "unavailable",
        (
            "Automation Suite 26.10 ships converged IXP without du-designtimeapi, so no IXP project can be "
            "created (UiPath/coder_eval_uipath .azure-pipelines/scripts/prepare_ete_provisioning.py, "
            "snapshot 2.2610.0-rc.13807591)"
        ),
        ("IXP",),
    ),
}

# Registry cache file -> (kind, sub-type).
CACHE_KINDS = {
    "action-apps-index.json": ("app", None),
    "agent-index.json": ("process", "agent"),
    "api-index.json": ("process", "api"),
    "process-index.json": ("process", None),
    "processOrchestration-index.json": ("process", "processorchestration"),
    "caseManagement-index.json": ("process", "casemanagement"),
    "function-index.json": ("process", "function"),
    "businessRule-index.json": ("process", "businessrule"),
    "flow-index.json": ("process", "flow"),
}

# SDD `**Type:**` / `**Binding Sub-Type:**` values -> sub-type.
SDD_SUBTYPES = {
    "api": "api",
    "api-workflow": "api",
    "agent": "agent",
    "processorchestration": "processorchestration",
    "agentic-process": "processorchestration",
    "case-management": "casemanagement",
    "casemanagement": "casemanagement",
    "flow": "flow",
    "function": "function",
    "business-rule": "businessrule",
    "businessrule": "businessrule",
    "rpa": None,
    "process": None,
}


# --- Model -------------------------------------------------------------------------


@dataclass
class Dependency:
    kind: str
    name: str
    folder: str | None = None
    sub_type: str | None = None
    identities: set[str] = field(default_factory=set)
    services: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    tasks: set[str] = field(default_factory=set)

    @property
    def key(self) -> str:
        parts = [self.kind, self.sub_type or "", self.folder or "", self.name]
        return ":".join(parts)


@dataclass
class Task:
    task_id: str
    path: str
    tier: str = "local"
    tier_evidence: list[str] = field(default_factory=list)
    tenant_verbs: set[str] = field(default_factory=set)
    helpers: set[str] = field(default_factory=set)
    dependency_keys: set[str] = field(default_factory=set)


class Catalog:
    def __init__(self) -> None:
        self.dependencies: dict[str, Dependency] = {}
        self.tasks: list[Task] = []

    def add(self, task: Task, dep: Dependency, source: str, identity: str | None = None) -> None:
        existing = self.dependencies.setdefault(dep.key, dep)
        existing.sources.add(source)
        existing.tasks.add(task.task_id)
        if identity:
            existing.identities.add(identity)
        existing.services |= dep.services
        task.dependency_keys.add(dep.key)


# --- File helpers ------------------------------------------------------------------


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def iter_text_files(roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            if (
                path.is_file()
                and path.suffix in TEXT_SUFFIXES
                and "__pycache__" not in path.parts
                and not path.name.startswith(("test_", "conftest"))
            ):
                resolved = path.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    yield path


def skill_names() -> set[str]:
    return {p.name for p in SKILLS_ROOT.iterdir() if p.is_dir()} if SKILLS_ROOT.is_dir() else set()


# --- Tenant verb detection ---------------------------------------------------------


SHELL_COMMAND_RE = re.compile(r"(?:^|[;&|(]\s*)uip\s")

# Command groups that name no operation on their own; a call cut off here had a variable sub-command.
INCOMPLETE_VERBS = {"maestro", "maestro case", "maestro flow", "maestro bpmn", "solution", "solution resources"}


def classify_verb(words: list[str]) -> str | None:
    """The tenant-calling verb these `uip` arguments name, or None when offline or incomplete."""
    verb = " ".join(words[:3])
    if not words or verb in INCOMPLETE_VERBS:
        return None
    if any(verb == v or verb.startswith(v + " ") for v in OFFLINE_VERBS):
        return None
    if words[0] not in {prefix.split()[0] for prefix, _ in VERB_SERVICES}:
        return None
    return verb


def verbs_in(text: str) -> set[str]:
    verbs: set[str] = set()
    for match in UIP_CALL_RE.finditer(text):
        verb = classify_verb(re.findall(r"[a-z][a-z-]*", match.group(1)))
        if verb:
            verbs.add(verb)
    return verbs


def services_for_verb(verb: str) -> tuple[str, ...]:
    for prefix, services in VERB_SERVICES:
        if verb == prefix or verb.startswith(prefix + " "):
            return services
    return ()


class PythonIndex:
    """Function-level tenant-verb analysis for Python helpers and checkers."""

    def __init__(self) -> None:
        self._modules: dict[Path, tuple[set[str], dict[str, set[str]], list[tuple[str, list[str]]]]] = {}

    def _parse(self, path: Path) -> tuple[set[str], dict[str, set[str]], list[tuple[str, list[str]]]]:
        if path in self._modules:
            return self._modules[path]
        source = read_text(path)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            result: tuple[set[str], dict[str, set[str]], list[tuple[str, list[str]]]] = (verbs_in(source), {}, [])
            self._modules[path] = result
            return result
        functions: dict[str, ast.AST] = {
            node.name: node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        direct = {name: _python_verbs(node) for name, node in functions.items()}
        calls = {name: _called_names(node) & functions.keys() for name, node in functions.items()}
        changed = True
        while changed:
            changed = False
            for name, callees in calls.items():
                merged = set(direct[name])
                for callee in callees:
                    merged |= direct[callee]
                if merged != direct[name]:
                    direct[name] = merged
                    changed = True
        module_body = [n for n in tree.body if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        module_verbs = set().union(*(_python_verbs(n) for n in module_body)) if module_body else set()
        imports: list[tuple[str, list[str]]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append((node.module, [a.asname or a.name for a in node.names]))
            elif isinstance(node, ast.Import):
                imports.extend((a.name, []) for a in node.names)
        result = (module_verbs, direct, imports)
        self._modules[path] = result
        return result

    def entry_verbs(self, path: Path, search_dirs: list[Path]) -> set[str]:
        """Verbs a script reaches when run: its own code plus the imported functions it uses."""
        module_verbs, functions, imports = self._parse(path)
        verbs = set(module_verbs)
        for function_verbs in functions.values():
            verbs |= function_verbs
        try:
            used = _called_names(ast.parse(read_text(path)))
        except SyntaxError:
            used = set()
        for module, names in imports:
            target = _resolve_module(module, [path.parent, *search_dirs])
            if target is None or target == path:
                continue
            _, imported_functions, _ = self._parse(target)
            wanted = set(names) if names else set(imported_functions)
            for name in wanted & used:
                verbs |= imported_functions.get(name, set())
        return verbs


def python_folder_constants(path: Path) -> set[str]:
    try:
        tree = ast.parse(read_text(path))
    except SyntaxError:
        return set()
    return {
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and FOLDER_RE.fullmatch(n.value)
    }


def _python_verbs(node: ast.AST) -> set[str]:
    """Verbs from `["uip", ...]` argument lists and from shell strings that contain a `uip` call."""
    verbs: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, (ast.List, ast.Tuple)) and n.elts:
            head = n.elts[0]
            if isinstance(head, ast.Constant) and head.value == "uip":
                words = []
                for element in n.elts[1:]:
                    if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
                        break
                    if element.value.startswith("-"):
                        break
                    words.append(element.value)
                verb = classify_verb(words)
                if verb:
                    verbs.add(verb)
        elif isinstance(n, ast.Call) and "uip" in _call_name(n).lower():
            words = []
            for arg in n.args:
                if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)) or arg.value.startswith("-"):
                    break
                words.append(arg.value)
            verb = classify_verb(words)
            if verb:
                verbs.add(verb)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and SHELL_COMMAND_RE.search(n.value):
            verbs |= verbs_in(n.value)
    return verbs


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                names.add(n.func.id)
            elif isinstance(n.func, ast.Attribute):
                names.add(n.func.attr)
    return names


def _resolve_module(module: str, search_dirs: list[Path]) -> Path | None:
    parts = module.split(".")
    for directory in search_dirs:
        for candidate in (directory.joinpath(*parts).with_suffix(".py"), directory.joinpath(*parts) / "__init__.py"):
            if candidate.is_file():
                return candidate
        if len(parts) > 1:
            candidate = directory.joinpath(*parts[1:]).with_suffix(".py")
            if candidate.is_file():
                return candidate
    return None


# --- Task loading ------------------------------------------------------------------


@dataclass
class TaskContext:
    yaml_path: Path
    data: dict[str, Any]
    skill_dir: Path
    reference_dir: Path
    mounts: dict[str, list[Path]]

    @property
    def task_dir(self) -> Path:
        return self.yaml_path.parent

    def commands(self) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        for phase in ("pre_run", "post_run"):
            for step in self.data.get(phase) or []:
                if isinstance(step, dict) and isinstance(step.get("command"), str):
                    found.append((phase, step["command"]))
        for criterion in self.data.get("success_criteria") or []:
            if isinstance(criterion, dict) and isinstance(criterion.get("command"), str):
                found.append(("success_criteria", criterion["command"]))
        return found

    def resolve_script(self, token: str) -> Path | None:
        token = token.strip("'\"")
        for var in ("$REFERENCE_DIR", "${REFERENCE_DIR}"):
            if token.startswith(var):
                candidate = self.reference_dir / token[len(var) :].lstrip("/")
                return candidate if candidate.is_file() else None
        head, _, rest = token.partition("/")
        for source in reversed(self.mounts.get(head, [])):
            candidate = source / rest
            if candidate.is_file():
                return candidate
        candidate = self.task_dir / token
        return candidate if candidate.is_file() else None

    def content_roots(self) -> list[Path]:
        """The files this task stages or owns, excluding the skill-wide shared helper dirs."""
        shared = {(self.skill_dir / name).resolve() for name in ("_setup", "_shared")}
        roots = [self.yaml_path]
        if self.task_dir.resolve() != self.skill_dir.resolve():
            roots.append(self.task_dir)
        for sources in self.mounts.values():
            roots.extend(s for s in sources if s.resolve() not in shared)
        for source in self.data.get("sandbox", {}).get("template_sources", []) or []:
            if isinstance(source, dict) and source.get("type") == "template_file" and source.get("path"):
                candidate = (self.task_dir / source["path"]).resolve()
                if candidate.is_file():
                    roots.append(candidate)
        return roots


def soft_signal(context: TaskContext) -> str | None:
    """Why the agent, not the grader, must reach the tenant; None when nothing says so."""
    for criterion in context.data.get("success_criteria") or []:
        if not isinstance(criterion, dict):
            continue
        pattern = criterion.get("command_pattern")
        if criterion.get("type") == "command_executed" and isinstance(pattern, str):
            text = re.sub(r"\(uip\|[^)]*\)\"?\??", "uip", pattern)
            text = re.sub(r"\\[sbw][+*?]?|[\\()^$?|]", " ", text)
            verbs = verbs_in(text)
            if verbs:
                return f"command_executed requires: {', '.join(sorted(verbs))}"
    prompt = f"{context.data.get('initial_prompt', '')}\n{context.data.get('description', '')}"
    match = SOFT_PROMPT_RE.search(prompt)
    if match:
        return f"prompt sends the agent to the tenant: {match.group(0)!r}"
    if "LIVE registry" in read_text(context.yaml_path):
        return "task header declares LIVE registry fixtures"
    return None


def load_task(yaml_path: Path, tasks_root: Path = TASKS_ROOT) -> TaskContext | None:
    try:
        data = yaml.safe_load(read_text(yaml_path))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict) or "task_id" not in data:
        return None
    skill_dir = tasks_root / yaml_path.relative_to(tasks_root).parts[0]
    reference = (data.get("reference") or {}).get("directory") or "."
    mounts: dict[str, list[Path]] = defaultdict(list)
    for source in (data.get("sandbox") or {}).get("template_sources", []) or []:
        if isinstance(source, dict) and source.get("type") == "template_dir" and source.get("path"):
            directory = (yaml_path.parent / source["path"]).resolve()
            if directory.is_dir():
                mounts[str(source.get("mount_point") or Path(source["path"]).name)].append(directory)
    return TaskContext(
        yaml_path=yaml_path,
        data=data,
        skill_dir=skill_dir,
        reference_dir=(yaml_path.parent / reference).resolve(),
        mounts=dict(mounts),
    )


# --- Extraction --------------------------------------------------------------------

CONNECTOR_TOKEN = r"(uipath-[a-z0-9]+(?:-[a-z0-9]+)+)(?![\w/-])"
CONNECTOR_CONTEXT_RE = re.compile(
    r"(?i)(?:connector|preflight_connections\.py|\bis\W+(?:connections|resources|triggers))"
    r"[^\n]{0,80}?(?<![\w/.@-])" + CONNECTOR_TOKEN
)
CONNECTOR_ANY_RE = re.compile(r"(?<![\w/.@-])" + CONNECTOR_TOKEN)
CONNECTION_ID_RE = re.compile(r"(?i)connection\s*id\W{0,8}(" + GUID + ")")
SCRIPT_TOKEN_RE = re.compile(r"""[\w${}./-]+\.py\b""")
SDD_FIELD_RE = re.compile(r"^\*\*([A-Za-z /()-]+):\*\*\s*(.*)$")
FOLDER_RE = re.compile(r"Shared(?:/[^/\n\"'`|*]+)*")
QUOTED_FOLDER_RE = re.compile(r"[`\"'](Shared(?:/[^/\n\"'`|*]+)*)[`\"']")
CONNECTOR_WINDOW = 4


def connector_vocabulary(files: Iterable[Path]) -> set[str]:
    """Connector keys seen in a connector context anywhere in the corpus, minus skill names."""
    vocabulary: set[str] = set()
    for path in files:
        vocabulary.update(CONNECTOR_CONTEXT_RE.findall(read_text(path)))
    return vocabulary - skill_names()


def clean_value(value: str) -> str:
    value = value.strip().strip("`").strip()
    value = re.sub(r"\s+\(.*\)$", "", value)
    return value.strip("`").strip()


def extract_sdd_resources(text: str) -> list[tuple[str, str | None, str, str | None, str | None, int]]:
    """(kind, sub_type, name, folder, identity, line) for each resolved SDD task detail."""
    results = []
    lines = text.splitlines()
    last_type: str | None = None
    for index, line in enumerate(lines):
        match = SDD_FIELD_RE.match(line.strip())
        if not match:
            continue
        label, value = match.group(1).strip().lower(), match.group(2)
        if label == "type":
            last_type = clean_value(value).lower()
        elif label == "resolved resource":
            fields = _block_fields(lines, index)
            name = clean_value(value)
            folder = clean_value(fields.get("folder path", ""))
            if PLACEHOLDER_RE.match(name) or not name or PLACEHOLDER_RE.match(folder or "—"):
                continue
            sub_raw = clean_value(fields.get("binding sub-type", "")).lower()
            sub_type = SDD_SUBTYPES.get(sub_raw) if sub_raw and not PLACEHOLDER_RE.match(sub_raw) else None
            if sub_type is None and last_type:
                sub_type = SDD_SUBTYPES.get(last_type)
            identity = GUID_RE.search(fields.get("resource identity", ""))
            results.append(("process", sub_type, name, folder, identity.group(0) if identity else None, index + 1))
        elif label == "action app id":
            fields = _block_fields(lines, index, backwards=True)
            identity = GUID_RE.search(value)
            folder = clean_value(fields.get("deployment folder", ""))
            name = clean_value(fields.get("hitl implementation", "")).removeprefix("Action App:").strip()
            if identity and folder and not PLACEHOLDER_RE.match(folder):
                results.append(("app", None, name or identity.group(0), folder, identity.group(0), index + 1))
    return results


def _block_fields(lines: list[str], index: int, backwards: bool = False) -> dict[str, str]:
    fields: dict[str, str] = {}
    span = (
        range(max(0, index - 6), min(len(lines), index + 8)) if backwards else range(index, min(len(lines), index + 8))
    )
    for line in (lines[i] for i in span):
        match = SDD_FIELD_RE.match(line.strip())
        if match:
            fields.setdefault(match.group(1).strip().lower(), match.group(2))
    return fields


def extract_caseplan_bindings(data: Any) -> list[tuple[str, str | None, str, str | None]]:
    """(kind, sub_type, name, folder) for each tenant resource a caseplan binds by name and folder."""
    results = []
    bindings = data.get("bindings") if isinstance(data, dict) else None
    by_key: dict[str, dict[str, Any]] = defaultdict(dict)
    for binding in bindings or []:
        if not isinstance(binding, dict) or str(binding.get("resource", "")).lower() == "connection":
            continue
        key = binding.get("resourceKey")
        if isinstance(key, str):
            entry = by_key[key]
            entry["kind"] = str(binding.get("resource", "")).lower()
            entry["sub_type"] = str(binding.get("resourceSubType") or "").lower() or None
            entry[binding.get("propertyAttribute") or binding.get("name")] = binding.get("default")
    for entry in by_key.values():
        folder = entry.get("folderPath")
        name = entry.get("name")
        if (
            not isinstance(folder, str)
            or not isinstance(name, str)
            or not folder
            or folder.startswith("solution_folder")
        ):
            continue
        kind = "app" if entry["kind"] in {"app", "apps", "actionapp"} else "process"
        results.append((kind, entry["sub_type"], name, folder))
    return results


def extract_registry_ledger(data: Any) -> list[tuple[str, str | None, str, str | None, str | None]]:
    entries = data.get("resolved") if isinstance(data, dict) else data
    results = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        kind, sub_type = CACHE_KINDS.get(str(entry.get("cacheFile")), (None, None))
        selected = entry.get("selected")
        if kind is None or not isinstance(selected, dict):
            continue
        name = selected.get("deploymentTitle") or selected.get("name") or entry.get("searchQuery")
        folder = (selected.get("deploymentFolder") or {}).get("fullyQualifiedName") or selected.get("folder")
        identity = selected.get("id") or selected.get("entityKey") or selected.get("identifier")
        if isinstance(name, str) and isinstance(identity, str) and GUID_RE.fullmatch(identity):
            results.append((kind, sub_type, name, folder if isinstance(folder, str) else None, identity))
    return results


def extract_entities(command: str, context: TaskContext) -> list[str]:
    names = []
    if "ensure_folder_entity.py" in command:
        for token in SCRIPT_TOKEN_RE.sub(" ", command).split():
            token = token.strip("'\"")
            if token.endswith(".json"):
                path = context.resolve_script(token)
                if path:
                    try:
                        name = json.loads(read_text(path)).get("name")
                    except (json.JSONDecodeError, AttributeError):
                        name = None
                    if isinstance(name, str):
                        names.append(name)
    names.extend(re.findall(r"\bdf\s+entities\s+create\s+[\"']?([A-Za-z_][\w]*)", command))
    return names


# --- Classification ----------------------------------------------------------------


def disposition(dep: Dependency) -> tuple[str, str, tuple[str, ...]]:
    if dep.kind == "connector":
        services = CONNECTOR_SERVICES.get(dep.name, ("Integration Service",))
        if dep.name in SAAS_CONNECTORS:
            return "substitutable", SAAS_REASON, services
        if dep.name in FIRST_PARTY_CONNECTORS:
            return "creatable", FIRST_PARTY_REASON, services
        return "unclassified", "no rule in tenant_catalog.py SAAS_CONNECTORS or FIRST_PARTY_CONNECTORS", services
    if dep.kind == "service":
        return SERVICE_RULES.get(
            dep.name, ("unclassified", f"no rule in tenant_catalog.py SERVICE_RULES for {dep.name}", ())
        )
    if dep.kind == "helper":
        return "creatable", "setup helper; it runs wherever its tenant services exist", tuple(sorted(dep.services))
    for key in ((dep.kind, dep.sub_type), (dep.kind, None)):
        if key in RESOURCE_RULES:
            return RESOURCE_RULES[key]
    return "unclassified", f"no rule in tenant_catalog.py RESOURCE_RULES for {dep.kind}/{dep.sub_type}", ()


def build_catalog(skill: str | None, tasks_root: Path | None = None) -> Catalog:
    catalog = Catalog()
    tasks_root = tasks_root or TASKS_ROOT
    root = tasks_root / skill if skill else tasks_root
    yaml_paths = sorted(p for p in root.rglob("*.yaml") if "_setup" not in p.parts and "fixtures" not in p.parts)
    contexts = [c for c in (load_task(p, tasks_root) for p in yaml_paths) if c is not None]
    vocabulary = connector_vocabulary(iter_text_files([tasks_root]))
    python = PythonIndex()

    for context in contexts:
        task = Task(task_id=str(context.data["task_id"]), path=rel(context.yaml_path))
        catalog.tasks.append(task)
        search_dirs = [context.skill_dir / "_shared", context.skill_dir / "_setup", context.skill_dir]

        for phase, command in context.commands():
            verbs = verbs_in(command)
            for token in SCRIPT_TOKEN_RE.findall(command):
                script = context.resolve_script(token)
                if script is None:
                    continue
                script_verbs = python.entry_verbs(script, search_dirs)
                verbs |= script_verbs
                if phase != "success_criteria" and script_verbs:
                    task.helpers.add(script.name)
                    services = {service for verb in script_verbs for service in services_for_verb(verb)}
                    catalog.add(task, Dependency(kind="helper", name=script.name, services=services), rel(script))
            if verbs and phase != "post_run":
                for verb in verbs:
                    for prefix, capability in VERB_DEPENDENCIES.items():
                        if verb == prefix or verb.startswith(prefix + " "):
                            catalog.add(task, Dependency(kind="service", name=capability), task.path)
                task.tenant_verbs |= verbs
                task.tier_evidence.append(f"{phase}: {', '.join(sorted(verbs))}")
            for entity in extract_entities(command, context):
                catalog.add(task, Dependency(kind="entity", name=entity), task.path)

        if task.tenant_verbs:
            task.tier = "hard"
        else:
            signal = soft_signal(context)
            if signal:
                task.tier = "soft"
                task.tier_evidence.append(signal)

        script_files = [
            s for _, c in context.commands() for t in SCRIPT_TOKEN_RE.findall(c) if (s := context.resolve_script(t))
        ]
        for path in iter_text_files([*context.content_roots(), *script_files]):
            text = read_text(path)
            source = rel(path)
            for token in set(CONNECTOR_ANY_RE.findall(text)) & vocabulary:
                catalog.add(task, Dependency(kind="connector", name=token), source)
            recent: list[tuple[int, str]] = []
            for number, line in enumerate(text.splitlines()):
                recent += [(number, k) for k in CONNECTOR_ANY_RE.findall(line) if k in vocabulary]
                connection = CONNECTION_ID_RE.search(line)
                nearby = [k for n, k in recent if number - n <= CONNECTOR_WINDOW]
                if connection and nearby:
                    dep = Dependency(kind="connector", name=nearby[-1])
                    catalog.add(task, dep, f"{source}:{number + 1}", identity=connection.group(1))
            if path.suffix == ".py":
                for folder in python_folder_constants(path):
                    catalog.add(task, Dependency(kind="folder", name=folder), source)
            elif path.suffix in {".md", ".yaml", ".yml"}:
                for line in text.splitlines():
                    if "resourceKey" not in line:
                        for folder in QUOTED_FOLDER_RE.findall(line):
                            catalog.add(task, Dependency(kind="folder", name=folder.rstrip(" ./")), source)
                for kind, sub_type, name, folder, identity, line in extract_sdd_resources(text):
                    dep = Dependency(kind=kind, sub_type=sub_type, name=name, folder=folder)
                    catalog.add(task, dep, f"{source}:{line}", identity)
                    if folder:
                        catalog.add(task, Dependency(kind="folder", name=folder), f"{source}:{line}")
            elif path.suffix in {".json", ".case"}:
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if path.name.startswith("caseplan"):
                    for kind, sub_type, name, folder in extract_caseplan_bindings(data):
                        catalog.add(task, Dependency(kind=kind, sub_type=sub_type, name=name, folder=folder), source)
                        if folder:
                            catalog.add(task, Dependency(kind="folder", name=folder), source)
                elif path.name == "registry-resolved.json":
                    for kind, sub_type, name, folder, identity in extract_registry_ledger(data):
                        dep = Dependency(kind=kind, sub_type=sub_type, name=name, folder=folder)
                        catalog.add(task, dep, source, identity)
    _drop_resource_keys_caught_as_folders(catalog)
    return catalog


def _drop_resource_keys_caught_as_folders(catalog: Catalog) -> None:
    """`<folder>.<name>` binding keys look like folder paths; fold them into their folder."""
    folders = {d.name: d for d in catalog.dependencies.values() if d.kind == "folder"}
    for name, dep in list(folders.items()):
        parent, dot, _ = name.rpartition(".")
        if dot and parent in folders:
            target = folders[parent]
            target.tasks |= dep.tasks
            target.sources |= dep.sources
            del catalog.dependencies[dep.key]
            for task in catalog.tasks:
                if dep.key in task.dependency_keys:
                    task.dependency_keys.discard(dep.key)
                    task.dependency_keys.add(target.key)


# --- Rendering ---------------------------------------------------------------------


def to_json(catalog: Catalog) -> dict[str, Any]:
    tiers = {t.task_id: t.tier for t in catalog.tasks}
    dependencies = []
    for dep in sorted(catalog.dependencies.values(), key=lambda d: (d.kind, d.sub_type or "", d.folder or "", d.name)):
        state, reason, services = disposition(dep)
        dependencies.append(
            {
                "kind": dep.kind,
                "sub_type": dep.sub_type,
                "name": dep.name,
                "folder": dep.folder,
                "disposition": state,
                "reason": reason,
                "services": list(services),
                "pinned_ids": sorted(dep.identities),
                "tasks": {tier: sorted(t for t in dep.tasks if tiers[t] == tier) for tier in ("hard", "soft", "local")},
                "sources": sorted(dep.sources),
            }
        )
    by_key = {d.key: d for d in catalog.dependencies.values()}
    tasks = []
    for task in sorted(catalog.tasks, key=lambda t: t.path):
        blocking = []
        services: set[str] = set()
        for verb in task.tenant_verbs:
            services.update(services_for_verb(verb))
        for key in sorted(task.dependency_keys):
            dep = by_key[key]
            state, _, dep_services = disposition(dep)
            services.update(dep_services)
            if state != "creatable":
                blocking.append({"dependency": key, "disposition": state})
        tasks.append(
            {
                "task_id": task.task_id,
                "path": task.path,
                "tier": task.tier,
                "tier_evidence": task.tier_evidence,
                "helpers": sorted(task.helpers),
                "services": sorted(services) if task.tier != "local" else [],
                "dependencies": sorted(task.dependency_keys) if task.tier != "local" else [],
                "blocking": blocking if task.tier != "local" else [],
                "runs_on_automation_suite": task.tier == "local" or not blocking,
            }
        )
    return {"dependencies": dependencies, "tasks": tasks}


def to_markdown(report: dict[str, Any], skill: str | None) -> str:
    tasks = report["tasks"]
    counts = {tier: sum(1 for t in tasks if t["tier"] == tier) for tier in ("hard", "soft", "local")}
    tenant_tasks = [t for t in tasks if t["tier"] != "local"]
    runnable = [t for t in tenant_tasks if t["runs_on_automation_suite"]]
    out = [
        f"# Tenant dependency catalog — {skill or 'all skills'}",
        "",
        "Generated by `tests/scripts/tenant_catalog.py`. Do not edit by hand.",
        "",
        (
            f"Tasks: {len(tasks)} — hard {counts['hard']}, soft {counts['soft']}, local {counts['local']}. "
            f"Tenant tasks whose dependencies are all creatable: {len(runnable)} of {len(tenant_tasks)}."
        ),
        "",
        "## Dependencies",
        "",
        "| Kind | Name | Folder | Disposition | Services | Hard | Soft | Pinned ids |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for dep in report["dependencies"]:
        hard, soft = dep["tasks"]["hard"], dep["tasks"]["soft"]
        if not hard and not soft:
            continue
        kind = dep["kind"] + (f"/{dep['sub_type']}" if dep["sub_type"] else "")
        out.append(
            f"| {kind} | {dep['name']} | {dep['folder'] or '—'} | {dep['disposition']} | "
            f"{', '.join(dep['services']) or '—'} | {len(hard)} | {len(soft)} | {len(dep['pinned_ids'])} |"
        )
    out += ["", "## Dispositions", ""]
    reasons = sorted(
        {(d["disposition"], d["reason"]) for d in report["dependencies"] if d["tasks"]["hard"] or d["tasks"]["soft"]}
    )
    out += [f"- **{state}**: {reason}" for state, reason in reasons]
    out += [
        "",
        "## Tenant tasks that cannot run on Automation Suite",
        "",
        "| Task | Tier | Blocking dependencies |",
        "|---|---|---|",
    ]
    for task in tenant_tasks:
        if not task["runs_on_automation_suite"]:
            blocking = "; ".join(f"{b['dependency']} ({b['disposition']})" for b in task["blocking"])
            out.append(f"| `{task['task_id']}` | {task['tier']} | {blocking} |")
    out += [
        "",
        "## Tenant tasks whose dependencies are all creatable",
        "",
        "| Task | Tier | Services |",
        "|---|---|---|",
    ]
    for task in runnable:
        out.append(f"| `{task['task_id']}` | {task['tier']} | {', '.join(task['services']) or '—'} |")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--skill", help="limit to tests/tasks/<skill>")
    parser.add_argument("--format", choices=("json", "md"), default="json")
    parser.add_argument("--out", type=Path, help="write to this file instead of stdout")
    parser.add_argument(
        "--strict", action="store_true", help="exit 1 when a tenant task has an unclassified dependency"
    )
    args = parser.parse_args(argv)

    if args.skill and not (TASKS_ROOT / args.skill).is_dir():
        parser.error(f"no such skill under tests/tasks: {args.skill}")
    report = to_json(build_catalog(args.skill))
    rendered = json.dumps(report, indent=2) + "\n" if args.format == "json" else to_markdown(report, args.skill)
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    unclassified = sorted(
        {b["dependency"] for t in report["tasks"] for b in t["blocking"] if b["disposition"] == "unclassified"}
    )
    if args.strict and unclassified:
        print(f"unclassified dependencies in tenant tasks: {len(unclassified)}", file=sys.stderr)
        for key in unclassified:
            print(f"  {key}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
