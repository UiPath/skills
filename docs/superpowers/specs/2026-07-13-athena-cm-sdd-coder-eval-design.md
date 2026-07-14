# Athena CM event case: SDD-to-case coder eval

## Goal

Add an integration coder-eval for `uipath-maestro-case` that takes a staged,
approved SDD for an Athena-style case-manager design and produces a valid local
case plan. The test ends at `uip maestro case validate`; it neither deploys nor
starts a debug session.

The SDD is the sole input. The evaluation must prove that the agent preserved
the case-plan-facing parts of the design instead of merely emitting a schema
valid case plan.

## Scope

The task will live at:

```text
tests/tasks/uipath-maestro-case/athena_cm_event/
  athena_cm_event.yaml
  fixtures/sdd.md
  check_athena_cm_event_sdd.py
  check_athena_cm_event_case.py
```

The task stages `fixtures/sdd.md` into the sandbox and asks the agent to build
the solution and project `AthenaCMEventCase`. Hard stops after the supplied SDD
are explicitly pre-approved for the non-interactive harness. It must not call
`AskUserQuestion`, debug, deploy, or publish.

The expected generated artifact is:

```text
AthenaCMEventCase/AthenaCMEventCase/caseplan.json
```

The task is tagged `uipath-maestro-case`, `integration`, `lifecycle:generate`,
`mode:build`, `shape:multi-node`, and `feature:trigger`.

## Fixture SDD

The fixture will describe a deliberately resource-neutral case plan:

- external case identity `InstanceExternalId` and event payload input
  `eventPayload`;
- three primary stages: Stage A, Stage B, and Stage C;
- seven generic tasks: two in Stage A, two in Stage B, and three in Stage C;
- required/run-only-once settings from the golden case;
- stage/task conditions: A2 after A1, Stage B completion, Stage C after Stage
  B, C1 at Stage C entry, and case completion after required stages complete;
- an enabled case-manager contract named `CaseManagerProc` with inputs
  `caseCurrentExecutionState`, `caseRulesDecisions`, and `eventPayload`, and
  output `caseManagerDecisions`;
- a documentation-only router decision table for the five external events and
  the two task-completion handoffs.

The SDD does not include tenant IDs, connection IDs, or a deployable router
process. Unknown resources must remain placeholders according to the skill's
normal rules.

## Grading

`athena_cm_event.yaml` will grade observable output, not the agent's prose:

1. Advisory evidence that the agent invoked case validation.
2. `uip maestro case validate ... --output json` succeeds on the generated
   caseplan.
3. `check_athena_cm_event_sdd.py` succeeds on the staged `sdd.md`.
4. `check_athena_cm_event_case.py` succeeds on the generated caseplan.
5. Shared cleanup removes any created solution after the run.

### `check_athena_cm_event_sdd.py`

This is a fixture-integrity guard. It reads the staged markdown after the agent
has run and fails if the SDD no longer contains the core Athena contract:

- the two case arguments and three-stage/seven-task inventory;
- the task settings and dependency/exit rules;
- the named case-manager input/output contract; and
- the event-routing decision table.

It prevents an agent from replacing the supplied SDD, reducing it to a generic
case, or silently using a different design. It does not assess prose quality or
infer case-plan JSON.

### `check_athena_cm_event_case.py`

This is the generated-artifact structural grader. It locates the expected
`caseplan.json`, resolves binding references by their display names, and checks:

- external identity and `eventPayload` argument/trigger wiring;
- Stage A/B/C plus the seven named tasks in their proper stages;
- required and run-only-once flags;
- A1-to-A2, Stage B, Stage C, C1, and case-completion rules;
- enabled Case Manager metadata with the named process and its declared inputs
  and output.

It reports a precise `FAIL:` reason and exits non-zero on a mismatch; otherwise
it prints a short `OK:` summary. It complements, rather than replaces, the CLI
schema validator.

## Boundary: external events and debug

The golden case's `event1` through `event5` routing is implemented by a
separate `CaseManagerProc` BPMN process. A caseplan static check cannot prove
that router's runtime decisions. Therefore this eval verifies the case plan's
manager interface and documents the routing table in the fixture, but it does
not claim event-driven runtime execution.

A true runtime event-routing eval is a separate future test: it would need to
stage and deploy a router process, inject external events with a real Case ID,
and use `uip maestro case debug` or an equivalent runtime endpoint to verify
the task-selection transitions.

## Verification before merge

- Exercise both checker scripts against a known-good generated plan and focused
  malformed inputs.
- Run the repository task linter.
- Run the single coder-eval task with the default experiment when credentials
  and the authenticated CLI are available; otherwise record that the structural
  validation was run locally and leave the full harness run for CI.
