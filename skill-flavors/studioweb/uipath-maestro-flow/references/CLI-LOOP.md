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
Each connection must be in the solution first. A `500` at `prepare-custom-debug` is
transient: retry once. These are the flags the host takes:

| Need | Exact form |
|---|---|
| JSON inputs | `-i '{"name":"value"}'`, inline only; the host does not read `@file` |
| Start trigger | `--entry-point <path>`, exactly as `entry-points.json` lists it; omit to start at the default root |
| Wait bound | `--timeout <seconds>`; the default is 120, the range is 10 to 150 |

The host ignores `--attachment`, `--output` and `--output-filter`.
<!--skill-flavor:debug-flags:end-->

<!--skill-flavor:debug-readback:start-->
### Reading the reply

The reply is plain text, not a JSON envelope. It has no `Data` fields, so no
projection applies to it:

```text
<status>
Trace ID: <id>
Run logs:
<logs>
Execution trace:
<json>
```

- **Line 1 is the status:** `Successful`, `Faulted`, or `TimedOut after <N>s`.
  The command exits 1 when the run failed.
- **`Trace ID`** is there only when the run returned one.
- **`Execution trace`** is JSON. Find the faulted element and its message
  there.
- **For more detail,** run `uip traces spans get <Trace ID>`.

The reply has no instance id, so the `debug-instance` commands have nothing to
take. Do not re-run the flow to read the reply again.

For example, a direct-input claim:

```bash
uip flow debug <Project> --inputs '{"name":"value"}'
```

`Successful` on line 1 is evidence for the product-runtime path; a bare exit
code is not.
<!--skill-flavor:debug-readback:end-->
