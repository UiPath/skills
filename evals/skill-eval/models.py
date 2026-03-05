from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SkillTestCase:
    # Unique ID used in the results table and artifact
    id: str
    # Skill(s) primarily under test — used for grouping in the report
    skill: str
    # The full prompt sent to Claude as the first (and only) user message
    prompt: str
    # Maximum number of AskUserQuestion calls allowed for this case to pass
    max_interruptions: int
    # Skill invocations (Skill tool calls) that MUST appear somewhere in the transcript
    required_skills: list[str] = field(default_factory=list)
    # Files that must exist in the workdir after the run (relative paths)
    expected_files: list[str] = field(default_factory=list)
    # Human-readable description shown in the report
    description: str = ""


@dataclass
class TurnMetrics:
    turn: int
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    is_interruption: bool = False
    skills_invoked: list[str] = field(default_factory=list)


@dataclass
class SkillEvalResult:
    case_id: str
    skill: str
    description: str
    # Core metrics
    interruption_count: int
    max_interruptions: int
    skills_invoked: list[str]          # flattened, ordered
    required_skills: list[str]
    missing_required_skills: list[str]
    # File check
    expected_files: list[str]
    missing_files: list[str]
    task_success: bool                  # all expected_files present
    # Token metrics
    total_input_tokens: int
    total_output_tokens: int
    turns: list[TurnMetrics]
    # Overall
    passed: bool
    failure_reason: str                 # empty string if passed
    # Raw output for debugging
    raw_output: str = ""
    error: str = ""
