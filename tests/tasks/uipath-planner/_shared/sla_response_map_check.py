"""Deterministic guards for the SDD **SLA Response Map** contract (uipath-planner assets/templates/case/case-sdd-template.md § SLA Response Map).

The map is the single place SLA breach / at-risk behavior is decided:

    | Scope | SLA | Status | Response | Target | Interrupting | Rationale |

Rules enforced here:

1. The section exists, with all seven columns, whenever any SLA is configured.
2. Every `Response` comes from the closed set.
3. `notify-only` rows carry no target and no interrupting decision (`—`).
4. Non-`notify-only` rows name a target. `enter-stage` / `exit-*` rows carry an explicit
   `Yes`/`No`; `start-task` rows carry `—`, because they are task-entry rules and a task
   entry interrupts nothing.
5. Closure both ways — a `start-task` / `enter-stage` row has a matching `sla-status-change`
   entry in the SDD, and every `sla-status-change` entry has a map row.
6. The map's `Interrupting` cell agrees with the `Interrupting` cell of the Stage Entry
   Conditions row it produces. This is the regression guard: the chosen value must survive
   into the conditions table instead of being defaulted to `Yes`.
"""

from __future__ import annotations

import re

RESPONSES = {"notify-only", "start-task", "enter-stage", "exit-stage", "exit-case"}
GRAPH_ENTRY_RESPONSES = {"start-task", "enter-stage"}
COLUMNS = ["scope", "sla", "status", "response", "target", "interrupting", "rationale"]
DASHES = {"", "-", "—", "–", "n/a", "na"}
HEADING = re.compile(r"^#{2,4}\s+.*SLA Response Map", re.IGNORECASE | re.MULTILINE)
SLA_CALL = re.compile(r"sla-status-change\s*\(([^)]*)\)", re.IGNORECASE)


def _is_dash(cell: str) -> bool:
    return cell.strip().strip("`*").casefold() in DASHES


def _split_row(line: str) -> list[str]:
    return [c.strip().strip("`*") for c in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s|:-]+\|", line.strip()))


def parse_map_rows(text: str) -> tuple[list[dict], list[str]]:
    """Return ``(rows, issues)`` for the SLA Response Map table."""
    issues: list[str] = []
    match = HEADING.search(text)
    if not match:
        return [], ["sdd.md has no `SLA Response Map` section (§1.2b is required when any SLA is configured)"]

    lines = text[match.end():].splitlines()
    header: list[str] | None = None
    rows: list[dict] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{2,4}\s+\S", stripped):
            break
        if not stripped.startswith("|"):
            continue
        if _is_separator(stripped):
            continue
        cells = _split_row(stripped)
        if header is None:
            header = [c.casefold() for c in cells]
            missing = [c for c in COLUMNS if c not in header]
            if missing:
                issues.append(
                    f"SLA Response Map is missing column(s) {missing}; expected "
                    f"{' | '.join(COLUMNS)}"
                )
            continue
        if len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        # Skip the template's own placeholder row.
        if "{" in row.get("response", ""):
            continue
        rows.append(row)

    if header is None:
        issues.append("SLA Response Map section has no table")
    elif not rows:
        issues.append("SLA Response Map table has no data rows")
    return rows, issues


def entry_condition_interrupting(text: str) -> dict[str, str]:
    """Map each ``sla-status-change(...)`` call in the SDD to its row's Interrupting cell.

    Keyed by the raw arg string so a row can be matched back to the map by SLA title.
    """
    found: dict[str, str] = {}
    for line in text.splitlines():
        call = SLA_CALL.search(line)
        if not call or not line.strip().startswith("|"):
            continue
        cells = _split_row(line)
        interrupting = ""
        for cell in reversed(cells):
            token = cell.strip().casefold()
            if token in {"yes", "no"}:
                interrupting = token
                break
        found[call.group(1).strip()] = interrupting
    return found


