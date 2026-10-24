<!--skill-flavor:host-scope:start-->
> **Studio Web:** the `uip codedapp` CLI tool is not available here, and there is no npm or full Node.js runtime — the shell's `node` is a QuickJS sandbox that cannot install, build or run the app (see SKILL.md § Studio Web Command Scope). This file's authoring guidance still applies to files you edit directly. Step 3.2 scaffolds by writing files; skip every install, build and run command, and hand the OAuth client setup in Step 4.2 to the user.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:scaffold-commands:start-->
### 3.2 — Write the base project files

Studio Web has no `create-vite` or npm, so write the files `create-vite` would generate, with the dependencies the CLI flow installs. The project root in every later step is `/solution/<ProjectName>/source/`.

1. Copy `package.json` — Coded Web App, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` and `index.html` from [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md) § Studio Web base files. Replace `{{APP_NAME}}` with `<app-name>`.
2. On `default styling = yes`, add the Q6 = yes dependencies that section lists to `package.json`.
3. On `default styling = no`, also copy `src/main.tsx` (Q6 = no) from that section. Step 5.1 writes every other source file.
4. Skip Step 5.2: there is no `.gitignore` here.

No `node_modules` exists here, so Step 4.1 has no per-method scope table: compose `<scopes>` from the Common Scope Bundles in [oauth-scopes.md](oauth-scopes.md).
<!--skill-flavor:scaffold-commands:end-->

<!--skill-flavor:scaffold-verify:start-->
### 5.3 — Verify the scaffold

Nothing builds the app in Studio Web, so verify by reading the files instead of running `npm run build`.

1. Confirm every expected file exists under `source/`.
   - **`default styling = yes`:** `package.json`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `index.html`, `vite.config.ts`, `uipath.json`, `postcss.config.js`, `src/index.css`, `src/hooks/useAuth.tsx`, `src/components/Theme.tsx`, `src/main.tsx`, `src/App.tsx`
   - **`default styling = no`:** the same list without `src/components/Theme.tsx`
2. Run the [Build checklist](../assets/templates/web-app-template.md) in § Studio Web base files over every file.

Fix every gap before telling the user the scaffold is ready.
<!--skill-flavor:scaffold-verify:end-->
