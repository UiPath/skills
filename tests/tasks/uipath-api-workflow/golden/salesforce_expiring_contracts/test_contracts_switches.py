#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import switches  # noqa: E402


def send():
    return {"call": "UiPath.IntSvc", "with": {"connector": "uipath-microsoft-outlook365", "method": "POST",
                                              "endpoint": "/send-mail-v2"}}


def if_(number, when, then=(), otherwise=(), then_exit=True, default=True):
    cases = [{"case": {"when": when, "then": f"If_{number}#Then"}}]
    if default:
        cases.append({"default": {"then": f"If_{number}#Else"}})
    then_branch = {"do": list(then), **({"then": "exit"} if then_exit else {})}
    return {f"If_{number}#Wrapper": {"do": [{f"If_{number}": {"switch": cases}}, {f"If_{number}#Then": then_branch},
                                            {f"If_{number}#Else": {"do": list(otherwise), "then": "exit"}}]}}


def task(name, activity):
    return {name: activity}


def workflow(*tasks):
    return {"do": [{"Sequence_1": {"do": [{"WorkflowStart": {"set": "${{}}"}}, *tasks]}}]}


class ConditionTests(unittest.TestCase):
    def holds(self, when, **env):
        return switches.condition("${" + when + "}", env)

    def test_reads_an_input_and_its_negation(self):
        self.assertTrue(self.holds("$workflow.input.send", send=True))
        self.assertFalse(self.holds("$workflow.input.send", send=False))
        self.assertTrue(self.holds("!$workflow.input.skipEmails", skipEmails=False))
        self.assertIsNone(self.holds("$workflow.input.send"))
        self.assertIsNone(self.holds("!$workflow.input.send", other=True))

    def test_compares_like_javascript_and_leaves_cross_type_loose_equality_unknown(self):
        self.assertTrue(self.holds("$workflow.input.disableSlack === false", disableSlack=False))
        self.assertFalse(self.holds("$workflow.input.dryRun !== true", dryRun=True))
        self.assertTrue(self.holds("$workflow.input.dryRun == true", dryRun=True))
        self.assertFalse(self.holds("$workflow.input.dryRun === 'true'", dryRun=True))
        self.assertTrue(self.holds("!$workflow.input.dryRun === false", dryRun=True))
        self.assertIsNone(self.holds("$workflow.input.dryRun == 'true'", dryRun=True))
        self.assertTrue(self.holds("$workflow.input.mode === 'a&&b'", mode="a&&b"))

    def test_reads_optional_chaining_brackets_boolean_and_nullish_defaults(self):
        for when in ("$workflow?.input?.send", "$workflow.input['send']", '$workflow.input?.["send"]',
                     "Boolean($workflow.input.send)", "!!$workflow.input.send", "($workflow.input.send ?? true)",
                     "( ($workflow.input.send) )"):
            with self.subTest(when=when):
                self.assertFalse(self.holds(when, send=False))
                self.assertTrue(self.holds(when, send=True))

    def test_and_or_decide_through_an_operand_they_cannot_read(self):
        unknown = "$context.outputs.query_1.content.length > 0"
        self.assertFalse(self.holds(f"$workflow.input.send && {unknown}", send=False))
        self.assertIsNone(self.holds(f"$workflow.input.send && {unknown}", send=True))
        self.assertFalse(self.holds(f"{unknown} && $workflow.input.send", send=False))
        self.assertTrue(self.holds(f"$workflow.input.dryRun || {unknown}", dryRun=True))
        self.assertIsNone(self.holds(f"$workflow.input.dryRun || {unknown}", dryRun=False))
        self.assertTrue(self.holds(f"!($workflow.input.send && {unknown})", send=False))

    def test_what_it_does_not_evaluate_is_unknown(self):
        for when in ("$workflow.input.send ? true : false", "$workflow.input.send = true", "(() => true)()",
                     "`${$workflow.input.send}` === 'true'", "/x/.test($workflow.input.send)",
                     "$workflow.input.send, true", "$context.variables.send", "$workflow.input.send.valueOf()",
                     "$workflow.input.send ?? true || false", "$workflow.input.send === true === true"):
            with self.subTest(when=when):
                self.assertIsNone(self.holds(when, send=False))
        self.assertIsNone(switches.condition("$workflow.input.send", {"send": False}))
        self.assertIsNone(switches.condition(False, {}))
        self.assertIsNone(switches.condition("${a} || ${b}", {}))


