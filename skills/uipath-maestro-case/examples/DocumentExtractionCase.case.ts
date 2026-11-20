/**
 * A Case document-extraction task: an invoice file case variable run through
 * an IXP deployment, its extraction mapped to the `extracted` variable.
 * `=result` is the whole extraction, `{ ExtractionResult, Taxonomy }`; read
 * the fields from `extracted.ExtractionResult`.
 *
 * The deployment's values are stand-ins, not a tenant's. Read real ones from
 * `uip ixp deployments list <project-name> --output json`, given the IXP
 * project's Name (model, deployment, folderKey), and from the row of `uip
 * solution resources list --kind IxpDeployment --source remote --output json`
 * whose Name is the deployment and whose FolderKey matches (deploymentKey,
 * folder).
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
