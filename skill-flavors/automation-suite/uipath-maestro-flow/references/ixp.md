<!--skill-flavor:ixp-taxonomy-lookup:start-->
A model taxonomy is needed only when the flow must select named extracted
fields. On Automation Suite, do not run `uip ixp` commands: every one calls the
IXP Design-Time API, which Automation Suite does not deploy, so
`deployments get-taxonomy` cannot answer. Use defensive reads from the
`Fields[]` or `Tables[]` paths above, state the assumed field names, and finish
the compile/validation loop.
<!--skill-flavor:ixp-taxonomy-lookup:end-->
