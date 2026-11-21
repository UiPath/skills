<!--skill-flavor:sdk-install:start-->
Resource handles need `@uipath/uipath-typescript` `1.9.0-preview.0` or newer (`/resources` subpath). Studio Web cannot install packages: when `package.json` pins an older SDK, set `"@uipath/uipath-typescript": "1.9.0-preview.0"` there and tell the user to run `npm install` and the build on their machine.
<!--skill-flavor:sdk-install:end-->

<!--skill-flavor:declare-shortcut:start-->
Studio Web adds nothing on its own when `uipath_resources.ts` is edited in Studio Web, in a cloud or local workspace, and has no CLI shortcut for declarations: declare by hand (section 1), then run steps 1–3 for every declaration. A solution uploaded from the CLI arrives with its declared resources already added; still run step 1 when you start work on it.
<!--skill-flavor:declare-shortcut:end-->

<!--skill-flavor:add-to-solution-scope:start-->
Here these commands act on the open solution and write its live Resources panel. `add` prints plain text even with `--output json`, and the list JSON carries no folder: match on kind and name. Never run `uip solution resources refresh` in Studio Web: there is no `.uipx`, so it always fails. In a local workspace, rows can already exist (Studio Web adds declarations copied in or edited on disk outside it, never on project open): step 1 lists them; add only what is missing.
<!--skill-flavor:add-to-solution-scope:end-->

<!--skill-flavor:local-stub-row:start-->
   | Resource the solution creates (asset/bucket/queue without `folderPath`) | `uip solution resources add --source local --kind <KIND> --output json`, once — Studio Web ignores `--name` and names the stub itself. Put the stub name from the output into the declaration, or rename the stub: read its name property with `uip solution resources get <KEY>`, then `uip solution resources edit <KEY> --patch '{"<PROPERTY>":"<NAME>"}'`. |
<!--skill-flavor:local-stub-row:end-->

<!--skill-flavor:add-idempotency:start-->
   Never repeat a local add: each run creates another stub.
<!--skill-flavor:add-idempotency:end-->
