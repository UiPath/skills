---
name: uipath-extension
description: "UiPath Maestro Extensions community nodes (`uip extension init|validate|upload|submit`; a JavaScript job function with a `uipath-extensions.json` template). Adopt a `uip function new` project, run the community-index gates, upload a dev build or a release to Orchestrator, and open the pull request that registers the node in the community index. For a plain coded function with no node →uipath-functions. For LLM or agent projects →uipath-agents. For authoring or running a `.flow` →uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Extension

A Maestro community node is a JavaScript job function that Maestro Flow can call as a node. You build it with `uip function` and add the Maestro Extensions parts when you run `init`.

<!--skill-flavor:host-scope:start-->
<!--skill-flavor:host-scope:end-->
## When to Use This Skill

- Turn a plain `uip function new` project into a node (`uip extension init`)
- Check a function project against the community-index gates (`uip extension validate`)
- Upload a dev build to a personal workspace, or a release to a tenant folder (`uip extension upload`)
- Register a node in the community index by opening the pull request (`uip extension submit`)
- Read a gate report or an adopt plan and fix what it names

Do NOT use this skill for:
- Writing or debugging the function itself, or a function that is not a node → `uipath-functions`
- LLM or agent projects → `uipath-agents`

## Critical Rules

1. **Create the project with `uip function new` first.** `init` adopts a project, and it does not create one.
2. **Run `init` before `validate`.** `validate` does not adopt and leaves the adopt files untouched, but its pack step can write build artifacts. When adopt would change the project, it stops with `Failed`, names `uip extension init` and runs no gate. `upload` and `submit` adopt a project that is not adopted yet in their own run, with the same plan. Run `init` first when the user wants to review the files on their own.
3. **A node is one job function.** The gates fail a package whose `operate.json` `targetRuntime` is not `javascript`, one with more than one entry point, and one whose `bindings_v2.json` holds an `HttpTrigger` resource.
4. **Pass the identity as `<PUBLISHER>.<NAME>`.** Each part uses lowercase letters, digits and single hyphens, for example `acme.word-count`. The full package name, `uipath-extensions.<PUBLISHER>.<NAME>`, is at most 100 characters. `init` and `submit` take it as the `[id]` argument, and all of `init`, `upload` and `submit` take `--id <PUBLISHER>.<NAME>`. On a terminal they ask for it when the package name does not hold it yet, and `init --yes` asks as well. Off a terminal, pass it, or the run fails and shows the plan.
5. **Show the adopt plan before you write it.** Preview with `init --no-interactive`. Without `--yes` it prints the files it would write and stops with `ConfirmationRequired`. A terminal run without `--no-interactive` can prompt for the node fields and write after the last answer, with no confirmation step. Show the plan to the user. Run `init --yes` only after the user agrees. `upload` and `submit` do the same when they have to adopt.
6. **Review the generated defaults.** Adopt writes `license` (`MIT` when `package.json` declares none), a label taken from the name, a sentence for each description, an empty tag list and a default `display.icon`. The `Generated` list of the result names the defaults adopt chose, and a field the user answered in a terminal prompt is not in it. Right after `init --yes`, ask the user for the icon, the name and the description (Workflow step 3). Replace the tags with real values before the node is submitted. A field that still holds `TODO` fails the gates.
7. **Never open the index pull request without the user's go-ahead.** Run `submit --dry-run` first, show the result, then run `submit` without it. The first registration of a node needs `--security-contact <SECURITY_CONTACT_EMAIL>`, an email address.
8. **`upload` needs a login.** Run `uip login` first. No `uip extension` command takes `--tenant`, because they read the tenant from that session.
9. **A release upload names one folder.** `upload --release` needs `--yes` and exactly one of `--folder-path` or `--folder-key`. It runs the gates first and never takes `--feed-id`.
10. **Read the outcome code, not only the exit code.** An expected stop such as `ConfirmationRequired` exits 1.

## Choose a Destination

Ask the user where the node goes with `AskUserQuestion`, then follow that row.

