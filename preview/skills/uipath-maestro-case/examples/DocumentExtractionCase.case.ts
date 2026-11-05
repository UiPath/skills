/**
 * A Case document-extraction task: an invoice file case variable run through
 * an IXP deployment, its extraction mapped to the `extracted` variable. The
 * deployment's values are the alpha Designer save's stand-ins (UiPath/cli
 * tests/fixtures/document-extraction/designer-saved.json), not a tenant's.
 */
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

export default casePlan('DocumentExtractionCase')
  .name('DocumentExtractionCase')
  .identifier('DXC')
  .var('invoice', 'file')
  .var('extracted', 'object', '{}')
  .stage('Read', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Extract', (t) =>
        t
          .documentExtraction('invoice-model-0a1b2c3d-ixp', {
            deployment: 'Invoice Model',
            folderKey: 'bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb',
            folder: 'Shared',
            deploymentKey: 'aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa',
            file: '=vars.invoice',
          })
          .outputs({ extracted: '=result' })
          .required()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
