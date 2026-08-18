#!/usr/bin/env python3
"""Validate every uipath-troubleshoot scenario task YAML against the suite contract.

The troubleshoot suite is ~300 near-identical faithful-replay scenarios grown
from one generator template. Nothing stopped a scenario (or the generator) from
drifting out of the shared shape, and a drifted simulation block is expensive
rather than loud: the 2026-07-28 nightly spent 126 extra minutes because 39
scenarios let the simulated user approve fix application, sending runs into an
edit + validate/build/pack loop that no criterion grades.

The contract lives in ``tests/contracts/troubleshoot-scenario-contract.yaml``
(required simulation constraints, required/forbidden criteria types, canonical
llm_judge shape, structural keys). This script enforces it against every
scenario AND against the generator template, so the two cannot diverge.

Usage:
    python3 scripts/check-troubleshoot-tasks.py                    # default suite root
    python3 scripts/check-troubleshoot-tasks.py <path> ...         # scan given roots/files

Exit codes:
    0 - every scenario and the generator template satisfy the contract
    1 - one or more violations (paths + fix hints printed, annotated in CI)
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITE_ROOT = REPO_ROOT / "tests" / "tasks" / "uipath-troubleshoot"
CONTRACT_PATH = REPO_ROOT / "tests" / "contracts" / "troubleshoot-scenario-contract.yaml"

# What each required llm_judge flag buys, quoted back to the author on failure.
JUDGE_FLAG_HINTS = {
    "include_reference": "the judge grades against RESOLUTION.md",
    "include_agent_output": "the judge needs the agent's final response",
    "include_dialog": (
        "without it the judge sees only the final turn, which is usually an "
        "acknowledgement, and scores a correct investigation 0.00"
    ),
}

# Dummy substitutions that render the generator's TASK_YAML_TEMPLATE into a
# parseable scenario. Values only need to keep the YAML valid.
TEMPLATE_FILLERS = {
    "slug": "placeholder",
    "domain_tags": "rpa, ",
    "shared_prefix": "../../",
    "process_source_block": "",
    "initial_prompt_indented": "  Placeholder prompt.",
}


class Violation:
    def __init__(self, path: Path, line: int, message: str, hint: str) -> None:
        self.path = path
        self.line = line
        self.message = message
        self.hint = hint


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        # Still POSIX: the GitHub annotation format requires forward slashes.
        return path.as_posix()


def _line_of(text: str, patterns: str | list[str], section: str | None = None) -> int:
    """1-indexed line for an annotation, or 0 when nothing matches.

    `patterns` is tried in order, so a specific anchor beats a generic fallback -
    a single alternated regex cannot do this, because a top-down line scan
    returns whichever alternative appears first in the file.

    `section` restricts the search to lines at or after that anchor, so
    `max_turns:` under `simulation:` is not reported at the `run_limits:` one.
    """
    lines = text.splitlines()
    start = 0
    if section:
        rx = re.compile(section)
        start = next((n for n, line in enumerate(lines) if rx.search(line)), 0)
    for pattern in [patterns] if isinstance(patterns, str) else patterns:
        rx = re.compile(pattern)
        for offset, line in enumerate(lines[start:]):
            if rx.search(line):
                return start + offset + 1
    return 0


def _iter_scenarios(args: list[str], exempt: list[str]) -> list[Path]:
    roots = [Path(a) for a in args] if args else [SUITE_ROOT]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("task.yaml")))
    exempt_suffixes = tuple(e.replace("\\", "/") for e in exempt)
    return [f for f in files if not _rel(f).endswith(exempt_suffixes)]


def _criteria(doc: dict, ctype: str) -> list[dict]:
    """EVERY criterion of `ctype`. Validating only the first lets a duplicate
    carrying a violation ride along unchecked."""
    return [
        c
        for c in doc.get("success_criteria") or []
        if isinstance(c, dict) and c.get("type") == ctype
    ]


def _check(doc: dict, text: str, path: Path, contract: dict, locate: bool = True) -> list[Violation]:
    """Validate one parsed scenario against the contract.

    `locate=False` suppresses line lookup: for the rendered generator template,
    a line number would refer to the rendered YAML while the annotation points at
    the .py file, so no number is better than a wrong one.
    """
    out: list[Violation] = []

    def fail(pattern: str | list[str], message: str, hint: str, section: str | None = None) -> None:
        line = _line_of(text, pattern, section) if locate else 0
        out.append(Violation(path, line, message, hint))

    # --- simulation ---------------------------------------------------------
    sim = doc.get("simulation")
    if not isinstance(sim, dict):
        fail(r"^task_id:", "no `simulation:` block", "Add the simulation block from the generator template.")
        sim = {}
    else:
        if sim.get("enabled") is not True:
            fail(r"^simulation:", "`simulation.enabled` is not true", "Set `enabled: true`.")
        mt = sim.get("max_turns")
        # bool is an int subclass: YAML `max_turns: true` would otherwise pass as 1.
        if not (isinstance(mt, int) and not isinstance(mt, bool) and mt > 0):
            fail([r"max_turns:", r"^simulation:"], f"`simulation.max_turns` must be a positive int (found {mt!r})", "Set `max_turns: 6`.", section=r"^simulation:")

    constraints = sim.get("constraints")
    if not isinstance(constraints, list) or not constraints:
        fail(r"^simulation:", "`simulation.constraints` is missing or empty", "Copy the constraints list from the generator template.")
        constraints = []
    joined = "\n".join(str(c) for c in constraints)
    for req in contract["simulation"]["required_constraints"]:
        if req["contains"] not in joined:
            fail(
                r"constraints:",
                f"missing required simulation constraint '{req['id']}'",
                f"Add a constraint containing: {req['contains']!r}\n    Why: {' '.join(req['why'].split())}",
            )

    # --- success_criteria ---------------------------------------------------
    crit = doc.get("success_criteria")
    if not isinstance(crit, list) or not crit:
        fail(r"^task_id:", "no `success_criteria`", "Add the skill_triggered + llm_judge criteria.")
        crit = []
    sc = contract["success_criteria"]
    # A non-mapping entry must be its own violation: silently dropping it here
    # would bypass the type whitelist below.
    for entry in crit:
        if not isinstance(entry, dict):
            fail(r"success_criteria:", f"success_criteria entry is not a mapping (found {entry!r})", "Each criterion is a mapping with a `type` key.")
    types = [c.get("type") for c in crit if isinstance(c, dict)]

    for req in sc["required_types"]:
        count = types.count(req)
        if count == 0:
            fail(r"success_criteria:", f"missing required criterion `type: {req}`", f"Add the canonical `{req}` criterion.")
        elif count > 1:
            fail(
                rf"type:\s*{req}",
                f"criterion `type: {req}` appears {count} times, must appear exactly once",
                "Every copy is graded by the harness. Delete the duplicate - keep one canonical criterion.",
            )
    for extra in dict.fromkeys(t for t in types if t not in sc["allowed_types"]):
        if extra in sc["forbidden_types"]:
            hint = (
                "Scenarios grade the presented diagnosis, not the investigation path.\n"
                "    Move the requirement into RESOLUTION.md and let the judge grade it."
            )
        else:
            hint = (
                f"`{extra}` is not in the contract's allowed_types. Add it there with a\n"
                "    rationale if it genuinely belongs, or move the requirement into RESOLUTION.md."
            )
        fail(rf"type:\s*{extra}", f"criterion `type: {extra}` is not allowed", hint)

    for st in _criteria(doc, "skill_triggered"):
        # BOTH fields: the harness detects engagement of skill_name and expects
        # it iff skill_name == expected_skill, so a drifted skill_name flips the
        # criterion into a negative row that passes without the skill running.
        for key, want in sc["skill_triggered"].items():
            if st.get(key) != want:
                fail(
                    [rf"{key}:", r"type:\s*skill_triggered"],
                    f"`skill_triggered.{key}` must be {want!r} (found {st.get(key)!r})",
                    f'Set `{key}: "{want}"` - the criterion asserts the skill ran only when skill_name and expected_skill both name it.',
                )

    jc = sc["llm_judge"]
    for judge in _criteria(doc, "llm_judge"):
        for key in jc["require_true"]:
            if judge.get(key) is not True:
                # A missing key has no line of its own - anchor on the criterion.
                fail([rf"^\s+{key}:", r"-\s*type:\s*llm_judge"], f"`llm_judge.{key}` must be true", f"Set `{key}: true` - {JUDGE_FLAG_HINTS.get(key, 'required by the contract')}.", section=r"-\s*type:\s*llm_judge")
        for key in jc["forbidden_keys"]:
            # Presence, not truthiness: `files: []` and `files: null` are still
            # the forbidden key.
            if key in judge:
                fail(rf"^\s+{key}:", f"`llm_judge.{key}` is forbidden", "The judge grades the presented diagnosis, not internal artifacts.", section=r"-\s*type:\s*llm_judge")
        for key in ("weight", "pass_threshold"):
            if judge.get(key) != jc[key]:
                fail([rf"^\s+{key}:", r"-\s*type:\s*llm_judge"], f"`llm_judge.{key}` must be {jc[key]} (found {judge.get(key)!r})", f"Set `{key}: {jc[key]}` - the judge shape is uniform across the suite.", section=r"-\s*type:\s*llm_judge")

    # --- structure ----------------------------------------------------------
    stc = contract["structure"]
    tags = doc.get("tags") or []
    if not isinstance(tags, list):
        # A scalar would satisfy the membership test below by substring.
        fail(r"^tags:", f"`tags` must be a list (found {type(tags).__name__})", "Use `tags: [uipath-troubleshoot, ...]`.")
        tags = []
    for tag in stc["required_tags"]:
        if tag not in tags:
            fail(r"^tags:", f"missing required tag `{tag}`", f"Add `{tag}` to tags.")

    ref = doc.get("reference")
    ref_file = ref.get("file") if isinstance(ref, dict) else None
    if ref_file != stc["reference_file"]:
        fail([r"^reference:", r"^task_id:"], f"`reference.file` must be {stc['reference_file']!r} (found {ref_file!r})", f"Point `reference.file` at {stc['reference_file']} - the judge reads it.")

    sandbox = doc.get("sandbox")
    mpd = sandbox.get("mock_path_dirs") if isinstance(sandbox, dict) else None
    if mpd != stc["mock_path_dirs"]:
        fail([r"mock_path_dirs:", r"^sandbox:"], f"`sandbox.mock_path_dirs` must be {stc['mock_path_dirs']} (found {mpd!r})", "Without it bare `uip` resolves to the real CLI and the run tries to authenticate.")

    if stc["require_run_limits"] and not isinstance(doc.get("run_limits"), dict):
        fail(r"^task_id:", "no `run_limits:` block", "Add run_limits (task_timeout / max_turns / turn_timeout).")

    # --- pre_run --------------------------------------------------------------
    steps = doc.get("pre_run")
    steps = [s for s in steps if isinstance(s, dict)] if isinstance(steps, list) else []
    for req in contract["pre_run"]["required_steps"]:
        matches = [s for s in steps if s.get("command") == req["command"]]
        if not matches:
            fail(
                [r"^pre_run:", r"^task_id:"],
                f"missing required pre_run step '{req['id']}' (`command: \"{req['command']}\"`)",
                f"Add the step from the generator template.\n    Why: {' '.join(req['why'].split())}",
            )
        for step in matches:
            # EVERY copy of the step must abort on failure, like the duplicate
            # criteria above: one compliant copy does not neutralize a second
            # that fails open.
            if req.get("fail_on_error") and step.get("fail_on_error") is not True:
                fail(
                    [r"fail_on_error:", r"command:", r"^pre_run:"],
                    f"pre_run step '{req['id']}' must set `fail_on_error: true` (found {step.get('fail_on_error')!r})",
                    "A seal that fails silently restores the fixture leak - the task must abort instead.",
                    section=r"^pre_run:",
                )

    return out


def _render_generator_template(contract: dict) -> tuple[str, Path] | Violation:
    """Render the generator's task template so it can be validated as a scenario.

    Returns a Violation rather than None when the template cannot be reached:
    an unreachable template silently disables half of this gate, and a rename or
    refactor must fail the build instead of quietly narrowing the scan.
    """
    gt = contract.get("generator_template") or {}
    path = REPO_ROOT / gt["path"]
    symbol = gt["symbol"]
    hint = (
        f"The contract points `generator_template` at {gt['path']}:{symbol}.\n"
        "    Update the contract if the generator moved, or keep the template a plain\n"
        "    string literal - the generator must stay contract-validated."
    )
    if not path.is_file():
        return Violation(path, 0, f"generator template file not found: {gt['path']}", hint)

    source = path.read_text(encoding="utf-8")
    # AST, not regex + exec: robust to indentation, string prefixes and rebinding,
    # and it never executes generator code.
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Violation(path, exc.lineno or 0, f"generator is not parseable Python: {exc.msg}", hint)

    node = next(
        (
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Assign)
            and any(getattr(t, "id", None) == symbol for t in n.targets)
        ),
        None,
    )
    if node is None:
        return Violation(path, 0, f"could not find assignment `{symbol}` in the generator", hint)
    try:
        template = ast.literal_eval(node)
    except ValueError:
        return Violation(
            path,
            getattr(node, "lineno", 0),
            f"`{symbol}` is not a plain string literal, so the template cannot be rendered",
            hint,
        )
    if not isinstance(template, str):
        return Violation(path, getattr(node, "lineno", 0), f"`{symbol}` is not a string", hint)

    try:
        return template.format(**TEMPLATE_FILLERS), path
    except KeyError as exc:
        return Violation(
            path,
            getattr(node, "lineno", 0),
            f"template placeholder {exc} has no filler",
            "Add it to TEMPLATE_FILLERS in scripts/check-troubleshoot-tasks.py.",
        )


def main(argv: list[str]) -> int:
    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    violations: list[Violation] = []

    scenarios = _iter_scenarios(argv, contract.get("exempt") or [])
    if not scenarios:
        # A gate that scans nothing reports OK, so an empty result must fail:
        # one folder move or path typo would otherwise turn a ~300-scenario
        # required check into a green no-op.
        target = " ".join(argv) if argv else _rel(SUITE_ROOT)
        print(f"FAIL - found no scenario task.yaml under {target} - the gate is scanning nothing.")
        print("  Fix: check the path. If the suite moved, update SUITE_ROOT in this script.")
        print(f"::error file={_rel(Path(__file__))},line=0::gate scanned 0 scenarios")
        return 1

    for path in scenarios:
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            violations.append(Violation(path, 0, f"invalid YAML: {exc.__class__.__name__}", "Fix the YAML syntax."))
            continue
        if not isinstance(doc, dict):
            violations.append(Violation(path, 0, "task YAML is not a mapping", "Fix the file structure."))
            continue
        violations.extend(_check(doc, text, path, contract))

    checked_template = False
    rendered = _render_generator_template(contract)
    if isinstance(rendered, Violation):
        violations.append(rendered)
    else:
        text, gen_path = rendered
        try:
            doc = yaml.safe_load(text)
            checked_template = True
            violations.extend(_check(doc, text, gen_path, contract, locate=False))
        except yaml.YAMLError as exc:
            violations.append(
                Violation(gen_path, 0, f"generator template does not render to valid YAML: {exc.__class__.__name__}", "Fix the template or update TEMPLATE_FILLERS in this script.")
            )

    scope = f"{len(scenarios)} scenario(s)" + (" + the generator template" if checked_template else "")
    if not violations:
        print(f"OK - {scope} satisfy the troubleshoot scenario contract.")
        return 0

    print(f"FAIL - {len(violations)} contract violation(s) across {scope}:\n")
    for v in violations:
        rel = _rel(v.path)
        loc = f"{rel}:{v.line}" if v.line else rel
        # GitHub annotations are 1-based; omit the key rather than emit line=0.
        anchor = f",line={v.line}" if v.line else ""
        print(f"::error file={rel}{anchor}::{v.message}")
        print(f"  {loc}\n    {v.message}\n    Fix: {v.hint}")
    print(f"\nContract: {_rel(CONTRACT_PATH)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
