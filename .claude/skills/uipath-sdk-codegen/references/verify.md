# Verifying against `uip` — the probe recipe, and its one fatal misuse

Enumeration and probing do different jobs. Using one for the other's job is how this
repo produced its two worst wrong answers.

| | discovers members? | proves acceptance? |
| --- | --- | --- |
| **enumerate** (zod / bundle) | **yes** | no |
| **probe** (`uip`) | **no** | **yes** |

## The fatal misuse: a failed probe is not proof of absence

A requirement needed "on SLA breach, the ops lead gets a task". To test whether the
platform could do it, an invented rule name was probed:

```ts
.entryWhen(rule('sla-breached' as any))     // ← a name that does not exist
```

`uip` returned `Invalid input`. That was reported as ground truth that the platform
lacks the capability, and the requirement was classified as a CAPABILITY gap. Two
independent agents agreed, which made it feel confirmed.

**It was wrong.** The real rule is `sla-status-change`, and `uip` accepts it. The
capability existed the whole time; the builder just couldn't emit it — a COVERAGE gap,
already documented as Gap D in `docs/CASE_SDK_GAP_PLAN.md`.

> **A probe can only refute names you thought of.** To claim something is impossible you
> must enumerate the space first (Step 1) and then probe the *real* members. "I tried a
> name I made up and it failed" is not evidence.

The tell that distinguishes the two outcomes is in the error text:

| verdict | means |
| --- | --- |
| `Invalid input` / `Invalid option: expected one of …` | the member is **not recognised** |
| a **semantic** complaint — `has no SLA selected`, `connector activity missing`, `task selection missing` | the member **is recognised**; your payload is incomplete |

A semantic error is a **pass** for the purpose of "does this member exist".

## The recipe

Minimal workspace, then one probe per candidate. **The wrappers are gone** — upstream
deleted `check-case.sh` / `compile-case.sh` and moved the loop into the published package,
so the probe drives the package CLIs directly and imports from the real subpath:

```bash
mkdir -p /tmp/probe && cd /tmp/probe
printf '{"type":"module"}\n' > package.json
mkdir -p node_modules/@uipath
ln -sfn "$REPO/typescript/sdk" node_modules/@uipath/flow-sdk   # the WORKING-TREE build
```

```bash
SDK=node_modules/@uipath/flow-sdk/dist/case
node $SDK/compile-cli.js Probe.case.ts -o caseplan.json   # runs the source check, then emits
uip maestro case validate caseplan.json --output json     # the only thing that decides
```

Symlink the working-tree build rather than `npm install`ing the published package: the
probe must interrogate the SDK you are changing, and installing needs `NODE_AUTH_TOKEN`
and pins a released version.

`compile-cli` refuses to emit when the source check fails, so a failure at that step is
OUR gate, not the platform's — `uip` never ran. Read it as `blocked-by-builder` and fix
the probe, never as evidence about the platform.

```ts
// Probe.case.ts — smallest case that reaches the field under test
import { casePlan, rule } from '@uipath/flow-sdk/case';
export default casePlan('probe').name('Probe').identifier('PR')
  .stage('S', s => s.required()
    .entryWhen(rule('case-entered'))
    .task('W', t => t.process('p', { folder: 'Shared' }).required()
      .entryWhen(rule('<CANDIDATE>' as any)))          // ← the cell under test
    .exitWhen(rule('required-tasks-completed'), { marksStageComplete: true }))
  .completeWhen(rule('required-stages-completed')).build();
```

```bash
uip maestro case validate caseplan.json --output json 2>&1 | grep -viE '^Updating|^Update |pinned version' | tail -6
```

Record the **verbatim verdict text** next to the generated member. That text is the
provenance; a member with no recorded verdict has not been verified.

### Rules for probing

- **`as any` is required and is a smell.** You are deliberately emitting something the
  builder's types forbid. Never leave a probe file in the repo.
- **Mutate exactly one cell.** An early probe mutated a *stage* node's `type` to task
  types; every value failed on shape, which looked like "the platform rejects all of
  these". Wrong node, meaningless result.
