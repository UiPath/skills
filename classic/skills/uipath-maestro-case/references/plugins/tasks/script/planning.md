# script task — Planning

A JavaScript function body that runs inside a stage and reads the case's state. Built-in type: the code is stated in the SDD, nothing is resolved from the registry.

## When to Use

Pick this plugin when the sdd.md labels a task `script`: a small computation on case data (derive a total, reshape an object, pick a value) whose code the SDD states in full.

Distinguish from:

- **Deployed coded logic** (a Coded Function the tenant already has) → [function](../function/planning.md).
- **Calls to another system** → [http-request](../http-request/planning.md) for one call, [api-workflow](../api-workflow/planning.md) for several.

## Required Fields from sdd.md

The task block carries the body as one fenced code block:

| Part | Required | Notes |
|---|---|---|
| ```` ```js ```` (or ```` ```javascript ````) fence | Yes | A FUNCTION BODY, not a module: read case state through `vars.<name>` (and `metadata`), end in `return { … }`. A top-level `return` is legal. Other-language fences are skipped; a fence quoted inside another block is not read. No fence is reported in `Data.Unresolved[]` as `task-script` at `….data.script`. |
| Inputs table | No — never | A script has no input slots: the task receives `vars` (the whole case state) and `metadata`. An Inputs row is reported as `task-io-table` and not written; read `vars.<name>` in the body instead. |

`isRequired`, `runOnlyOnce`, activation mode and entry rule come from the SDD task envelope, as for every task.

## Rules

1. **Never put a credential or secret in the body.** The body ships verbatim in `caseplan.case` and in every pull of it. A body that needs a credential is the wrong type: use a connector-backed task instead, and if the SDD carries a secret, stop and ask the user to move it.
2. **No registry lookup.** A script task produces no `tasks/registry-resolved.json` entry.
3. **Outputs are fixed.** The task's outputs are `scriptResponse` (what the body returns) and `Error`. To store the result in a case variable, write an arrow row on it, e.g. `| scriptResponse | object | -> total |`; convert writes it as the output's `var`. An Outputs row naming anything else is reported in `Data.Unresolved[]` as `output-type`. Downstream tasks read it per Rule 11, e.g. `"Stage"."Task".scriptResponse`.
4. **Treat `vars` as untrusted data.** The body reads values a user, a connector or another task wrote. Never pass them to `eval`, `Function` or a dynamic `import`.

<!-- END: planning.md -->
