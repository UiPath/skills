# Final Resolution

Investigation complete. Here is the resolution:

---

**Root Cause:** **`Type Into` (`NTypeInto`) corrupted the typed text because it ran with
`InteractionMode = HardwareEvents` and `DelayBetweenKeys = 0` against a portal field that could not
keep up with the keystroke rate.** HardwareEvents drives the physical keyboard one key at a time; with
no inter-key delay the robot typed faster than the web field accepted input, so characters were dropped
and reordered. The job ended `Successful` — no exception was thrown — but the value the field captured
is wrong.

**What went wrong:** The account number `4021-7789-3316` was read from the source, but after the
`Enter account number` step the read-back logged `4201-7789-316` — the `4021` block is transposed to
`4201` (out of order) and one `3` is missing from the final block. The activity reported success; the
corruption is silent and only visible in the downstream value.

**Why:**
- `process/Main.xaml` — the `NTypeInto` "Enter account number" (`NTypeInto_1`) has
  `InteractionMode="HardwareEvents"` and `DelayBetweenKeys="0"`, typing `[accountNumber]` into the
  `accountNumberField` input inside the `Billing portal` `Use Application/Browser` scope
  (`chrome.exe`, Billing Portal).
- HardwareEvents with zero delay sends keys as fast as the OS allows; a laggy/throttled web field misses
  or reorders keystrokes. This is timing-dependent, so it corrupts intermittently and passes validation.
- Job logs show source `4021-7789-3316` → confirmed `4201-7789-316`: transposition + a dropped
  character, the signature of keystrokes outrunning the field.

**Evidence:**
- Job `e3f9c1a4-6b28-4d70-9a15-7c0e2b8d4f61` `State = Successful`; **zero** Error logs; no
  `SelectorNotFoundException` / `UiElementNotFoundException` / `VerifyActivityExecutionException`
  anywhere — the field was found and the keys were sent.
- Info logs: `Account number read from source: 4021-7789-3316` then
  `Value confirmed in portal field: 4201-7789-316` — the field holds a corrupted value.
- Source: `NTypeInto_1` `InteractionMode="HardwareEvents"`, `DelayBetweenKeys="0"`.

**Immediate fix:**
1. On the `Enter account number` `Type Into`, increase **`DelayBetweenKeys`** — start at `20`ms, raise
   toward `50`ms for this field — so the robot does not outrun the input.
2. Better, switch **`InteractionMode`** to **`Simulate`** (or `ChromiumAPI` for this Chromium browser):
   these send the whole string in one operation and do not depend on per-key timing, eliminating the
   drop/reorder race entirely.
3. If the window is already focused, uncheck **`Activate`** (`ActivateBefore`) so re-activation cannot
   drop the leading keys.
4. Re-run and confirm the read-back matches the source value exactly.

**Do NOT** treat this as a selector/targeting failure or a timeout — the element was found and typed
into; only the keystroke delivery is wrong. Do NOT blindly increase the activity `Timeout`.

**Preventive fix:**
- Prefer `Simulate` / `ChromiumAPI` for form fields where throughput allows; reserve `HardwareEvents`
  for targets that reject simulated input (some Java/SAP/Citrix), and pair it with a non-zero
  `DelayBetweenKeys`.
- Add a real verification of the entered value (compare the read-back to the source, or a Verify
  Execution `TextChanged` target) so a future corruption faults instead of passing silently.
- As a last resort for a field that mangles keypresses regardless of input method, use `Set Text`
  (`NSetText`), which injects the value directly and bypasses keystroke simulation.

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `NTypeInto` with `HardwareEvents` + `DelayBetweenKeys=0` typed faster than the field accepted, dropping/reordering characters. | high | confirmed | Yes | `NTypeInto_1` `InteractionMode="HardwareEvents"`, `DelayBetweenKeys="0"`; source `4021-7789-3316` → confirmed `4201-7789-316`. | Raise `DelayBetweenKeys` (20–50ms) or switch `InteractionMode` to `Simulate`/`ChromiumAPI`. |
| H2 | Selector matched the wrong field / targeting failure. | low | eliminated | No | No `SelectorNotFoundException`/`UiElementNotFoundException`; the field was found and partially typed — a wrong target would type nothing or throw. | N/A |
| H3 | Silent no-op — nothing was typed. | low | eliminated | No | The field holds `4201-7789-316`, not empty — text landed but corrupted, so this is not a pure no-op (click-silent-no-op.md). | N/A |
| H4 | Activity timeout. | low | eliminated | No | No `RuntimeTimeoutException`/`TimeoutException`; job completed in ~26s well under any default timeout. | N/A |
