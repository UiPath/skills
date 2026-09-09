<!--skill-flavor:ixp-impl-fileref-runtime:start-->
At runtime the variable holds a `{ ID, FullName, MimeType, Metadata }` Attachment object — keys are case-sensitive; `ID` is uppercase, not `Id`. `uip flow debug` cannot upload a file for a `file` input in Studio Web (`--attachment` is ignored): keep the `type: "file"` + `triggerNodeId` declaration, validate with `flow validate`, and test with a sample document from the designer's Debug panel or an upstream node that yields the attachment. Do not declare the variable as `type: "object"`, do not reference it as `=js:$vars.<variableId>` directly without the trigger output path, and do not pass a bare GUID/URL/path/`.ID`/`.FullName`.
<!--skill-flavor:ixp-impl-fileref-runtime:end-->

<!--skill-flavor:ixp-impl-mock-validate-step:start-->
6. Run `uip maestro flow validate /solution/<FlowProject>/new.flow --output json` once after all edits complete.
<!--skill-flavor:ixp-impl-mock-validate-step:end-->
