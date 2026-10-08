"""Unit tests for execute_check.py: a setting counts only where the project reads it as an asset,
and open items count only in the file the open-items guide describes.

Run: pytest tests/tasks/uipath-genome/_shared/ -v
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import execute_check  # noqa: E402

NAMES = ["Sales_InputFolder", "Sales_OutputFolder"]
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def workbook(path: Path, sheets: dict[str, list[str]]) -> None:
    """A minimal .xlsx: one sheet per entry, its cells in column A as shared strings."""
    strings = [s for cells in sheets.values() for s in cells]
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{MAIN_NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   + "".join(f'<sheet name="{n}" sheetId="{i}" r:id="rId{i}"/>' for i, n in enumerate(sheets, 1)) + "</sheets></workbook>")
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + "".join(f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml"/>' for i in range(1, len(sheets) + 1)) + "</Relationships>")
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{MAIN_NS}">' + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
        index = 0
        for i, cells in enumerate(sheets.values(), 1):
            rows = "".join(f'<row r="{r}"><c r="A{r}" t="s"><v>{index + r - 1}</v></c></row>' for r in range(1, len(cells) + 1))
            z.writestr(f"xl/worksheets/sheet{i}.xml", f'<worksheet xmlns="{MAIN_NS}"><sheetData>{rows}</sheetData></worksheet>')
            index += len(cells)


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "Sales"
    root.mkdir()
    (root / "project.json").write_text(json.dumps({"name": "Sales", "main": "Main.xaml"}), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return root


def settings() -> int:
    return execute_check.cmd_settings(argparse.Namespace(expect=NAMES))


def test_assets_sheet_counts(project):
    (project / "Data").mkdir()
    workbook(project / "Data" / "Config.xlsx", {"Settings": ["Name"], "Assets": ["Name", "Asset", *NAMES]})
    assert settings() == 0


def test_settings_sheet_does_not_count(project):
    (project / "Data").mkdir()
    workbook(project / "Data" / "Config.xlsx", {"Settings": ["Name", *NAMES], "Assets": ["Name", "Asset"]})
    assert settings() == 1


def test_xaml_asset_names_count(project):
    (project / "Main.xaml").write_text(
        '<Activity xmlns:ui="http://schemas.uipath.com/workflow/activities">'
        f'<ui:GetRobotAsset AssetName="&quot;{NAMES[0]}&quot;" DisplayName="Get input folder" />'
        '<ui:GetRobotAsset DisplayName="Get output folder"><ui:GetRobotAsset.AssetName><InArgument x:TypeArguments="x:String">'
        f'<CSharpValue x:TypeArguments="x:String">"{NAMES[1]}"</CSharpValue></InArgument></ui:GetRobotAsset.AssetName></ui:GetRobotAsset>'
        "</Activity>", encoding="utf-8")
    assert settings() == 0


def test_name_beside_an_unrelated_asset_read_does_not_count(project):
    (project / "Main.xaml").write_text(
        '<Activity xmlns:ui="http://schemas.uipath.com/workflow/activities">'
        '<ui:GetRobotAsset AssetName="&quot;Sales_Mailbox&quot;" />'
        f'<ui:LogMessage Message="&quot;{NAMES[0]} {NAMES[1]}&quot;" /></Activity>', encoding="utf-8")
    assert settings() == 1


def test_coded_constant_counts(project):
    (project / "Main.cs").write_text(
        f'const string InputAsset = "{NAMES[0]}";\nvar input = system.GetAsset(InputAsset);\n'
        f'var output = system.GetAsset("{NAMES[1]}");\n', encoding="utf-8")
    assert settings() == 0


def open_items(*flags: str) -> int:
    return execute_check.cmd_open_items(argparse.Namespace(expect=NAMES, sections="--sections" in flags))


def test_open_items_file_counts(project):
    sections = "\n\n".join(execute_check.SECTIONS)
    (project.parent / "sales-open-items.md").write_text(f"# Open items: Sales in production\n\n{sections}\n\n{' '.join(NAMES)}\n", encoding="utf-8")
    assert open_items() == 0
    assert open_items("--sections") == 0


def test_brief_naming_the_tokens_does_not_count(project):
    (project.parent / "migration").mkdir()
    (project.parent / "migration" / "run-brief.md").write_text(f"# Run brief\n\nAssets: {' '.join(NAMES)}\n", encoding="utf-8")
    assert open_items() == 1


def test_open_items_inside_the_project_fail(project):
    (project / "open-items.md").write_text(f"# Open items: Sales\n\n{' '.join(NAMES)}\n", encoding="utf-8")
    assert open_items() == 1