def check(text: str) -> list[str]:
    """Return a list of contract violations; empty means the map is well-formed."""
    rows, issues = parse_map_rows(text)
    if not rows:
        return issues

    entries = entry_condition_interrupting(text)

    for row in rows:
        response = row.get("response", "").casefold()
        label = f"{row.get('scope', '?')} / {row.get('sla', '?')} / {row.get('status', '?')}"
        if response not in RESPONSES:
            issues.append(
                f"SLA Response Map row [{label}] has Response {row.get('response')!r}; "
                f"allowed: {sorted(RESPONSES)}"
            )
            continue
        if response == "notify-only":
            if not _is_dash(row.get("target", "")):
                issues.append(
                    f"SLA Response Map row [{label}] is notify-only but names Target "
                    f"{row.get('target')!r}; a notification mints no stage or task"
                )
            if not _is_dash(row.get("interrupting", "")):
                issues.append(
                    f"SLA Response Map row [{label}] is notify-only but sets Interrupting "
                    f"{row.get('interrupting')!r}; there is no active work to interrupt"
                )
            continue
        if _is_dash(row.get("target", "")):
            issues.append(f"SLA Response Map row [{label}] is {response} but names no Target")
        interrupting = row.get("interrupting", "").strip().casefold()
        if response == "start-task":
            # A start-task response is a TASK-entry rule, and a task entry interrupts
            # nothing — so `—` is the only legal value. `No` is not: it implies the
            # stage-re-entry shape, which re-runs every task in the breached stage whose
            # shouldRunOnlyOnce is false (the default). See skills/uipath-maestro-case/
            # references/sla-response-shapes.md section 5, defect 4.
            if not _is_dash(row.get("interrupting", "")):
                issues.append(
                    f"SLA Response Map row [{label}] is start-task with Interrupting "
                    f"{row.get('interrupting')!r}; a start-task response is the follow-up "
                    "task's own task-entry rule, which has no interrupting cell — use `—`. "
                    "(`No` would imply stage re-entry, which re-runs the breached stage's "
                    "other tasks.)"
                )
        elif interrupting not in {"yes", "no"}:
            issues.append(
                f"SLA Response Map row [{label}] is {response} but Interrupting is "
                f"{row.get('interrupting')!r}; it must be an explicit Yes or No"
            )

    graph_rows = [r for r in rows if r.get("response", "").casefold() in GRAPH_ENTRY_RESPONSES]
    if graph_rows and not entries:
        issues.append(
            f"{len(graph_rows)} SLA Response Map row(s) declare a stage response but no "
            "`sla-status-change(...)` entry condition exists anywhere in the SDD"
        )
    if entries and not graph_rows:
        issues.append(
            f"the SDD has {len(entries)} `sla-status-change(...)` entry row(s) with no "
            "matching SLA Response Map row"
        )

    # Interrupting must survive from the map into the entry-conditions table.
    # Matching is (SLA title AND scope↔target): a case-level and a stage-level SLA may
    # legally share a title, so a title-only match can satisfy closure with a row for
    # the wrong target. `root` matches Scope `case`; a stage target matches
    # `stage: <name>`.
    def _scope_matches_target(scope: str, target: str) -> bool:
        scope = scope.strip().casefold()
        target = target.strip().strip('"').strip("'").casefold()
        if target == "root":
            # Case scope is documented as the bare word `case`; an agent
            # generalising from `stage: <name>` / `task: <name>` writes
            # `case: root`, which names the same target. Closure is about the
            # target, not the vocabulary — the template-conformance gate owns
            # wording. Run 33448258234 failed on exactly this.
            return bool(re.fullmatch(r"case(?:\s*:\s*(?:root|case))?", scope))
        match = re.match(r"stage\s*:\s*(.+)", scope)
        if not match:
            return False
        # The Scope cell may carry the stage's slug as a trailing qualifier —
        # `stage: Assess (`assess`)` — which is annotation, not part of the
        # stage name. Branch run 33429105211 was told every row titled
        # 'Assess SLA' was "scoped ['stage: Assess (`assess`)']" and therefore
        # did not match target 'Assess', which is the same name.
        name = re.sub(r"\s*\([^)]*\)\s*$", "", match.group(1)).strip().strip("`")
        return name == target

    for args, entry_interrupting in entries.items():
        sla_title = ""
        target = ""
        parts = [p.strip().strip('"').strip("'") for p in args.split(",")]
        if parts:
            target = parts[0]
        if len(parts) >= 2:
            sla_title = parts[1]
        titled = [r for r in graph_rows if r.get("sla", "").strip() == sla_title]
        if not titled:
            issues.append(
                f"`sla-status-change({args})` references SLA {sla_title!r}, which has no "
                "SLA Response Map row"
            )
            continue
        candidates = [r for r in titled if _scope_matches_target(r.get("scope", ""), target)]
        if not candidates:
            scopes = sorted({r.get("scope", "?") for r in titled})
            issues.append(
                f"`sla-status-change({args})` targets {target!r} but every SLA Response Map "
                f"row titled {sla_title!r} is scoped {scopes} — the map row must be scoped to "
                "the call's target (root → `case`; a stage target → `stage: <name>`)"
            )
            continue
        if not entry_interrupting:
            # A task-entry condition table has no Interrupting column at all — correct for a
            # start-task response. Only a row that SHOULD carry one (a stage entry, i.e. an
            # enter-stage response) is a defect.
            if any(r.get("response", "").casefold() == "enter-stage" for r in candidates):
                issues.append(
                    f"the Stage Entry Conditions row for `sla-status-change({args})` has no "
                    "Yes/No Interrupting cell"
                )
            continue
        declared = {r.get("interrupting", "").strip().casefold() for r in candidates}
        if entry_interrupting not in declared:
            issues.append(
                f"Interrupting mismatch for `sla-status-change({args})`: the entry row says "
                f"{entry_interrupting!r} but the SLA Response Map says {sorted(declared)}"
            )

    return issues
