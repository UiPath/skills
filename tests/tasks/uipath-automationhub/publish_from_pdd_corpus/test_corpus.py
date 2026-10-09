"""Offline consistency checks for the corpus task: rows, templates and manifests agree.

The graders trust expected/<id>.json; these tests keep it honest about the staged
documents: every row has a manifest, every document it names is staged as a
token-bearing template, the title is the PDD's own, and every system alias it
expects is something the documents actually say.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROWS = [json.loads(line) for line in (HERE / "corpus.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
PLACEHOLDER = "{{RUN_TOKEN}}"


def manifest(row_id: str) -> dict:
    return json.loads((HERE / "expected" / f"{row_id}.json").read_text(encoding="utf-8"))


def template_of(rendered: str) -> Path:
    path = Path(rendered)
    return HERE / path.parent / f"{path.stem}-template{path.suffix}"


def staged_text(row_id: str) -> str:
    return "\n".join(template_of(p).read_text(encoding="utf-8") for p in manifest(row_id)["documents"].values())


def test_rows_and_manifests_match_one_to_one() -> None:
    ids = [row["id"] for row in ROWS]
    assert len(ids) == len(set(ids))
    assert sorted(ids) == sorted(p.stem for p in (HERE / "expected").glob("*.json"))
    assert sorted(ids) == sorted(p.name for p in (HERE / "corpus").iterdir() if p.is_dir())


def test_task_yaml_reads_this_dataset() -> None:
    # Plain text, not a YAML parse: the CI job installs pytest only.
    task = (HERE / "publish_from_pdd_corpus.yaml").read_text(encoding="utf-8")
    assert re.search(r'^dataset:\n  paths: \["corpus\.jsonl"\]$', task, re.M)
    tags = re.search(r"^tags: \[(.*)\]$", task, re.M).group(1).split(", ")
    assert "integration" in tags and "smoke" not in tags


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["id"])
def test_row_documents_are_staged_templates(row: dict) -> None:
    documents = manifest(row["id"])["documents"]
    assert "pdd" in documents
    for path in documents.values():
        assert f"`{path}`" in row["documents"], f"prompt does not name {path}"
        template = template_of(path)
        assert template.is_file(), template
        assert PLACEHOLDER in template.read_text(encoding="utf-8")
    staged = {p.relative_to(HERE).as_posix() for p in (HERE / "corpus" / row["id"]).iterdir()}
    assert staged == {template_of(p).relative_to(HERE).as_posix() for p in documents.values()}


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["id"])
def test_title_is_the_pdds_own(row: dict) -> None:
    pdd = template_of(manifest(row["id"])["documents"]["pdd"]).read_text(encoding="utf-8")
    assert f"# {manifest(row['id'])['name_contains']} {PLACEHOLDER}\n" in pdd


@pytest.mark.parametrize("row", ROWS, ids=lambda r: r["id"])
def test_every_alias_is_in_the_documents(row: dict) -> None:
    text = re.sub(r"\s+", " ", staged_text(row["id"])).lower()
    expected = manifest(row["id"])
    for table in ("systems", "optional_systems"):
        for name, aliases in (expected.get(table) or {}).items():
            # Same whole-token rule as check_publish.names_alias.
            found = any(re.search(rf"(?<![a-z0-9]){re.escape(a.lower())}(?:e?s)?(?![a-z0-9])", text) for a in (aliases or [name]))
            assert found, f"{table} {name!r} not in the documents"
