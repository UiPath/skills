"""Generate a uipath-diagnostics test scenario from a real session.

Two modes:
    --dry-run (default): print the plan; write nothing.
    --apply:             write the scenario folder.

The script never touches files outside the scenario output directory
unless `--output` is overridden.

Usage:
    python generate_scenario.py \
        --investigation <.investigation dir> \
        --project <uipath project dir> \
        --transcript <claude code jsonl> \
        [--resolution <RESOLUTION.md>] \
        [--scenario-name <slug>] \
        [--output <dir>] \
        [--scrub-map <json>] \
        [--apply]

Read tests/tasks/uipath-diagnostics/CLAUDE.md before invoking this.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

def _find_repo_root() -> Path:
    """Walk up from this file until we find the repo's `.git` marker."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    raise RuntimeError("Could not locate repo root (no .git ancestor found)")


REPO_ROOT = _find_repo_root()
EXTRACT_SCRIPT = Path(__file__).with_name("extract_session.py")
DEFAULT_OUTPUT_BASE = REPO_ROOT / "tests" / "tasks" / "uipath-diagnostics"

EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
WIN_PATH_RE = re.compile(r"\b[A-Z]:[\\/](?:[^\s\"'<>|]*)", re.IGNORECASE)

# Stdout from a redirect-captured call is just bash trailer noise: the
# tool returns "(Bash completed with no output)" or "EXIT_CODE=N" or
# similar. Treat any of these as "data lives in the redirect target file".
EMPTY_STDOUT_PATTERNS = (
    r"^\s*$",
    r"^\(Bash completed with no output\)\s*$",
    r"^EXIT_CODE=\d+\s*$",
    r"^Exit:\s*\d+\s*$",
    r"^Exit\s+code\s+\d+\s*$",
)
EMPTY_STDOUT_RE = re.compile("|".join(EMPTY_STDOUT_PATTERNS), re.IGNORECASE)


# ---------- text artifact templates ----------

TASK_YAML_TEMPLATE = """\
task_id: skill-diagnostics-{slug}
description: >
  Faithful replay of a real UiPath diagnostic investigation. The agent
  runs the uipath-diagnostics skill against a uip CLI mock whose
  responses are the verbatim sub-agent outputs from the real session.
  Success = the agent reaches the same root cause as RESOLUTION.md.
tags: [uipath-diagnostics, e2e, faithful-replay]

agent:
  type: claude-code
  allowed_tools: ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill", "Agent", "AskUserQuestion", "TodoWrite"]
  max_turns: 60
  turn_timeout: 1200

sandbox:
  driver: tempdir
  python: {{}}
  template_sources:
    - type: template_dir
      path: ../_shared/mock_template
{process_source_block}    - type: template_dir
      path: fixtures
  # Prepend ./mocks to the agent's PATH so bare `uip` resolves to the mock.
  mock_path_dirs: ["mocks"]

reference:
  file: RESOLUTION.md

initial_prompt: |
{initial_prompt_indented}

success_criteria:
  - type: skill_triggered
    description: "Agent invoked the uipath-diagnostics skill"
    skill_name: "uipath:uipath-diagnostics"
    expected: "yes"
    weight: 1.0

  - type: llm_judge
    description: "Agent matched the correct playbook AND reached the same conclusion as RESOLUTION.md"
    weight: 3.0
    pass_threshold: 0.7
    include_reference: true
    include_agent_output: true
    include_tool_calls: true
    files:
      - .investigation/state.json
      - .investigation/hypotheses.json
    prompt: |
      You are grading a UiPath diagnostic agent against a known-correct
      reference outcome (the attached RESOLUTION.md).

      DIMENSION A -- Correct playbook
        The matching playbook should appear in state.json's
        `matched_playbooks`. Acceptable: the agent also Reads
        neighboring playbooks during exploration.

      DIMENSION B -- Same conclusion as RESOLUTION.md
        The agent's final answer should converge on the same root cause
        and fix described in RESOLUTION.md. Evidence sources: state.json
        (`requirements`, `triage_summary`, scope/domain), hypotheses.json
        (the hypothesis flagged `is_root_cause: true`), and the agent's
        last text response.

      SCORING RUBRIC (single score):
        1.0  Both dimensions correct: right playbook AND same root cause.
        0.8  Both partially correct.
        0.5  Only one dimension correct.
        0.2  Recognized the surface but neither matched the playbook nor
             reached the conclusion.
        0.0  Misdiagnosed or got blocked.

      Return JSON: {{"score": <float>, "rationale": "<one sentence>"}}

max_iterations: 1
task_timeout: 2400

# Auto-answer the diagnostic skill's AskUserQuestion calls so the test runs
# end-to-end without a human. The simulator always picks the recommended /
# affirmative option, and never invents data — keeps the diagnostic flow
# faithful to the original session.
simulation:
  enabled: true
  persona: |
    You are the UiPath user who originally reported the failing process.
    You are waiting for the diagnostic agent to finish its investigation
    and trust its expertise. You only have the information you wrote in
    your initial report — no extra data.
  goal: |
    Let the agent complete its diagnostic flow without imposing
    constraints. Approve every scope expansion or clarification the
    agent requests so the investigation reaches the final resolution.
  constraints:
    - "If the agent asks whether to expand investigation scope (any new product domain such as ui-automation, integration-service, maestro, orchestrator), always answer Yes — pick the recommended / first / affirmative option."
    - "If the agent asks how to proceed when data is missing, tell it to proceed with best-effort findings using the evidence already gathered."
    - "Never invent or provide new factual data — you don't know any details beyond your initial report."
    - "Keep replies short (one sentence or pick a numbered option)."
    - "Never instruct the agent to stop, abort, or skip phases."
  max_turns: 6

llm_reviewer:
  enabled: false
"""


