<!--skill-flavor:script-function-returns-check:start-->
- `returns` is what the `.flow` declares. Match its fields to what the function returns. In Studio Web no type checker runs, and `compile` does not check types, so a wrong `returns` field shows no error. Without `returns`, the body's type is inferred as for a string body.
<!--skill-flavor:script-function-returns-check:end-->

<!--skill-flavor:script-function-sdk-version:start-->
The function form needs `@uipath/maestro-builder-sdk` 6.57.0 or later. Check that `dist/api-index.md` of the SDK that Studio Web ships lists `ScriptValue`. If not, write `script({ code })`. An older SDK fails on a function with `compile: Cannot read properties of undefined (reading 'matchAll')`.
<!--skill-flavor:script-function-sdk-version:end-->

<!--skill-flavor:script-function-metadata-sdk-version:start-->
The metadata parameter needs an SDK whose `dist/api-index.md` lists `FlowMetadata`. Check the SDK that Studio Web ships. If it does not list it, read `$metadata` from `script({ code })`: an older SDK refuses a function with two parameters, and a function that reads `$metadata` at all.
<!--skill-flavor:script-function-metadata-sdk-version:end-->
