<!--skill-flavor:field-variable-sdk-version:start-->
  Needs `@uipath/maestro-builder-sdk` 6.44.0 or later; an older SDK ignores
  `variable` (the row is written as `vars.<id>`, so the reads fail
  `EXPR_UNDECLARED_REF`) and its decompile warns that it cannot write the
  designer's row back. If Studio Web's SDK is older, tell the user.
<!--skill-flavor:field-variable-sdk-version:end-->

<!--skill-flavor:field-type-sdk-version:start-->
  Needs `@uipath/maestro-builder-sdk` 6.31.9 or later; an older SDK reports
  `HITL_FIELD_TYPE_UNKNOWN` (do not follow its `type: 'string'` hint).
  If Studio Web's SDK is older, tell the user.
<!--skill-flavor:field-type-sdk-version:end-->

<!--skill-flavor:field-settings-sdk-version:start-->
  These keys need `@uipath/maestro-builder-sdk` 6.35.0 or later;
  an older SDK drops them on decompile and does not write them on compile.
  If Studio Web's SDK is older, tell the user.
<!--skill-flavor:field-settings-sdk-version:end-->