README_TEMPLATE = """\
# {scenario_title} — Faithful Replay

This scenario replays a real UiPath diagnostic investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session.

## What the original session uncovered

{summary}

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | frozen snapshot of the failing UiPath project |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session transcript |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-diagnostics` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`

## Re-running the extraction

If the source transcript or project changes, regenerate the scenario:

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \\
    --investigation <path> --project <path> --transcript <path> \\
    --scenario-name {slug} --apply
```
"""


# ---------- ignore patterns for project snapshot ----------

PROJECT_SNAPSHOT_IGNORE_DIRS = {
    ".investigation",
    ".objects",
    "bin",
    "obj",
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    ".vs",
    ".idea",
}
PROJECT_SNAPSHOT_IGNORE_SUFFIXES = {".pyc", ".pdb"}


# ---------- helpers ----------


def _slugify(text: str) -> str:
    out = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return out or "diagnostic-scenario"


def _backfill_redirect_stdouts(uip_calls: list[dict], investigation: Path) -> dict:
    """For calls with empty stdout and a redirect target, load the file.

    Tries:
      1. The exact `redirect_target` path if it exists on disk.
      2. The basename matched anywhere under `investigation` (rglob).

    Returns counts: {"backfilled": N, "missing": M, "skipped": K}.
    """
    by_basename: dict[str, Path] = {}
    if investigation.is_dir():
        for p in investigation.rglob("*"):
            if p.is_file():
                by_basename.setdefault(p.name, p)

    backfilled = missing = skipped = 0
    for call in uip_calls:
        stdout = call.get("stdout") or ""
        if not _is_empty_stdout(stdout):
            skipped += 1
            continue
        target = call.get("redirect_target")
        if not target:
            skipped += 1
            continue
        target_path = Path(target)
        loaded: str | None = None
        if target_path.is_file():
            try:
                loaded = target_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                loaded = None
        if loaded is None:
            mapped = by_basename.get(target_path.name)
            if mapped is not None:
                try:
                    loaded = mapped.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    loaded = None
        if loaded is not None:
            call["stdout"] = loaded
            call["_backfilled_from"] = str(target_path) if target_path.is_file() else str(by_basename.get(target_path.name))
            backfilled += 1
        else:
            missing += 1
    return {"backfilled": backfilled, "missing": missing, "skipped": skipped}