class NumberTests(unittest.TestCase):
    def test_numbers_with_a_leading_zero_are_unknown(self):
        self.assertTrue(switches.condition("${$workflow.input.n === 10}", {"n": 10}))
        self.assertIsNone(switches.condition("${$workflow.input.n === 010}", {"n": 10}))
        self.assertIsNone(switches.condition("${$workflow.input.n === 00}", {"n": 0}))


class UnreachedTests(unittest.TestCase):
    def reached(self, wf, activity, **env):
        return id(activity) not in switches.unreached(wf, env)

    def test_a_branch_runs_only_when_its_case_can_hold(self):
        email = send()
        wf = workflow(if_(1, "${$workflow.input.send}", [task("Send_1", email)]))
        self.assertFalse(self.reached(wf, email, send=False))
        self.assertTrue(self.reached(wf, email, send=True))
        self.assertTrue(self.reached(wf, email))

    def test_a_then_branch_without_exit_falls_through_into_else(self):
        write = send()
        wf = workflow(if_(1, "${$workflow.input.dryRun}", [task("Log_1", {"set": {}})], [task("Write_1", write)],
                          then_exit=False))
        self.assertTrue(self.reached(wf, write, dryRun=True))

    def test_an_inner_exit_ends_only_its_own_branch(self):
        later, after_branch = send(), send()
        then = [task("Skip_1", {"set": {}, "then": "exit"}), task("Later_1", later)]
        wf = workflow(if_(1, "${$workflow.input.flag}", then, [task("Else_1", after_branch)], then_exit=False))
        self.assertFalse(self.reached(wf, later, flag=True))
        self.assertTrue(self.reached(wf, after_branch, flag=True))

    def test_a_task_that_ends_the_run_cuts_off_what_follows(self):
        email = send()
        response = {"response": "${$context.variables}", "then": "end"}
        wf = workflow(if_(1, "${$workflow.input.dryRun}", [task("Response_1", response)]), task("Send_1", email))
        self.assertFalse(self.reached(wf, email, dryRun=True))
        self.assertTrue(self.reached(wf, email, dryRun=False))

    def test_a_jump_skips_the_tasks_between_and_an_unknown_target_reaches_everything(self):
        email = send()
        wf = workflow(task("First_1", {"set": {}, "then": "Third_1"}), task("Send_1", email), task("Third_1", {"set": {}}))
        self.assertFalse(self.reached(wf, email))
        wf = workflow(task("First_1", {"set": {}, "then": "Nowhere_1"}), task("Response_1", {"then": "end"}),
                      task("Send_1", email))
        self.assertTrue(self.reached(wf, email))

    def test_a_switch_that_may_match_nothing_without_a_default_counts_as_falling_through(self):
        email = send()
        wf = workflow(if_(1, "${$workflow.input.send}", [task("Send_1", email)], default=False))
        self.assertTrue(self.reached(wf, email, send=False))

    def test_a_default_before_a_case_leaves_both_targets_possible(self):
        email = send()
        wf = workflow(if_(1, "${$workflow.input.dryRun}", [], [task("Send_1", email)]))
        switch = wf["do"][0]["Sequence_1"]["do"][1]["If_1#Wrapper"]["do"][0]["If_1"]["switch"]
        switch.reverse()
        self.assertTrue(self.reached(wf, email, dryRun=True))

    def test_catches_and_loop_bodies_are_reached_with_their_task(self):
        in_try, in_catch, in_loop, after_loop = send(), send(), send(), send()
        throw = {"run": {"script": {"code": "throw new Error('x')"}}}
        wf = workflow(task("Try_Catch_1", {"try": [task("Js_1", throw), task("Send_1", in_try)],
                                           "catch": {"as": "error", "do": [task("Send_2", in_catch)]}}),
                      task("For_Each_1", {"for": {"each": "item", "in": "${[]}"},
                                          "do": [{"For_Each_1#Body": {"do": [task("Send_3", in_loop),
                                                                              task("End_1", {"then": "end"})]}}]}),
                      task("Send_4", after_loop))
        for activity in (in_try, in_catch, in_loop, after_loop):
            self.assertTrue(self.reached(wf, activity))

    def test_an_activity_outside_the_lists_it_follows_counts_as_reached(self):
        email = send()
        wf = workflow(task("Response_1", {"then": "end"}), task("Fork_1", {"fork": {"branches": [task("Send_1", email)]}}))
        self.assertFalse(self.reached(wf, email))
        wf = workflow(if_(1, "${$workflow.input.send}"), task("Fork_1", {"fork": {"branches": [task("Send_1", email)]}}))
        self.assertTrue(self.reached(wf, email, send=False))
        self.assertTrue(self.reached({"elsewhere": [task("Send_1", email)]}, email))


    def test_a_task_whose_if_is_false_is_skipped_and_one_that_may_be_runs(self):
        guarded, disabled, literal = {**send(), "if": "${$workflow.input.send}"}, {**send(), "if": "${false}"}, \
            {**send(), "if": "false"}
        wf = workflow(task("Send_1", guarded), task("Send_2", disabled), task("Send_3", literal))
        self.assertFalse(self.reached(wf, guarded, send=False))
        self.assertTrue(self.reached(wf, guarded, send=True))
        self.assertTrue(self.reached(wf, guarded))
        self.assertFalse(self.reached(wf, disabled))
        self.assertTrue(self.reached(wf, literal))

    def test_a_skipped_task_does_not_end_the_run(self):
        email = send()
        wf = workflow(task("Response_1", {"response": "${1}", "if": "${$workflow.input.dryRun}", "then": "end"}),
                      task("Send_1", email))
        self.assertFalse(self.reached(wf, email, dryRun=True))
        self.assertTrue(self.reached(wf, email, dryRun=False))
        self.assertTrue(self.reached(wf, email))


