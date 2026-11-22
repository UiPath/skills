/**
 * CreditDecision — a Case plan that calls a published business rule and copies
 * one decision's output into a case variable.
 *
 *   .businessRule('CreditRisk', { folder: 'Shared', resultSchema })
 *
 * emits a `business-rule` task (`data.version: 'v3'`) bound by a `BusinessRule`
 * name + folderPath binding pair keyed `Shared.CreditRisk`, and adds the task's
 * own `output` (`=result`) and `Error` (`=Error`) rows ahead of your extracts.
 * Do not use `.process()` for a business rule and do not hand-write those rows.
 * For a rule built in the same solution as the case, pass
 * `folder: 'solution_folder'` (the folder `registry search --local` reports):
 * the binding is keyed `solution_folder.CreditRisk` and its folderPath is empty.
 *
 * An extract's `source` reads from the rule's result object directly:
 * `=RiskDecision.riskBand`, never `=result.RiskDecision.riskBand` or
 * `=output.RiskDecision.riskBand` (`uip maestro case check` rejects both).
 * `resultSchema` is the `_jsonSchema` on the `output` row that
 * `uip maestro case tasks describe --type business-rule` returns.
 *
 * `RiskDecision` is a decision key, and a rule carries one per decision. A rule
 * that holds several decisions returns them all, so name the one you want:
 * `=RiskDecision.riskBand` reads that decision, `=RateDecision.interestRate`
 * another. Take the keys from the `_jsonSchema` above rather than guessing —
 * they are the decisions' names, not the entry points' display names, and a
 * display name reads null.
 */
import { casePlan, rule } from '@uipath/maestro-builder-sdk/case';

const resultSchema = {
  type: 'object',
  properties: {
    RiskDecision: { type: 'object', properties: { riskBand: { type: 'string' } } },
  },
};

export default casePlan('credit-decision')
  .name('CreditDecision')
  .identifier('CD')
  .var('creditScore', 'integer')
  .var('riskBand', 'string')
  .stage('Review', (s) =>
    s
      .required()
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Score Credit Risk', (t) =>
        t
          .businessRule('CreditRisk', { folder: 'Shared', resultSchema })
          .inputs({ creditScore: { value: '=vars.creditScore', type: 'number' } })
          .outputs({ riskBand: { source: '=RiskDecision.riskBand', type: 'string' } })
          .required()
          .entryWhen(rule('current-stage-entered')),
      ),
  )
  .completeWhen(rule('required-stages-completed'))
  .build();
