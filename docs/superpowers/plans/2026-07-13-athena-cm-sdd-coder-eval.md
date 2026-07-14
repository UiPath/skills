# Athena CM SDD-to-case coder eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Add a uipath-maestro-case integration task that builds a validated Athena caseplan from a staged SDD and deterministically verifies the design.

**Architecture:** A task-local markdown fixture supplies the approved design. Two executable, dependency-free Python graders run after the agent: one protects the fixture's non-negotiable content, the other verifies the generated caseplan using the existing _shared.case_check readers and helpers. The YAML coordinates staging, validation, grading, and cleanup.

**Tech Stack:** coder_eval task YAML, Python 3 standard library, existing uip CLI, tests/tasks/uipath-maestro-case/_shared/case_check.py.

## Global Constraints

- Create the task below tests/tasks/uipath-maestro-case/athena_cm_event/; keep exactly one task YAML in that leaf.
- Use the staged sdd.md as the sole agent input; do not encode tenant IDs, connection IDs, or a deployable router process.
- Stop at uip maestro case validate; do not ask questions, debug, publish, deploy, or create external resources.
- Grade filesystem and command outcomes only. Validation-command evidence is advisory; a successful validator and checker runs are the gates.
- Preserve the repository's 2D data.tasks lane representation and resolve process names through bindings rather than generated binding IDs.
- Run the checker unit tests before and after implementation, the task linter, and the task when the authenticated coder-eval environment is available.

---

### Task 1: Specify checker behavior with isolated unit tests

**Files:**
- Create: tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py

**Interfaces:**
- Consumes the two executable scripts at tests/tasks/uipath-maestro-case/athena_cm_event/check_athena_cm_event_sdd.py and check_athena_cm_event_case.py.
- Produces run(script, cwd), write_sdd(path, include_router=True), and write_caseplan(stage_c_task_3_once=True) test helpers.

- [ ] **Step 1: Write the failing test**

Create a standard-library unittest module. Its run helper executes a script in a temporary sandbox without raising, preserving stdout and stderr for assertions:

~~~python
ROOT = Path(__file__).parent
SDD_CHECK = ROOT / "check_athena_cm_event_sdd.py"
CASE_CHECK = ROOT / "check_athena_cm_event_case.py"

def run(script: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)], cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
~~~

The module must create a valid SDD and a valid AthenaCMEventCase/AthenaCMEventCase/caseplan.json in its temporary directory. The plan fixture contains one event trigger, two input variables (InstanceExternalId and eventPayload), three case-management:Stage nodes, 2D task lanes, bindings with default process names, and case-manager metadata.

~~~python
def test_sdd_checker_accepts_complete_fixture(self):
    self.write_sdd(self.workdir / "sdd.md")
    result = run(SDD_CHECK, self.workdir)
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

def test_sdd_checker_rejects_missing_router_table(self):
    self.write_sdd(self.workdir / "sdd.md", include_router=False)
    result = run(SDD_CHECK, self.workdir)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("router", result.stdout + result.stderr)

def test_case_checker_accepts_expected_structure(self):
    self.write_caseplan()
    result = run(CASE_CHECK, self.workdir)
    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

def test_case_checker_rejects_wrong_run_only_once_flag(self):
    self.write_caseplan(stage_c_task_3_once=False)
    result = run(CASE_CHECK, self.workdir)
    self.assertNotEqual(result.returncode, 0)
    self.assertIn("StageCTask3", result.stdout + result.stderr)
~~~

- [ ] **Step 2: Run test to verify it fails**

Run: python3 tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py

Expected: FAIL because both checker scripts do not exist yet.

- [ ] **Step 3: Commit the failing test**

~~~bash
git add tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py
git commit -m "test: specify Athena CM eval checkers"
~~~

### Task 2: Implement the fixture-integrity checker and structural case checker

**Files:**
- Create: tests/tasks/uipath-maestro-case/athena_cm_event/check_athena_cm_event_sdd.py
- Create: tests/tasks/uipath-maestro-case/athena_cm_event/check_athena_cm_event_case.py
- Create: tests/tasks/uipath-maestro-case/athena_cm_event/fixtures/sdd.md

