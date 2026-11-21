> when: writing a new process chain from scratch without a decompiled seed or staged example

## Minimal shape

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
