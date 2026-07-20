# Placeholder-Selector Stub Pattern

Sometimes you must generate a UI automation workflow without live app access — the app is not installed on the build machine, the agent has no GUI, the user has explicitly deferred target capture to a developer who will run Indicate later, or the UIA package cannot be installed (Rule 7a). In that case, the workflow ships with placeholder selectors. The pattern below is the **only** acceptable shape. It requires no UIA package or CLI — that is the point.

## Rule

When live capture is unavailable, write the **real** UIA activity (XAML `<NApplicationCard>` / `<NTypeInto>` / `<NClick>` / `<NGetText>` / etc., or coded `uiAutomation.Open` / `Attach` / `TypeInto` / `Click`) with the target descriptor's selector left as a placeholder and a `TODO Indicate` marker embedded in the activity's `DisplayName` (XAML) or in a `// TODO[Indicate]` comment immediately adjacent to the call (coded).

Do **NOT** replace the activity itself with a `Log` call.

## Why this matters

A `Log("LoginWorkflow: type username")` stub:

- Passes `uip rpa validate` (no UIA activity, no selectors to validate).
- Passes `uip rpa build` (just a string in a Log activity).
- Runs cleanly via `uip rpa run` (the Log activity emits a message).
- **Does nothing.** The workflow looks complete to the validator, looks complete to a CI smoke test, and silently fails to perform the actual automation.

A real `<uix:NTypeInto>` activity with placeholder selector + `TODO Indicate` marker:

- Build/validate surface the unconfigured targets ("Target or Input UI Element must be set" — hard errors in current packages) — useful, since they tell the developer what is left to do. A stub-mode deliverable therefore does NOT reach a clean `build`; its acceptance bar is that the ONLY remaining validate/build errors are the expected unconfigured-target ones.
- The activity is wired into the workflow's control flow, package dependencies, scope, and Object Repository registration plumbing. The developer's only remaining work is **Indicate**.
- The TODO marker is visible in Studio's designer pane and grep-able in the file.
- The cost of "what does this stub actually need from the developer?" drops from "read this carefully and infer" to "click Indicate on the marked activities."

## XAML example

```xml
<uix:NApplicationCard ApplicationWindow="{x:Null}"
                      DisplayName="TODO Indicate — Use Application/Browser (ACME WI app)"
                      sap2010:WorkflowViewState.IdRef="NApplicationCard_1">
    <uix:NApplicationCard.Body>
        <Sequence sap2010:WorkflowViewState.IdRef="Sequence_1">
            <uix:NTypeInto DisplayName="TODO Indicate — Type Username"
                           Text="[in_Username]"
                           sap2010:WorkflowViewState.IdRef="NTypeInto_1" />
            <uix:NTypeInto DisplayName="TODO Indicate — Type Password"
                           Text="[in_Password]"
                           sap2010:WorkflowViewState.IdRef="NTypeInto_2" />
            <uix:NClick DisplayName="TODO Indicate — Click Login"
                        sap2010:WorkflowViewState.IdRef="NClick_1" />
            <uix:NGetText DisplayName="TODO Indicate — Read WIID field"
                          Text="[out_WIID]"
                          sap2010:WorkflowViewState.IdRef="NGetText_1" />
        </Sequence>
    </uix:NApplicationCard.Body>
</uix:NApplicationCard>
```

What this gives the developer:
- `NApplicationCard` is in the right place (entry point of the screen).
- Three `NTypeInto` / `NClick` / `NGetText` are wired into the Sequence in the right order.
- `Text` arguments are bound to the right input/output variables.
- Each activity's `DisplayName` is `TODO Indicate — <human description>`. Studio shows this on the canvas; the developer clicks each and runs Indicate.
- Once Indicate is run, `DisplayName` is updated, `Target` becomes a real descriptor, and the workflow is shippable.

What you must NOT do:

```xml
<!-- WRONG: replaces the actual activity with a log stub -->
<ui:LogMessage Message="LoginWorkflow: type username" Level="Info" />
<!-- TODO[selectors]: replace this with an actual TypeInto activity once capture is done -->
```

That XAML compiles, validates, runs — and does nothing. A re-run of the build pipeline at a later date silently ships the same broken automation.

## Coded example

```csharp
[Workflow]
public void Execute(string in_Username, string in_Password, out string out_WIID)
{
    // TODO[Indicate]: attach to the ACME WI app — replace placeholder with Descriptors.<App>.<Screen>
    using var app = uiAutomation.Open(/* TODO[Indicate]: Descriptors.AcmeWi.Login */);

    // TODO[Indicate]: target the Username field
    app.TypeInto(/* TODO[Indicate]: Descriptors.AcmeWi.Login.Username */ "username-placeholder", in_Username);

    // TODO[Indicate]: target the Password field
    app.TypeInto(/* TODO[Indicate]: Descriptors.AcmeWi.Login.Password */ "password-placeholder", in_Password);

    // TODO[Indicate]: target the Login button
    app.Click(/* TODO[Indicate]: Descriptors.AcmeWi.Login.LoginButton */ "login-button-placeholder");

    // TODO[Indicate]: target the WIID readout field on the next screen
    using var home = uiAutomation.Attach(/* TODO[Indicate]: Descriptors.AcmeWi.Home */);
    out_WIID = home.GetText(/* TODO[Indicate]: Descriptors.AcmeWi.Home.WIIDField */ "wiid-field-placeholder");
}
```

What this gives the developer:
- The actual `uiAutomation.Open` / `Attach` / `TypeInto` / `Click` / `GetText` calls are in the right order with the right argument bindings.
- Every `TODO[Indicate]` marker tells the developer the exact descriptor to wire up.
- The placeholder string argument lets the project build and `uip rpa packages inspect` succeed; once Indicate runs and `Descriptors.<App>.<Screen>.<Element>` exists, replace the placeholder string with the descriptor reference.

What you must NOT do:

```csharp
[Workflow]
public void Execute(string in_Username, string in_Password, out string out_WIID)
{
    // TODO[selectors]: replace these with real uiAutomation calls once Object Repository is populated
    Log("LoginWorkflow: type username " + in_Username);
    Log("LoginWorkflow: type password");
    Log("LoginWorkflow: click Login");
    Log("LoginWorkflow: read WIID");
    out_WIID = "";
}
```

This compiles, validates, runs, and does nothing. It is the most expensive kind of stub.

## When the rule does NOT apply

- **Live capture is available.** Run `uia-configure-target` / Indicate first; the workflow ships with real descriptors. No stub pattern needed.
- **The activity is not UI.** Logging is fine for actual logging steps (e.g., "Log the transaction ID before processing"). The rule applies only to UI-interaction steps that, in a finished workflow, would be `NTypeInto` / `NClick` / `NGetText` / etc.

## Acceptance check

Before declaring a stub-mode workflow done, re-read every UI-interaction step in the PDD / SDD and confirm that the workflow contains a **real UIA activity** (XAML element or coded `uiAutomation.*` call) for each one — not a Log call. Grep for `Log\(` and `LogMessage` inside the workflow body; for every match, verify it represents an actual logging step, not a substitute for a UI action.
