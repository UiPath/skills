"""Copy-chain derivation in check_df_contractregistry_crud_filters."""

from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_GRADER = Path(__file__).parent / "check_df_contractregistry_crud_filters.py"
UPDATE_OUTPUT = "Var_UpdateResponse"


def _load():
    spec = importlib.util.spec_from_file_location("check_df_contractregistry_crud_filters", _GRADER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()


def _sources(copies: list[tuple[str, str]]) -> dict[str, list[str]]:
    outputs = "".join(f'<uipath:output var="{var}" source="{source}" />' for var, source in copies)
    root = ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{checker.NS["bpmn"]}" xmlns:uipath="{checker.NS["uipath"]}">'
        f"<bpmn:process id=\"P\"><bpmn:task id=\"T\"><bpmn:extensionElements>{outputs}"
        "</bpmn:extensionElements></bpmn:task></bpmn:process></bpmn:definitions>"
    )
    return checker.var_sources(root)


def _chain(hops: int) -> list[tuple[str, str]]:
    names = [UPDATE_OUTPUT] + [f"Var_Copy{i}" for i in range(1, hops + 1)]
    return [(names[i], f"=vars.{names[i - 1]}.Id") for i in range(1, hops + 1)]


def _derives(var_id: str, copies: list[tuple[str, str]]) -> bool:
    return checker.derives_from(var_id, {UPDATE_OUTPUT}, _sources(copies), checker.COPY_CHAIN_HOPS)


@pytest.mark.parametrize("hops,expected", [(0, True), (1, True), (3, True), (4, False)])
def test_copy_chain_hop_limit(hops, expected) -> None:
    tip = f"Var_Copy{hops}" if hops else UPDATE_OUTPUT
    assert _derives(tip, _chain(hops)) is expected


def test_every_writer_of_a_variable_is_followed() -> None:
    copies = [("Var_Id", "=vars.Var_CreateResponse.Id"), ("Var_Id", f"=vars.{UPDATE_OUTPUT}.Id")]
    assert _derives("Var_Id", copies)


def test_unrelated_variable_does_not_derive() -> None:
    assert not _derives("Var_Title", [("Var_Title", "=vars.Var_NewTitle")])


def test_prefix_named_variable_is_not_the_update_output() -> None:
    assert checker.VAR_REF_RE.findall(f"=vars.{UPDATE_OUTPUT}Old.Id") == [f"{UPDATE_OUTPUT}Old"]
    assert not _derives(f"{UPDATE_OUTPUT}Old", [])
