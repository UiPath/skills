"""Unit tests for one_shot_check.py. Run with ``pytest`` from any directory.

Pins that a DMN shaped like the pipeline's passes each mode, and that the plausible failures
(a hand-built DMN, a missing policy_decision, wrong outcomes, quote-style citations) fail.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import one_shot_check as osc  # noqa: E402

NS = 'xmlns="https://www.omg.org/spec/DMN/20230324/MODEL/" xmlns:uipdm="http://uipath.com/schema/1.0/dmn-ext/decision-model"'


def dmn(exporter=osc.EXPORTER, decision_name="policy_decision",
        answers='"Approve", "Deny", "Refer"', inputs=("request_amount",), ref='page="1" box="1,2,3,4"'):
    data = "".join(f'<inputData id="i{n}" name="{n}"/>' for n in inputs)
    return ET.fromstring(
        f'<definitions {NS} exporter="{exporter}">{data}'
        f'<decision id="d0" name="cond_C001"><extensionElements><uipdm:sourceRefs><uipdm:sourceRef {ref}/>'
        f'</uipdm:sourceRefs></extensionElements></decision>'
        f'<decision id="decision_final" name="{decision_name}">'
        f'<allowedAnswers>{answers}</allowedAnswers></decision></definitions>'
    )


def failing(fn, root):
    with pytest.raises(SystemExit):
        fn(root)


def test_pipeline_shaped_dmn_passes_every_mode():
    root = dmn()
    osc.grade_pipeline(root)
    osc.grade_declared(root)
    osc.grade_refs(root)


def test_pipeline_fails_for_a_hand_built_dmn():
    failing(osc.grade_pipeline, dmn(exporter="agent"))


def test_pipeline_fails_without_a_policy_decision():
    failing(osc.grade_pipeline, dmn(decision_name="other"))


def test_declared_fails_on_other_outcomes():
    failing(osc.grade_declared, dmn(answers='"Approved", "Denied", "Refer"'))


def test_declared_fails_without_inputs():
    failing(osc.grade_declared, dmn(inputs=()))


def test_refs_fail_when_a_ref_carries_a_quote():
    failing(osc.grade_refs, dmn(ref='page="1" box="1,2,3,4" quote="x"'))


def test_refs_fail_without_a_box():
    failing(osc.grade_refs, dmn(ref='page="1"'))
