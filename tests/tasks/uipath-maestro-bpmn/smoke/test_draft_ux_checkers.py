#!/usr/bin/env python3
"""Unit tests for the draft-mode UX graders: check_draft_reply.py and
check_skeleton_kinds.py. Stdlib and pytest only.

Each check gets a passing and a failing fixture. Transcripts are built as
Claude Code session JSONL in a temp dir; the failing replies are the drift
real runs produced (status preamble, "Flow:" prose, a drawn diagram, a
gateway-variable line, events listed as boxes).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reply = _load("check_draft_reply", "check_draft_reply.py")
kinds = _load("check_skeleton_kinds", "check_skeleton_kinds.py")

URL = "https://alpha.uipath.com/org/studio_/designer/00000000-0000-0000-0000-000000000000"
BOXES = ["Record invoice [Execute script]", "Manager review [Action app]", "Auto approve [Execute script]"]

GATE_OK = """InvoiceIntakeSketch: outline ready (draft mode).
`InvoiceIntakeSketch/InvoiceIntakeSketch.bpmn`

- Record invoice [Execute script]: no resource needed
- Manager review [Action app]: none yet, create it or name one
- Auto approve [Execute script]: no resource needed

Is this the process you want?
1. **Build it**: make every step work.
2. **Change it**: tell me what to add, remove, or move.
3. **Keep it**: stop here with this outline."""

FINAL_OK = f"""ShippingQuote: built, validated, uploaded (draft mode).
{URL}

- Base price box now runs a script on the weight
- Surcharge box adds 15% for international orders

