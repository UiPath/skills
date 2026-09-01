#!/usr/bin/env python3
"""Check the procurement SLA design and plan regression contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def read_required(path: Path) -> str:
    if not path.is_file():
        fail(f"missing {path}")
    return path.read_text(encoding="utf-8")


def has_near(text: str, left: str, right: str, distance: int = 500) -> bool:
    return re.search(
        rf"{re.escape(left)}.{{0,{distance}}}{re.escape(right)}",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ) is not None


def task_section(plan: str, task_name: str, stage_name: str | None = None) -> str:
    heading = (
        # Accepts the compact plan title (`T21: task "Name"`) AND the canonical
        # full-form build title (`T21: Add <type> task "Name" to "Stage"`).
        rf"^#{{2,3}}\s+T\d+(?:\.\d+)?\s*(?:[:—-])\s*"
        rf"(?:[^\"\n]*?\btask\s+)?(?:Task:\s*)?(?:\"{re.escape(task_name)}\"|{re.escape(task_name)}\b)[^\n]*\n"
    )
    next_heading = rf"^#{{2,3}}\s+T\d+(?:\.\d+)?\s*(?:[:—-])"
    matches = list(re.finditer(
        rf"(?ims){heading}.*?(?={next_heading}|\Z)",
        plan,
    ))
    if stage_name is not None:
        matches = [
            match
            for match in matches
            if re.search(
                rf'(?im)^[-*]?\s*stage:\s*["`]?{re.escape(stage_name)}["`]?\s*$',
                match.group(0),
            )
        ]
    if not matches:
        location = f" in stage {stage_name!r}" if stage_name else ""
        fail(f"missing tasks.md T-entry for {task_name!r}{location}")
    if len(matches) > 1:
        location = f" in stage {stage_name!r}" if stage_name else ""
        fail(f"ambiguous tasks.md T-entry for {task_name!r}{location}")
    return matches[0].group(0)


def rule_type(value: str, task_name: str, field: str) -> str:
    match = re.search(r"[a-z][a-z0-9-]*", value.casefold().replace("`", ""))
    if not match:
        fail(f"missing {field} rule type for task {task_name!r}")
    return match.group(0)


def sdd_task_activation(sdd: str) -> dict[tuple[str, str], tuple[str, str]]:
    """Return each SDD task's declared activation mode and entry-rule type."""
    headings = list(
        re.finditer(
            r"(?im)^#####\s+Task\s+[^:\n]+:\s*(.+?)\s*$",
            sdd,
        )
    )
    stage_headings = list(re.finditer(STAGE_HEADING, sdd))
    contracts: dict[tuple[str, str], tuple[str, str]] = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(sdd)
        section = sdd[heading.start() : end]
        task_name = re.sub(r"\s+\(`[^`]+`\)\s*$", "", heading.group(1)).strip()
        stage_heading = next(
            (candidate for candidate in reversed(stage_headings) if candidate.start() < heading.start()),
            None,
        )
        if stage_heading is None:
            fail(f"task {task_name!r} appears before any SDD stage heading")
        stage_name = re.sub(
            r"\s*\([^)]*\)\s*$", "", stage_heading.group(1)
        ).strip()

        activation = re.search(
            r"(?im)^\*\*Activation Mode:\*\*\s*([^\n]+)",
            section,
        )
        if not activation:
            fail(f"missing SDD Activation Mode for task {task_name!r}")

        entry_block = re.search(
            r"(?ims)^\*\*Entry Condition:\*\*\s*(.*?)(?=^\*\*Task envelope|^######|\Z)",
            section,
        )
        if not entry_block:
            fail(f"missing SDD Entry Condition for task {task_name!r}")
        entry_rule = None
        for line in entry_block.group(1).splitlines():
            if not line.strip().startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not cells or cells[0].casefold() == "when" or re.fullmatch(r"[-:\s]+", cells[0]):
                continue
            entry_rule = rule_type(cells[0], task_name, "SDD entry")
            break
        if entry_rule is None:
            fail(f"missing SDD entry-rule row for task {task_name!r}")

        key = (stage_name, task_name)
        if key in contracts:
            fail(f"duplicate SDD task {task_name!r} in stage {stage_name!r}")
        contracts[key] = (
            rule_type(activation.group(1), task_name, "SDD activation"),
            entry_rule,
        )

    if not contracts:
        fail("SDD declares no task detail blocks")
    return contracts


