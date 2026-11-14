"""Contract tests between the two genome skills: uipath-planner writes genomes from its templates and guides and
checks them with scripts/check-genome.mjs; uipath-genome builds them. Neither skill reads the other's
files, so these tests hold the planner's templates and skill mapping to the checker's constants, and every
`file.md § Section` pointer in either skill to a heading of that skill's own file.

Run: pytest tests/tasks/uipath-planner/_shared/test_genome_contract.py -v
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PLANNER = REPO / "skills" / "uipath-planner"
BUILDER = REPO / "skills" / "uipath-genome"
CHECKER = PLANNER / "scripts" / "check-genome.mjs"
TEMPLATES = PLANNER / "assets" / "templates"
MAPPING_GUIDE = PLANNER / "references" / "shared" / "skill-mapping-guide.md"
LEVELS = {"component": "COMPONENT_SECTIONS", "process": "PROCESS_SECTIONS"}


def checker_constants() -> dict:
    """The checker's exported constants, Sets as sorted lists."""
    script = (f"import * as c from {json.dumps(CHECKER.as_uri())};"
              "const out = {};"
              "for (const [k, v] of Object.entries(c)) if (typeof v !== 'function') out[k] = v instanceof Set ? [...v].sort() : v;"
              "process.stdout.write(JSON.stringify(out));")
    r = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(r.stdout)


C = checker_constants()


def template(level: str) -> str:
    return (TEMPLATES / f"{level}-genome-template.md").read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}(?=\s|$)[^\n]*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def table_after(text: str, first_cell: str) -> list[list[str]]:
    """The table whose header's first cell is `first_cell`: its header, then its body rows, cells stripped."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and cells[0].lower() == first_cell.lower():
            rows = [cells]
            for body in lines[i + 1:]:
                if not body.lstrip().startswith("|"):
                    break
                if not set(body.strip()) <= set("|-: "):
                    rows.append([c.strip() for c in body.strip().strip("|").split("|")])
            return rows
    return [[]]


@pytest.mark.parametrize("level", LEVELS)
def test_template_sections_are_the_checkers_in_order(level):
    headings = re.findall(r"^## (.+)$", template(level), re.M)
    assert [h for h in headings if h != "Source Map"] == C[LEVELS[level]]


@pytest.mark.parametrize("level", LEVELS)
def test_template_preamble_and_blockquote_are_what_the_checker_reads(level):
    text = template(level)
    assert f"UIPATH-AUTOMATION-GENOME: {level}" in text
    assert "This is a UiPath automation blueprint" in text
    comment = re.search(r"<!--\s*UIPATH-AUTOMATION-GENOME[\s\S]*?-->", text).group(0)
    blockquote = re.search(r"^>.*UiPath automation blueprint.*$", text, re.M).group(0)
    assert C["BUILDER"] in comment and C["BUILDER"] in blockquote


@pytest.mark.parametrize("level", LEVELS)
def test_template_transactional_shape_tables_are_the_checkers(level):
    ts = section(template(level), "Transactional Shape")
    assert C["STUB"] in ts
    assert [c.lower() for c in table_after(ts, "Unit of work")[0]] == C["SPLIT_COLUMNS"]
    outcomes = {row[0] for row in table_after(ts, "Outcome")[1:]}
    assert outcomes and outcomes <= set(C["OUTCOME_ROWS"])


def test_component_template_step_table_is_the_checkers():
    assert [c.lower() for c in table_after(section(template("component"), "Source Map"), "Step")[0]] == C["STEPS_COLUMNS"]


def mapping_skills(heading: str, column: int) -> set[str]:
    rows = [line for line in section(MAPPING_GUIDE.read_text(encoding="utf-8"), heading).splitlines()
            if line.lstrip().startswith("|") and not set(line.strip()) <= set("|-: ")]
    cells = [[c.strip() for c in row.strip().strip("|").split("|")] for row in rows[1:]]
    return {s for row in cells for s in re.findall(r"`(uipath-[a-z-]+)`", row[column])}


def test_mapping_guide_build_skills_are_checker_build_skills():
    listed = mapping_skills("Build Skills", 1)
    assert listed and listed - set(C["VALID_SKILLS"]) == set()


def test_mapping_guide_platform_skills_are_checker_operate_skills():
    listed = mapping_skills("Platform Dependencies (not Build With)", 1)
    assert listed and listed - set(C["OPERATE_SKILLS"]) == set()


def template_placeholders() -> list[str]:
    """The checker's own derivation: each `{…}` of a Transactional Shape, a one-word one with the word before it."""
    found: list[str] = []
    for level in LEVELS:
        for m in re.finditer(r"(\S+ )?(\{[a-z][^}]*\})", section(template(level), "Transactional Shape")):
            p = (m.group(1) or "") + m.group(2) if re.fullmatch(r"\{[a-z]+\}", m.group(2)) else m.group(2)
            if p not in found:
                found.append(p)
    return found


