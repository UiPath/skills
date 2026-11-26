"""Unit tests for the engine path of graph_check.py — `engine_outputs` and `grade_engine`.

These four functions carry the weight-5.0 criterion of three e2e tasks and were
reached by none of the suite's tests: the engine path only runs against a live
tenant, so nothing offline ever entered it. Every branch here is a branch that
decides whether a real run passes, and a defect in one is scored as the agent's.

`uip` is replaced throughout. What is under test is how the grader reads what
the CLI says, including the ways it says nothing useful.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graph_check as gc  # noqa: E402
import rules_check as rc  # noqa: E402

PROJECT = Path("LoanRules")


class _Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def debug_payload(decisions: list[dict]) -> str:
    return json.dumps({"Result": "Success", "Data": {"result": {"decisions": decisions}}})


@pytest.fixture
def cli(monkeypatch):
    """Replace `uip`; the test sets `cli.answer(argv) -> _Completed` and reads `cli.calls`."""

    class Fake:
        def __init__(self):
            self.calls = []
            self.answer = lambda argv: _Completed(0, debug_payload([]))

        def run(self, argv, **_):
            self.calls.append(argv)
            return self.answer(argv)

    fake = Fake()
    monkeypatch.setattr(gc.subprocess, "run", fake.run)
    return fake


def fails_with(message_fragment, call):
    """`call` must exit non-zero through `fail`, printing `message_fragment`."""
    with pytest.raises(SystemExit) as raised:
        call()
    assert raised.value.code == 1
    return message_fragment


class TestEngineOutputs:
    def test_a_table_answers_under_its_output_columns(self, cli):
        cli.answer = lambda argv: _Completed(0, debug_payload(
            [{"decisionName": "risk", "outputs": {"riskBand": "Low"}},
             {"decisionName": "rate", "outputs": {"interestRate": 5.5}}]))

        assert gc.engine_outputs(PROJECT, {"creditScore": 700}) == {"riskBand": "Low", "interestRate": 5.5}

    def test_a_literal_expression_answers_under_the_decision_name(self, cli):
        # Not a dict: the one value, keyed by the decision that returned it.
        cli.answer = lambda argv: _Completed(0, debug_payload(
            [{"decisionName": "fee", "outputs": 400.0}]))

        assert gc.engine_outputs(PROJECT, {"loanAmount": 20000}) == {"fee": 400.0}

    def test_the_inputs_reach_the_cli_as_json(self, cli):
        gc.engine_outputs(PROJECT, {"creditScore": 700, "income": 0})

        argv = cli.calls[0]
        assert argv[:3] == ["uip", "rules", "debug"]
        assert json.loads(argv[argv.index("--inputs") + 1]) == {"creditScore": 700, "income": 0}
        assert "--output" in argv and argv[argv.index("--output") + 1] == "json"

    def test_two_decisions_answering_under_one_name_are_refused(self, cli):
        # `dict.update` let whichever came last win, so a wrong value from the decision the case
        # names passed whenever another decision happened to answer under that name.
        cli.answer = lambda argv: _Completed(0, debug_payload(
            [{"decisionName": "risk", "outputs": {"riskBand": "Low"}},
             {"decisionName": "shadow", "outputs": {"riskBand": "High"}}]))

        with pytest.raises(SystemExit):
            gc.engine_outputs(PROJECT, {"creditScore": 700})

    def test_a_non_zero_exit_says_the_engine_returned_no_answer(self, cli, capsys):
        cli.answer = lambda argv: _Completed(2, "", "ECONNREFUSED")

        with pytest.raises(SystemExit):
            gc.engine_outputs(PROJECT, {"creditScore": 700})

        printed = capsys.readouterr().out
        assert "exited 2" in printed
        assert "no answer to grade" in printed
        assert "ECONNREFUSED" in printed

    def test_a_zero_exit_that_is_not_json_is_a_transport_failure(self, cli, capsys):
        # The branch that used to raise a bare JSONDecodeError out of the grader, which the
        # harness scores exactly like a wrong value — so a broken CLI read as a failed agent.
        cli.answer = lambda argv: _Completed(0, "Checking for updates.\nNo updates found.\n")

        with pytest.raises(SystemExit):
            gc.engine_outputs(PROJECT, {"creditScore": 700})

        printed = capsys.readouterr().out
        assert "did not return JSON" in printed
        assert "transport failure, not a wrong rule" in printed
        assert "Checking for updates" in printed

    def test_an_empty_payload_answers_nothing_rather_than_raising(self, cli):
        cli.answer = lambda argv: _Completed(0, json.dumps({"Result": "Success"}))

        assert gc.engine_outputs(PROJECT, {"creditScore": 700}) == {}


class TestGradeEngine:
    @staticmethod
    def _answer_correctly(argv):
        inputs = json.loads(argv[argv.index("--inputs") + 1])
        band = next(b for case, b in rc.POLICY
                    if case["creditScore"] == inputs["creditScore"] and case["income"] == inputs["income"])
        return _Completed(0, debug_payload([
            {"decisionName": "risk", "outputs": {"riskBand": band}},
            {"decisionName": "rate", "outputs": {
                "interestRate": gc.interest_rate(band, inputs["loanAmount"])}},
        ]))

    @pytest.fixture
    def project(self, tmp_path, monkeypatch):
        folder = tmp_path / "LoanRules"
        folder.mkdir()
        (folder / "project.uiproj").write_text(
            json.dumps({"Name": "LoanRules", "ProjectType": "BusinessRules"}), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        return folder

    def test_a_correct_engine_passes_every_case(self, project, cli, capsys):
        cli.answer = self._answer_correctly

        gc.grade_engine()

        assert f"all {len(gc.ENGINE_CASES)} cases" in capsys.readouterr().out
        assert len(cli.calls) == len(gc.ENGINE_CASES)

    def test_one_wrong_rate_fails_and_names_the_case(self, project, cli, capsys):
        def wrong(argv):
            completed = self._answer_correctly(argv)
            payload = json.loads(completed.stdout)
            payload["Data"]["result"]["decisions"][1]["outputs"]["interestRate"] = 99.0
            return _Completed(0, json.dumps(payload))

        cli.answer = wrong

        with pytest.raises(SystemExit):
            gc.grade_engine()

        assert "interestRate=99.0" in capsys.readouterr().out

    def test_a_number_where_the_case_wants_a_band_is_not_equal(self, project, cli):
        # `same_value`, through the engine path: Python holds `True == 1`, FEEL does not.
        cli.answer = lambda argv: _Completed(0, debug_payload(
            [{"decisionName": "risk", "outputs": {"riskBand": True}},
             {"decisionName": "rate", "outputs": {"interestRate": 1}}]))

        with pytest.raises(SystemExit):
            gc.grade_engine()

    def test_the_project_name_is_honoured(self, tmp_path, monkeypatch, cli):
        # Parsed and then ignored, `graph_check.py engine OtherRules` graded LoanRules silently.
        folder = tmp_path / "OtherRules"
        folder.mkdir()
        (folder / "project.uiproj").write_text(
            json.dumps({"Name": "OtherRules", "ProjectType": "BusinessRules"}), encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        cli.answer = self._answer_correctly

        gc.grade_engine("OtherRules")

        assert folder.is_dir()
        assert {argv[3] for argv in cli.calls} == {"OtherRules"}

    def test_a_missing_project_fails_before_the_engine_is_called(self, tmp_path, monkeypatch, cli):
        monkeypatch.chdir(tmp_path)

        with pytest.raises(SystemExit):
            gc.grade_engine()

        assert cli.calls == []


class TestCheckModelCalled:
    """The static half of the model grade: declared, required, and actually called."""

    @staticmethod
    def graph(logic: str, requirement: str = '<knowledgeRequirement><requiredKnowledge href="#bkm_rate"/></knowledgeRequirement>') -> object:
        import xml.etree.ElementTree as ET
        return ET.fromstring(
            f'<definitions xmlns="{rc.DMN_NS}" id="d" name="FeeRules" namespace="urn:f">'
            f'  <decision id="decision_fee" name="fee">'
            f'    {requirement}'
            f'    <literalExpression><text>{logic}</text></literalExpression>'
            f'  </decision>'
            f'  <businessKnowledgeModel id="bkm_rate" name="rate">'
            f'    <variable name="rate" typeRef="number"/>'
            f'    <encapsulatedLogic><formalParameter name="amount" typeRef="number"/>'
            f'      <literalExpression><text>0.02</text></literalExpression></encapsulatedLogic>'
            f'  </businessKnowledgeModel>'
            f'</definitions>')

    def test_a_decision_that_requires_and_calls_the_model_passes(self):
        root = self.graph("loanAmount * rate(loanAmount)")
        fee = gc.decision_for_output(root, "fee")

        assert gc.check_model_called(root, fee, "rate") == ["loanAmount"]

    def test_a_model_the_file_does_not_declare_fails(self):
        root = self.graph("loanAmount * rate(loanAmount)")
        fee = gc.decision_for_output(root, "fee")

        with pytest.raises(SystemExit):
            gc.check_model_called(root, fee, "bkm_rate")  # the id, not the name

    def test_a_model_that_is_called_but_not_required_fails(self):
        root = self.graph("loanAmount * rate(loanAmount)", requirement="")
        fee = gc.decision_for_output(root, "fee")

        with pytest.raises(SystemExit):
            gc.check_model_called(root, fee, "rate")

    def test_a_model_required_but_never_called_fails(self, capsys):
        # Declared and wired is not called. The engine returns the right fee either way, so the
        # engine grade alone passed a rule whose model never ran.
        root = self.graph("loanAmount * 0.02")
        fee = gc.decision_for_output(root, "fee")

        with pytest.raises(SystemExit):
            gc.check_model_called(root, fee, "rate")

        assert "never calls rate(...)" in capsys.readouterr().out

    def test_a_name_ending_in_the_models_is_not_a_call(self):
        root = self.graph("loanAmount * netRate(loanAmount)")
        fee = gc.decision_for_output(root, "fee")

        with pytest.raises(SystemExit):
            gc.check_model_called(root, fee, "rate")

    def test_whitespace_before_the_parenthesis_is_still_a_call(self):
        root = self.graph("loanAmount * rate (loanAmount)")
        fee = gc.decision_for_output(root, "fee")

        assert gc.check_model_called(root, fee, "rate") == ["loanAmount"]


class TestRunValidate:
    """The other CLI boundary in the shared graders. `rules_check.py validate` is a weight-2.0
    or 3.0 criterion in six tasks, and nothing exercised what it does when `uip` answers badly."""

    @pytest.fixture
    def project(self, tmp_path):
        folder = tmp_path / "RiskRules"
        folder.mkdir()
        return folder

    def test_a_clean_validate_passes(self, project, monkeypatch):
        monkeypatch.setattr(rc.subprocess, "run",
                            lambda argv, **_: _Completed(0, json.dumps({"Result": "Success"})))

        rc.run_validate(project)  # no exit

    def test_the_project_and_json_flag_reach_the_cli(self, project, monkeypatch):
        seen = []
        monkeypatch.setattr(rc.subprocess, "run",
                            lambda argv, **_: (seen.append(argv), _Completed(0, "{}"))[1])

        rc.run_validate(project)

        assert seen[0][:3] == ["uip", "rules", "validate"]
        assert seen[0][3] == str(project)
        assert seen[0][-2:] == ["--output", "json"]

    def test_diagnostics_reach_the_failure_message(self, project, monkeypatch, capsys):
        payload = json.dumps({"Data": {"Diagnostics": [{"Code": "DMN_FEEL_SYNTAX"}]}})
        monkeypatch.setattr(rc.subprocess, "run", lambda argv, **_: _Completed(1, payload))

        with pytest.raises(SystemExit):
            rc.run_validate(project)

        assert "DMN_FEEL_SYNTAX" in capsys.readouterr().out

    def test_a_failure_that_printed_only_to_stderr_is_still_reported(self, project, monkeypatch, capsys):
        # `completed.stdout or completed.stderr` — the branch that reads stderr was never taken
        # by any test, and a CLI that writes its error there would have failed with an empty
        # message telling the reader nothing.
        monkeypatch.setattr(rc.subprocess, "run",
                            lambda argv, **_: _Completed(1, "", "EACCES: permission denied"))

        with pytest.raises(SystemExit):
            rc.run_validate(project)

        assert "EACCES" in capsys.readouterr().out

    def test_a_non_json_failure_does_not_raise_out_of_the_grader(self, project, monkeypatch, capsys):
        # `run_validate` never parses, so this is a regression guard: adding a `json.loads` here
        # would reintroduce the hole `engine_outputs` had.
        monkeypatch.setattr(rc.subprocess, "run",
                            lambda argv, **_: _Completed(1, "Checking for updates.\n"))

        with pytest.raises(SystemExit) as raised:
            rc.run_validate(project)

        assert raised.value.code == 1
        assert "Checking for updates" in capsys.readouterr().out

    def test_a_cli_that_is_not_installed_is_not_swallowed(self, project, monkeypatch):
        # Not caught on purpose: `validate` is the criterion, so a missing CLI must not read as
        # a clean validate. It surfaces as a traceback rather than as a pass.
        def missing(argv, **_):
            raise FileNotFoundError("uip")

        monkeypatch.setattr(rc.subprocess, "run", missing)

        with pytest.raises(FileNotFoundError):
            rc.run_validate(project)
