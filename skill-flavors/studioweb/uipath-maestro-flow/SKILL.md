<!--skill-flavor:sdk-project-layout:start-->
**In Studio Web the builder SDK is built in.** `uip maestro flow check`, `compile`, `decompile` and `merge` run `@uipath/maestro-builder-sdk` inside the page, in the same sandbox as `node`: nothing to install, no `npm`, and no Node process. `examples/` contains authored examples, and `references/` contains the details routed from this guide.

**The open solution is the workspace.** `/solution` is the Studio Web solution the user has open; never create another one. Each project is a folder `/solution/<Project>/`, and a Flow project holds exactly one `.flow` file (Studio Web names a new one `new.flow`; find it with `ls /solution/<Project>/*.flow`). That `.flow` is the single source of truth: the user can change it on the canvas between your turns, so never keep a `.flow.ts` from an earlier turn — decompile a fresh one every turn.

**Create a Flow project only when the request needs a new one:** `uip maestro flow init <Project>` creates it through Studio Web and seeds a trigger-only `.flow`. An existing project needs no `init`.

**Author in a scratch folder, never in the project.** Keep the source and the intermediate artifacts under `/tmp/flow-sdk/<Project>/`, so nothing but the `.flow` lands in the user's project. Run the SDK verbs from the project folder:

```bash
cd /solution/<Project>
uip maestro flow decompile <file>.flow -o /tmp/flow-sdk/<Project>/<Project>.flow.ts
```

The decompiled source carries the flow id and name Studio Web assigned; do not hand-write the skeleton.
<!--skill-flavor:sdk-project-layout:end-->

<!--skill-flavor:sdk-connector-discovery:start-->
**Choose the node before writing it.** Studio Web does not ship the connector library yet: `uip maestro registry` is not available here, so a connector action (`connector()`), connector event trigger (`onEvent()`) or connector wait (`waitForEvent()`) cannot compile in this host. When the request needs one, say so plainly and offer what does work here: `http()` when the service has an HTTP API, or a `mock()` placeholder the user can replace on the canvas. Never stand in a `script()` returning fixed values. For a tenant capability (agent, process, API workflow), run the family's `uip maestro flow registry search` ([`references/agent.md`](references/agent.md)).
<!--skill-flavor:sdk-connector-discovery:end-->

<!--skill-flavor:sdk-lifecycle:start-->
Every change — a new flow or an edit — is the same round trip from the project's `.flow`, so the merge keeps everything the SDK does not model (canvas layout, positions, sidecars) exactly as the user left it. Run it from `/solution/<Project>`, with `W=/tmp/flow-sdk/<Project>` spelled out in each command:

```bash
cd /solution/<Project>
# 1. Seed: a fresh source and the pristine baseline, every turn
uip maestro flow decompile <file>.flow -o /tmp/flow-sdk/<Project>/<Project>.flow.ts
uip maestro flow compile /tmp/flow-sdk/<Project>/<Project>.flow.ts -o /tmp/flow-sdk/<Project>/baseline.flow --no-check
# 2. Edit /tmp/flow-sdk/<Project>/<Project>.flow.ts, then check until clean
uip maestro flow check /tmp/flow-sdk/<Project>/<Project>.flow.ts --source
# 3. Compile the edit and merge only the delta back into the project's .flow
uip maestro flow compile /tmp/flow-sdk/<Project>/<Project>.flow.ts -o /tmp/flow-sdk/<Project>/edited.flow
uip maestro flow merge /tmp/flow-sdk/<Project>/edited.flow --original <file>.flow --baseline /tmp/flow-sdk/<Project>/baseline.flow -o <file>.flow
# 4. The product's own static check on what the designer will open
uip maestro flow validate <file>.flow --output json
```

Valid is top-level `Result` plus `Data.Status: "Valid"`; treat `Data.Warnings` as failures. Never run `format` on the merged file: it re-lays out the user's canvas. The canvas updates as soon as the merge writes the `.flow`. Run the flow only for a stated runtime-behavior claim, with `uip flow debug <Project>` (a real run, up to 5 minutes), or ask the user to run it from the designer.
<!--skill-flavor:sdk-lifecycle:end-->

<!--skill-flavor:sdk-editing:start-->
In brownfield work, preserve the supplied source, step names, and unaffected wiring. Insert a step by moving the old edge through it, not by creating a second path. Edit the decompiled source narrowly and let the merge carry only that delta back ([Lifecycle](#lifecycle)); validate the merged `.flow`, never the intermediate `edited.flow`. Studio Web has no `.pipeline.mjs` helper: `decompile` here never writes one.

**True-brownfield procedure:**
**[`references/brownfield.md`](references/brownfield.md)** — read its judgments; its shell sequences assume a terminal, so use the round trip above instead.
<!--skill-flavor:sdk-editing:end-->

<!--skill-flavor:sdk-api-index:start-->
**Every signature, option shape and field is indexed in the SDK that Studio Web ships**, not in this guide. Its package root is `/plugins/bundled/uipath-studio-web/flow-sdk/`, and a row's path is relative to it:

| you have | look in | a row gives you |
| --- | --- | --- |
| a field or method — `outcomePorts`, `stepToList` (the usual case) | `dist/api-members.md` | the shape that declares it, and the lines that do |
| an exported symbol — `HitlInputs`, `hitl`, `FlowBuilder` | `dist/api-index.md` | its kind, area, and the lines that declare it |

**Match one name; do not read either file end to end** — `grep` it. Then read the span (e.g. `dist/core/actions.d.ts:583-597`): the whole declaration with its doc comment, so one read answers the question. A name in neither index is probably a RUNTIME output key, which the node references carry.
<!--skill-flavor:sdk-api-index:end-->

<!--skill-flavor:sdk-operate:start-->
Debug, publish, deploy, trigger, inspect a job, and drive an instance's
lifecycle. You are already signed in to the user's tenant — never run
`uip login`. Run with `uip flow debug <Project>`; publish the open solution
with `uip solution publish` (the destination is the user's choice). Read
**[`references/operate.md`](references/operate.md)** for what the results mean.
<!--skill-flavor:sdk-operate:end-->
