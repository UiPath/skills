/**
 * CAPABILITY: place a phone call, talk to the person, hang up.
 *
 * The call is identified by a `callContext` OBJECT. Pass the WHOLE thing —
 * `out('dial', 'callContext')` — never a field inside it. The node's schema
 * types that field as `object`, so a scalar such as
 * `out('dial', 'callContext.conversationId')` passes the file's schema and then
 * fails at dispatch; `check` catches it as `VOICE_CALL_CONTEXT_NOT_OBJECT`.
 *
 * `createOutgoingCall` dials out and publishes the context. An inbound flow
 * instead uses `.trigger(voiceTrigger())`, whose start step publishes the same
 * `callContext`. A persona belongs to its voice model, and `maxIterations` is
 * capped at 8.
 *
 * Generic scenario: remind a customer their pottery is ready for collection.
 */
import {
  flow, createOutgoingCall, voiceAgent, endCall, input, out, types,
} from '@uipath/flow-sdk';

export default flow('pottery-studio-callback')
  .name('PotteryStudioCallback')
  .version('1.0.0')
  .input({ customerName: types.string, customerPhone: types.string, pieceCount: types.number })
  .output({ callSummary: types.string })
  .step('dial', createOutgoingCall({
    from: '+15550001111',
    to: input('customerPhone'),
  }))
  .step('talk', voiceAgent({
    systemPrompt:
      'Tell {{input.customerName}} that {{input.pieceCount}} finished pieces are ready '
      + 'for collection, and offer a weekday or weekend pickup.',
    inputs: { customerName: input('customerName'), pieceCount: input('pieceCount') },
    callContext: out('dial', 'callContext'),
    voice: { model: 'gemini-3.1-flash-live-preview', persona: 'Kore' },
    maxIterations: 4,
  }))
  .step('hangUp', endCall({ callContext: out('dial', 'callContext') }))
  .return({ callSummary: out('talk') })
  .build();
