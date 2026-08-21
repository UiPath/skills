---
confidence: medium
---

# Dependency / Version Conflict — UIAutomationNext Assembly Fails to Bind

## Context

A UIAutomationNext activity (`NClick`, `NTypeInto`, `NGetText`, `NApplicationCard`, …) fails **before it interacts with any UI element** — the failure is in loading or binding the `UiPath.UIAutomationNext.Activities` assembly, not in resolving a selector. Distinct from the targeting/execution families: no selector was ever evaluated.

Two signatures, two root causes, two fixes. Discriminate first.

### Signature A — Method not found (`MissingMethodException`)

- Message: `Method not found: 'Void UiPath.UIAutomationNext.Activities…'` (or `System.MissingMethodException` naming a UIAutomationNext type/member).
- The assembly **loaded**, but a member the caller was compiled against is absent.
- Surfaces at project **open / validation** in Studio, or at first activity execution.
Two different skews produce this same exception. **Split them on whether the failure is environment-dependent** — this decides the fix, and the two fixes are not interchangeable.

**A1 — same package, different version per environment** (check this first when a robot is involved). The project pins one `UiPath.UIAutomation.Activities` version, but the machine that *runs* the workflow restored a different build of that same package. The assembly loads (so there is no `FileLoadException`), yet the member the compiled `.xaml` was built against is absent from the restored build.

- Tell: **works in Studio / Debug on the authoring machine, faults on the robot or Assistant.** Same project, same `.xaml`, different outcome per environment.
- The pinned version in `project.json` alone does not confirm agreement — it states what the project asks for, not what each environment actually restored.
- This is *not* a disagreement between two different packages. Do not attribute it to `UiPath.System.Activities` (or any sibling) merely because its version also differs; that difference is incidental unless the missing member belongs to that package's assembly.

**A2 — version mismatch inside the project's own dependency set.** The package set in `project.json` pins versions whose bundled `UiPath.UIAutomationNext` / `UiPath.UIAutomationNext.Activities` disagree. Fails everywhere, including Studio. Most common triggers:
  - `UiPath.UIAutomation.Activities` bumped in isolation while `UiPath.System.Activities` (or a dependent package) stayed on an older, incompatible line — or vice versa.
  - A sibling package (`UiPath.Testing.Activities`, `UiPath.MicrosoftOffice365.Activities`, a shared **library**) compiled against a different UIAutomationNext version than the one the project resolves; the older `.dll` wins at load and the newer caller's method is missing.

### Signature B — Could not load file or assembly (`FileNotFoundException` / `FileLoadException`)

- Message: `Could not load file or assembly 'UiPath.UIAutomationNext.Activities' … Version=x.y.z.w` (or `FileLoadException` on a version/strong-name mismatch).
- The exact assembly version **could not be loaded at all**.
- Classic tell: **works in Studio, fails in Assistant / on the robot** (attended or unattended). The environment difference is the giveaway.
- Root cause: **the runtime can't supply the pinned version.** Either the robot's local NuGet cache (`%userprofile%\.nuget\packages`) is stale/corrupt/partial, or the Orchestrator (tenant) NuGet feed is missing the version the published package pins — frequent when a published **library** locks a UIAutomation version that is not on the feed the robot restores from.

## Investigation

