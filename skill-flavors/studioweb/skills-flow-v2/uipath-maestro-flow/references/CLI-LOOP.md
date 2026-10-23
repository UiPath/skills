<!--skill-flavor:loop-choice:start-->
Studio Web has one loop: the round trip in
[SKILL.md — Lifecycle](../SKILL.md#lifecycle). It merges every change into the
target `.flow` and validates that file. The emit-only mode and the packaged-SDK
local gates below are for a terminal; do not use them here.
<!--skill-flavor:loop-choice:end-->

<!--skill-flavor:install-package:start-->
Studio Web ships the SDK in the page, so install nothing. When `uip` reports
that the SDK is below its minimum version, tell the user: Studio Web owns that
copy.
<!--skill-flavor:install-package:end-->

<!--skill-flavor:local-gates:start-->
Studio Web does not use these gates. Its loop is
[SKILL.md — Lifecycle](../SKILL.md#lifecycle): `check --source`, each `prepare`
it names, `compile` into `.flow-sdk/edited/`, `merge` into the target `.flow`,
then `validate`. There is no compiled-artifact `check`; `validate` is that rung.

Warnings require deliberate review; whether one blocks a release comes from the
surrounding task or release policy.

Never run `uip maestro flow format` on a merged file: it lays out every node
again and discards the positions on the canvas of the user.
<!--skill-flavor:local-gates:end-->

<!--skill-flavor:product-cli-scaffold:start-->
In Studio Web the project and its `.flow` come from Studio Web itself, and the
SDK verbs run in the page — see
[SKILL.md — Project layout](../SKILL.md#project-layout) and
[Lifecycle](../SKILL.md#lifecycle).
<!--skill-flavor:product-cli-scaffold:end-->

<!--skill-flavor:debug-flags:start-->
In Studio Web the verb is `uip flow debug <Project>`. `<Project>` is a project
name in the open solution, not a path; it defaults to the open project.
Resource refresh must run first. A `500` at `prepare-custom-debug` is
transient: retry once. The host uses only the project name and
`-i, --inputs '<inline JSON>'`. It ignores `--attachment`, and it does not read
`@file` inputs. Add `--output json`. If the reply ignores `--output-filter`,
read the same fields from the full envelope.
<!--skill-flavor:debug-flags:end-->

<!--skill-flavor:debug-example:start-->
```bash
uip flow debug <Project> --inputs '{"name":"value"}' \
  --output-filter "{status:finalStatus,instance:instanceId,url:studioWebUrl,failed:elementExecutions[?status!='Completed'].{id:elementId,status:status},<Out>:variables.globals.<Out>,incidents:incidents}" \
  --output json
```
<!--skill-flavor:debug-example:end-->
