/**
 * ClaimReviewSLA — a Case plan that puts SLAs (deadlines) on the whole case and
 * on both stages, and escalates as those deadlines approach and are missed.
 *
 * Case-level SLA, priority order (first match wins; the default is LAST):
 *   1. Urgent   (conditional) — 30 min; escalate on breach to a user group.
 *   2. Standard (conditional) — 5 days; no escalation.
 *   3. default  (always)      — 3 weeks; at-risk @ 80% to a MULTI-RECIPIENT
 *                               notification (a user AND a group).
 *
 * Stage-level SLAs:
 *   Review  — flat monthly (1 m) SLA.
 *   Resolve — CONDITIONAL stage SLA (first match wins; default LAST):
 *     1. Urgent (conditional) — 2 weeks; displayName for sla-status-change ref.
 *     2. default (always)     — 1 month.
 *
 * Together this exercises conditional SLAs (`when`) at both case and stage
 * level, both escalation triggers (`at-risk` + `sla-breached`), both recipient
 * scopes (`toUser`/`toGroup`), a multi-recipient notification, and SLAs across
 * four units (min/d/w/m).
 */
import { casePlan, rule, escalation, toUser, toGroup } from '@uipath/maestro-builder-sdk/case';

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
      // Stage-level SLA: flat (unconditional) — 1 month from stage entry.
      .sla({ count: 1, unit: 'm' }),
  )
  .stage('Resolve', (s) =>
    s
      .required()
      .description('Final resolution; carries conditional stage-level SLAs.')
      .entryWhen(rule('selected-stage-completed', { stage: 'Review' }))
      .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true })
      .task('Close claim', (t) =>
        t
          .action({ title: 'Close the claim', priority: 'Normal', recipient: 'closer@corp.com' })
          .required()
          .entryWhen(rule('current-stage-entered')),
      )
      // Stage-level CONDITIONAL SLAs — same `when` + default-last pattern as case-level.
      .sla({ when: '=js:vars.priority === "Urgent"', count: 2, unit: 'w', displayName: 'Resolve Urgent SLA' })
      .sla({ count: 1, unit: 'm' }),
  )
  .completeWhen(rule('required-stages-completed'))
  // Case-level conditional SLAs, in priority order — the default (no `when`) is LAST.
  .sla({
    when: '=js:vars.priority === "Urgent"',
    count: 30,
    unit: 'min',
    escalations: [escalation({ trigger: 'sla-breached', notify: [toGroup('<UNRESOLVED: Incident Response Team group id>', 'Incident Response Team')], displayName: 'Notify Incident Response' })],
  })
  .sla({ when: '=js:vars.priority === "Standard"', count: 5, unit: 'd' })
  .sla({
    count: 3,
    unit: 'w',
    escalations: [
      escalation({
        trigger: 'at-risk',
        atRiskPercentage: 80,
        notify: [toUser('manager@corp.com'), toGroup('<UNRESOLVED: Operations Leadership group id>', 'Operations Leadership')],
        displayName: 'Notify Manager + Ops Leadership',
      }),
    ],
  })
  .build();
