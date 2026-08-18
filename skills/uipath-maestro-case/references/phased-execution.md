# Preview, publish, debug, and Orchestrator gates

Load this reference only at the structural preview or after local verification
passes. Every external mutation is optional and user-gated.

## Structural preview boundary

The up-front preference chooses one branch.

### Straight through

Print the structural validation profile and counts, then continue into the
detail pass without a prompt.

### Pause at preview

After structural validation, report:

- solution/project and `caseplan.json` path
- stage, task, trigger, condition, SLA, and escalation counts
- placeholder/unresolved counts
- structural validation profile and findings

Ask:

- `Publish for review`
- `Skip publish and continue`
- `Abort`

On publish:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution upload <SolutionDir> --output json \
  --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"
```

Print `DesignerUrl` as plain text, then ask:

- `Continue to implementation`
- `Abort`

Preview upload is not final publish consent. The final Studio Web gate still
runs after full verification.

On abort, write `build-issues.md`, report all artifact paths, and leave partial
state in place. Never roll back or delete work automatically.

## Local verification retry gate

The full local gate is:

1. sidecar/resource invariants
2. `check-caseplan`
3. `check-parity` for an SDD-driven build
4. `uip maestro case validate ... --output json`

Every retry requires an intervening edit. After three failed repair cycles,
show remaining errors and ask:

- `Retry with fix`
- `Pause for manual edit`
- `Abort`

The counter does not reset on retry. Pause and abort both preserve artifacts
and write the issue report.

## Studio Web gate

After all local gates pass, report:

1. `sdd.md` and `caseplan.json` paths
2. stage/task/condition/SLA summary
3. deterministic check summaries
4. CLI validation result and warnings
5. placeholders, unresolved resources, missing connections, and open items
6. inline-created siblings and any built-but-unreferenced resources

Ask:

- `Publish to Studio Web`
- `Skip to Debug`

On publish:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution upload <SolutionDir> --output json \
  --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"
```

Always run resource refresh first. Print the returned Designer URL. Do not pack
or publish to the solution feed at this gate.

## Debug gate

Ask:

- `Run debug session`
- `Continue to publish`

Warn that debug executes the case and may send email, post messages, call APIs,
or write databases. Run only after the explicit selection:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip maestro case debug <ProjectDir> --log-level debug --output json
```

After debug, report status, outputs, and incidents. Offer the same gate again
until the user continues. A fix made after debug re-enters local deterministic
and CLI validation; if already uploaded, upload the fixed build again only
after consent.

Inline-built API-workflow siblings may require a full deployed solution and
cannot always execute through Case debug alone. Offer a full deploy separately;
never infer consent from debug.

## Orchestrator publish gate

Ask:

- `Publish to Orchestrator`
- `Done`

On publish:

```bash
uip solution resources refresh --solution-folder <SolutionDir> --output json
uip solution pack <SolutionDir> <SolutionDir>/dist --output json
uip solution publish <packagePath> --wait --output json
```

Pack the solution directory, never the Case project and never with
`uip maestro case pack`. Read `<packagePath>` from `Data.Packages`; do not guess
the filename. Bump the version when the same name/version already exists.

This gate publishes to the tenant solution feed. Deployment/activation into an
Orchestrator folder is a separate action and outside this workflow unless the
user explicitly requests it.

## Abort and recovery

At any gate, abort means:

1. write `build-issues.md`
2. report source, project, Case JSON, and sidecar paths
3. stop without cleanup

On resume, run `check-sdd`, `check-caseplan`, and `check-parity` to locate the
first incomplete boundary. Do not regenerate an intermediate plan.

<!-- END: phased-execution.md -->