1. Capture the **exception type** and full message. `MissingMethodException` / "Method not found" → Signature A. `FileNotFoundException` / `FileLoadException` / "Could not load file or assembly" → Signature B. This single fact selects the branch — do not proceed without it.
1b. For Signature A, split A1 from A2 on **environment dependence**: does the same project run in Studio/Debug and fail only on the robot or Assistant? Yes → **A1** (same package, different restored build per environment). Fails everywhere including Studio → **A2** (the project's own package set disagrees). Note which package owns the member named in the message — that is the package to realign, and a version difference in an unrelated sibling is not the cause.
2. Read `project.json` `dependencies` and `studioVersion`. Record every package that carries UI Automation: `UiPath.UIAutomation.Activities`, and any of `UiPath.Testing.Activities`, `UiPath.MicrosoftOffice365.Activities`, plus referenced libraries. Note whether one was bumped out of step with `UiPath.System.Activities`.
3. Note **where** it fails: design-time (open/validate) vs runtime, and **which environment** (Studio vs Assistant/robot). Studio-only-passes + robot-fails means the two environments resolved different packages — but the exception type decides which branch that is: a load failure → Signature B, `MissingMethodException` → Signature A1. The environment tell alone does not select B.
4. For Signature B: identify the pinned `UiPath.UIAutomation*` version and confirm whether that exact version exists on the Orchestrator/tenant feed and in the robot's `%userprofile%\.nuget\packages`.
5. Confirm the assembly named is `UiPath.UIAutomationNext.Activities` (or its transitive `UiPath.UIAutomationNext` / `UiPath.UIAutomationCore`). A different assembly name → a different package's conflict; apply the same reasoning to that package.

## Resolution

Walk from the signature you confirmed in Investigation step 1.

### Signature A1 — pin one exact version across every environment

Use this when the failure is environment-dependent (runs in Studio/Debug, faults on the robot).

1. Open **Manage Packages** → Project Dependencies and read the installed `UiPath.UIAutomation.Activities` version.
2. Choose **one stable version and make it identical everywhere** the project runs — authoring Studio, the robot, and any other execution machine. Upgrade or downgrade so they match.
3. **Pin that exact version in `project.json` — not a floating range.** A range is what let the two environments resolve different builds; re-pinning is the fix, not a precaution.
4. Restore/rebuild and **republish** so the robot picks up the aligned dependency.
5. Re-run on the robot. `Method not found` clears once the restored assembly exposes the signature the `.xaml` was built against.

Keep the recommendation scoped to the package that owns the missing member. Bumping the whole foundational set here is broader than the defect and changes packages that were never implicated.

### Signature A2 — align the project's dependency set (Manage Packages)

Use this when the failure reproduces everywhere, Studio included. The fix lives in `project.json` / **Manage Packages**, not on the robot.

1. Open **Manage Packages** in Studio.
2. Update **all foundational packages together** to a mutually compatible, latest-stable line: `UiPath.System.Activities`, `UiPath.UIAutomation.Activities`, and every package that brings `UiPath.UIAutomationNext` (Testing, Office365, referenced libraries). Do **not** bump one in isolation — that is what produced the mismatch.
3. If a referenced **library** pins the conflicting UIAutomationNext version, rebuild/republish that library against the aligned version first, then update the consuming project to it.
4. Reopen / revalidate the workflow. `MissingMethodException` clears once the loaded UIAutomationNext assembly exposes the member the caller expects.

> Do NOT clean the NuGet cache to fix Signature A — the assembly loaded fine; the versions disagree, and cache work does not change which versions `project.json` resolves. Republishing is likewise pointless for A2 (nothing about the robot's environment is wrong) but **is** required for A1, so the robot restores the newly pinned version.

### Signature B — make the runtime resolve the pinned version (cache + feed + republish)

The fix is on the robot's package resolution, not in the activity properties.

1. **Clean the robot's local NuGet cache:** delete the `UiPath.UIAutomation*` folders under `%userprofile%\.nuget\packages` (or clear the cache) so the robot re-restores on next run.
2. **Confirm the feed has the version:** verify the exact `UiPath.UIAutomation*` version the project pins exists on the Orchestrator/tenant NuGet feed the robot restores from. If missing, publish/add it, or realign the project to a version that is present.
3. **Republish with deterministic resolution:** set dependency resolution to **Lowest Applicable Version** (or **Strict**) and republish, so the resolved version is one the feed can serve rather than a floating range the robot cannot satisfy.
4. Re-run on the robot. `Could not load file or assembly` clears once the pinned version is restorable in the robot's environment.

> "Works in Studio, fails in Assistant" with a **load failure** is Signature B — Studio restored the version locally; the robot could not. Fix the robot-side resolution, not the workflow. The same environment tell with a `MissingMethodException` is Signature A1 instead: there the assembly loaded, so the fix is version alignment across environments, not cache/feed repair.

## Not this playbook

- Selector matched zero/multiple, or element found-but-not-actionable, or a timeout → the assembly loaded and a selector was evaluated. Use [ambiguous-selector.md](./ambiguous-selector.md), [timeout-issue.md](./timeout-issue.md), [application-not-found.md](./application-not-found.md), or the `selector-failure-*.md` / `element-found-not-actionable.md` playbooks.
- Nothing physically clicks though the activity reports success → input-mode / verify issue, not an assembly-load failure. See [click-coordinate-off-screen.md](./click-coordinate-off-screen.md) and [verify-execution-failure.md](./verify-execution-failure.md).