ARGUMENTS = '${{ "$context": $context, "$workflow": $workflow, "$input": $input }}'


class TrustTests(unittest.TestCase):
    def guarded(self):
        return workflow(if_(1, "${$workflow.input.send}", [task("Send_1", send())]))

    def test_a_workflow_shaped_like_the_designer_writes_it_is_trusted(self):
        wf = self.guarded()
        for name, arguments in (("Js_1", ARGUMENTS), ("Js_2", ARGUMENTS.replace('"', '\\"'))):
            wf["do"][0]["Sequence_1"]["do"].insert(0, task(name, {
                "run": {"script": {"code": "const { daysAhead = 30 } = $workflow.input; return $input.days ?? daysAhead;",
                                   "language": "javascript", "arguments": arguments}},
                "export": {"as": '{ ...$context, outputs: { ...$context?.outputs, "' + name + '": $output } }'}}))
        wf["do"][0]["Sequence_1"]["do"].insert(0, task("WorkflowStart", {
            "set": "${{}}", "output": {"as": "${$input}"},
            "export": {"as": "{ ...$context, variables: { ...$context.variables, ...$output } }"}}))
        self.assertTrue(switches.trusted(wf))

    def test_shapes_the_analysis_does_not_follow_are_not_trusted(self):
        def changed(edit):
            wf = self.guarded()
            edit(wf["do"][0]["Sequence_1"]["do"])
            return wf

        for edit in (lambda tasks: tasks[1]["If_1#Wrapper"]["do"][0].update(metadata={}),
                     lambda tasks: tasks[1]["If_1#Wrapper"]["do"][0]["If_1"].update({"if": "${false}"}),
                     lambda tasks: tasks[1]["If_1#Wrapper"]["do"][0]["If_1"].update(then="exit"),
                     lambda tasks: tasks.append(task("Set_1", {"set": {}, "then": "continue"})),
                     lambda tasks: tasks.append(task("end", {"set": {}}))):
            with self.subTest(edit=edit):
                self.assertFalse(switches.trusted(changed(edit)))

    def test_code_that_could_rewrite_an_input_is_not_trusted(self):
        for code in ("$workflow.input.send = true;", "$input['send'] = true;", "delete $workflow.input.send;",
                     "const input = $workflow.input; input.send = true;", "Object.assign($input, { send: true });",
                     "const o = $context.outputs.If_1; o.send = true;", "({ ...$context }).outputs.If_1.send = true;",
                     "[$input.send] = [true];", "(f()).send = true;", "return $input;"):
            with self.subTest(code=code):
                wf = self.guarded()
                wf["do"][0]["Sequence_1"]["do"].insert(0, task("Js_1", {"run": {"script": {"code": code}}}))
                self.assertFalse(switches.trusted(wf))
        for arguments in ('${{ "$workflow": $context }}', '${{ "$input": $input, "x": $context.outputs.If_1 }}'):
            with self.subTest(arguments=arguments):
                wf = self.guarded()
                wf["do"][0]["Sequence_1"]["do"].insert(0, task("Js_1", {"run": {"script": {
                    "code": "return 1;", "arguments": arguments}}}))
                self.assertFalse(switches.trusted(wf))
        for export in ("{ ...$context, stash: $output }", "{ ...$context, stash: { ...$context.outputs } }"):
            with self.subTest(export=export):
                wf = self.guarded()
                wf["do"][0]["Sequence_1"]["do"].insert(0, task("Set_1", {"set": {}, "export": {"as": export}}))
                self.assertFalse(switches.trusted(wf))

    def test_switch_off_pins_nothing_in_a_workflow_it_cannot_trust(self):
        email = send()
        wf = workflow(task("Js_1", {"run": {"script": {"code": "$workflow.input.send = true;"}}}),
                      if_(1, "${$workflow.input.send}", [task("Send_1", email)]))
        self.assertEqual(switches.switch_off(wf, [("Send_1", email)], {}, ["send"]), ({}, ["Send_1"]))


