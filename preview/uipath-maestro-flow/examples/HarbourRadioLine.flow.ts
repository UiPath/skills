/**
 * CAPABILITY: answer an INBOUND phone call (`core.trigger.voice`).
 *
 * `voiceTrigger()` takes no arguments — the platform hands the flow a call that
 * has already connected, and the start step publishes its `callContext`. That
 * is the only difference from the outbound shape in
 * `PotteryStudioCallback.flow.ts`, which dials first and reads the context off
 * the dial step instead.
 *
 * Pass `out('start', 'callContext')` whole. It is an OBJECT; reaching inside it
 * for `conversationId` passes the file's schema and then fails at dispatch.
 *
 * Generic scenario: answer the harbour's information line.
 */
import { flow, voiceTrigger, voiceAgent, endCall, out, types } from '@uipath/flow-sdk';

export default flow('harbour-radio-line')
  .name('HarbourRadioLine')
  .version('1.0.0')
  .output({ callSummary: types.string })
  .trigger(voiceTrigger())
  .step('greet', voiceAgent({
    systemPrompt:
      'Answer the harbour information line. Give tide times and berth availability, '
      + 'and take a message for the harbourmaster if you cannot help.',
    callContext: out('start', 'callContext'),
    voice: { model: 'gemini-3.1-flash-live-preview', persona: 'Kore' },
  }))
  .step('hangUp', endCall({ callContext: out('start', 'callContext') }))
  .return({ callSummary: out('greet') })
  .build();