# entry-rule -> the activation modes it may legally carry, per the tasks.md
# template's pairing table (assets/templates/tasks-md-template.md) and
# audit_plan.py, which rejects an illegal pair outright.
LEGAL_ACTIVATION_FOR_RULE = {
    "runs-sequentially": {"sequential", "parallel-after-predecessor"},
    "current-stage-entered": {"parallel"},
    "adhoc": {"adhoc"},
    "selected-tasks-completed": {"fan-in", "conditional-gate"},
    "wait-for-connector": {"event-triggered"},
}


def _pair_is_legal(activation: str, entry_rule: str) -> bool:
    """An entry-rule the table does not constrain pairs with whatever permits it."""
    allowed = LEGAL_ACTIVATION_FOR_RULE.get(entry_rule)
    return allowed is None or activation in allowed


def check_plan_preserves_task_activation(sdd: str, plan: str) -> None:
    """The no-build handoff must not reinterpret confirmed task semantics.

    Exception: an SDD pair that is itself ILLEGAL must not be propagated. The
    skill's doctrine is explicit — "an invalid selector is a stop-and-repair,
    never an authoritative carryover" (references/planning.md) — and
    audit_plan.py rejects an illegal pair, so a plan that mirrored one could
    never pass the skill's own gate. Seen in run 33459371042: the SDD declared
    'Screen Application Data' as sequential/current-stage-entered (illegal —
    that rule pairs only with `parallel`), the plan legally normalised it to
    sequential/runs-sequentially, and this check failed the correct behaviour.
    When the SDD pair is illegal, the plan need only keep the activation mode
    and land on a legal pair.
    """
    for (stage_name, task_name), (sdd_activation, sdd_entry_rule) in sdd_task_activation(sdd).items():
        section = task_section(plan, task_name, stage_name)
        activation = re.search(r"(?im)^[-*]?\s*activation-mode:\s*([^\n]+)", section)
        entry_rule = re.search(r"(?im)^[-*]?\s*entry-rule:\s*([^\n]+)", section)
        if not activation:
            fail(f"missing tasks.md activation-mode for task {task_name!r}")
        if not entry_rule:
            fail(f"missing tasks.md entry-rule for task {task_name!r}")

        plan_activation = rule_type(activation.group(1), task_name, "plan activation")
        plan_entry_rule = rule_type(entry_rule.group(1), task_name, "plan entry")
        if not _pair_is_legal(sdd_activation, sdd_entry_rule):
            # The SDD itself is invalid here. Either half may be the one that
            # gives way — planning.md documents both landings ("a singleton task
            # that starts with its stage remains parallel + current-stage-entered",
            # and "sequential tasks say runs-sequentially") — so require only that
            # the plan lands on a LEGAL pair. Sequencing the requirement actually
            # states is asserted separately for the Supplier Setup trio.
            if not _pair_is_legal(plan_activation, plan_entry_rule):
                fail(
                    f"tasks.md must normalise {task_name!r} to a legal pair "
                    f"(SDD pair {sdd_activation}/{sdd_entry_rule} is illegal); "
                    f"got {plan_activation}/{plan_entry_rule}"
                )
            continue

        if plan_activation != sdd_activation or plan_entry_rule != sdd_entry_rule:
            fail(
                f"tasks.md changes {task_name!r} activation from "
                f"{sdd_activation}/{sdd_entry_rule} to "
                f"{plan_activation}/{plan_entry_rule}"
            )


def stage_section(sdd: str, stage_name: str) -> str:
    heading = rf"^#{{2,4}}\s+(?:(?:Primary\s+)?Stage\s+\d+:\s*|Secondary\s+Stage(?:\s+S?\d+)?:\s*)?{re.escape(stage_name)}\b[^\n]*\n"
    next_stage = r"^#{2,4}\s+(?:(?:Primary\s+)?Stage\s+\d+|Secondary\s+Stage(?:\s+S?\d+)?:)"
    match = re.search(
        rf"(?ims){heading}.*?(?={next_stage}|\Z)",
        sdd,
    )
    if not match:
        fail(f"missing SDD stage section for {stage_name!r}")
    return match.group(0)


