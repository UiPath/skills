<!--skill-flavor:host-scope:start-->
## Studio Web Command Scope

**The `uip codedapp` CLI tool is not available in Studio Web.** The browser bundle does not ship it and the host intercepts none of its verbs, so `init`, `push`, `pull`, `pack`, `publish` and `deploy` all fail here. Neither is there npm, `create-vite`, a dev server or a full Node.js runtime to scaffold, install, build or run the React app: the shell's `node` / `js-exec` is a QuickJS sandbox for small scripts over files in `/solution` and `/tmp`, not a Node.js toolchain.

A coded app here is always an in-solution AppV2 project. If the open solution has no AppV2 project for this app, create it before scaffolding with the `CreateProjects` host tool. Read its live schema first and use exactly the fields and enum values it declares: the app name, project type `AppV2`, and the sub-type for a Coded Web App or a Coded Action App. When the request does not say which, ask first (Critical Rule 1). If the user already created the project, use it. Read the project name from the tool result and write the app's sources under `/solution/<ProjectName>/source/`; the build writes its bundle to `source/dist/`. The host writes `project.uiproj` and `webAppManifest.json` and registers the app as a solution resource, so do not create those two files yourself.

Everything else in this skill applies. Read and edit the app's files directly — React/TypeScript source, `package.json`, `uipath.json`, `webAppManifest.json`, OAuth scopes and SDK usage — following the authoring rules below. Nothing compiles the app in Studio Web: its first build runs later from `source/` with no lock file (`npm install`, then `npm run build`, which is `tsc -b && vite build`), so write every config file that build needs and keep every import type-correct. Do not run install, build, run, pack, publish or deploy commands, and do not report the app as built, run or deployed. Diagnosing a deployed failure works from the project files plus the families that *are* bundled (`uip or`, `uip traces`).

**`npm install <package>` in any step:** add the package to `package.json` instead. A package the Studio Web base files list takes their range. Any other package takes the version the step pins (`<package>@x.y.z` or `--save-exact`), else `"latest"`.

<!--skill-flavor:host-scope:end-->

<!--skill-flavor:lifecycle-entry-points:start-->
> **One lifecycle in Studio Web: the in-solution coded app.** The project comes from `CreateProjects` (§ Studio Web Command Scope) and its sources go under `source/`. There is no standalone app, no `create-vite` and no `uip codedapp init` here. For the solution side (publish, deploy) see [/uipath:uipath-solution](/uipath:uipath-solution).
<!--skill-flavor:lifecycle-entry-points:end-->

<!--skill-flavor:login-rule:start-->
2. **The host signs you in.** Never run `uip login` or `uip login status` here, and skip every login step in the references. Cloud commands this host bundles, such as `uip admin external-apps` and `uip or`, run as written.
<!--skill-flavor:login-rule:end-->

<!--skill-flavor:build-step-rule:start-->
3. **Check the build by reading, after scaffolding and after every edit.** Run [web-app-template.md](assets/templates/web-app-template.md) § Build checklist over every file under `source/` before handing the app over.
<!--skill-flavor:build-step-rule:end-->

<!--skill-flavor:installed-types-rule:start-->
19. **Never guess SDK method signatures.** No `node_modules` exists here. When the host can fetch URLs, read a service's types from the published package at `https://unpkg.com/@uipath/uipath-typescript@<VERSION>/dist/<SUBPATH>/index.d.ts`, with `<VERSION>` from `package.json`. Otherwise use only the calls the template and `references/sdk/*.md` show, and tell the user which SDK calls you could not verify. Read the `.d.ts`, never the compiled bundle.
<!--skill-flavor:installed-types-rule:end-->

<!--skill-flavor:scaffold-rule:start-->
20. **Scaffold by writing files; never run a scaffolder.** Write the Studio Web base files as [create-web-app.md](references/create-web-app.md) Step 3.2 and [create-action-app.md](references/create-action-app.md) § Project Scaffolding list them. The app is not React until `src/main.tsx` exists: confirm it before handing the app over.
<!--skill-flavor:scaffold-rule:end-->

<!--skill-flavor:completion-next-steps:start-->
4. **Next steps** — the app is scaffolded, not built: say that nothing has compiled it yet and that its first build runs from `source/` (§ Studio Web Command Scope), and name every SDK call you could not verify.
<!--skill-flavor:completion-next-steps:end-->

<!--skill-flavor:completion-preview:start-->
<!--skill-flavor:completion-preview:end-->

<!--skill-flavor:freeze-stop:start-->
24. **When the CLI reports a freeze, stop and show the user.** If a `uip` failure's `Message` mentions a freeze, a frozen config or a pin, show the user the `Message` and `Instructions` and stop. The Studio Web host bundles its CLI, so no install, update or config command run here can fix it.
<!--skill-flavor:freeze-stop:end-->
