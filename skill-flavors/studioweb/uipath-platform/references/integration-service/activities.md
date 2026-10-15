<!--skill-flavor:flow-sdk-ceql:start-->
**Never hand-write the CEQL string.** The tree is the only authored form; the grammar below describes what the compiler emits, so you can read a compiled query and recognize a malformed one. For a connector node in a Maestro flow, follow the filter-tree step in [uipath-maestro-flow — connector/impl.md Step 6a](../../../uipath-maestro-flow/references/author/plugins/connector/impl.md), which discovers the FilterBuilder parameter name from the node registry.
<!--skill-flavor:flow-sdk-ceql:end-->

<!--skill-flavor:flow-sdk-custom-fields:start-->
**For Maestro flows**, this lives on the activity node as `essentialConfiguration.customFieldsRequestDetails`. Authoring contract → [uipath-maestro-flow connector/impl.md Step 6c](../../../uipath-maestro-flow/references/author/plugins/connector/impl.md).
<!--skill-flavor:flow-sdk-custom-fields:end-->
