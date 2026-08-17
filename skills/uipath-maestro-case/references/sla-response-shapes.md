# SLA Response Shapes — moved

This content now lives in the shared case-knowledge layer (single source, probe-verified):

- Response model (5 responses + selection test): **K-SLA-4 / K-SLA-5**
- Status rides on the escalation reference (breach = `slaId` alone; at-risk = same-SLA `escalationId`): **K-SLA-3**
- Validate-verified shape matrix: [case-knowledge/facts/sla.yaml](case-knowledge/facts/sla.yaml) (K-SLA-7)
- The defects `validate` cannot see: **K-ERR-2** ([case-knowledge/errors/validate-codes.md](case-knowledge/errors/validate-codes.md))

Emit-side JSON shapes stay in the owning plugins: [plugins/sla/impl-json.md](plugins/sla/impl-json.md)
(clocks + escalations), [plugins/conditions/stage-entry-conditions/impl-json.md](plugins/conditions/stage-entry-conditions/impl-json.md)
(`enter-stage`), [plugins/conditions/task-entry-conditions/impl-json.md](plugins/conditions/task-entry-conditions/impl-json.md)
(`start-task`).

<!-- END: sla-response-shapes.md -->
