# State Machine, Parallel and Flowchart

Each is an activity like any other, `s.StateMachine(id, variables, {…})`, and the variables it declares after its id are in scope everywhere inside it.

## State Machine

```ts
import { Assign, Int32, Sequence, vb } from '@uipath/rpa-builder-sdk';

s.StateMachine('machine', { index: [Int32, 0], retries: [Int32, 0] }, {
  InitialState: 'init',
  States: {
    init: { DisplayName: 'Initialization', Entry: Sequence('Sequence_2', 'Initialize', (e) => e…), Transitions: [{ To: 'get' }] },
    get: {
      Entry: Sequence('Sequence_3', 'Retrieve Data', (e) => e…),
      Transitions: [
        { To: 'process', DisplayName: 'New Transaction', Condition: vb('item IsNot Nothing') },
        { To: 'end', DisplayName: 'No Data', Condition: vb('item Is Nothing') },
      ],
    },
    process: { Entry: Sequence('Sequence_4', (e) => e…), Transitions: [{ To: 'get', Action: Assign('next', { to: (v) => v.index, value: (v) => v.index + 1 }) }] },
    end: { IsFinal: true, Entry: … },
  },
})
```

- `States` names each state; `InitialState` and each transition's `To` name one. A state is `{ DisplayName?, Entry?, Exit?, Transitions?, IsFinal? }`, a transition `{ To, DisplayName?, Condition?, Trigger?, Action? }`; `Entry`, `Exit`, `Trigger` and `Action` are each one activity. A state's transitions are tried in order.
- The machine's variables are in scope in every state, its entries, exits and transitions.
- When a state has more than one transition without a `Trigger`, every one of them needs a `Condition`: there is no `else`. Give the fallback the others' conditions negated, `vb('Not aborted AndAlso Not retrying')`; `check` reports a missing one as `TRANSITION_CONDITION_MISSING`.
- For a REFramework-style process, the states are Initialization, Get Transaction Data, Process Transaction and End Process.

## Parallel

```ts
s.Parallel('both', { done: [Int32, 0] }, {
  CompletionCondition: (v) => v.done >= 2,
  Branches: [LogMessage('a', …), Sequence('Sequence_5', (b) => b.Assign('b1', …).Assign('b2', …))],
})
```

- Every branch starts at once; the Parallel ends when all have ended, or when `CompletionCondition` holds after any one ends, which cancels the rest.
- Each branch is one activity; a branch of several steps is a `Sequence`. The Parallel's variables are in scope in every branch.

## Flowchart

```ts
import { Assign, LogMessage, String } from '@uipath/rpa-builder-sdk';

s.Flowchart('route', { reason: String }, {
  StartNode: 'anything',
  Nodes: {
    anything: { DisplayName: 'Anything to approve?', Condition: (v) => v.in_Amount > 0, True: 'approve', False: 'reject' },
    approve: { Action: Assign('ok', { to: (v) => v.out_Route, value: 'approved' }), Next: 'report' },
    reject: { Action: Assign('no', { to: (v) => v.out_Route, value: 'rejected' }), Next: 'report' },
    report: { Action: LogMessage('log', { Message: (v) => v.out_Route }) },
  },
})
```

- `Nodes` names each node; `StartNode`, `Next`, `True` and `False` name one. A step is `{ Action?, Next? }`, a decision `{ Condition, True?, False?, DisplayName? }`; a node with nowhere to go ends the flowchart.
- Node names become `x:Name`s, so they must be identifiers: letters, digits and `_`, not starting with a digit.
- Several nodes may go to the same one, and a link may go back to an earlier node, which makes a loop.
- The flowchart's variables are in scope in every node.
- A variable spec can be `{ type, default, readOnly: true }` for a constant, here or in any container's variables, or `.variable(name, type, default, { readOnly: true })`.