| Destination | Command | Notes |
|---|---|---|
| Personal workspace, for a quick try | `uip extension upload --run --input '<INPUT_JSON>' --output json` | Uploads `<PACKAGE_VERSION>-dev.<TIMESTAMP>` to your personal workspace feed and runs a job. No gates run. The job output prints each key with a leading capital, so the declared `markdown` appears as `Markdown`. |
| A tenant folder | `uip extension upload --release --folder-path "<FOLDER_PATH>" --yes --output json` | Runs the gates, then uploads the package version. |
| The community index | `uip extension submit --security-contact "<SECURITY_CONTACT_EMAIL>" --dry-run --output json` | Needs `gh` signed in with push access to the index repository. Drop `--dry-run` only after the user approves the pull request. |

Every command takes `--path <PROJECT_DIR>`. The default is the current folder.

## Workflow

1. Create the project and enter it.

   ```bash
   uip function new <PROJECT_NAME> --language ts
   cd <PROJECT_NAME>
   ```

2. Preview the adopt. This run prints the planned writes and stops with `ConfirmationRequired`. It writes no adopt file, but its pack step can leave build artifacts such as `entry-points.json` and `bindings_v2.json`.

   ```bash
   uip extension init <PUBLISHER>.<NAME> --no-interactive --output json
   ```

   When the project has no `uipath-extensions.json`, `init` and `submit` read the template schema from the index repository through `gh`. Sign `gh` in with access to that repository before the first `init` or `submit`. `upload` adopts without `gh`, and `validate` needs no `gh`.

   The JSON lists each planned write as a path and an action. It does not hold the file contents, so open the files after the write when the user wants to see them. After the user agrees, write them.

   ```bash
   uip extension init <PUBLISHER>.<NAME> --yes --output json
   ```

   Adopt writes `uipath-extensions.json`, renames the package to `uipath-extensions.<PUBLISHER>.<NAME>`, writes a default icon when the project has none, and adds `maestro/connection.ts` when the function reads connection inputs. In that case adopt also adds `@types/node` to `devDependencies`, so run `npm install` before `validate`. It never deletes a file. A project that is already adopted needs no change, and `init` succeeds with nothing written.

3. Ask the user for the icon, the name and the description. Adopt wrote defaults the user has not seen yet, so use one `AskUserQuestion` call with three questions and let each one fall back to the default. When the request already gives a value, or the user answered it in an `init` prompt on a terminal, use it and skip that question.

   - Icon. A path to a PNG, or keep the default. Write the file to `assets/icon.png` in the project and leave `display.icon` as it is. The gates accept a PNG of at most 32768 bytes, and the index accepts at most 512 pixels on each side.
   - Name. The label that Flow shows, 1 to 40 characters. Write it to `display.label` in `uipath-extensions.json`.
   - Description. One sentence of 1 to 200 characters. Write it to `display.description`.

   Neither text holds `<` or `>`. Do not ask for the package id again, because `init` already set it.

4. Review the remaining generated defaults, then check the project.

   ```bash
   uip extension validate --output json
   ```

   `validate` runs the gates in local mode. It needs no login and reads no index. Its pack step still creates `.uipath/`. An entry point input with no description is a `review` finding, not a failure. Add the description when the user wants the node to read well in Flow.

   The `contract` gate reads descriptions from the JSON Schema literals in `defineFunction({ input, output })`, or from `.describe()` on a validator. A comment on a TypeScript interface does not count. It fails an output schema that lacks `additionalProperties: false`. It reviews an optional input that forbids the empty string, so do not put `minLength` above 0, a `format` such as `uri`, `email` or `uuid`, or an `enum` without `""` on an optional input.

   Add one file to `fixtures/` for each case, as the index does in `nodes/rliuup/slugify/fixtures`. A success case holds `operation`, `input` and `output`. A fault case is named `<CASE>.fault.json` and holds `operation`, `input` and `error`, the message the function throws. Adopt writes `fixtures/example.json` with `operation` only. The local `validate` does not run the fixtures, so the `fixtures` gate counts as skipped there, and the index CI runs it.