Assumed: base price is 5 per kg.  Unverified: none."""


class Transcript:
    """Builds Claude Code session records: one human prompt per turn."""

    def __init__(self, cwd: str = "/sandbox"):
        self.cwd = cwd
        self.records: list[dict] = []
        self._n = 0

    def _add(self, rtype: str, content, **extra) -> None:
        self._n += 1
        self.records.append({"type": rtype, "uuid": f"u{self._n}", "timestamp": f"2026-01-01T00:00:{self._n:02d}Z",
                             "cwd": self.cwd, "isSidechain": False, "message": {"role": rtype, "content": content},
                             **extra})

    def user(self, text: str) -> "Transcript":
        self._add("user", text)
        return self

    def say(self, text: str) -> "Transcript":
        self._add("assistant", [{"type": "text", "text": text}])
        return self

    def bash(self, command: str, result: str = "") -> "Transcript":
        tid = f"t{self._n + 1}"
        self._add("assistant", [{"type": "tool_use", "id": tid, "name": "Bash", "input": {"command": command}}])
        self._add("user", [{"type": "tool_result", "tool_use_id": tid, "content": result}])
        return self

    def write(self, directory: Path) -> Path:
        path = directory / "session.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in self.records), encoding="utf-8")
        return path


def upload_result(url: str = URL) -> str:
    return json.dumps({"Result": "Success", "Data": {"Action": "Imported", "DesignerUrl": url}})


def turns_of(t: Transcript) -> list:
    return reply.split_turns(t.records)


class TranscriptParsingTests(unittest.TestCase):
    def test_reply_is_the_text_after_the_last_tool_call(self):
        t = Transcript().user("go").say("Running preflight.").bash("uip login status").say(GATE_OK)
        self.assertEqual(turns_of(t)[0].reply, GATE_OK)

    def test_turns_split_on_human_prompts_only(self):
        t = (Transcript().user("go").bash("ls").say("one")
             .user("1").bash("uip maestro bpmn validate x").say("two"))
        got = turns_of(t)
        self.assertEqual([x.prompt for x in got], ["go", "1"])
        self.assertEqual([x.reply for x in got], ["one", "two"])

    def test_meta_and_sidechain_records_are_not_turns(self):
        t = Transcript().user("go")
        t._add("user", [{"type": "text", "text": "Base directory for this skill"}], isMeta=True)
        t.say("done")
        with tempfile.TemporaryDirectory() as d:
            path = Transcript.write(t, Path(d))
            extra = {"type": "user", "uuid": "side", "timestamp": "2026-01-01T00:00:59Z", "cwd": "/sandbox",
                     "isSidechain": True, "message": {"role": "user", "content": "subagent prompt"}}
            path.write_text(path.read_text() + "\n" + json.dumps(extra))
            got = reply.split_turns(reply.load_records(str(path)))
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].reply, "done")

    def test_live_transcript_is_found_by_cwd(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as sandbox:
            sandbox = os.path.realpath(sandbox)
            project = Path(home) / "projects" / "-renamed-project-dir"
            project.mkdir(parents=True)
            Transcript(cwd=sandbox).user("go").say("hello").write(project)
            other = Path(home) / "projects" / "-elsewhere"
            other.mkdir()
            Transcript(cwd="/elsewhere").user("other").say("not this").write(other)
            with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": home}), _cwd(sandbox):
                got = reply.split_turns(reply.load_records(None))
        self.assertEqual([x.reply for x in got], ["hello"])

    def test_records_after_a_cd_stay_in_the_turn(self):
        t = Transcript().user("go").bash("cd Project && uip maestro bpmn validate x.bpmn")
        t.cwd = "/sandbox/Project"
        t.say(GATE_OK)
        with tempfile.TemporaryDirectory() as d:
            got = reply.split_turns(reply.load_records(str(t.write(Path(d)))))
        self.assertEqual(got[0].reply, GATE_OK)

    def test_missing_transcript_fails_with_a_reason(self):
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as sandbox:
            with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": home}), patch.object(Path, "home", lambda: Path(home)), \
                    _cwd(sandbox):
                with self.assertRaises(reply.Fail):
                    reply.load_records(None)


@contextmanager
def _cwd(path: str):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class GateReplyTests(unittest.TestCase):
    def check(self, text: str, boxes=BOXES, uploaded=False) -> list[str]:
        return reply.check_gate(text, "InvoiceIntakeSketch", boxes, uploaded)

    def test_template_reply_passes(self):
        self.assertEqual(self.check(GATE_OK), [])

    def test_uploaded_reply_with_url_and_lookup_note_passes(self):
        text = (GATE_OK.replace("outline ready (draft", "outline ready, uploaded (draft")
                .replace("`InvoiceIntakeSketch/InvoiceIntakeSketch.bpmn`",
                         f"[Open in Studio Web]({URL})\nThe app lookup failed (504), so it is not checked."))
        self.assertEqual(self.check(text, uploaded=True), [])

    def test_status_preamble_fails(self):
        errors = self.check("Skeleton validated. Here is the outline:\n\n---\n\n" + GATE_OK)
        self.assertTrue(errors and "first line" in errors[0], errors)

    def test_second_note_or_status_line_fails(self):
        text = GATE_OK.replace("\n- Record", "\nValidated with one expected warning.\n- Record")
        self.assertTrue(any("outside the template" in e for e in self.check(text)))

    def test_flow_prose_and_gateway_variable_lines_fail(self):
        text = GATE_OK.replace(
            "\n- Record", "\nFlow: Start → Record invoice → Amount ≥ 1000? → Manager review\n\n- Record").replace(
            "\nIs this", "\nGateway variable: `InvoiceAmount` (number), assigned by Record invoice.\n\nIs this")
        errors = self.check(text)
        self.assertTrue(any("description of the flow" in e for e in errors), errors)
        self.assertGreaterEqual(len(errors), 2, errors)

    def test_drawn_diagram_fails(self):
        text = GATE_OK.replace("\n- Record", "\n```\nStart ──► Record invoice ──► ◇\n```\n- Record")
        self.assertTrue(self.check(text))

    def test_event_listed_as_a_box_fails(self):
        text = GATE_OK.replace("\n- Record", "\n- Daily 06:00 (timer start): not checked\n- Record")
        self.assertTrue(any("box line(s) for 3 task box" in e for e in self.check(text)))

    def test_missing_box_fails(self):
        text = GATE_OK.replace("- Auto approve [Execute script]: no resource needed", "- Approval: none")
        self.assertTrue(any("missing from the box lines" in e for e in self.check(text)))

    def test_options_must_be_the_three_fixed_ones(self):
        text = GATE_OK + "\n4. **Run it**: run it now."
        self.assertTrue(self.check(text))
        text = GATE_OK.replace("Keep it", "Park it")
        self.assertTrue(self.check(text))

    def test_missing_question_fails(self):
        self.assertTrue(self.check(GATE_OK.replace("Is this the process you want?", "Shall I build it?")))

    def test_heading_fails(self):
        self.assertTrue(self.check(GATE_OK.replace("\n- Record", "\n## Boxes\n- Record")))

    def test_upload_flag_must_match(self):
        self.assertTrue(self.check(GATE_OK, uploaded=True))

    def test_long_box_line_fails(self):
        text = GATE_OK.replace("no resource needed", "x" * 220, 1)
        self.assertTrue(any("longer than" in e for e in self.check(text)))

    def test_unknown_boxes_are_held_to_the_line_cap(self):
        self.assertEqual(reply.check_gate(GATE_OK, "InvoiceIntakeSketch", None, None), [])
        many = GATE_OK.replace("- Record", "\n".join(f"- Box {i}: none" for i in range(9)) + "\n- Record")
        self.assertTrue(reply.check_gate(many, "InvoiceIntakeSketch", None, None))


class FinalReplyTests(unittest.TestCase):
    def check(self, text: str) -> list[str]:
        return reply.check_final(text, "ShippingQuote", True, "draft")

    def test_template_reply_passes(self):
        self.assertEqual(self.check(FINAL_OK), [])

    def test_extra_section_fails(self):
        self.assertTrue(self.check(FINAL_OK + "\n\n## Next steps\n1. Publish it."))

    def test_next_steps_prose_fails(self):
        self.assertTrue(self.check(FINAL_OK + "\nWant me to publish and run it?"))

    def test_more_than_five_changes_fails(self):
        text = FINAL_OK.replace("- Base", "\n".join(f"- change {i}" for i in range(5)) + "\n- Base")
        self.assertTrue(any("change lines" in e for e in self.check(text)))

    def test_wrong_mode_and_missing_uploaded_fail(self):
        self.assertTrue(self.check(FINAL_OK.replace("(draft mode)", "(auto mode)")))
        self.assertTrue(self.check(FINAL_OK.replace(", uploaded", "")))

    def test_preamble_fails(self):
        self.assertTrue(self.check("Done! Here's the summary.\n\n" + FINAL_OK))


class DialogTests(unittest.TestCase):
    def dialog(self, final_text: str = FINAL_OK, answer: str = "1") -> Transcript:
        gate = GATE_OK.replace("`InvoiceIntakeSketch/InvoiceIntakeSketch.bpmn`", URL)
        return (Transcript().user("show me first")
                .bash("uip solution upload ShippingQuoteSolution --output json", upload_result()).say(gate)
                .user(answer)
                .bash("uip maestro bpmn registry pull --output json")
                .bash("uip solution upload ShippingQuoteSolution --output json", upload_result()).say(final_text))

    def test_designer_url_in_both_replies_passes(self):
        self.assertEqual(reply.check_designer_url(turns_of(self.dialog()), [1, 2]), [])

    def test_designer_url_missing_from_reply_fails(self):
        t = self.dialog(FINAL_OK.replace(URL, "ShippingQuote/ShippingQuote.bpmn"))
        self.assertTrue(reply.check_designer_url(turns_of(t), [1, 2]))

    def test_no_upload_in_turn_fails(self):
        t = Transcript().user("go").say(FINAL_OK)
        self.assertTrue(reply.check_designer_url(turns_of(t), [1]))

    def test_build_it_answered_with_the_report_passes(self):
        self.assertEqual(reply.check_after_approval(turns_of(self.dialog()), 1), [])

    def test_question_after_build_it_fails(self):
        t = self.dialog("Which Action app should the review use?").user("Your call").say(FINAL_OK)
        errors = reply.check_after_approval(turns_of(t), 1)
        self.assertTrue(any("came in turn 3" in e for e in errors), errors)

    def test_report_that_also_asks_fails(self):
        t = self.dialog(FINAL_OK + "\nShall I run it now?")
        self.assertTrue(reply.check_after_approval(turns_of(t), 1))

    def test_user_who_never_approved_fails(self):
        self.assertTrue(reply.check_after_approval(turns_of(self.dialog(answer="Change the surcharge")), 1))

    def test_forbidden_command_scoped_to_its_turn(self):
        got = turns_of(self.dialog())
        pattern = r"registry\s+(pull|search|get)\b"
        self.assertEqual(reply.check_commands(got[0], pattern), [])
        self.assertTrue(reply.check_commands(got[1], pattern))

    def test_cli_entry_point_reports_pass_and_fail(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.dialog().write(Path(d))
            with _cwd(d):
                self.assertEqual(reply.main(["final", "ShippingQuote", "--turn", "2", "--uploaded",
                                             "--mode", "draft", "--transcript", str(path)]), 0)
                self.assertEqual(reply.main(["gate", "ShippingQuote", "--turn", "1", "--no-bpmn",
                                             "--transcript", str(path)]), 1)


REGISTRY = {"Data": {"ExtensionTypes": [
    {"ExtensionType": "Actions.HITL", "Kind": "Action app", "Label": "Create action app task"},
    {"ExtensionType": "Orchestrator.StartJob", "Kind": "RPA workflow", "Label": "Start and wait for RPA workflow"},
    {"ExtensionType": "BPMN.ScriptTask", "Kind": None, "Label": "Execute script"},
    {"ExtensionType": "Orchestrator.BusinessRules", "Kind": None, "Label": "Execute business rule [Preview]"},
    {"ExtensionType": "Maestro.NotificationService", "Kind": None, "Label": "Notification service"},
    {"ExtensionType": "Maestro.CaseManagerPlaceholder", "Kind": None, "Label": "Case manager placeholder"},
    {"ExtensionType": "BPMN.Variables", "Kind": None, "Label": "BPMN Variables"},
]}}


class KindTests(unittest.TestCase):
    def setUp(self):
        self.toolbox, self.case_only = kinds.kind_sets(REGISTRY["Data"]["ExtensionTypes"])

    def check(self, boxes):
        return kinds.check(boxes, self.toolbox, self.case_only)

    def test_kinds_and_labels_from_the_list_pass(self):
        self.assertEqual(self.check(BOXES + ["Score risk [Execute business rule [Preview]]",
                                             "Classify [RPA workflow] → Classification",
                                             "Review [action app]"]), [])

    def test_box_without_a_kind_fails(self):
        self.assertTrue(self.check(["Record invoice"]))

    def test_invented_kind_fails(self):
        errors = self.check(["Send summary [Email]"])
        self.assertIn("not a Kind or Label", errors[0])

    def test_case_only_type_fails(self):
        errors = self.check(["Tell the manager [Notification service]", "Hold [Case manager placeholder]"])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("case-management" in e for e in errors), errors)

    def test_cli_entry_point_on_a_skeleton(self):
        bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_1">
    <bpmn:task id="A" name="Record invoice [Execute script]" />
    <bpmn:task id="B" name="Manager review [Action app]" />
  </bpmn:process>
</bpmn:definitions>"""
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "P").mkdir()
            (Path(d) / "P" / "P.bpmn").write_text(bpmn)
            (Path(d) / "P" / "project.uiproj").write_text("{}")
            (Path(d) / "reg.json").write_text(json.dumps(REGISTRY))
            with _cwd(d):
                self.assertEqual(kinds.main(["P", "--registry-json", "reg.json"]), 0)
                (Path(d) / "P" / "P.bpmn").write_text(bpmn.replace("[Action app]", "[Approval]"))
                self.assertEqual(kinds.main(["P", "--registry-json", "reg.json"]), 1)


if __name__ == "__main__":
    unittest.main()
