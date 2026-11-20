"""The tiers that read a workflow: parse, untouched, compile and contract.

`compile` is the runner's `inspect`: CoreWF loads the XAML against the real activity
assemblies and validates it, which compiles every VB expression, so an undeclared variable,
a type mismatch or a C# operator in a VB project fails here rather than at run time.
"""

from __future__ import annotations

import hashlib
import json
import subprocess

# Stdlib ET, not defusedxml, for the reason the BPMN verifier gives: no dependencies inside the
# sandbox, the input is the agent's own output, and ET does not resolve external entities.
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from . import runner

WF_NS = "http://schemas.microsoft.com/netfx/2009/xaml/activities"
X_NS = "http://schemas.microsoft.com/winfx/2006/xaml"
EXPRESSION_NAMESPACES = (
    "Microsoft.VisualBasic.Activities",
    "Microsoft.CSharp.Activities",
    "System.Activities.Expressions",
)


@dataclass
class TierResult:
    name: str
    passed: bool
    skipped: bool = False
    messages: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.skipped:
            return "skip"
        return "pass" if self.passed else "FAIL"


def t_parse(path: Path) -> TierResult:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return TierResult("parse", False, messages=[f"not well-formed XML: {exc}"])
    if root.tag != f"{{{WF_NS}}}Activity":
        return TierResult("parse", False, messages=[f"root element is {root.tag}, expected Activity in {WF_NS}"])
    if f"{{{X_NS}}}Class" not in root.attrib:
        return TierResult("parse", False, messages=["root Activity has no x:Class"])
    return TierResult("parse", True)


def t_untouched(path: Path, spec: dict, spec_dir: Path | None) -> TierResult:
    """Reject a repair candidate byte-identical to its fixture, which is shipped valid on purpose."""
    declared = spec.get("fixture")
    if not declared:
        return TierResult("untouched", True, skipped=True, messages=["no fixture: authoring task"])
    fixture = Path(declared)
    if not fixture.is_absolute():
        fixture = (spec_dir or Path.cwd()) / fixture
    if not fixture.exists():
        return TierResult("untouched", False, messages=[f"spec declares a fixture that is missing: {fixture}"])
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()  # noqa: E731
    if digest(fixture) == digest(path):
        return TierResult("untouched", False, messages=["byte-identical to the fixture: nothing was repaired"])
    return TierResult("untouched", True)


def project_workflows(candidate: Path) -> list[Path]:
    """Every other `.xaml` in the candidate's project, which Studio compiles and publishes with it."""
    root = candidate.parent
    return sorted(
        p
        for p in root.rglob("*.xaml")
        if p != candidate and not any(part.startswith(".") for part in p.relative_to(root).parts[:-1])
    )


def _inspect(path: Path) -> tuple[dict | None, list[str]]:
    try:
        report = runner.inspect(path)
    except runner.RunnerMissingError as exc:
        return None, [f"runner unavailable: {exc}"]
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        return None, [f"runner failed: {exc}"]
    if report.get("loaded") and not report.get("errors"):
        return report, []
    lines = []
    for err in (report.get("errors") or [])[:6]:
        where = f" (line {err['line']})" if err.get("line") else ""
        lines.append(f"{err.get('message', err)}{where}")
    return report, lines or ["did not load"]


def t_compile(path: Path) -> tuple[TierResult, dict | None]:
    """Compile the candidate and every workflow it could invoke; activities are pooled for contract."""
    report, lines = _inspect(path)
    if report is None:
        return TierResult("compile", False, messages=lines), None
    for other in project_workflows(path):
        rel = other.relative_to(path.parent).as_posix()
        sub, sub_lines = _inspect(other)
        lines += [f"{rel}: {line}" for line in sub_lines]
        if sub is not None and not sub_lines:
            report.setdefault("activities", []).extend({**a, "file": rel} for a in sub.get("activities") or [])
            report.setdefault("workflows", {})[rel] = {"arguments": sub.get("arguments") or []}
    if lines:
        return TierResult("compile", False, messages=lines[:6]), report
    return TierResult("compile", True), report


def _project_messages(project_dir: Path, candidate: Path) -> list[str]:
    project_json = project_dir / "project.json"
    if not project_json.exists():
        return ["project.json is missing"]
    try:
        project = json.loads(project_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"project.json does not parse: {exc}"]
    problems = []
    if project.get("main") != candidate.name:
        problems.append(f"project.json main is {project.get('main')!r}, expected {candidate.name!r}")
    if project.get("targetFramework") != "Portable":
        problems.append(f"project.json targetFramework is {project.get('targetFramework')!r}, expected 'Portable'")
    if project.get("expressionLanguage") != "VisualBasic":
        problems.append(f"project.json expressionLanguage is {project.get('expressionLanguage')!r}")
    if "UiPath.System.Activities" not in (project.get("dependencies") or {}):
        problems.append("project.json no longer depends on UiPath.System.Activities")
    return problems


def _argument_messages(declared_list: list | None, wanted_list: list | None) -> list[str]:
    messages = []
    declared = {a["name"]: a for a in declared_list or []}
    wanted = {a["name"]: a for a in wanted_list or []}
    for name, arg in wanted.items():
        got = declared.get(name)
        if got is None:
            messages.append(f"argument {name} is not declared")
            continue
        if got["direction"] != arg["direction"] or got["type"] != arg["type"]:
            messages.append(
                f"argument {name} is {got['direction']} {got['type']}, expected {arg['direction']} {arg['type']}"
            )
    for name in sorted(set(declared) - set(wanted)):
        messages.append(f"argument {name} is not part of the contract")
    return messages


def t_contract(report: dict | None, spec: dict, candidate: Path) -> TierResult:
    """The interface the prompt fixed: arguments, required and forbidden activities, project.json."""
    contract = spec.get("contract") or {}
    messages = _project_messages(candidate.parent, candidate)
    if report is None or not report.get("loaded") or report.get("errors"):
        return TierResult("contract", False, messages=[*messages, "no compiled workflow to check"])

    messages += _argument_messages(report.get("arguments"), contract.get("arguments"))
    for workflow in contract.get("workflows") or []:
        got = (report.get("workflows") or {}).get(workflow["file"])
        if got is None:
            messages.append(f"{workflow['file']} is missing or did not compile")
            continue
        messages += [
            f"{workflow['file']}: {m}" for m in _argument_messages(got["arguments"], workflow.get("arguments"))
        ]

    activities = report.get("activities") or []
    types = {a["type"] for a in activities}
    for type_name in contract.get("required_activity_types") or []:
        if type_name not in types:
            messages.append(f"no {type_name} activity")
    forbidden = set(contract.get("forbidden_activity_types") or [])
    for act in activities:
        if act["type"] in forbidden:
            where = f" in {act['file']}" if act.get("file") else ""
            messages.append(f"{act['type']} is not allowed ({act['displayName']!r}{where})")

    return TierResult("contract", not messages, messages=messages)
