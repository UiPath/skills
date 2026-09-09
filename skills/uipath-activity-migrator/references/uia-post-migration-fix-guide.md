# Post-Migration Fix Guide — expression selectors

Classic UIA workflows commonly hold selectors in **string variables**. The Activity Migrator turns each such target into a marker expression, `[(var).ToStringWithDelimiter()]`, and, because it cannot compare expression selectors statically, emits hedge constructions around it. Some look correct at design time and fail only at runtime; Check App State can fail silently. This procedure detects and repairs them.

Run it before any selector recovery or hardening on a migrated project: these are structural defects. A selector rewrite (the UIA package's recover-selector or configure-target flows) cannot fix them, wastes runs, and destroys the config-driven variable binding.

**Inputs.** `<MIGRATED_DIR>` below is the migrated project: the workflow's `<OUTPUT_DIR>` once it has been built (SKILL.md Step 5), or the project the user pointed at in the fix-only entry. It is never the Legacy source (`<PROJECT_DIR>` in SKILL.md). Optionally one XAML file to restrict the scan. The sequence is fixed: scan, classify, report, one confirmation, fix, validate. Run it project-wide, not only on activities seen failing: a loose Check App State fails silently, so failure-driven discovery misses it. Use forward slashes in every path.

**Never author or invent selector values.** The single sanctioned exception is Fix 1's OCR branch, where the enclosing card's literal selector is transcribed onto the generated card.

## Failure signatures

The marker is a no-op: at runtime the target's own resolution detects it in the expression text and splits the evaluated value into a window part (scope) and an element part, and a marker-bearing generated card likewise attaches to the window part of its evaluated value. Full values (window + element) therefore work throughout. What remains broken:

| Shape | Structure | Element-only value (`<webctrl …/>`) | Full value (`<html …/><webctrl …/>`) |
|---|---|---|---|
| **Generated card** | Activity wrapped in a *generated* Use Application/Browser whose application selector is the marker expression | Checks: silent `Exists=False`. Actions: `ApplicationNotFoundException` "The specified combination of selector, filter and scope is not supported." (no window part to attach with) | **Works** — the card attaches to the value's window part; redundant but harmless |
| **Loose check** | Check-family activity inside a real card **or an `NElementScope`** (classic Element Scope, e.g. Find Children loops), migrated with `IsLoose="True"` and a marker scope selector | Silent `Exists=False`, **no search is even started** | Works (loose attach via the split window part) |
| **Loose check, no scope** | Same flag, no card and no element scope above it | Left alone and reported | Left alone and reported |
| **Loose `NElementScope`** | Text/image-based classic activity (Text Exists, Find Text, Click Image…) migrated into a *generated* `NElementScope` that is itself `IsLoose="True"` with a marker target | Top-level: pre-existing. Inside a card: reported for manual review | Works |
| **Standalone** | Marker target, no card, no `IsLoose` | Silent `Exists=False` — **pre-existing**: was equally broken in classic; not a migration regression | Works (runtime loose fallback) |

**Healthy constructions — leave alone:**

- A marker target *inside* a real (human-authored or migrated-scope) card without `IsLoose`: the card supplies the scope, the marker split handles the rest.
- A *generated* card whose variable holds a **full** selector: the card attaches to the value's window part; redundant but working. Do not unwrap working constructions.
- A **migrated Attach Window**: a *real* card whose selector carries the marker (`IsDisplayNameAuto` false/absent, kept its classic display name; its children's selectors do not mirror the card selector). The variable holds a window selector there; attaching with the raw value is correct, at any nesting depth.
- Any target with a bound `InUiElement`: element-relative search; the scope constraint is waived.

Detection is structural (marker text + card discriminators). A `[PostMigration Action Required]` annotation is a useful hint when present, it sits on the wrapped child and points straight at a finding, but never the filter: some defect shapes carry none.

## Scan (structural)

Grep shortlists candidates; **Read confirms structure before classifying**: attribute order and line breaks vary, and every signature below correlates two or more nodes.

```bash
grep -rn "ToStringWithDelimiter\|IsLoose=\"True\"" --include=*.xaml "<MIGRATED_DIR>"
```

With a single-file scope, grep only that file. For each hit file, Read the XAML and classify every marker-carrying construction:

| Finding | Structure |
|---|---|
| **S1-nested** | *Generated* `NApplicationCard` (discriminators below) whose `TargetApp` `Selector` carries the marker, nested inside a real card |
| **S1-top** | Generated card with marker selector, no enclosing real card |
| **Attach Window (migrated)** | *Real* card with marker selector — `IsDisplayNameAuto` false/absent, kept its classic display name; children's selector arguments do NOT mirror the card selector. Healthy at any nesting depth — never touch |
| **S2 loose check** | Activity with `IsLoose="True"` whose `TargetAnchorable` `ScopeSelectorArgument` carries the marker, **and** an enclosing scope — a real `NApplicationCard` or an `NElementScope` (a check migrated from inside a classic Element Scope, e.g. a Find Children loop, lands under an `NElementScope` with no card; the fix is verified there too) |
| **Skip: loose without any scope** | `IsLoose="True"` + marker, no `NApplicationCard` and no `NElementScope` ancestor. Leave `IsLoose`; report `loose-no-scope` |
| **Loose `NElementScope`** | `IsLoose="True"` on a *generated* `NElementScope` (from text/image-based classic activities — Text Exists, Find Text, Click Image…) whose own target carries the marker. Top-level: classify by value like S3. Inside a real card: report `manual-review` — removing the flag on the scope itself is unverified |
| **S3 standalone** | Marker `TargetAnchorable`, no enclosing scope (neither card nor element scope), no `IsLoose` |
| **Skip: InUiElement bound** | Any of the above with a bound `InUiElement` — element-relative search, scope constraint waived; not a victim |
| **Skip: healthy in-scope** | Marker target inside a real card or an `NElementScope`, no `IsLoose` — the scope supplies the search root; runtime marker split works |

Generated-vs-real card discriminators, required pair: the `IsDisplayNameAuto="True"` attribute is **present** **and** the card selector expression **equals** the wrapped child's `ScopeSelectorArgument`. On a migrated container the attribute is **absent** (the migrator sets false, the serialization default, so nothing is written). `OpenMode="Never"` + `CloseMode="Never"` + `AttachMode="SingleWindow"` corroborates only that the card *came from migration*; both card kinds carry it, so it says nothing about generated-vs-Attach-Window. The default "Use Application/Browser" display name is weak corroboration, localized under a non-English Studio; never require it.

Record per finding: file, activity type + `DisplayName`/`IdRef`, variable name(s) in the expression, annotation present (`[PostMigration Action Required]: `) yes/no. Annotation is corroboration only: top-level generated cards and loose checks from package 25.10.31 onwards carry none.

`IsLoose="True"` with a **literal** (non-marker) scope selector is a valid cross-window probe, never a finding.

## Classify variable values

Needed for every finding; every action is value-dependent. Trace each variable, bounded: find its assignment sites, take the value that reaches the activity, and stop there. Do not map every usage across the project.

1. Grep the variable name across `<MIGRATED_DIR>`: `Assign` activities and workflow-invocation arguments. An assignment that runs before the activity **overrides** any XAML `Variable` `Default`.
2. No assignments → the XAML `Default` value is the value.
3. The assignment pulls from a config source (config workbook, typically a Selectors sheet, or an Orchestrator asset) → read that source if locally available; otherwise ask the user for the value.

Value classes:

- **window-only**: only window-level tags (`<html/>`, `<wnd/>` with an `app` attribute, `<rdp/>`), no element tags. The runtime window split accepts only these as first tag; any other first tag (e.g. `<uia/>`) or an app-less `<wnd/>` yields an **empty** window part, so classify those as element-only.
- **full**: window tag(s) followed by element tag(s) (e.g. `<html …/><webctrl …/>`).
- **element-only**: element tags only, no window tag (e.g. `<webctrl …/>`).
- **cross-window full**: a full value that targets a different window than the enclosing card or element scope.
- **unresolvable**: no authoritative value found.

**Mis-trace check:** element-only on S1-top or S3 is near-impossible in a previously-working classic project (a classic top-level activity searched from desktop root; only full selectors ever worked there). Before concluding, re-verify the trace (right variable? right config sheet/environment?); if still element-only, confirm the value with the user.

## Decision table

| Finding | window-only | full | element-only |
|---|---|---|---|
| S1-nested | n/a in practice | healthy — report as redundant generated card, leave alone | **Fix 1: unwrap** |
| S1-top | n/a in practice | healthy — report as redundant generated card, leave alone | pre-existing — report only |
| Attach Window (migrated) | healthy — leave alone | unexpected — re-verify trace | unexpected — re-verify trace |
| S2 loose check (enclosing card or element scope) | — | **Fix 2: remove IsLoose** (hardening) — but **skip + report** when the value targets a *different* window than the enclosing scope | **Fix 2: remove IsLoose** (required) |
| loose without any scope | report `loose-no-scope` | report `loose-no-scope` | report `loose-no-scope` |
| S3 standalone | healthy | healthy (runtime loose fallback) | pre-existing — report only |
| unresolvable | ask the user for the value; if none can be supplied, report `unresolved` and plan no edit | | |

Full values are healthy in generated cards: the runtime reduces a marker-bearing card selector to its window part before attaching, the same shape a human would author, so the card is redundant but working, and a working construction is never edited. Element-only values have no window part: the card attaches with a raw element selector and fails, which is why the S1 fixes are gated on the element-only class.

**Pre-existing** = broken before migration too (an element-only value with no scope source is not a migration regression). Nothing to fix here: report it and explain that a scope source is needed, either a properly configured Use Application/Browser around the activity (the UIA package's configure-target flow) or a full selector (window + element) in the config value.

## Report and confirm

Open with one line stating how many marker constructions were scanned, how many edits are planned, and how many annotations will be rewritten to record a healthy verdict (see Annotation rewrite), for example "7 marker constructions scanned, 2 planned edits, 3 annotations to mark verified healthy". Then a findings table, shape, file, activity, variable, value class, planned action, listing only constructions with a planned edit (Fix 1, Fix 2) or a non-healthy result (`manual-review`, `pre-existing`, `loose-no-scope`, `unresolved`). Healthy constructions and non-findings (literal loose probes, migrated Attach Windows, redundant full-value cards) are counted in the opening line and not listed. Then ask once, a single `AskUserQuestion` with three options: apply all planned edits and annotation rewrites, apply a chosen subset, or apply none. Annotation rewrites on healthy constructions are edits to the user's XAML and sit behind the same gate. This question is the only gate: nothing is edited before it, and "none" ends the procedure with the findings table as the result. When the user asked only to scan or report, they pick "none" here; there is no separate mode to track.

## Fix

**Apply every change with the `Edit` tool**: targeted find/replace on the exact attribute or element (drop `IsLoose="True"`, move/delete a specific `NApplicationCard`, rewrite one annotation line). Each fix is a handful of precise edits. **Do NOT** rewrite the file with a script (Bash/Python string surgery, XML re-serialization, whole-file `Write`): that reflows formatting, risks encoding/whitespace/BOM changes across untouched activities, and can corrupt the XAML. Read the surrounding XAML, edit the minimal snippet, move on. Annotation texts differ slightly between package versions; copy the exact line from the file into the edit, never from memory.

### Fix 1 — unwrap generated card (S1-nested, element-only value)

Guards: if any holds, report `manual-review` and leave the card alone: `OpenMode` or `CloseMode` ≠ `Never`; card binds `OutUiElement`.

**OCR branch — repair from parent instead of unwrapping.** Every generated card carries an `NApplicationCard.OCREngine` block; normally it is an empty `ActivityFunc` (only its `Argument`). When it has a **handler** (an OCR engine activity; the classic OCR-based Click/Hover/Get Text/Find/Exists carried it), unwrapping would lose the engine the child depends on. Instead: keep the card and the child in place, replace the card's `TargetApp` `Selector` marker expression with the **enclosing card's literal `Selector`** (XML-escaped as-is), and copy the enclosing card's `InUiElement` if it binds one. The card now attaches to the same window as its parent; `OCREngine`, `ScopeIdentifier`, and the child are untouched.

Otherwise, unwrap:

1. Locate the card's content: `NApplicationCard.Body` → `ActivityAction` → its handler activity (typically an auto-generated `Sequence` named "Do").
2. Move the content to the card's position in the parent: when the card sits in a `Sequence`, hoist the handler `Sequence`'s child activities directly (in order, dropping the "Do" wrapper); otherwise hoist the handler activity whole. If the handler `Sequence` declares `Variables`, hoist it whole in every case; dropping the wrapper would orphan the variable references.
3. On each moved activity, replace `ScopeIdentifier` values equal to the card's `ScopeGuid` with the **enclosing real card's** `ScopeGuid`.
4. Delete the card element entirely; its `TargetApp` and `OCREngine` subtrees go with it. If the file ends with a `ViewStateManager` block, the card's orphaned `ViewStateData` entry may be removed; leaving it is harmless.

### Fix 2 — remove IsLoose (S2, per decision table)

Precondition: the activity has an enclosing scope, a real `NApplicationCard` or an `NElementScope` (that is what S2 means; both runtime-verified). Delete the `IsLoose="True"` attribute. Nothing else. The activity becomes scope-aware again and searches within its surrounding card or element scope. Safety follows the decision table: element-only values never worked loose (empty window part → no attach, no search), so removal cannot regress them; same-window full values find the same element under in-card scoping (hardening). Cross-window full values are the one case where removal would break a working loose attach; that is exactly what the skip is for. Never touch `IsLoose` where the scope selector is a literal.

The designer-side alternative, setting the target's Window selector to the surrounding card's literal selector, is the same remediation via another path; `IsLoose` has no designer editor, which is why the fix edits the XAML flag.

### Annotation rewrite (fixes and verified-healthy constructions)

Migrator annotations are **one line per message**: each line is `[PostMigration Action Required]: <TYPE>: <message>`, lines joined by newline, with an optional `[Existing annotation]: <user text>` tail. An annotation can carry several unrelated migration messages; never replace it wholesale.

Where a fixed activity (the wrapped child or the card for Fix 1; the check for Fix 2) carries `sap2010:Annotation.AnnotationText`, replace **only the line whose message is the fixed defect** with `Remediated by uipath-activity-migrator on <YYYY-MM-DD>: <one line — what was done>`. Every other line, including the `[Existing annotation]: ` tail, stays verbatim. No line matches the fixed defect → leave the annotation untouched.

A **healthy** construction whose annotation carries a migrator line about its expression selector (a redundant full-value generated card, its wrapped child, a migrated Attach Window) gets the same treatment: replace only that line with `Verified healthy by uipath-activity-migrator on <YYYY-MM-DD>: <value class and why it works>`, for example "full-value selector; the card attaches to its window part". This removes the action request from Studio and from the analyzer warnings, so the report need not mention the construction. Rewrite only when the value class came from an authoritative source (XAML default, `Assign`, config read locally); leave the annotation untouched for `unresolved` values or values supplied from memory.

## Validate

After each edited file:

```bash
uip rpa validate --project-dir "<MIGRATED_DIR>" --file-path "<project-relative.xaml>" --min-severity error --output json
```

Must report 0 errors. `<MIGRATED_DIR>` must be absolute; `--file-path` is relative to the project directory; `--min-severity error` matters, migrated projects routinely carry pre-existing warnings. Validation is also the safety net that catches a structurally wrong edit (e.g. an action left without a required scope). Rebuild the project afterwards with the build and fix loop in the verification guide.

## Not auto-fixable (pre-existing)

Standalone activity or top-level generated card + element-only value: nothing supplies a window scope, and nothing did in classic either. Either wrap the activity in a properly configured Use Application/Browser (the UIA package's configure-target flow) or change the config value to a full selector (window + element).

## Output

Every finding ends in one result: `fixed` | `skipped-cross-window` | `manual-review` | `loose-no-scope` | `pre-existing` | `unresolved` | `healthy`. Report in this shape, and nothing else:

```markdown
## Post-migration fix result
Build <passed|failed>. <N> findings: fixed ×<a>, manual-review ×<b>, pre-existing ×<c>, healthy ×<d>.

### Findings                         <- one line per finding that is not healthy
- <file>: <activity> — <result> — <what was changed, or what the user must do>

### Next steps
- Open <MIGRATED_DIR> with Studio 2024.10 or later and run the affected workflows once in Debug.
```

Omit result kinds with a zero count. Healthy constructions get no line: their annotations were rewritten under Fix so Studio shows the verdict, and nothing "left alone" is narrated. When annotations were rewritten, add one line under Findings: "<k> annotations rewritten to Verified healthy (no structural change)". When this procedure runs inside the migration workflow, its `fixed` lines go into the report's "Fixes applied" block and everything else that is not `healthy` goes under "Needs attention"; do not produce this shape a second time there. The two transforms above double as manual recipes for the user when a finding is left to them.