- **Ignore the `uip` self-update banner on stderr.** Cosmetic. Judge the `"Result"` /
  `Status:` field, never stderr emptiness.
- **Probe placement, not just existence.** Rule legality is slot-dependent; a rule valid
  at task entry may be rejected at stage entry. One cell per (member, slot).

## Cross-check: enumeration vs validator

After generating, assert the two agree — the disagreement *is* the drift signal:

```js
import { validateCaseDiskJsonSchema } from '@uipath/case-schema';
// for each enumerated member: mutate a known-good caseplan, expect valid === true
// for a nonsense member: expect valid === false   ← proves the check has teeth
```

The nonsense case matters. Without it a validator that accepts everything reads as
"full coverage". `validateCaseDiskJsonSchema` genuinely does accept anything for
`slaRules[].unit` — `"zzz"`, `""`, `null`, `42` all pass — so for those fields the
cross-check is vacuous and only `uip` can decide.

## Verify the BINDING, not the checker

Every measurement failure in this program has been the same shape, and none of them was a
wrong checker. The checker ran, ran clean, and answered a question nobody had asked. Four
instances in one session:

| what broke | how it looked |
|---|---|
| eval task prompts asked for `api-workflow` while the grader asserted `api-workflow` | 5 tasks, `SUCCESS score=1.0`, six of six criteria, measuring nothing |
| a filter keyed on `c.get('passed')` when the field is `score` | every criterion printed as FAILED, next to `Score: 1.00` |
| `artifacts/**/*.case.ts` also matched the SDK's OWN example sources in `node_modules` | a plausible 4/5, not an obvious 0/5 |
| `gen-case-skill` built its doc from a hand-maintained method list | `--check` green while the doc taught none of five new methods |

The generalisation, which a peer session reached independently after the same `passed`/`score`
bug: **"I verified the checker" is worth very little; the checker was never the risk.** The
risk is the join between checker and data — a field name, a glob, an argv, a hand-list.

So assert the binding itself:

- **Does the thing under test match the thing asserted?** For a generated eval task: does the
  prompt's type equal the grader's argv type? Print the argv, do not trust the intent.
- **Would this filter catch anything?** A "find the failures" filter returning 100% of rows —
  or 0% — is a bug signal regardless of what the rows say.
- **Did the manipulation land?** Read it back from the artifact the run actually loaded, not
  from the flag you passed. A control arm CANNOT do this for you: a control isolates the
  variable you varied and is structurally blind to a fault shared by BOTH arms. Instrument
  checks must be absolute.
- **Is the file you read the file it produced?** Exclude `node_modules`; require the expected
  basename.

## Leave your own context to verify

Every finding of consequence in this session came from stepping outside the code just
written, and none came from re-reading it:

- `npm pack` and **unpack the tarball** — that is how the doc bug surfaced, with every gate green.
- Read the **emitted artifact** (`caseplan.json`), not the builder source — that is how invented
  resource references and a wrong node type surfaced.
- Open **someone else's fixtures** — that is how a capability this program had called absent
  turned out to be specified with a negative case.

The common property: each is a different *representation* of the same work. A bug that
survives one representation rarely survives two. Re-reading your own source is the one check
that never finds anything, because it is the representation the bug was written in.

## Reporting

- Say **"validator-accepted"**, not "supported", unless a live run proved execution.
- Use **candidate** for anything unsettled, and say what would settle it.
- Distinguish the classes: **COVERAGE** (schema supports it, builder can't emit it) /
  **CAPABILITY** (no layer supports it) / **MODELING** (expressible, awkward).
  Getting this wrong misdirects the fix — a CAPABILITY misfiling makes people stop
  looking for a solution that exists.
- Some questions **cannot** be answered offline. `uip maestro case validate` is a
  schema/structure check, not a runtime engine — whether a `skipWhen`-skipped task
  satisfies `selected-tasks-completed` needs the live `debug` rung (blocked by the
  personal-robot tenant gap). Write "unknown" rather than inventing an answer.
