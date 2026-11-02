/**
 * CAPABILITY: keep an unfinished step in a deployable graph with `mock()`.
 *
 * A placeholder publishes no value. Downstream work must use author-supplied
 * data until the real implementation replaces the placeholder.
 *
 * Generic scenario: reserve a map-rendering step while a festival layout is
 * still being designed.
 */
import { flow, mock, script, out, types, type FlowVars } from '@uipath/maestro-builder-sdk';

export default flow('festival-map-scaffold')
  .name('FestivalMapScaffold')
  .version('1.0.0')
  .input({ mapName: types.string })
  .output({ note: types.string })
  .step('drawLegend', mock())
  .step('announceDraft', script(announceDraft))
  .return({ note: out('announceDraft') })
  .build();

function announceDraft($vars: FlowVars) {
  return "festival map draft: " + $vars.start.output.mapName;
}
