<!--skill-flavor:flow-sdk-generated-activity:start-->
The activity can be placed in a Maestro flow as a node of type
`uipath.connector.custom.<connector-key>.<slug>`. Nothing is published: `uip maestro
flow node add <file>.flow <type> --metadata $WORK/<Name>.json --scripts $WORK`
builds the node definition from the metadata and embeds every script in the node,
and `node configure` reads the metadata from the node. Keep `$WORK` until that
has run. The flow-side steps are the `uipath-maestro-flow` skill's
[connector/impl-inline.md](../../../uipath-maestro-flow/references/author/plugins/connector/impl-inline.md);
hand off to it rather than authoring the node from here.
<!--skill-flavor:flow-sdk-generated-activity:end-->
