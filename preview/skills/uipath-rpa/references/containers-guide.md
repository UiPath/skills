# State Machine, Parallel and Flowchart

Each is a step like any other, `s.step(id, StateMachine({…}))`, and each declares `Variables` in scope everywhere inside it.

## State Machine

```ts
import { StateMachine, Int32, vb } from '@uipath/rpa-builder-sdk';

s.step('machine', StateMachine({
  InitialState: 'init',
  Variables: { index: [Int32, 0], retries: [Int32, 0] },
  States: {
    init: { DisplayName: 'Initialization', Entry: (e) => e…, Transitions: [{ To: 'get' }] },
    get: {
      Entry: (e) => e…,
      Transitions: [
        { To: 'process', DisplayName: 'New Transaction', Condition: vb('item IsNot Nothing') },
        { To: 'end', DisplayName: 'No Data', Condition: vb('item Is Nothing') },
      ],
    },
    process: { Entry: (e) => e…, Transitions: [{ To: 'get', Action: (a) => a.step('next', Assign({ to: (v) => v.index, value: (v) => v.index + 1 })) }] },
    end: { IsFinal: true, Entry: (e) => e… },
  },
}))
```

- `States` names each state; `InitialState` and each transition's `To` name one. A state is `{ DisplayName?, Entry?, Exit?, Transitions?, IsFinal? }`, a transition `{ To, DisplayName?, Condition?, Trigger?, Action? }`; a state's transitions are tried in order.
- The machine's `Variables` are in scope in every state, its entries, exits and transitions.
- When a state has more than one transition without a `Trigger`, every one of them needs a `Condition`: there is no `else`. Give the fallback the others' conditions negated, `vb('Not aborted AndAlso Not retrying')`; `check` reports a missing one as `TRANSITION_CONDITION_MISSING`.
- For a REFramework-style process, the states are Initialization, Get Transaction Data, Process Transaction and End Process.

## Parallel

```ts
s.step('both', Parallel({
  Variables: { done: [Int32, 0] },
  CompletionCondition: (v) => v.done >= 2,
  Branches: [(b) => b.step('a', …), (b) => b.step('b1', …).step('b2', …)],
}))
```

- Every branch starts at once; the Parallel ends when all have ended, or when `CompletionCondition` holds after any one ends, which cancels the rest.
- A branch with several steps is a Sequence of them, as any slot is. Its `Variables` are in scope in every branch.

## Flowchart

```ts
import { Flowchart, Assign, LogMessage, String } from '@uipath/rpa-builder-sdk';

s.step('route', Flowchart({
  StartNode: 'anything',
  Variables: { reason: String },
  Nodes: {
    anything: { DisplayName: 'Anything to approve?', Condition: (v) => v.in_Amount > 0, True: 'approve', False: 'reject' },
    approve: { Action: (a) => a.step('ok', Assign({ to: (v) => v.out_Route, value: 'approved' })), Next: 'report' },
    reject: { Action: (a) => a.step('no', Assign({ to: (v) => v.out_Route, value: 'rejected' })), Next: 'report' },
    report: { Action: (a) => a.step('log', LogMessage({ Message: (v) => v.out_Route })) },
  },
}))
```

- `Nodes` names each node; `StartNode`, `Next`, `True` and `False` name one. A step is `{ Action?, Next? }`, a decision `{ Condition, True?, False?, DisplayName? }`; a node with nowhere to go ends the flowchart.
- Node names become `x:Name`s, so they must be identifiers: letters, digits and `_`, not starting with a digit.
- Several nodes may go to the same one, and a link may go back to an earlier node, which makes a loop.
- The flowchart's `Variables` are in scope in every node.
- A variable spec can be `{ type, default, readOnly: true }` for a constant, here or in any `Variables`, or `.variable(name, type, default, { readOnly: true })`.

