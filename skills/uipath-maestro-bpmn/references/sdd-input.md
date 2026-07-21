# Supplied BPMN SDD semantic intake

Use this path when a supplied `sdd.md` is the source for a new BPMN project.
Skip Phase 0: the SDD already represents the reviewed business shape. Do not
rewrite it, invent missing semantics, or make it conform by silently dropping a
node, flow, condition, variable, event, subprocess, loop, or resource intent.

## 1. Extract one semantic model

Read the SDD and extract:

- process identity, objective, and implementation readiness;
- participants and start trigger;
- logical nodes and their BPMN kind, inputs, outputs, and resource intent;
- logical flows, gateway conditions, and default paths;
- variables with types, process or subprocess scopes, producers, and consumers
  (including a flow ID when its condition reads the variable);
- events, exception behavior, subprocess declarations, and loop rules; and
- every resource intent, including required status and unresolved markers.

Use the SDD logical IDs as the plan's source IDs. Keep an explicit mapping
only when a valid BPMN identifier must be normalized; do not replace an SDD
identity with a registry key.

Treat the declared graph as an invariant: preserve each flow's source and
target, not only its ID. Do not insert a synthetic gateway, merge, node, or
flow to satisfy a style preference or a speculative validator concern. If the
declared graph is actually invalid, stop and ask a focused question instead of
silently changing its topology.

## 2. Validate semantics before registry discovery

Check graph completeness before registry discovery:

- one declared start and at least one reachable end outcome;
- every flow endpoint names a declared node;
- every non-terminal node has its intended incoming and outgoing behavior;
- every gateway path has an explicit condition or default path, and no default
  path also carries a condition;
- every variable consumer has a compatible producer in a valid declared scope;
  and
- every event, subprocess, and loop has the declared parent, trigger, and exit
  behavior.

Ask a focused question when the supplied SDD is ambiguous. Do not use registry
results to fill a business-logic gap.

## 3. Resolve implementation resources

After semantic intake passes, refresh the live connection inventory **exactly
once** with `uip is connections list --all-folders` before choosing registry
resources. This is mandatory on every supplied-SDD executable path, even when
the SDD marks a resource resolved or none of its resources appear to need a
connection. Then follow the existing [registry workflow](registry-workflow.md):
pull once, list or search each required extension type, and retrieve the
selected template with `registry get`. Inventory membership is not permission to
bind a connection: use one only when the selected template requires it and it
matches the SDD resource intent. A supplied resolved resource intent is
the business selection; if discovery would change it, request the normal
confirmation rather than substituting a candidate.

For a required unresolved resource, retain the SDD's intended name and mark the
implementation blocked. It does not block SDD review, but it blocks executable
BPMN: do not emit a placeholder registry wrapper or claim the file can run.

## 4. Reuse the existing BPMN authoring machinery

Use the extracted semantic model to drive the existing structural guidance in
[structural BPMN](structural-bpmn.md), the registry-owned XML templates, and
the mandatory BPMNDI shape/edge generation. Create the complete local project
described in [project layout](shared/project-layout.md): `project.uiproj`,
`bindings_v2.json`, `entry-points.json`, `operate.json`, and
`package-descriptor.json` alongside the BPMN source. Keep their references
consistent with the BPMN filename and the actual root start event. Then run the
bundled validator as the final local check. The SDD itself never gains registry
XML or BPMNDI.
