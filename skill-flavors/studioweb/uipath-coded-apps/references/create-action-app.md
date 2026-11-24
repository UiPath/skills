<!--skill-flavor:host-scope:start-->
> **Studio Web:** the `uip codedapp` CLI tool is not available here, and there is no npm or full Node.js runtime — the shell's `node` is a QuickJS sandbox that cannot install, build or run the app (see SKILL.md § Studio Web Command Scope). This file's authoring guidance still applies to files you edit directly. § Project Scaffolding scaffolds by writing files; skip every install, build and run command. Q4b creates the External Application here with `uip admin external-apps`; the host signs you in, so skip its login check.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:scaffold-commands:start-->
Studio Web has no `create-vite` or npm, so write the files `create-vite` would generate. The project root in every later step is `/solution/<ProjectName>/source/`.

1. Copy `package.json` from [../assets/templates/action-app-template.md](../assets/templates/action-app-template.md) § Studio Web base files, and `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` and `index.html` from [../assets/templates/web-app-template.md](../assets/templates/web-app-template.md) § Studio Web base files. Replace `{{APP_NAME}}` with `<app-name>`.
2. Add `@uipath/uipath-typescript` to `package.json` only when SDK services are needed, and `react-pdf` only for the PDF viewer below, with the ranges the `package.json` section lists. Any other `npm install` follows SKILL.md § Studio Web Command Scope.
3. Write every other file from the sections below.

Nothing builds the app in Studio Web: its first `npm install` and `npm run build` (`tsc -b && vite build`) run later from `source/`. Before telling the user the scaffold is ready, run the [Build checklist](../assets/templates/web-app-template.md) in web-app-template.md § Studio Web base files over every file — the schema-adapted `Form.tsx` most of all.

<!--skill-flavor:scaffold-commands:end-->