def _is_empty_stdout(stdout: str) -> bool:
    """True if `stdout` is just bash-trailer noise (no real content)."""
    if not stdout.strip():
        return True
    # If every non-empty line matches a trailer pattern, treat as empty.
    lines = [l for l in stdout.splitlines() if l.strip()]
    if not lines:
        return True
    return all(EMPTY_STDOUT_RE.fullmatch(l.strip()) for l in lines)


def _run_extract(transcript: Path) -> dict:
    """Invoke extract_session.py as a subprocess and return its parsed JSON."""
    proc = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT), str(transcript)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"extract_session.py failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _detect_scrub_map(samples: list[str]) -> "OrderedDict[str, str]":
    """Auto-detect emails and personal Windows paths across all sampled text.

    Returns an ordered map of {real_value: placeholder}. Email detection
    assigns the first distinct email seen to `original_email@test.com`
    and the second to `replacement_email@test.com`; further emails get
    numeric suffixes. Windows paths are replaced with the empty string
    so `D:/Process/X/foo.json` becomes `foo.json` (the caller may need
    to retype these as relative paths during review).
    """
    mapping: "OrderedDict[str, str]" = OrderedDict()
    seen_emails: list[str] = []
    seen_names: set[str] = set()

    placeholders = ["original_email@test.com", "replacement_email@test.com"]

    for text in samples:
        if not isinstance(text, str):
            continue
        for m in EMAIL_RE.finditer(text):
            full = m.group(0)
            if full in mapping or full in placeholders:
                continue
            if full not in seen_emails:
                seen_emails.append(full)
            idx = seen_emails.index(full)
            placeholder = (
                placeholders[idx] if idx < len(placeholders) else f"user{idx + 1}@test.com"
            )
            mapping[full] = placeholder
            # Also map the bare local-part if it has structure (looks like a real name).
            local = m.group(1)
            if "." in local and local not in seen_names:
                seen_names.add(local)
                mapping[local] = f"user{idx + 1}"
        for m in WIN_PATH_RE.finditer(text):
            raw = m.group(0).rstrip("\\/")
            if raw and raw not in mapping:
                mapping[raw] = ""

    return mapping


def _apply_scrub(text: str, mapping: "OrderedDict[str, str]") -> str:
    if not isinstance(text, str):
        return text
    out = text
    # Apply longer keys first so substring overlaps don't mangle.
    for key in sorted(mapping.keys(), key=len, reverse=True):
        out = out.replace(key, mapping[key])
    return out


def _scrub_path(path: Path, mapping: "OrderedDict[str, str]") -> Path:
    """Apply scrub mapping to each path component (filenames containing real emails)."""
    parts = list(path.parts)
    new_parts = [_apply_scrub(p, mapping) for p in parts]
    return Path(*new_parts) if new_parts else path


