# Minimal shape

```ts
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('notify')
  .name('Notify')
  .flowMode('sequence')
  .var('status', 'string')
  .startEvent('start')
  .task('record', { set: { status: 'ready' } })
  .endEvent('done')
  .build();
```

In sequence mode each element continues to the next, so a process written top to bottom has no `.sequenceFlow()`; branch with `.choose()`, attach handlers in an activity's body, and read `bpmn check --graph` to see the wiring that resulted.
The explicit form — `.sequenceFlow('start', 'record')` after the elements, in the default mode — is what `bpmn decompile` writes for an import unless `--style nested` lifts it, and both forms mix freely.

## Nested shape

```ts
export default bpmn('approval')
  .var('action', 'string')
  .var('outcome', 'string', { default: 'RUNNING' })
  .startEvent('start')
  .humanTask('approve', { form: { fields: [], outcomes: ['Approved', 'Rejected'] }, outputs: { action: '=Action' } }, (t) => {
    t.onTimer('PT1H', { interrupting: false }, (b) => b.task('remind').endEvent('reminded'));
    t.onError(true, { errorVar: 'failure' }, (b) => b.endEvent('failed', { name: 'Approval failed' }));
  })
  .choose('approved', [
    { when: '=js:vars.action == "Approved"', label: 'Yes', body: (b) => b.task('post') },
    { otherwise: true, label: 'No', body: (b) => b.task('reject') },
  ])
  .endEvent('done')
  .sequenceFlow('start', 'approve')
  .sequenceFlow('approve', 'approved')
  .eventSubProcess('failures', { error: true }, (h) =>
    h.task('record', { set: { outcome: '=js:"FAILED: " + JSON.parse(vars.failures_Error).message' } }).endEvent('recorded', { name: 'Failure recorded' }))
  .build();
```