**Interfaces:**
- check_athena_cm_event_sdd.py reads exactly one recursive sdd.md below its current working directory, prints OK: on success, and exits via sys.exit("FAIL: ...") on a missing contract item.
- check_athena_cm_event_case.py reads the generated plan through _shared.case_check.read_caseplan, prints OK: on success, and exits via sys.exit("FAIL: ...") on one failed structural assertion.

- [ ] **Step 1: Implement check_athena_cm_event_sdd.py minimally**

Use glob.glob("**/sdd.md", recursive=True) excluding .venv and a require(pattern, description) helper using re.search(..., re.I | re.S). Require these concrete patterns:

~~~python
REQUIREMENTS = {
    "InstanceExternalId": r"\bInstanceExternalId\b",
    "event payload": r"\beventPayload\b",
    "Stage A": r"Stage\s*A",
    "Stage B": r"Stage\s*B",
    "Stage C": r"Stage\s*C",
    "StageATask1": r"\bStageATask1\b",
    "StageATask2": r"\bStageATask2\b",
    "StageBTask1": r"\bStageBTask1\b",
    "StageBTask2": r"\bStageBTask2\b",
    "StageCTask1": r"\bStageCTask1\b",
    "StageCTask2": r"\bStageCTask2\b",
    "StageCTask3": r"\bStageCTask3\b",
    "CaseManagerProc": r"\bCaseManagerProc\b",
    "case manager output": r"\bcaseManagerDecisions\b",
    "event router": r"event1[\s\S]*event5",
}
~~~

Also require selected-tasks-completed, selected-stage-completed, current-stage-entered, and required-stages-completed. Print OK: Athena CM SDD fixture contract preserved.

- [ ] **Step 2: Implement check_athena_cm_event_case.py minimally**

Import assert_tasks_nested, find_node_by_label, find_stages, find_triggers, first_rule_of_condition, get_case_exit_conditions, get_variables, and read_caseplan from _shared.case_check. Add focused helpers:

~~~python
def stage_task(plan: dict, stage: dict, label: str) -> dict:
    for lane in (stage.get("data") or {}).get("tasks") or []:
        for task in lane or []:
            data = task.get("data") or {}
            if label in {data.get("displayName"), data.get("label"), task_process_name(plan, task)}:
                return task
    fail(f"missing task {label!r} in stage {stage_label(stage)!r}")

def binding_default(plan: dict, reference: str) -> str | None:
    binding_id = reference.removeprefix("=bindings.").split(".", 1)[0]
    return next((b.get("default") for b in plan.get("bindings") or []
                 if b.get("id") == binding_id), None)

def task_process_name(plan: dict, task: dict) -> str | None:
    name = (task.get("data") or {}).get("name")
    return binding_default(plan, name) if isinstance(name, str) else None

def has_rule(conditions: list[dict], rule_name: str, **fields: object) -> bool:
    return any((rule or {}).get("rule") == rule_name and all(
        (rule or {}).get(key) == value for key, value in fields.items()
    ) for condition in conditions for group in condition.get("rules") or []
      for rule in group or [])
~~~

Check one Intsvc.EventTrigger, both root inputs, exactly three primary stages named StageA, StageB, and StageC, and the seven named process tasks in their declared stages. Assert this task-flag mapping:

~~~python
{
  "StageATask1": (True, False), "StageATask2": (True, True),
  "StageBTask1": (False, False), "StageBTask2": (True, False),
  "StageCTask1": (False, True), "StageCTask2": (False, True),
  "StageCTask3": (True, True),
}
~~~

Assert A2 selects A1; Stage B exits on required-tasks-completed and marks complete; Stage C enters after Stage B completes, C1 uses current-stage-entered, and Stage C exits on required-tasks-completed and marks complete; the case exits on required-stages-completed and marks complete. Inspect metadata.caseManagerData directly: it must be enabled, contain exactly one process task resolving to CaseManagerProc, accept caseCurrentExecutionState, caseRulesDecisions, eventPayload, and expose caseManagerDecisions as an output.

