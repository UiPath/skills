/**
 * ClaimReviewSLA — a Case plan that puts SLAs (deadlines) on the whole case and
 * on its review stage, and escalates as those deadlines approach and are missed.
 *
 * Case-level SLA, priority order (first match wins; the default is LAST):
 *   1. Urgent   (conditional) — 30 min; escalate on breach to a user group.
 *   2. Standard (conditional) — 5 days; no escalation.
 *   3. default  (always)      — 3 weeks; at-risk @ 80% to a MULTI-RECIPIENT
 *                               notification (a user AND a group).
 * The Review stage carries its own monthly (1 m) SLA.
 *
 * Together this exercises conditional SLAs (`when`), both escalation triggers
 * (`at-risk` + `sla-breached`), both recipient scopes (`toUser`/`toGroup`), a
 * multi-recipient notification, and case + stage SLAs across four units
 * (min/d/w/m). SLAs need no bindings or connector library — compile with
 * `uip maestro case compile`, check source with `uip maestro case check`, and validate
 * the artifact with `uip maestro case validate`.
 */
import { casePlan, rule, escalation, toUser, toGroup } from '@uipath/flow-sdk/case';

export default casePlan('claim-review-sla')
  .name('ClaimReviewSLA')
  .identifier('CRS')
  .var('priority', 'string', 'Standard')
  .stage('Review', (s) =>
    s
      .required()
      .description('Active review stage; carries its own monthly SLA.')
      .entryWhen(rule('case-entered'))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Assess claim', (t) =>
        t
          .action({ title: 'Assess the claim', priority: 'High', recipient: 'adjuster@corp.com' })
          .required()
          .entryWhen(rule('current-stage-entered')),
      )
      // Stage-level SLA: 1 month from stage entry.
      .sla({ count: 1, unit: 'm' }),
  )
  .completeWhen(rule('required-stages-completed'))
  // Case-level conditional SLAs, in priority order — the default (no `when`) is LAST.
  .sla({
    when: '=js:vars.priority === "Urgent"',
    count: 30,
    unit: 'min',
    escalations: [escalation({ trigger: 'sla-breached', notify: [toGroup('Incident Response Team')], displayName: 'Notify Incident Response' })],
  })
  .sla({ when: '=js:vars.priority === "Standard"', count: 5, unit: 'd' })
  .sla({
    count: 3,
    unit: 'w',
    escalations: [
      escalation({
        trigger: 'at-risk',
        atRiskPercentage: 80,
        notify: [toUser('manager@corp.com'), toGroup('Operations Leadership')],
        displayName: 'Notify Manager + Ops Leadership',
      }),
    ],
  })
  .build();
