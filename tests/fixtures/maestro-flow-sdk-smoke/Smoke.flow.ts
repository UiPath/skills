import { flow, out, script, types } from '@uipath/flow-sdk';

export default flow('sdk-smoke')
  .name('SdkSmoke')
  .version('1.0.0')
  .output({ message: types.string })
  .step('makeMessage', script({
    code: 'return { message: "ready" };',
  }))
  .return({ message: out('makeMessage', 'message') })
  .build();