class SwitchOffTests(unittest.TestCase):
    def test_without_effects_nothing_is_pinned(self):
        self.assertEqual(switches.switch_off(workflow(), [], {"daysAhead": 30}, ["send"]), ({"daysAhead": 30}, []))

    def test_the_value_comes_from_the_condition_not_the_name(self):
        for when, name, value in (("!$workflow.input.skipEmails", "skipEmails", True),
                                  ("$workflow.input.disableSlack === false", "disableSlack", True),
                                  ("$workflow.input.isTestModeDisabled", "isTestModeDisabled", False),
                                  ("$workflow.input.sendReminders", "sendReminders", False)):
            with self.subTest(when=when):
                email = send()
                wf = workflow(if_(1, "${" + when + "}", [task("Send_1", email)]))
                self.assertEqual(switches.switch_off(wf, [("Send_1", email)], {}, [name]), ({name: value}, []))

    def test_a_declared_switch_that_no_condition_reads_covers_nothing(self):
        for name in ("dryRun", "includePreviewText", "isTestModeDisabled"):
            with self.subTest(name=name):
                write = send()
                wf = workflow(task("Close_1", write))
                self.assertEqual(switches.switch_off(wf, [("Close_1", write)], {}, [name]), ({}, ["Close_1"]))

    def test_a_switch_covers_only_what_its_if_routes_around(self):
        email, write = send(), send()
        wf = workflow(if_(1, "${$workflow.input.send}", [task("Send_1", email)]), task("Task_1", write))
        inputs, left = switches.switch_off(wf, [("Send_1", email), ("Task_1", write)], {}, ["send"])
        self.assertEqual((inputs, left), ({"send": False}, ["Task_1"]))

    def test_the_fewest_switches_are_pinned_and_inputs_already_chosen_stay(self):
        email, write = send(), send()
        wf = workflow(if_(1, "${$workflow.input.notify}", [task("Send_1", email)]),
                      if_(2, "${!$workflow.input.dryRun}", [task("Task_1", write)]),
                      if_(3, "${$workflow.input.verbose}", [task("Log_1", {"set": {}})]))
        effects = [("Send_1", email), ("Task_1", write)]
        self.assertEqual(switches.switch_off(wf, effects, {"daysAhead": 30}, ["dryRun", "notify", "verbose"]),
                         ({"daysAhead": 30, "dryRun": True, "notify": False}, []))
        self.assertEqual(switches.switch_off(wf, effects[:1], {}, ["dryRun", "notify", "verbose"]),
                         ({"notify": False}, []))

    def test_only_declared_booleans_the_caller_did_not_set_are_tried(self):
        email = send()
        wf = workflow(if_(1, "${$workflow.input.send}", [task("Send_1", email)]))
        self.assertEqual(switches.switch_off(wf, [("Send_1", email)], {}, []), ({}, ["Send_1"]))
        self.assertEqual(switches.switch_off(wf, [("Send_1", email)], {"send": True}, ["send"]),
                         ({"send": True}, ["Send_1"]))

    def test_condition_inputs_lists_what_the_switches_and_guards_read(self):
        wf = workflow(if_(1, "${$workflow.input.a && $workflow.input['b'] || $context.variables.c}"),
                      if_(2, "${$workflow?.input?.d}"), task("Send_1", {**send(), "if": "${!$workflow.input.e}"}))
        self.assertEqual(switches.condition_inputs(wf), {"a", "b", "d", "e"})

    def test_a_guard_on_the_activity_itself_is_a_switch(self):
        email = {**send(), "if": "${$workflow.input.sendEmails}"}
        wf = workflow(task("Send_1", email))
        self.assertEqual(switches.switch_off(wf, [("Send_1", email)], {}, ["sendEmails"]), ({"sendEmails": False}, []))


if __name__ == "__main__":
    unittest.main()
