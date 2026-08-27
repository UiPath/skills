# Final Resolution

Here is the investigation result.

---

**Root Cause:** The classic `Type Into 'Account Number'` activity (`UiPath.Core.Activities.TypeInto`,
`IdRef TypeInto_1`) in `Main.xaml` has `EmptyField = False` (the field is **not** cleared before
typing) and no clear-field step (`ClickBeforeTyping = NONE`, no `[k(ctrl)]a[k(del)]`). The target
account field on the Vendor Master form was **already populated** (`0000`), so the intended text
`8891245` was **appended** to the existing content, writing `00008891245` instead of `8891245`. The
job reported **Successful** with zero Error logs because `Type Into` found the field and posted the
keystrokes (they DID land — just concatenated onto the old value), and classic `Type Into` has **no
post-write verification** to catch the wrong result.

**What went wrong:** A value was written incorrectly (old value + new value concatenated) yet the job
succeeded, because the field was not cleared before typing and nothing asserted the resulting value.

**Why (causal chain):**
- **Confirmed (the wrong value):** Info logs show `Current account on file: 0000` before the type, then
  `Account submitted for vendor V-40817: 00008891245` after. The written value is exactly the
  pre-existing `0000` **followed by** the intended `8891245` — a concatenation, not a replacement.
  This is runtime proof, not a source suspicion.
- **Confirmed (the cause):** `Main.xaml` → `TypeInto_1` `Type Into 'Account Number'` has
  `EmptyField="False"` and `ClickBeforeTyping="NONE"`, with `Text="8891245"`. Classic `Type Into`
  clears the field first only when `EmptyField = True`; with it false and a pre-filled field, the new
  text is appended. That produces exactly the observed `00008891245`.
- **Confirmed (why it was silent):** classic `Type Into` has no Verify Execution / post-write assertion
  (that is a modern `Type Into` feature), so nothing checked that the field held `8891245` and the job
  ended `Successful`.

**Evidence:**

### Classic UI Automation (Root Cause)
- `Main.xaml` → `TypeInto_1` `Type Into 'Account Number'`: `EmptyField="False"`, `ClickBeforeTyping="NONE"`, `Text="8891245"`, target selector `<wnd app='vendormgr.exe' ... /><wnd ctrlid='txtAccountNumber' />` (the field was found — no `SelectorNotFoundException`).
- Project `VendorOnboarding`: classic `UiPath.UIAutomation.Activities 23.10.7`, `UiPath.Core.Activities.TypeInto`.
- The field was pre-populated: `Get Text 'Current Account'` returned `0000` (logged) before the type.

### Orchestrator (Runtime evidence)
- Job `VendorOnboarding` (folder `Finance`, key `9d2f4a71-6c83-4e15-b0a7-3f8c1e5d9b40`): `State = Successful`, Unattended, host `MOCK-HOST`.
- Error logs: **zero** entries. No `SelectorNotFoundException` / `ElementOperationException` / `ActivityTimeoutException`.
- Info logs: `Current account on file: 0000` → `Type Into 'Account Number' execution ended` → `Account submitted for vendor V-40817: 00008891245`. Written value = old `0000` + intended `8891245`.

**What is NOT the cause (rule-outs):**
- Not a pure silent no-op — text WAS entered; the field changed, it is just wrong (the value is `0000`+`8891245`, not the unchanged `0000`). A true no-op (nothing typed) would be `click-silent-no-op`.
- Not element-not-found / not-editable — no `SelectorNotFoundException` / `ElementOperationException`; both `Get Text` reads succeeded against the same field.
- Not an input-method (`SimulateType`/`SendWindowMessages`) drop — both are unset (Default hardware typing), and the intended characters all landed (they were appended, not lost).

**Immediate fix:**
1. On `Type Into 'Account Number'` set **`EmptyField = True`** so the field is cleared before typing
   (equivalently, prepend an explicit clear: enable `ClickBeforeTyping` and type
   `[k(ctrl)]a[k(del)]` before the value). Then the field holds `8891245`, not `00008891245`.
   - **Where:** `Main.xaml` → `ui:TypeInto` `TypeInto_1`. **Who:** RPA developer.
2. Re-run and confirm the read-back value equals the intended text before republishing.

**Preventive fix:**
1. Add a post-write verification — a read-back `Get Text` that asserts the field equals the intended
   value (or migrate to the modern `Type Into` with Verify Execution), so a wrong-value write faults
   instead of completing silently.
2. Data-integrity note: the vendor record now holds a corrupted account number (`00008891245`) — the
   already-processed record must be corrected in the target system.

**Investigation summary**

| # | Hypothesis | Confidence | Status | Root Cause? | Key Evidence | Resolution |
|---|------------|------------|--------|-------------|--------------|------------|
| H1 | `Type Into` never entered anything (silent no-op) | Low | Rejected | No | Info logs show the field value changed to `00008891245` — text DID land, so it is not a no-op | Re-scoped to H2 |
| H2 | `Type Into` appended to an uncleared, pre-filled field (`EmptyField=False`) → value concatenated | High | Confirmed | **Yes** | `Current account on file: 0000` then `Account submitted ...: 00008891245` (= `0000`+`8891245`); source `EmptyField="False"`, `ClickBeforeTyping="NONE"`, `Text="8891245"`; zero Error logs | Set `EmptyField=True` (or clear the field first); add read-back verification |

---

The fix is a source change to `Main.xaml` (`Type Into` `EmptyField`), applied under the approval gate
and delegated to `uipath-rpa`; the already-corrupted vendor record must also be corrected downstream.
