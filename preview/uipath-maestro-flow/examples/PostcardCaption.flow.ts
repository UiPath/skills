/**
 * CAPABILITY: an `inlineAgent` — an LLM step defined in this project, with a
 * typed output contract.
 *
 *   systemPrompt / userPrompt : the instruction and the turn (use `{{input.x}}`)
 *   inputs                    : values wired into the prompt from the flow
 *   returns                   : the TYPED object the agent must produce — read
 *                               downstream as `$vars.<step>.output.<field>`
 *
 * A local run cannot call the model, so a `--dry-run` returns `{}` and the reads
 * below are genuinely absent offline — which is the honest bar: a green run
 * proves the agent node is WIRED and its contract is declared, not that the model
 * answered. This one carries no tools or escalation (those are the agent-resource
 * family); it is the plain shape.
 *
 * Generic scenario: draft a short caption for a travel postcard.
 */
import { flow, inlineAgent, script, out, input, types } from '@uipath/flow-sdk';

export default flow('postcard-caption')
  .name('PostcardCaption')
  .version('1.0.0')
  .input({ place: types.string, mood: types.string })
  .output({ caption: types.string })

  .step('write', inlineAgent({
    model: 'gpt-5.4',
    systemPrompt:
      'You write postcard captions. Given a place and a mood, return ONLY a JSON '
      + 'object with keys "caption" (one cheerful sentence, no more than 15 words) '
      + 'and "tone" (one word). No other text.',
    userPrompt: 'Place: {{input.place}}\nMood: {{input.mood}}',
    inputs: { place: input('place'), mood: input('mood') },
    returns: { caption: 'string', tone: 'string' },
  }))

  // Reads only the agent's own declared returns — the one contract a local run
  // can honestly assert.
  .step('render', script({
    code: 'return "[" + String($vars.write.output.tone) + "] " + String($vars.write.output.caption);',
  }))
  .return({ caption: out('render') })

  .build();