def task_lane(section: str, task_name: str) -> int:
    match = re.search(r"(?im)^[-*]?\s*[^\n]*\blane:\s*(\d+)\b", section)
    if not match:
        fail(f"missing lane for sequential task {task_name!r}")
    return int(match.group(1))


STAGE_HEADING = r"(?im)^#{3,4}\s+(?:(?:Primary\s+)?Stage\s+\d+|Exception Stage|Secondary Stage(?:\s+S?\d+)?):\s*(.+)$"

# Primary phases the prompt names; each must carry its own SLA.
PRIMARY_STAGES = ("Intake", "Supplier Setup", "Compliance Review", "Decision", "Close")


def sections_by_target(sdd: str) -> dict[str, str]:
    """SDD text split per SLA target: `root` plus one entry per stage label.

    Everything before the first stage heading is the case (`root`) scope — §1
    Case Definition — and each stage heading owns the text up to the next one.
    SLA and escalation titles are only unique *within* a target, so resolution
    has to be scoped the same way.
    """
    headings = list(re.finditer(STAGE_HEADING, sdd))
    sections = {"root": sdd[: headings[0].start()] if headings else sdd}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(sdd)
        label = re.sub(r"\s*\([^)]*\)\s*$", "", heading.group(1)).strip().casefold()
        if label:
            sections[label] = sections.get(label, "") + sdd[heading.start() : end]
    return sections


def case_level_aliases(sdd: str) -> set[str]:
    """Casefolded spellings that unambiguously mean the case-level target.

    The canonical target is the literal `root`; designs also show up with
    "Case" or the case's own name from the `# SDD — {Case Name}` heading.
    All three resolve to the same SLA scope, so grading treats them as root —
    anything else still fails target closure.
    """
    aliases = {"root", "case"}
    title = re.search(r"(?m)^#\s+SDD\s+—\s+(.+?)\s*$", sdd)
    if title:
        aliases.add(title.group(1).strip().casefold())
    return aliases


def sla_references(sdd: str) -> list[tuple[int, list[str]]]:
    """(line number, quoted args) for every sla-status-change(...) in the SDD."""
    references = []
    for line_no, line in enumerate(sdd.splitlines(), 1):
        call = re.search(r"sla-status-change\s*\(([^)]*)\)", line, re.IGNORECASE)
        if call:
            args = re.findall(r"[\"']([^\"']+)[\"']", call.group(1))
            # Zero quoted args means summary-table / prose shorthand, not an
            # executable reference; real rule coverage is enforced per stage +
            # root below, so a malformed real rule still fails there.
            if args:
                references.append((line_no, args))
    return references


def declared_sla_titles(sdd: str) -> set[str]:
    """Titles an SLA rule / escalation is actually declared under.

    Three declaration sites: the `| SLA Title | … |` metadata row, the
    `**SLA Title:**` field in a Stage SLA block, and the trailing `Display Name`
    columns of the escalation / Variable SLA Rules tables. Matching whole cells
    (not substrings) is what separates a real title from the SLA *status* word —
    `Breached` sits in column 1 of the escalation table and is never a title.
    """
    titles = set()
    for match in re.finditer(r"(?im)^\|\s*(?:Case\s+)?SLA Title\s*\|\s*([^|]+)\|", sdd):
        titles.add(match.group(1).strip().casefold())
    for match in re.finditer(r"(?im)^\*\*SLA Title:\*\*\s*(.+)$", sdd):
        titles.add(match.group(1).strip().casefold())

    # Title columns of SLA / escalation tables only. A header qualifies when it
    # has a title column AND an SLA-ish column, which admits the escalation and
    # Variable SLA Rules tables while excluding condition tables (`WHEN | IF |
    # Interrupting | Display Name`) and every unrelated table — a stray cell in
    # a task-summary row must never satisfy an escalation reference.
    title_columns: list[int] = []
    for line in sdd.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            title_columns = []
            continue
        if re.fullmatch(r"[\s:|-]+", stripped.strip("|")):
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        lowered = [cell.casefold() for cell in cells]
        candidates = [
            index
            for index, cell in enumerate(lowered)
            if re.search(r"(display name|title)$", cell)
        ]
        if candidates and any(
            token in cell
            for cell in lowered
            for token in ("sla", "threshold", "at-risk", "breach", "expression")
        ):
            title_columns = candidates
            continue
        if "sla-status-change" in stripped.casefold():
            continue
        for index in title_columns:
            if index < len(cells) and cells[index]:
                titles.add(cells[index].casefold())
    return {
        title
        for title in titles
        if title and not re.fullmatch(r"[-—:\s]+", title)
    }


