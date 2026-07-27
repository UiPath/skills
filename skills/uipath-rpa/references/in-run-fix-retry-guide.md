# In-Run Fix and Retry — repairing a workflow without restarting the session

A debug session that has stopped on a problem is holding something valuable: the application is in the exact state that reached the failure. Logged in, three dialogs deep, a queue item already popped. Restarting the run throws all of that away and makes you drive back to the same spot.

`uip rpa debug apply-file-changes` reconciles an on-disk edit into the **paused session** via hot-reload, so the current execution picks it up with no restart. Fix the workflow file, name what you changed, resume.

This works on both backends (headless and Studio Desktop) and needs no `focus-activity`.

---

## When this applies

The entry condition is a **state**, not a command: the session is at a stable pause. It does not matter who started it or how you arrived — `debug start`, `debug continue`, a step, a breakpoint hit.

| Current `DebugState` | Situation | Edit, apply, then… |
|---|---|---|
| `Suspended` | An unhandled exception. The faulting activity is in `DebugDetails` | `debug continue-retry` — the runtime re-executes the faulted activity **with your fix** |
| `Paused` | Stopped at a breakpoint or after a step. The activity has **not run yet** | `debug continue` — plain continue is enough; the activity executes for the first time with your fix |
| `Running` / `Completed` / `None` | No stable pause to reconcile against | Nothing is applied. The response says so — see [Reading the response](#reading-the-response) |

The `Paused` row is worth planning for deliberately: if you suspect an activity is misconfigured, set a breakpoint **before** it, fix it at the pause, and continue — you never have to let it throw.

---

## The loop

```bash
# 1. You are at a pause. Read DebugDetails for the faulting activity and its IdRef.
uip rpa debug state --output json

# 2. Fix the workflow file on disk — a normal file edit. Change only the property that is wrong.

# 3. Name what you changed. One --file-changes occurrence per edited property.
uip rpa debug apply-file-changes \
  --file-changes 'workflowFile=Main.xaml,activityIdRef=NTypeInto_1,propertyName=Target' \
  --output json

# 4. Resume according to the state you were in.
uip rpa debug continue-retry --output json    # was Suspended
uip rpa debug continue       --output json    # was Paused
```

Repeat as often as you like within one session: pause → edit → apply → continue → pause → edit → apply. Each failure advances the application to the next problematic state, so the loop is self-correcting.

### Addressing the edit

| Key | Value |
|---|---|
| `workflowFile` | Workflow path **relative to the project root** (e.g. `Main.xaml`) |
| `activityIdRef` | The activity's `sap2010:WorkflowViewState.IdRef` attribute, read straight from the XAML — the same stable identifier `--breakpoints` uses |
| `propertyName` | The edited property as it is named in the XAML (`Target`, `Text`, `Selector`, …) |

Repeat the flag for several edits in one call; each gets its own verdict. Whole payload from a file: `--file-changes-file changes.json`.

---

## Reading the response

```json
{
  "applied":  [{ "workflowFile": "Main.xaml", "activityIdRef": "NTypeInto_1", "propertyName": "Target" }],
  "rejected": [],
  "debugState": "Suspended"
}
```

This is the whole decision procedure — there is no other signal to consult:

- **`rejected` empty** → every edit is live in the session. Resume and expect the fix to take effect.
- **Something in `rejected`** → that edit was **not** absorbed; each entry carries a `reason`. The file on disk is untouched and still correct, so the edit will apply naturally on the **next session start**. Either start a fresh session (`execution cancel`, then `debug start` — start verbs reload the project from disk) or continue knowingly without that fix.
- **`applied` and `rejected` both empty with `debugState` of `None` / `Running` / `Completed`** → there was no paused session to reconcile against. Nothing was applied and nothing broke. This is a plain no-op, not an error.

Calling this command speculatively is free and idempotent. When in doubt, call it.

---

## What can and cannot be hot-reloaded

**Applies:** the value of a property on an activity that already exists in the running workflow. A selector `Target`, an expression, a literal, a timeout, an option.

**Rejected — needs a session restart:** anything structural. Adding, removing, or reordering activities; new variables or arguments; changing an activity's type. The response names it rather than failing silently.

Also rejected, with a reason naming the cause:

- The `activityIdRef` is not present in the workflow file. **Every activity you author must carry a `WorkflowViewState.IdRef`** — without one it can be neither breakpointed nor repaired in place.
- The activity has no such property, or the property has no value to apply.

## Selectors stored in the Object Repository

A selector held in the Object Repository is healed the same way, with one thing to know: you edit the **descriptor**, not the workflow file — yet you still name the **referencing activity's `Target`** in `--file-changes`.

```bash
# 1. Heal the Object Repository element (see "Working out what to write" below).
# 2. Name the activity that references it — the property is the trigger, not the carrier.
uip rpa debug apply-file-changes \
  --file-changes 'workflowFile=Main.xaml,activityIdRef=NClick_1,propertyName=Target' --output json
uip rpa debug continue-retry --output json
```

### Working out what to write

A suspended selector failure is the **best possible moment** to recover a selector: the application is still on the screen where the search failed, so it can be asked directly what it contains. Restart first and you throw that away.

Follow the recover procedure shipped with the UI Automation package — `.local/docs/packages/UiPath.UIAutomation.Activities/skills/uia-improve-selector/USAGE.md`, **Form 2 (Object Repository reference)**, situation **(b.2) live, window selector works**: pull the element's definition, capture the live application through it, and let the tooling resolve a selector from the element you pick.

**Never hand-write the selector** — choose the element, let the CLI write the target (Rule 7). When several candidates look alike, resolving each one and comparing is a legitimate way to choose: a candidate the tooling can only address positionally (`idx='8'`) is a worse bet than one it can reach through named ancestors.

Then write it back:

```bash
uip rpa uia object-repository replace-elements \
  --elements '[{"ReferenceId":"<or-ref>","DefinitionFilePath":"<recovered>.xaml"}]'
```

> **The package's own procedure is out of date here.** Its write-back step reads *"`object-repository update-element` (when available)"*. That verb does not exist; `replace-elements` is the write-back, shipped in **UiPath.UIAutomation.Activities 26.10.1**. On 26.10.0 there is no way to update a repository element at all — start a fresh session instead. (26.10.1 also dropped `--folder-path` from the `get-definition` verbs, so the staging examples in that document fail as written.)

Getting the element wrong is cheap: the activity suspends again on the same session with the application untouched, and you try the next candidate. That is the whole advantage of repairing in place.

Why naming an unchanged property works: during a debug session the runtime re-resolves Object Repository references instead of caching them, and applying a change to an activity makes it re-read its target when it next runs. The healed descriptor therefore wins — including over the stale copy of the selector cached in the workflow file.

Two consequences worth remembering:

- The activity's cached inline selector in the XAML is **not** what executes; the repository is authoritative. Editing the XAML copy alone will not change the run.
- A selector that lives in a **published UI Library** is a package dependency, not a project file. It cannot be healed in place — republish the library and start a fresh session.

## Expression language

Do **not** pre-filter your edits by the project's language. Three routes exist, and only one of them touches a compiler:

| Route | Example | Language-sensitive? |
|---|---|---|
| Literal | `Text="hello"` | No — serialized as XAML, parsed by the runtime |
| Value / opaque object | a UIA `Target` selector | No — same XAML round-trip. **The flagship selector repair is this route** |
| Expression | `Text="[DateTime.Now.ToString()]"` | Yes — evaluated in the project's language |

Both languages work on all three routes: VB is interpreted directly in the paused frame; C# compiles a throwaway activity with Roslyn. Both are validated end to end.

One diagnostic worth recognising: a rejection whose reason mentions *"requires compilation"* means the C# compile failed **upstream** and the runtime tripped over the uncompiled expression. It does not mean hot-reload declined your edit — treat it as a broken expression to fix, not a capability limit.

---

## Worked example — repairing a broken selector

A UI Automation workflow suspends on `NodeNotFoundException`. The application is open and on the right screen; that state is exactly what a new selector must be captured against.

```bash
# The response that brought you here says:
#   debugState: "Suspended"
#   debugDetails → exception NodeNotFoundException, activity IdRef "NTypeInto_1"

# 1. Recover a working selector against the live application — the app is already in the right state.
#    Follow uia-starter-guide.md § Runtime Selector Failure Recovery for the recovery procedure.

# 2. Write the recovered selector into Main.xaml, on the NTypeInto_1 activity's Target property.

# 3. Reconcile it into the paused session.
uip rpa debug apply-file-changes \
  --file-changes 'workflowFile=Main.xaml,activityIdRef=NTypeInto_1,propertyName=Target' \
  --output json
#   → applied: [NTypeInto_1/Target], rejected: [], debugState: "Suspended"

# 4. Re-run the activity that threw — this time it finds the element.
uip rpa debug continue-retry --output json
#   → debugState: "Completed", hasErrors: false
```

No restart, no re-navigation, no second login.

---

## Notes

- **Edits accumulate freely.** Writing files while execution is `Running` is fine; they sit on disk, inert, until you apply them at a pause or until the next session start reads them.
- **A rejection never reverts your file.** The disk copy is the source of truth throughout; this command only decides what the *running* session absorbs.
- **Skipping the command is legal.** An agent that never calls it loses nothing durable — start verbs reload from disk. The command exists solely to make an edit visible to the execution that is paused right now.
- **Studio Desktop only:** ending a session in which changes were applied may raise a keep/discard prompt in the designer. Headless sessions never prompt.

## See also

- [debugging.md § The stable-state debug loop](debugging.md#the-stable-state-debug-loop-headless) — the pause states this guide plugs into
- [debugging.md § Exception Investigation](debugging.md) — the full set of choices at a `Suspended` pause
- [uia-starter-guide.md § Runtime Selector Failure Recovery](uia-starter-guide.md) — how to recover a selector against the live application
