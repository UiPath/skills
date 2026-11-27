"""Calibrates check_sdd_data_model.py: an ideal table scores 1.0 and each defect costs its component."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_sdd_data_model import score  # noqa: E402

GOLDEN = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))
HEADER = "| Entity | Source of record | Fields | Links | Written by | Read by |\n|---|---|---|---|---|---|\n"


def sdd(source=lambda o: "SQL Server", written=lambda o: "—", drop=()):
    rows = []
    for o in GOLDEN["objects"]:
        if o["name"] in drop:
            continue
        fields = ", ".join(f"{f['name']}: {f['type']}" for f in o["fields"])
        links = ", ".join(f"{l['field']} → {l['target']} (to-one)" for l in o["links"]) or "—"
        rows.append(f"| {o['name']} | {source(o)} | {fields} | {links} | {written(o)} | Insights flow |\n")
    return "# SDD\n\n### Data model\n\nOntology: none\n\n" + HEADER + "".join(rows) + "\n## Next\n"


def test_the_ideal_table_scores_one():
    assert score(sdd(), GOLDEN)[0] == 1.0


def test_no_table_scores_zero():
    assert score("# SDD\n\nNo data model here.\n", GOLDEN)[0] == 0.0


def test_copying_the_connection_and_table_into_the_source_of_record_costs_the_source_component():
    total, notes = score(sdd(source=lambda o: f"SQL Server (`birdadmin_sqlserver`, table `bird_student_club_{o['name'].lower()}`)"), GOLDEN)
    assert total == 0.8
    assert any("source of record not the system alone" in n for n in notes)


def test_a_writer_on_a_federated_row_costs_the_read_only_component():
    assert score(sdd(written=lambda o: "Insights flow"), GOLDEN)[0] == 0.9


def test_a_missing_object_costs_objects_fields_source_and_its_links():
    total, notes = score(sdd(drop=("Member",)), GOLDEN)
    assert 0.6 < total < 0.9
    assert "objects missing: ['member']" in notes
