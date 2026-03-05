"""
Skill interruption harness for uipath-coded-agents.

Runs each SkillTestCase by invoking the `claude` CLI in non-interactive
(--print) mode with stream-json output, then measures:
  - interruption_count  : number of AskUserQuestion tool calls
  - skills_invoked      : ordered list of Skill tool calls (per turn and total)
  - per-turn token usage : input_tokens / output_tokens per assistant message
  - task_success        : all expected_files present in the temp workdir

Usage:
    python harness.py [--cases case_id,case_id] [--output results.json]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cases import ALL_CASES
from models import SkillEvalResult, SkillTestCase, TurnMetrics

REPO_ROOT = Path(__file__).parent.parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "uipath-coded-agents"

# Timeout per test case (seconds). Building a full agent can take a while.
CASE_TIMEOUT = 300


async def run_case(case: SkillTestCase, workdir: Path) -> SkillEvalResult:
    """
    Run a single test case and return its metrics.

    The claude CLI is invoked with:
      --print            non-interactive, exits when done
      --output-format stream-json   one JSON object per line on stdout
      --allowedTools all            allow the skill to use Bash/Write/Read/etc.
      -p <prompt>        the user's message
    """
    interruption_count = 0
    all_skills_invoked: list[str] = []
    turns: list[TurnMetrics] = []
    raw_lines: list[str] = []
    error_msg = ""

    # Track per-message state — each API call streams multiple events with the same
    # message ID (one per content block). We deduplicate by ID and flush when the ID changes.
    seen_message_id: str | None = None
    current_turn_interruption = False
    current_turn_skills: list[str] = []
    current_turn_input = 0
    current_turn_output = 0
    current_turn_cache_creation = 0
    current_turn_cache_read = 0
    turn_number = 0

    def flush_turn() -> None:
        nonlocal turn_number, current_turn_interruption, current_turn_skills
        nonlocal current_turn_input, current_turn_output
        nonlocal current_turn_cache_creation, current_turn_cache_read
        if seen_message_id is None:
            return
        turns.append(TurnMetrics(
            turn=turn_number,
            input_tokens=current_turn_input,
            output_tokens=current_turn_output,
            cache_creation_tokens=current_turn_cache_creation,
            cache_read_tokens=current_turn_cache_read,
            is_interruption=current_turn_interruption,
            skills_invoked=list(current_turn_skills),
        ))
        turn_number += 1
        current_turn_interruption = False
        current_turn_skills = []
        current_turn_input = 0
        current_turn_output = 0
        current_turn_cache_creation = 0
        current_turn_cache_read = 0

    try:
        # Strip CLAUDECODE so the subprocess isn't blocked as a nested session
        env = {k: v for k, v in __import__("os").environ.items() if k != "CLAUDECODE"}

        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--print",
            "--verbose",
            "--output-format", "stream-json",
            "--allowedTools", "all",
            "--dangerously-skip-permissions",
            "-p", case.prompt,
            cwd=str(workdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=CASE_TIMEOUT,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")

        if proc.returncode != 0 and not stdout.strip():
            error_msg = stderr.strip() or f"claude exited with code {proc.returncode}"

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            raw_lines.append(line)
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") != "assistant":
                continue

            message = event.get("message", {})
            msg_id = message.get("id")

            # New API response — flush the previous turn first
            if msg_id != seen_message_id:
                flush_turn()
                seen_message_id = msg_id
                usage = message.get("usage", {})
                current_turn_input = usage.get("input_tokens", 0)
                current_turn_output = usage.get("output_tokens", 0)
                current_turn_cache_creation = usage.get("cache_creation_input_tokens", 0)
                current_turn_cache_read = usage.get("cache_read_input_tokens", 0)

            for block in message.get("content", []):
                if block.get("type") != "tool_use":
                    continue
                name = block.get("name", "")
                if name == "AskUserQuestion":
                    interruption_count += 1
                    current_turn_interruption = True
                elif name == "Skill":
                    skill_name = block.get("input", {}).get("skill", "unknown")
                    current_turn_skills.append(skill_name)
                    all_skills_invoked.append(skill_name)

        flush_turn()  # flush the last turn

    except asyncio.TimeoutError:
        error_msg = f"Timed out after {CASE_TIMEOUT}s"
    except FileNotFoundError:
        error_msg = "'claude' CLI not found — is it installed and on PATH?"
    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc)

    # Check expected files — Claude may create a project subdirectory, so search
    # recursively for each filename anywhere under the workdir.
    all_files = {p.name for p in workdir.rglob("*") if p.is_file()}
    missing_files = [
        f for f in case.expected_files
        if Path(f).name not in all_files
    ]
    task_success = len(missing_files) == 0

    # Check required skills
    invoked_set = set(all_skills_invoked)
    missing_required_skills = [s for s in case.required_skills if s not in invoked_set]

    # Determine pass/fail
    failures: list[str] = []
    if error_msg:
        failures.append(f"run error: {error_msg}")
    if interruption_count > case.max_interruptions:
        failures.append(
            f"interruptions={interruption_count} exceeded max={case.max_interruptions}"
        )
    if missing_required_skills:
        failures.append(f"skills not invoked: {missing_required_skills}")
    if missing_files:
        failures.append(f"missing files: {missing_files}")

    return SkillEvalResult(
        case_id=case.id,
        skill=case.skill,
        description=case.description,
        interruption_count=interruption_count,
        max_interruptions=case.max_interruptions,
        skills_invoked=all_skills_invoked,
        required_skills=case.required_skills,
        missing_required_skills=missing_required_skills,
        expected_files=case.expected_files,
        missing_files=missing_files,
        task_success=task_success,
        total_input_tokens=sum(t.input_tokens for t in turns),
        total_output_tokens=sum(t.output_tokens for t in turns),
        turns=turns,
        passed=len(failures) == 0,
        failure_reason="; ".join(failures),
        raw_output="\n".join(raw_lines[-100:]),  # keep last 100 lines for debug
        error=error_msg,
    )


def result_to_dict(r: SkillEvalResult) -> dict:
    return {
        "case_id": r.case_id,
        "skill": r.skill,
        "description": r.description,
        "passed": r.passed,
        "failure_reason": r.failure_reason,
        "interruption_count": r.interruption_count,
        "max_interruptions": r.max_interruptions,
        "skills_invoked": r.skills_invoked,
        "required_skills": r.required_skills,
        "missing_required_skills": r.missing_required_skills,
        "task_success": r.task_success,
        "missing_files": r.missing_files,
        "total_input_tokens": r.total_input_tokens,
        "total_output_tokens": r.total_output_tokens,
        "turns": [
            {
                "turn": t.turn,
                "input_tokens": t.input_tokens,
                "cache_creation_tokens": t.cache_creation_tokens,
                "cache_read_tokens": t.cache_read_tokens,
                "output_tokens": t.output_tokens,
                "is_interruption": t.is_interruption,
                "skills_invoked": t.skills_invoked,
            }
            for t in r.turns
        ],
        "error": r.error,
    }


async def main(case_ids: list[str] | None, output_path: str) -> int:
    cases_to_run = ALL_CASES
    if case_ids:
        cases_to_run = [c for c in ALL_CASES if c.id in case_ids]
        unknown = set(case_ids) - {c.id for c in cases_to_run}
        if unknown:
            print(f"Unknown case IDs: {unknown}", file=sys.stderr)
            return 1

    print(f"Running {len(cases_to_run)} case(s)...\n")
    results: list[SkillEvalResult] = []

    for case in cases_to_run:
        print(f"  [{case.skill}] {case.id}")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = await run_case(case, Path(tmpdir))
        results.append(result)

        status = "PASS" if result.passed else "FAIL"
        tokens = f"{result.total_input_tokens}/{result.total_output_tokens} tok"
        skills = ", ".join(result.skills_invoked) or "-"
        print(
            f"    {status} | interruptions={result.interruption_count}/{result.max_interruptions}"
            f" | turns={len(result.turns)} | {tokens}"
            f" | skills=[{skills}]"
        )
        if not result.passed:
            print(f"    REASON: {result.failure_reason}")
        print()

    # Write JSON artifact
    payload = [result_to_dict(r) for r in results]
    Path(output_path).write_text(json.dumps(payload, indent=2))
    print(f"Results written to {output_path}")

    failed = [r for r in results if not r.passed]
    passed = len(results) - len(failed)
    print(f"\n{passed}/{len(results)} passed")

    if failed:
        print("\nFailed cases:")
        for r in failed:
            print(f"  - {r.case_id}: {r.failure_reason}")
        return 1

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill interruption eval harness")
    parser.add_argument(
        "--cases",
        help="Comma-separated list of case IDs to run (default: all)",
        default=None,
    )
    parser.add_argument(
        "--output",
        help="Path to write JSON results (default: skill-eval-results.json)",
        default="skill-eval-results.json",
    )
    args = parser.parse_args()

    case_ids = [c.strip() for c in args.cases.split(",")] if args.cases else None
    sys.exit(asyncio.run(main(case_ids, args.output)))
