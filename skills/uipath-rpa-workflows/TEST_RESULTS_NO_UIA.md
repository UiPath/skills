# TEST_RESULTS_NO_UIA

Results from running TEST_PLAN_NO_UIA.md across models. Each run is a fresh conversation with no prior context.

Skill version at time of run is noted in each section.

---

## Haiku 4.5 — skill v1 (before reference files)

| Test | Description | Score | Time | Fix Cycles | CLI Calls | Notes |
|------|-------------|-------|------|------------|-----------|-------|
| T01 | Create + Log | 10 | 1m | 0 | 4 | Clean first try |
| T02 | ForEach + String | 10 | 1.5m | 0 | 4 | Clean first try, used ForEach with If() |
| T03 | Sub-Workflow + Invoke | 8 | 3m | 2 | 7 | x:Class naming error, then argument type syntax |
| T04 | REST API + JSON | 8 | 2.5m | 2 | 8 | Forgot WebAPI package, wrong `Url` vs `EndPoint` |
| T05 | Try-Catch HTTP | 3 | 3m | 4+ | 10+ | Never resolved System.Exception namespace, Studio cache issues |
| T06 | Email + Attachment | 10 | 1m | 0 | 3 | Clean after get-default-activity-xaml |
| T07 | Install Package + PDF | 10 | 1m | 0 | 4 | Identified + installed PDF package |
| T08 | Excel Filter/Write | 5 | 1m | 1 | 3 | Correct logic but 15 type resolution errors unresolved |
| **TOTAL** | | **64/80** | **~13m** | **9** | **43** | |

---

## Opus 4.6 — skill v1 (before reference files)

| Test | Description | Score | Time | Fix Cycles | CLI Calls | Notes |
|------|-------------|-------|------|------------|-----------|-------|
| T01 | Create + Log | 10 | 1m | 0 | 4 | Clean first try |
| T02 | ForEach + String | 10 | 1m | 0 | 3 | Clean first try, ForEach with If() |
| T03 | Sub-Workflow + Invoke | 10 | 1.5m | 0 | 5 | Both files 0 errors first try, correct x:Class |
| T04 | REST API + JSON | 10 | 1.5m | 0 | 6 | Installed WebAPI upfront, correct EndPoint property |
| T05 | Try-Catch HTTP | 10 | 1.5m | 0 | 5 | Used s:Exception from get-default-activity-xaml template |
| T06 | Email + Attachment | 10 | 1m | 0 | 3 | Clean after get-default-activity-xaml |
| T07 | Install Package + PDF | 10 | 1m | 0 | 5 | Identified + installed PDF package |
| T08 | Excel Filter/Write | 8 | 4.5m | 2 | 16 | Business activities IReadRangeRef issue, pivoted to classic workbook |
| **TOTAL** | | **78/80** | **~13m** | **2** | **47** | |

---

## Sonnet 4.6 — skill v2 (with exception-and-type-patterns.md + excel-workbook-activities.md)

| Test | Description | Score | Time | Fix Cycles | CLI Calls | Notes |
|------|-------------|-------|------|------------|-----------|-------|
| T01 | Create + Log | 8 | 1m | 0 | 4 | 0 errors; run-file CLI error (file not open in designer) |
| T02 | ForEach + String | 10 | 1m | 0 | 3 | Clean first try, ForEach with If() |
| T03 | Sub-Workflow + Invoke | 9 | 1.5m | 1 | 6 | Dict type x:String,x:Object → x:String,Argument |
| T04 | REST API + JSON | 10 | 1.5m | 0 | 5 | Installed WebAPI upfront, correct EndPoint property |
| T05 | Try-Catch HTTP | 10 | 1m | 0 | 4 | Used s:Exception from get-default-activity-xaml template |
| T06 | Email + Attachment | 4 | 1m | 1 | 4 | Forgot to install Mail package; still 2 errors after install |
| T07 | Install Package + PDF | 9 | 1.5m | 1 | 5 | OverloadGroup: removed Item child, used FileName only |
| T08 | Excel Filter/Write | 10 | 1m | 0 | 3 | Classic workbook activities, LINQ filter — clean first try |
| **TOTAL** | | **70/80** | **~10m** | **3** | **34** | |

---

## Summary

| Model | Score | Fix Cycles | CLI Calls | Skill version |
|-------|-------|------------|-----------|---------------|
| Haiku 4.5 | 64/80 (80%) | 9 | 43 | v1 |
| Opus 4.6 | 78/80 (97%) | 2 | 47 | v1 |
| Sonnet 4.6 | 70/80 (87%) | 3 | 34 | v2 |

**Notable improvements from v1→v2:**
- T05 TryCatch: Haiku 3 → Sonnet 10 (exception-and-type-patterns.md)
- T08 Excel: Haiku 5, Opus 8 → Sonnet 10 (excel-workbook-activities.md)

**Remaining gaps:**
- T06 Email: Sonnet forgot to install Mail package upfront (skill should add UiPath.Mail.Activities to known packages list)
- T01 run-file: CLI requires file open in Studio designer panel — needs investigation
