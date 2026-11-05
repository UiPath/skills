/**
 * A Case document-extraction task: an invoice file case variable run through
 * an IXP deployment, its extraction mapped to the `extracted` variable.
 * `=result` is `{ ExtractionResult, Taxonomy }`. Discovery commands:
 *   uip ixp projects list --output json
 *   uip ixp deployments list <project-name> --output json
 * The deployment values below are stand-ins, not a live tenant's.
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