5. Run the command from the destination table. For the index, check first.

   ```bash
   uip extension submit --security-contact "<SECURITY_CONTACT_EMAIL>" --dry-run --output json
   ```

   For the first registration of a node, ask only for the security contact. Tell the user that `submit` writes the signed-in GitHub account as the only maintainer of the node. Only a listed maintainer, or someone with write access to the index, may submit new versions. When `Data` of the dry run holds a `MaintainersNote`, tell the user why no maintainer was written.

   Run `submit` again without `--dry-run` after the user approves the pull request.

6. Add more maintainers later, by hand. `submit` has no option for them. A person who is already a maintainer adds each new one in a pull request to the index. Show the user this entry to add to the `maintainers:` list in `nodes/<PUBLISHER>/<NAME>/registration.yaml`.

   ```yaml
   maintainers:
     - login: <GITHUB_LOGIN>
       id: <GITHUB_USER_ID>
   ```

   Get each id with `gh api users/<GITHUB_LOGIN> --jq .id`. Write each login in lowercase, and list at most 20 people. Edit the file only after the user agrees. Once the list is on `main`, the index refuses a pull request for the node from anyone who is not on it, unless that person can write to the index repository.

   A `submit` for a later version keeps the list of the default branch as it is. A first registration that is not merged yet has no list there, so every `submit` that updates its pull request writes the list again from the signed-in account. Add people only after that pull request is merged.

## Outcome Codes

A success prints an envelope with the code `ExtensionInit`, `ExtensionValidate`, `ExtensionUpload` or `ExtensionSubmit`. Any other outcome prints a failure envelope and exits 1. Read the envelope. On a terminal, prompts or a summary can share the stream, so do not parse the whole stdout as one JSON document.

| Code | Meaning | Next step |
|---|---|---|
| `GatesFailed` | A gate failed. `Data` holds the gate results and the findings. Read the keys by name, because their casing can differ between a failure and a success. | Fix each finding, then run `validate` again. After 3 failing runs, show the user the report and ask how to proceed. |
| `ConfirmationRequired` | The command needs `--yes`. For `init`, `upload` and `submit` it lists the planned adopt writes. | Show the user what it will do, then repeat with `--yes`. A Ctrl+C at an `init` prompt on a terminal returns the same code with empty `Data`, so ask the user before you repeat. |
| `InputRequired` | An input is missing or two inputs conflict. | Read `Instructions` and pass the missing input, for example `--id`. For `submit`, keep `--dry-run` until the user approves the pull request. |
| `Failed` | The project or a tool it needs has a problem. `validate` also returns it, with the instruction to run `init`, on a project that adopt would change. | Read `Message` and `Instructions`. A missing `gh` says how to install it. |

## What NOT to Do

- Do not install or call a standalone `uipath-extensions` author command. `uip extension` is the only author CLI.
- Do not add `@uipath/uipath-extensions-sdk` to the node. A node depends on `@uipath/coded-functions-js-sdk`.
- Do not copy a `uipath-extensions.json` from an older node. Adopt writes the template schema the index accepts.
- Do not add `maestro.min`, `egress` or `version` to the template. Schema 2 has none of them.
- Do not add a third-party npm package. The `dependency-policy` gate fails any dependency that is not on the index allow list, and that list holds `@uipath/coded-functions-js-sdk` only. Write the logic in the function.
- Do not give a helper module a plain name in `functions/`. Every file there without a leading underscore is an entry point, and `pack` fails when it has no default export. Name helpers `functions/_<NAME>.ts`.
- Do not delete or force-push the `register/<PUBLISHER>__<NAME>` branch, and do not look for another route, when `submit` stops on that branch or on a pull request for it. Read the failure message and follow the case that matches. Closing a pull request leaves its branch in place, so never tell the user to close one.
  - The branch exists and has no open pull request. There is nothing to edit. Tell the user to open the pull request from that branch by hand, or to ask the branch owner to.
  - An open pull request belongs to another user. Tell the user to ask that author to update it, or to run `submit` as that author.
  - An open pull request belongs to the same user. Run `submit` again and it updates that pull request.