def check_canonical_stage_sla(section: str, stage: str) -> None:
    if re.search(r"(?im)^####\s+Stage SLA\s*$", section) is None:
        fail(f"primary phase {stage!r} has no canonical '#### Stage SLA' block")
    titles = [t.strip() for t in re.findall(r"(?im)^\*\*SLA Title:\*\*\s*(.+)$", section)]
    # Exactly one concrete line-start `**SLA Title:**` per stage — the field shape
    # is contractual (line-start titles are what reference resolution matches).
    # The NAME is graded semantically: any concrete stage-scoped title works as
    # long as references resolve (closure is checked separately); the preferred
    # deterministic spelling is '<Stage Name> SLA' but variants like
    # '<Stage Name> Phase SLA' carry the same meaning.
    if len(titles) != 1 or not titles[0] or re.fullmatch(r"[-—:\s]+", titles[0]):
        fail(
            f"primary phase {stage!r} must declare exactly one concrete "
            f"'**SLA Title:**' line; got {titles or 'nothing'}"
        )
    if stage.casefold() not in titles[0].casefold():
        fail(
            f"primary phase {stage!r} declares SLA title {titles[0]!r}, which does not "
            f"name its own stage — each phase declares its own scoped SLA"
        )


def check_sla_reference_closure(sdd: str) -> None:
    """Every sla-status-change entry must resolve to a declared SLA + escalation.

    The rule carries no duration or threshold of its own — it fires off an SLA
    rule and one of that rule's escalations, resolved by title within the named
    target. A reference to titles the SDD never declares cannot resolve to
    `slaId` / `escalationId`, so the lane silently never fires. Counting the
    rule name is not enough; the names have to point at something.
    """
    references = sla_references(sdd)
    if not references:
        fail("no sla-status-change entry condition names its SLA")

    sections = sections_by_target(sdd)
    targets: list[str] = []
    aliases = case_level_aliases(sdd)
    for line_no, args in references:
        # Arg count carries the status: 2 args is a Breached rule (it references the
        # SLA alone — an absent escalation IS the persisted Breached shape), 3 args is
        # an At-Risk rule naming a concrete at-risk escalation on that same SLA.
        if len(args) not in (2, 3):
            fail(
                f"sdd.md:{line_no}: sla-status-change takes two args "
                '("<SLA target>","<SLA Title>") for a breach, or three '
                '("<SLA target>","<SLA Title>","<At-Risk Escalation Display Name>") '
                f"for at-risk; got {args!r}"
            )
        target, sla_title = args[0], args[1]
        escalation_title = args[2] if len(args) == 3 else None
        target_key = "root" if target.casefold() in aliases else target.casefold()
        if target_key not in sections:
            fail(
                f"sdd.md:{line_no}: sla-status-change target {target!r} is neither "
                "'root' (case-level SLA) nor a stage declared in this SDD"
            )
        targets.append(target_key)

        # Scoped to the named target: an escalation declared on a different SLA
        # cannot be borrowed, because Phase 1 resolves the id within the target.
        declared = declared_sla_titles(sections[target_key])
        for title in (t for t in (sla_title, escalation_title) if t is not None):
            if title.casefold() not in declared:
                fail(
                    f"sdd.md:{line_no}: sla-status-change references {title!r}, which "
                    f"target {target!r} does not declare as an SLA Title / escalation "
                    f"Display Name (it declares: {sorted(declared) or 'nothing'})"
                )

    # The prompt asks for both a phase (stage) breach lane and a 15-day case
    # breach lane, so the SDD must reference SLAs at both scopes.
    if "root" not in targets:
        fail("no sla-status-change references the case-level SLA (target 'root')")
    if not [t for t in targets if t != "root"]:
        fail("no sla-status-change references a stage-level (phase) SLA")

    # "Every primary phase has an SLA target" and "on a phase breach, globally
    # interrupt" are both literal in the prompt: each named phase declares its
    # own SLA, and each phase's breach routes into the lane. Declaring five SLAs
    # but wiring only one breach leaves four phases silently unescalated.
    for stage in PRIMARY_STAGES:
        section = next(
            (text for label, text in sections.items() if stage.casefold() in label), None
        )
        if section is None:
            fail(f"missing SDD stage section for primary phase {stage!r}")
        check_canonical_stage_sla(section, stage)
        if not declared_sla_titles(section):
            fail(
                f"primary phase {stage!r} declares no stage SLA (prompt: every primary "
                "phase has an SLA target) — needs an SLA Title plus escalation titles"
            )
        if not [t for t in targets if stage.casefold() in t]:
            fail(
                f"no sla-status-change routes {stage!r}'s SLA breach into the escalation "
                "lane (prompt: on a phase breach, globally interrupt)"
            )