def test_checker_placeholders_are_the_templates():
    assert C["TEMPLATE_PLACEHOLDERS"] == template_placeholders()


# --- section pointers -----------------------------------------------------------------------------------------

POINTER = re.compile(r"([\w./-]+\.md)\)?\]?(?:\([^)]*\))?\s*§\s*([^\n]+)")
OTHER_SKILL = re.compile(r"`?(uipath-[a-z-]+)`?'s\s+$")
CUT = re.compile(r"\]\(|\)|,|;|:|\.(?:\s|$)| \(| —| –|\*\*|`|\|")


def lead(text: str) -> str:
    """A heading or pointer up to its first punctuation, lower-cased: `Step 3: Proceed` and `Step 3 when` both lead
    with `step 3`."""
    return CUT.split(re.sub(r"[`*]", "", text), maxsplit=1)[0].strip().lower()


def headings_of(path: Path) -> list[str]:
    return [lead(h) for h in re.findall(r"^#{1,6} (.+)$", path.read_text(encoding="utf-8"), re.M)]


SKILL_FILES = {p.name for p in (REPO / "skills").rglob("*.md")}


def unresolved_pointers(skill: Path) -> list[str]:
    files = {p.name: p for p in skill.rglob("*.md")}
    misses = []
    for path in sorted(skill.rglob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in POINTER.finditer(line):
                name = Path(m.group(1)).name
                before = line[max(0, m.start() - 80):m.start()]
                sentence = re.split(r"(?:\.\s|;\s|\|)", before)[-1]
                other = OTHER_SKILL.search(sentence)
                if "<" in m.group(1) or (other and other.group(1) != skill.name) or name not in SKILL_FILES:
                    continue  # a placeholder path, another skill's file, or a generic example such as `guide.md § Section`
                target = files.get(name)
                cut = lead(m.group(2))
                if not cut:
                    continue
                if target is None or not any(h and (h.startswith(cut) or cut.startswith(h)) for h in headings_of(target)):
                    misses.append(f"{path.relative_to(REPO)}:{n}: {name} § {cut}")
    return misses


@pytest.mark.parametrize("skill", [PLANNER, BUILDER], ids=lambda p: p.name)
def test_section_pointers_resolve_in_the_skills_own_files(skill):
    assert unresolved_pointers(skill) == []


# The requests sent to uipath-planner's edit, by the files that send them; each must be matched by an edit-guide row.
EDIT_REQUESTS = {
    "The SDD was revised: update the genome": ("uipath-planner design", PLANNER / "references" / "design"),
    "Findings from `uipath-genome`": ("uipath-genome", BUILDER / "references"),
    "Apply the readiness answers": ("uipath-genome", BUILDER / "references"),
}


@pytest.mark.parametrize("request_text", EDIT_REQUESTS)
def test_edit_requests_have_an_edit_guide_row(request_text):
    sender, folder = EDIT_REQUESTS[request_text]
    sent = "".join(p.read_text(encoding="utf-8") for p in folder.glob("*.md"))
    edit_rows = [line for line in (PLANNER / "references" / "edit" / "edit-guide.md").read_text(encoding="utf-8").splitlines()
                 if line.startswith(f'| "{request_text}"')]
    assert request_text in sent, f"{sender} no longer sends {request_text!r}"
    assert edit_rows, f"uipath-planner's edit-guide.md has no row starting with {request_text!r}"
