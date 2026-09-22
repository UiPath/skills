# Diagnose — why a run failed

Triage order matters. Each step is cheaper and more specific than the next, and
starting at the wrong end is how a diagnosis turns into twenty tool calls.

1. **The debug response you already have.** A faulted run carries its own cause.
2. **Incidents** on the instance.
3. **Runtime variables** at the point of failure.
4. **The deployed artifact** — what is actually on the tenant, not what is on disk.
5. **Traces**, last. They are the whole execution timeline.

Never start at traces, and never re-run `flow debug` to "get a better look" — a
re-run executes the flow again for real and returns the same information the
first one did.

## Step 0 — read the cause in the output you already have

`Data.finalStatus: "Faulted"` means the response in hand holds the reason. On a
faulted run the CLI ignores `--output-filter` and prints the whole envelope, so
redirect it and search the file rather than re-running:

```bash
UIP_LOG_LEVEL=info uip maestro flow debug <project-dir> --output json > /tmp/flow-debug.json
```

Look for the faulted element and its message. The node id in the fault maps
back to the `.step('<id>', …)` that produced it, so the fix is usually a source
edit rather than a platform question.

## Incidents, variables, and the deployed artifact

```bash
# what went wrong
uip maestro flow instance incidents <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow incident get <INCIDENT_ID> -f <FOLDER_KEY> --output json
uip maestro flow incident summary --output json          # across instances

# state at the point of failure
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance variables <INSTANCE_ID> -f <FOLDER_KEY> \
  --parent-element-id <ELEMENT_ID> --output json         # scoped to one element
uip maestro flow instance element-executions <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance cursors <INSTANCE_ID> -f <FOLDER_KEY> --output json

# what is deployed, and which instances exist
uip maestro flow instance asset <INSTANCE_ID> -f <FOLDER_KEY> --output json
uip maestro flow instance list -f <FOLDER_KEY> --output json
uip maestro flow instance get <INSTANCE_ID> -f <FOLDER_KEY> --output json

# last resort
uip maestro flow job status <job-key> --output json
uip maestro flow job traces <job-key> --output json
```

All of these need `uip login`. Every `instance` command and `incident get` also
needs `--folder-key` (`-f`) or it is rejected before reaching the API. Get the key from
`uip or folders list --output json`, or from the job or process context.

**Use these commands, never the underlying APIs.** The CLI applies the tenant
and folder resolution the raw endpoints do not, so a direct call that appears to
work is reading a different scope from the one the run used.

When local and deployed disagree, the deployed artifact is the one that ran.
A flow edited but not re-uploaded is the most common explanation for "I fixed
that already".

## Failure modes that survive the SDK path

The builder makes several classic `.flow` defects unreachable — see the next
section. These are the ones it does NOT:

**An expression that is really a literal.** The builder does not force a `$vars`
reference through `js\`…\`` or `out()`. A plain string containing
`$vars.step.output` compiles to a bare literal with no `=js:` prefix, `check`
reports no issues, and the node receives the text `"$vars.step.output"` at run
time instead of the value. Symptom: a downstream node acting on a string that
looks like an expression. Fix: `out('step')` or `` js`${out('step')}` ``.

**A HITL outcome with no route.** More than one outcome routes per outcome by
default, and an outcome with no arm leaves the run stalled when a reviewer picks
it. `check` warns `HITL_OUTCOME_UNROUTED`; the warning is the diagnosis. Fix:
`.stepSwitch` with an arm per outcome.

**`Completed` with the work not done.** A node with error handling enabled and
no handler, or an error edge routed back into the happy path, lets a failed step
report success upward. Symptom: green run, absent side effect. Read the node's
own status, not the run's.

**A reused connection or resource key.** A key copied from another flow is
well formed, so `check` and `validate` both accept it and the node faults at run
time against a connection this tenant does not have. Read keys from
`registry list --local` or the generated resource file, never from another
project.

**A single-nested project that upload rejects.** `uip maestro flow init` with
`--skip-solution-registration` opts out of auto-scaffold and registration and
leaves `<Project>/<Project>.flow` where `<Solution>/<Project>/<Project>.flow` is
required; `Data.SolutionRegistration.Status` comes back `OptedOut` or
`NotInSolution`, and upload and packaging both fail on structure. Without the
flag, `flow init` outside a solution scaffolds and registers on its own, so this
is opt-in rather than accidental. Fix by deleting the partial scaffold and
running `uip solution init` then `flow init` from inside the solution; add
`uip solution projects add` only if `Status` is not `Registered`. Carry
`--automate` on the rebuild if the original was a Maestro Automate project — a
`.maestro_automate` file in the project root says it was, and rebuilding without
the flag silently returns a plain Flow.

**Misshapen nodes on the canvas.** `compile` writes a placeholder
`ui.position` on each node — all of them on one row — and no top-level `layout`
block, which is what the canvas renders from. Symptom: the flow behaves
correctly and is unreadable, a switch's arms strung out in a line instead of
side by side. This is not a run-time fault and no check reports it — `validate`
passes, because layout is not an authoring concern. Fix:
`uip maestro flow format <Name>.flow`, which is owed before an upload, a debug,
or anyone opening the project in a designer — see
[`operate.md`](operate.md#lay-out-the-emitted-flow-first).

**Green `validate`, faulted `debug`.** Structural correctness and runtime
correctness are different claims. `validate` proves the emitted `.flow` is well
formed; only a run proves the tenant resolves what it references. Start at
step 0.

## Failure modes the builder removes

Do not spend triage on these — the compiler emits the structure that used to be
missing. Verified against the SDK rather than assumed:

| Classic `.flow` defect | Why it cannot happen here |
| --- | --- |
| `variables.nodes[]` missing, so `$vars.X.output` is undefined downstream | `compile` emits the node variable declarations unasked — a four-step flow gets eight entries |
| `bindings[]` missing on a resource node, giving "Folder does not exist or the user does not have access" | `compile` derives the bindings from the node spec — an `agent(…)` step emits its `name` and `folderPath` bindings on its own |

A defect in this table showing up in a real run means the artifact was
hand-edited after `compile`, which is its own answer.

## Evidence boundary

A diagnosis is only as good as what was read. Name the artifact the conclusion
came from — the debug envelope, the incident, the deployed flow — and say when a
cause is inferred rather than observed. "The connector is misconfigured" read
off a timeout is a guess; the same claim read off an incident's message is not.