def check_plan_carries_sla_references(sdd: str, plan: str) -> None:
    """tasks.md must carry the SLA interrupt it inherited from the SDD.

    The compact no-build plan contract (planning.md § Compact
    tasks/tasks.md contract) requires the global-event entry to name its rule
    type and, for `sla-status-change`, the SLA it fires off (plus the at-risk
    escalation when the row is at-risk; a breach row names the SLA alone).
    Grading only sdd.md would let a plan that drops the interrupt entirely pass.
    """
    lowered_plan = plan.casefold()
    if "sla-status-change" not in lowered_plan:
        fail("tasks/tasks.md carries no sla-status-change condition entry")
    missing = sorted(
        {
            title
            for _, args in sla_references(sdd)
            for title in args[1:3]
            if title.casefold() not in lowered_plan
        }
    )
    if missing:
        fail(
            "tasks/tasks.md does not carry the SLA/escalation titles its "
            f"sla-status-change entries reference: {missing}"
        )


def main() -> None:
    sdd = read_required(Path("sdd.md"))
    plan = read_required(Path("tasks/tasks.md"))
    combined = f"{sdd}\n{plan}"

    if combined.lower().count("sla-status-change") < 2:
        fail("phase/case breach work is not modeled with SLA stage-entry rules")

    check_sla_reference_closure(sdd)
    check_plan_carries_sla_references(sdd, plan)

    for stage in ("SLA Escalation", "Case SLA Review", "Withdrawn"):
        if not has_near(sdd, stage, "Interrupting", 1200):
            fail(f"{stage!r} is not documented as an interrupting secondary stage")

    withdrawn_section = stage_section(sdd, "Withdrawn")
    if "wait-for-connector" not in withdrawn_section.lower():
        fail("Withdrawn is not entered by the global supplier-portal event")
    if not (
        has_near(withdrawn_section, "Supplier Portal", "Withdraw", 500)
        # The connector source may be declared once in the Triggers table /
        # Section 4 rollup and referenced from the stage by event title; the
        # wait-for-connector entry check above already pins the stage's rule.
        or has_near(sdd, "Supplier Portal", "Withdraw", 500)
    ):
        fail("Withdrawn connector rule does not preserve the supplier-portal withdrawal event")

    sequential_tasks = ("Verify Supplier Identity", "Set Supplier Record", "Invite Supplier")
    lanes: list[int] = []
    for task in sequential_tasks:
        if not has_near(combined, task, "runs-sequentially", 700):
            fail(f"{task!r} does not preserve the explicit sequential mode")
        section = task_section(plan, task)
        if not has_near(section, "activation-mode", "sequential", 120):
            fail(f"{task!r} does not expose activation-mode: sequential")
        if not has_near(section, "entry-rule", "runs-sequentially", 120):
            fail(f"{task!r} does not expose entry-rule: runs-sequentially")
        lanes.append(task_lane(section, task))
    expected_lanes = list(range(lanes[0], lanes[0] + len(lanes))) if lanes else []
    if lanes != expected_lanes:
        fail(
            "Supplier Setup strict sequential tasks must use consecutive "
            f"single-task lane/task-set indices; got {lanes!r}, "
            f"expected {expected_lanes!r}"
        )

    check_plan_preserves_task_activation(sdd, plan)

    if sdd.lower().count("rationale") < 4:
        fail("SDD does not preserve enough design rationale")
    if plan.lower().count("rationale") < 4:
        fail("tasks.md does not carry the SDD rationale into planning")

    print(
        "OK: global interrupts, resolvable SLA references, task activation, "
        "and rationale are preserved"
    )


if __name__ == "__main__":
    main()
