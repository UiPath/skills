"""check_sdd_entities.py: a table mirroring the golden scores 1.0; defects lower only their slice."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_sdd_entities.py"
GOLDEN = HERE / "golden.json"


def table_from_golden(golden: dict) -> str:
    rows = ["## 5. Data Definitions", "", "### Data Fabric entities", "",
            "| Entity | Class | System of record → connector key | External object · primary key | Fields (source field → type) | Joins | Solution / folder |",
            "|---|---|---|---|---|---|---|"]
    for g in golden["entities"]:
        live = next((v for k, v in g["live"].items() if k.startswith("uipath-uipath-jdbc|birdadmin")), None)
        obj = live["externalObjectName"] if live else f"bird_student_club_{g['name']}"
        pk = (live or {}).get("primaryKey") or (g["primaryKey"][0] if g["primaryKey"] else "id")
        fields = ", ".join(f"`{f['sourceField']} → {f['type']}`" for f in g["fields"])
        joins = "; ".join(f"`{j['joinField']} → {j['relatedEntity']}.{j['relatedJoinField']}` (LeftJoin)" for j in g["joins"]) or "none"
        rows.append(f"| {g['name'].title().replace('_', '')} | Federated | SQL Server → `uipath-uipath-jdbc` | `{obj}` · `{pk}` | {fields} | {joins} | `student-club-insights` / Shared |")
    rows += ["", "## 6. Value Mappings", ""]
    return "\n".join(rows)


def run(sdd: Path) -> tuple[float, str]:
    r = subprocess.run([sys.executable, str(CHECKER), "--golden", str(GOLDEN), "--sdd", str(sdd)], capture_output=True, text=True)
    lines = r.stdout.splitlines()
    return float(lines[0]), "\n".join(lines[1:])


@pytest.fixture()
def golden() -> dict:
    return json.loads(GOLDEN.read_text())


def test_perfect_table_scores_one(tmp_path, golden):
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(table_from_golden(golden))
    s, d = run(sdd)
    assert s == pytest.approx(1.0, abs=1e-6), d


def test_missing_table_scores_zero(tmp_path):
    sdd = tmp_path / "x-sdd.md"; sdd.write_text("## 5. Data Definitions\n\nnothing here\n")
    s, d = run(sdd)
    assert s == 0.0, d


def test_dropped_entity_and_wrong_connector_lower_score(tmp_path, golden):
    text = table_from_golden(golden).replace("| Member | Federated", "| Sponsor | Federated", 1).replace("`uipath-uipath-jdbc`", "`uipath-hubspot-hubspot`", 1)
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(text)
    s, d = run(sdd)
    assert s < 1.0 and "unmatched rows 1" in d and "not an allow-listed" in d, d


def test_sme_review_cells_are_not_penalised_as_wrong(tmp_path, golden):
    text = table_from_golden(golden).replace("SQL Server → `uipath-uipath-jdbc`", "SQL Server → [SME REVIEW]")
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(text)
    s, d = run(sdd)
    assert 0.8 < s < 1.0 and "not an allow-listed" not in d, d


def test_plain_comma_field_lists_are_credited(tmp_path, golden):
    import re
    text = table_from_golden(golden)
    # strip the backticks and types from the Fields column only: "`a → STRING`, `b → DECIMAL`" -> "a, b"
    text = re.sub(r"`([A-Za-z0-9_]+) → [A-Z_]+`", r"\1", text)
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(text)
    s, d = run(sdd)
    assert s == pytest.approx(1.0, abs=1e-6), d


def test_numbered_heading_is_found(tmp_path, golden):
    text = table_from_golden(golden).replace("### Data Fabric entities", "### 3.2 Data Fabric entities")
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(text)
    s, d = run(sdd)
    assert s == pytest.approx(1.0, abs=1e-6), d


def test_reuse_marker_and_prefixed_join_targets_score_full(tmp_path, golden):
    """A deployed-fixture reuse row: class "Federated · reuse", entity and join targets named mssql_<table>."""
    import re
    text = table_from_golden(golden).replace("| Federated |", "| Federated · reuse |")
    text = re.sub(r"→ ([A-Za-z]+)\.", lambda m: f"→ mssql_{m.group(1).lower()}.", text)
    sdd = tmp_path / "x-sdd.md"; sdd.write_text(text)
    s, d = run(sdd)
    assert s == pytest.approx(1.0, abs=1e-6), d
