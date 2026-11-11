/**
 * NotifyChannel — a Maestro BPMN process with an Integration Service **connector**
 * service task: post a Slack message to a channel, between a start and end event.
 *
 * `.connector(...)` emits a `bpmn:sendTask` carrying a `uipath:activity` of type
 * `Intsvc.ActivityExecution` — the connector wiring (connectorKey + connection +
 * method/path/objectName) in a `uipath:context`, the inputs split into
 * path/query/body, output rows, and a process-level `uipath:bindings` block for
 * the connection/folder. The op's shape is resolved from the connector library at
 * compile ($FLOW_SDK_LIBRARY_JSON), the same data the Flow node and Case task use.
 *
 * `connection`/`folder` are symbolic binding names — `check` and `compile` accept them
 * as `=bindings.<name>` (with a CONNECTION_BINDING_NOT_GUID warning), but `refresh`
 * and a live run need the real connection id, which `uip maestro registry prepare`
 * writes into bindings.json. Compile with
 * `uip maestro bpmn compile NotifyChannel.bpmn.ts -o NotifyChannel.bpmn
 * --library "$FLOW_SDK_LIBRARY_JSON"`, then `uip maestro bpmn validate`.
 */
import { bpmn } from '@uipath/maestro-builder-sdk/bpmn';

export default bpmn('notify-channel')
  .name('NotifyChannel')
  .startEvent('start', { name: 'Start' })
  .connector(
    'post',
    'uipath-salesforce-slack',
    'send-message-to-channel',
    { channel: '#general', messageToSend: 'BPMN says hi', send_as: 'bot' },
    { connection: 'slack', folder: 'shared', name: 'Post to Slack' },
  )
  .endEvent('done', { name: 'Done' })
  .sequenceFlow('start', 'post')
  .sequenceFlow('post', 'done')
  .build();
