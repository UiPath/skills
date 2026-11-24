<!--skill-flavor:flow-sdk-generated-activity-source:start-->
2. Add the step. Studio Web's source loader cannot read files: an import of
   `node:fs`, or of a `.json` file, fails before compile runs. Pass the metadata
   and every script as literals in `<Name>.flow.ts`: paste the content of
   `<Name>.json` as an object, and each `<scriptRef>.js` as a JavaScript string literal keyed by its
   `scriptRef`: the file's whole content serialized with `JSON.stringify`, so
   every backslash, quote and newline keeps its meaning. Never paste a script
   into a template literal: escaping only backticks and `${` changes `\d` to
   `d`. `inputs` take the metadata's own parameter and field names;
   compile puts each one in the query, path or body slot the metadata names. A
   name the metadata declares in two slots is two inputs keyed `<slot>:<name>`:
   a PATCH with path parameter `id` and request field `id` takes
   `{ 'path:id': …, 'body:id': … }`, and a bare `id` is refused.

   ```ts
   import { inlineActivity, input } from '@uipath/maestro-builder-sdk';

   const metadata = { /* the content of <Name>.json, verbatim */ };
   const scripts = {
     // JSON.stringify(<content of ListUsergroupUsers.js>), pasted as is:
     ListUsergroupUsers: "async function run(input) {\n  const res = await fetch(...);\n  ...\n}\n",
   };

   // inside the flow chain:
   .step('listMembers', inlineActivity(
     { metadata, scripts },
     { usergroup: input('group') },
     { connection: 'slack', folder: 'shared' },
   ))
   ```

   A List activity's output is the bare array of records: read `out('listMembers')`.
<!--skill-flavor:flow-sdk-generated-activity-source:end-->