- [ ] **Step 3: Create the staged fixtures/sdd.md**

Use the Case Management SDD format. State the exact task/flag inventory and declarative rules above. Include a Case Manager section with the exact input and output names. End with this external-router decision table:

~~~text
event1 -> run StageATask1 and StageBTask1
event2 -> run StageBTask1
event3 -> run StageBTask2
event4 -> cancel event1:StageBTask1
event5 -> run StageCTask2
StageATask1 completed -> run StageATask2
StageBTask2 completed -> enter StageC and run StageCTask1
StageCTask2 completed -> run StageCTask3
~~~

State that the table documents the external CaseManagerProc boundary; this task generates only the case plan.

- [ ] **Step 4: Run the checker unit tests to verify they pass**

Run: python3 tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py

Expected: PASS; the valid fixtures pass and each focused mutation produces its expected FAIL: message.

- [ ] **Step 5: Commit the checker implementation and fixture**

~~~bash
git add tests/tasks/uipath-maestro-case/athena_cm_event
git commit -m "feat: add Athena CM eval checkers"
~~~

### Task 3: Add and validate the coder-eval task definition

**Files:**
- Create: tests/tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml

**Interfaces:**
- Consumes fixtures/sdd.md, both checkers, $TASK_DIR, and $SKILLS_REPO_PATH supplied by coder_eval.
- Produces an integration task requiring a valid AthenaCMEventCase/AthenaCMEventCase/caseplan.json and cleanup of created solutions.

- [ ] **Step 1: Create the task YAML from the repository template**

Use task_id skill-case-athena-cm-event, tags uipath-maestro-case, integration, lifecycle:generate, mode:build, shape:multi-node, and feature:trigger. Stage fixtures through sandbox.template_sources. Prompt the agent to load uipath-maestro-case, build AthenaCMEventCase from the supplied SDD only, take hard stops as pre-approved, skip debug and publish, and finish only after validation. Do not add the UiPath CLI to sandbox packages.

Add these criteria in order:

~~~yaml
- type: command_executed
  command_pattern: 'uip\s+maestro\s+case\s+validate[^\n]*AthenaCMEventCase/AthenaCMEventCase/caseplan\.json'
  weight: 1.0
  pass_threshold: 0
- type: run_command
  command: 'uip maestro case validate AthenaCMEventCase/AthenaCMEventCase/caseplan.json --output json'
  expected_exit_code: 0
  weight: 3.0
- type: run_command
  command: 'python3 $TASK_DIR/check_athena_cm_event_sdd.py'
  expected_exit_code: 0
  weight: 2.0
- type: run_command
  command: 'python3 $TASK_DIR/check_athena_cm_event_case.py'
  expected_exit_code: 0
  weight: 5.0
~~~

Use the shared cleanup_solutions.py in post_run.

- [ ] **Step 2: Run static validation**

Run: git diff --check

Run: python3 tests/tasks/uipath-maestro-case/athena_cm_event/test_checkers.py

Expected: both commands exit 0.

- [ ] **Step 3: Run the repository task linter and single task when available**

Run the repository task-lint command for tests/tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml. Then run:

~~~bash
cd tests
SKILLS_REPO_PATH=$(cd .. && pwd) .venv/bin/coder-eval run \
  tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml \
  -e experiments/default.yaml
~~~

Expected: the task produces a valid caseplan and both deterministic graders pass. If credentials or the harness are unavailable, report the exact blocking command/output rather than claim a passing eval.

- [ ] **Step 4: Commit the task definition**

~~~bash
git add tests/tasks/uipath-maestro-case/athena_cm_event/athena_cm_event.yaml
git commit -m "test: add Athena CM SDD build eval"
~~~

## Self-review

- The task stages an SDD, builds only a local caseplan, validates it, and runs both required graders.
- The SDD checker covers the fixture contract; the case checker covers caseplan topology, flags, rules, variables, trigger, and Case Manager bindings.
- The explicit event-router boundary prevents a false claim of runtime event-driven coverage.
- The plan contains no tenant-specific data, deploy/debug steps, unbounded task discovery, or undefined checker interfaces.
