<!--skill-flavor:host-scope:start-->
## Automation Suite Scope

**`uip ixp` does not work on Automation Suite.** Every `uip ixp` command calls the IXP Design-Time API (`du_/api/designtimeapi`), and Automation Suite does not deploy that API, so project, document, taxonomy, labelling, model and deployment commands all fail there.

Do not run `uip ixp` commands, and do not work around a failure with REST calls or another tool. Tell the user that IXP projects on Automation Suite are created, labelled, published and deployed in the IXP application on their Automation Suite tenant, and stop. This applies to a handoff from `uipath-maestro-flow` too: report that the project cannot be created from the CLI on Automation Suite, and hand control back without creating anything.

<!--skill-flavor:host-scope:end-->
