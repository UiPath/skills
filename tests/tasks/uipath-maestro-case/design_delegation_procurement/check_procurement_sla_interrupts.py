#!/usr/bin/env python3
"""Check the procurement SLA design regression contract (design-only run)."""

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


def main() -> None:
    sdd = read_required(Path("sdd.md"))

    if sdd.lower().count("sla-status-change") < 2:
        fail("phase/case breach work is not modeled with SLA stage-entry rules")

    check_sla_reference_closure(sdd)

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

    # Each of the three Supplier Setup tasks declares sequential activation in its
    # own SDD detail block; sdd_task_activation() below proves every task carries
    # both fields, this pins the three that must be sequential.
    activation = sdd_task_activation(sdd)
    for task in ("Verify Supplier Identity", "Set Supplier Record", "Invite Supplier"):
        declared = [
            value for (_, name), value in activation.items() if name == task
        ]
        if not declared:
            fail(f"SDD declares no task detail block for {task!r}")
        if len(declared) > 1:
            fail(f"ambiguous SDD task detail blocks for {task!r}")
        mode, entry_rule = declared[0]
        if mode != "sequential":
            fail(f"{task!r} declares activation mode {mode!r}, not sequential")
        if entry_rule != "runs-sequentially":
            fail(f"{task!r} declares entry rule {entry_rule!r}, not runs-sequentially")

    if sdd.lower().count("rationale") < 4:
        fail("SDD does not preserve enough design rationale")

    print(
        "OK: global interrupts, resolvable SLA references, task activation, "
        "and rationale are preserved"
    )


if __name__ == "__main__":
    main()