def _build_manifest_rules(uip_calls: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """One rule per unique `args`. Returns (rules, fixture_filename_by_args).

    Fixture filenames are derived from a slug of the args. When two distinct
    args slug-collide (rare), a numeric suffix is appended.
    """
    rules: list[dict] = []
    fixture_by_args: dict[str, str] = {}
    used_filenames: set[str] = set()

    for call in uip_calls:
        args = call["args"]
        if args in fixture_by_args:
            continue
        slug = _slugify(args)[:60] or "call"
        candidate = f"{slug}.json"
        n = 2
        while candidate in used_filenames:
            candidate = f"{slug}-{n}.json"
            n += 1
        used_filenames.add(candidate)
        fixture_by_args[args] = candidate
        rule = {"match": args, "file": candidate}
        if call.get("exit_code") not in (None, 0):
            rule["exit_code"] = call["exit_code"]
        rules.append(rule)
    return rules, fixture_by_args


def _snapshot_project(
    src: Path, dst: Path, mapping: "OrderedDict[str, str] | None" = None
) -> list[tuple[Path, str | bytes]]:
    """Walk `src` and prepare an in-memory list of (relative_dst_path, content).

    Text files (.json, .xaml, .md, .py, .yaml, .yml, .txt, .uipath, .config,
    .nuspec, .csproj, .uiproj) get scrubbed when `mapping` is non-empty.
    Pass `None` or an empty mapping to skip scrub (e.g., during the
    sample-collection pass before the scrub map has been computed).
    Other files copied as bytes. Returns list of (path_relative_to_dst,
    content). Caller writes them.
    """
    apply_scrub = bool(mapping)
    text_suffixes = {
        ".json",
        ".xaml",
        ".md",
        ".py",
        ".yaml",
        ".yml",
        ".txt",
        ".uipath",
        ".config",
        ".nuspec",
        ".csproj",
        ".uiproj",
        ".cs",
    }
    plan: list[tuple[Path, str | bytes]] = []
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        # Skip ignored directories anywhere in the path.
        if any(part in PROJECT_SNAPSHOT_IGNORE_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() in PROJECT_SNAPSHOT_IGNORE_SUFFIXES:
            continue
        scrubbed_rel = _scrub_path(rel, mapping) if apply_scrub else rel
        if p.suffix.lower() in text_suffixes:
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                plan.append((scrubbed_rel, p.read_bytes()))
                continue
            content = _apply_scrub(text, mapping) if apply_scrub else text
            plan.append((scrubbed_rel, content))
        else:
            plan.append((scrubbed_rel, p.read_bytes()))
    return plan


def _format_initial_prompt(extracted: dict, scenario_name: str) -> str:
    """Indented YAML block for task.yaml's initial_prompt field.

    Uses the user's first message from the transcript if available;
    otherwise emits a generic prompt that the contributor must edit.
    """
    body = (extracted.get("user_initial_prompt") or "").strip()
    if not body:
        body = (
            "This process is failing. Diagnose it using the uipath-diagnostics skill.\n"
            f"(Generated for scenario {scenario_name} — review and customize.)"
        )
    return "\n".join("  " + line for line in body.splitlines())


def _build_resolution_md(extracted: dict, resolution_arg: Path | None) -> str:
    if resolution_arg is not None:
        return resolution_arg.read_text(encoding="utf-8")
    text = extracted.get("presenter_output") or ""
    if not text:
        return (
            "# Final Resolution\n\n"
            "_Generator could not extract a presenter output from the transcript._\n"
            "_Fill this in manually before running the test — the LLM judge depends on it._\n"
        )
    if not text.lstrip().startswith("#"):
        text = "# Final Resolution\n\n" + text.lstrip()
    return text.rstrip() + "\n"


def _build_readme_md(scenario_name: str, summary: str) -> str:
    return README_TEMPLATE.format(
        scenario_title=scenario_name.replace("-", " ").title(),
        slug=scenario_name,
        summary=summary or "_Add a 1–3 sentence summary of the original investigation here._",
    )


def _build_task_yaml(
    scenario_name: str, initial_prompt_indented: str, has_project: bool
) -> str:
    process_source_block = (
        "    - type: template_dir\n      path: process\n" if has_project else ""
    )
    return TASK_YAML_TEMPLATE.format(
        slug=scenario_name,
        initial_prompt_indented=initial_prompt_indented,
        process_source_block=process_source_block,
    )


# ---------- main pipeline ----------


def plan_scenario(args: argparse.Namespace) -> dict:
    """Build the in-memory plan. Pure: no file writes."""
    transcript = Path(args.transcript)
    investigation = Path(args.investigation)
    project = Path(args.project) if args.project else None
    if not transcript.exists():
        raise FileNotFoundError(f"transcript not found: {transcript}")
    if not investigation.is_dir():
        raise FileNotFoundError(f"investigation not found: {investigation}")
    if project is not None and not project.is_dir():
        raise FileNotFoundError(f"project not found: {project}")

    extracted = _run_extract(transcript)
    scenario_name = args.scenario_name or extracted.get("inferred_scenario_name") or "diagnostic-scenario"
    scenario_name = _slugify(scenario_name)

    # Backfill empty stdouts from the investigation's saved files. The
    # original session redirected `uip ... > some/raw/file.json`, leaving
    # an empty bash stdout — the real data lives on disk.
    backfill_stats = _backfill_redirect_stdouts(extracted["uip_calls"], investigation)

    # Build manifest + fixtures.
    rules, fixture_by_args = _build_manifest_rules(extracted["uip_calls"])
    fixtures: dict[str, str] = {}
    for call in extracted["uip_calls"]:
        fname = fixture_by_args[call["args"]]
        # Last write wins — for duplicate args, we keep the last response,
        # but in practice the manifest only references args once.
        fixtures[fname] = call["stdout"]

    # Build resolution.
    resolution_md = _build_resolution_md(
        extracted, Path(args.resolution) if args.resolution else None
    )

    # Build readme.
    summary = (extracted.get("presenter_output") or "").splitlines()
    summary_oneline = next((s.strip() for s in summary if s.strip().startswith("**")), "") or (
        summary[0].strip() if summary else ""
    )
    readme_md = _build_readme_md(scenario_name, summary_oneline)

    # Build task.yaml.
    initial_prompt_indented = _format_initial_prompt(extracted, scenario_name)
    task_yaml = _build_task_yaml(
        scenario_name, initial_prompt_indented, has_project=project is not None
    )

    # Aggregate sample text for scrub detection.
    samples = [resolution_md, readme_md, task_yaml]
    samples.extend(fixtures.values())
    samples.extend(rule["match"] for rule in rules)

    # Snapshot the project (raw — scrub happens after we compute the map).
    if project is not None:
        project_plan = _snapshot_project(project, Path("process"), mapping=None)
        for rel, content in project_plan:
            if isinstance(content, str):
                samples.append(content)
    else:
        project_plan = []

    if args.scrub_map:
        scrub_map = OrderedDict(json.loads(Path(args.scrub_map).read_text(encoding="utf-8")))
    else:
        scrub_map = _detect_scrub_map(samples)

    # Apply scrub to all text content.
    resolution_md = _apply_scrub(resolution_md, scrub_map)
    readme_md = _apply_scrub(readme_md, scrub_map)
    task_yaml = _apply_scrub(task_yaml, scrub_map)
    fixtures = {fn: _apply_scrub(c, scrub_map) for fn, c in fixtures.items()}
    rules = [{**r, "match": _apply_scrub(r["match"], scrub_map)} for r in rules]
    project_plan_scrubbed: list[tuple[Path, str | bytes]] = []
    for rel, content in project_plan:
        rel_scrubbed = _scrub_path(rel, scrub_map)
        if isinstance(content, str):
            project_plan_scrubbed.append((rel_scrubbed, _apply_scrub(content, scrub_map)))
        else:
            project_plan_scrubbed.append((rel_scrubbed, content))

    out_base = Path(args.output) if args.output else (DEFAULT_OUTPUT_BASE / scenario_name)

    return {
        "scenario_name": scenario_name,
        "output_dir": out_base,
        "extracted_diagnostics": extracted["diagnostics"],
        "backfill_stats": backfill_stats,
        "scrub_map": scrub_map,
        "manifest": {
            "version": 2,
            "_doc": "Auto-generated by generate_scenario.py — review fixtures + add expected_calls.",
            "rules": rules,
            "unmocked_default": {
                "response": "[]\n",
                "exit_code": 0,
                "_doc": "Permissive fallback: any uip command not matched by `rules` returns an empty array. Lets the agent explore beyond the recorded path without aborting.",
            },
        },
        "fixtures": fixtures,
        "resolution_md": resolution_md,
        "readme_md": readme_md,
        "task_yaml": task_yaml,
        "project_files": project_plan_scrubbed,
    }


def render_dry_run(plan: dict) -> str:
    out: list[str] = []
    out.append(f"Scenario: {plan['scenario_name']}")
    out.append(f"Output:   {plan['output_dir']}")
    out.append("")
    out.append("Extracted from transcript:")
    diag = plan["extracted_diagnostics"]
    out.append(f"  uip calls:     {diag['uip_calls_total']}")
    out.append(f"  unmatched:     {diag['uip_calls_unmatched']}")
    out.append(f"  lines parsed:  {diag['transcript_lines']}")
    bf = plan["backfill_stats"]
    out.append(
        f"  redirect backfill: {bf['backfilled']} loaded, {bf['missing']} missing, {bf['skipped']} skipped"
    )
    out.append("")
    out.append("Scrub map (review carefully):")
    if not plan["scrub_map"]:
        out.append("  (none detected)")
    else:
        for k, v in plan["scrub_map"].items():
            out.append(f"  {k!r:<60s} -> {v!r}")
    out.append("")
    out.append(f"Manifest rules: {len(plan['manifest']['rules'])}")
    for r in plan["manifest"]["rules"][:20]:
        suffix = f" exit={r['exit_code']}" if "exit_code" in r else ""
        out.append(f"  - {r['match']!r:<60s} -> {r['file']}{suffix}")
    if len(plan["manifest"]["rules"]) > 20:
        out.append(f"  ... +{len(plan['manifest']['rules']) - 20} more")
    out.append("")
    out.append(f"Project snapshot: {len(plan['project_files'])} files")
    out.append("")
    out.append("Files that would be written:")
    base = plan["output_dir"]
    out.append(f"  {base / 'task.yaml'}                             ({len(plan['task_yaml'])} bytes)")
    out.append(f"  {base / 'README.md'}                             ({len(plan['readme_md'])} bytes)")
    out.append(f"  {base / 'RESOLUTION.md'}                         ({len(plan['resolution_md'])} bytes)")
    out.append(f"  {base / 'fixtures' / 'mocks' / 'responses' / 'manifest.json'}")
    out.append(f"  {base / 'fixtures' / 'mocks' / 'responses' / '<rule>.json'} x {len(plan['fixtures'])}")
    out.append(f"  {base / 'process' / '<files>'} x {len(plan['project_files'])}")
    out.append("")
    out.append("(dry-run — no files written. Pass --apply to write.)")
    return "\n".join(out)


def apply_plan(plan: dict) -> None:
    base: Path = plan["output_dir"]
    if base.exists() and any(base.iterdir()):
        raise FileExistsError(
            f"output dir is not empty: {base}. Move it aside or pick a new --scenario-name."
        )
    base.mkdir(parents=True, exist_ok=True)

    (base / "task.yaml").write_text(plan["task_yaml"], encoding="utf-8")
    (base / "README.md").write_text(plan["readme_md"], encoding="utf-8")
    (base / "RESOLUTION.md").write_text(plan["resolution_md"], encoding="utf-8")

    fixtures_dir = base / "fixtures" / "mocks" / "responses"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    (fixtures_dir / "manifest.json").write_text(
        json.dumps(plan["manifest"], indent=2) + "\n", encoding="utf-8"
    )
    for fname, content in plan["fixtures"].items():
        (fixtures_dir / fname).write_text(content, encoding="utf-8")

    process_dir = base / "process"
    for rel, content in plan["project_files"]:
        target = process_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--investigation", required=True)
    parser.add_argument("--project", default=None, help="Optional. UiPath project dir to snapshot into process/.")
    parser.add_argument("--transcript", required=True, help="JSONL file or directory containing main + subagent transcripts.")
    parser.add_argument("--resolution", default=None)
    parser.add_argument("--scenario-name", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--scrub-map", default=None)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the scenario folder to disk. Without this flag the script previews and writes nothing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without writing (default behavior; flag is for explicitness).",
    )
    args = parser.parse_args(argv[1:])

    if args.apply and args.dry_run:
        print("--apply and --dry-run are mutually exclusive", file=sys.stderr)
        return 2

    plan = plan_scenario(args)

    if args.apply:
        apply_plan(plan)
        print(f"Wrote scenario: {plan['output_dir']}")
        return 0

    print(render_dry_run(plan))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
