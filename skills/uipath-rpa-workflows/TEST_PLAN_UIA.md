# Test Plan: UIA Scenarios

Each test starts from scratch. Fresh conversation, no pre-existing project. Target app/browser must be open before giving the prompt.

**Scoring:** 0-10 per test.

## Pre-test checklist

1. Studio Desktop is running
2. Create folder `C:\Users\Alberto\Desktop\SkillTests` (if it doesn't exist)
3. Delete leftover project folders inside `SkillTests` from previous run
4. Fresh conversation — no prior context
5. Open the target app/browser BEFORE giving the prompt

---

## T01: UIBank Loan Lookup (Simple — 1 field + 1 button)

### Pre-condition
Open browser to `https://uibank.uipath.com/loans/lookup`

### User prompt
```
Create a UiPath project "LoanLookup" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that types loan ID "LN-001234" into the field on the UIBank Loan Lookup page open in my browser, clicks "Retrieve Loan Details", grabs whatever result text shows up, and logs it. Run it.
```

### Validation
- `get-errors` returns 0
- `run-file` types into the field and clicks the button

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, used configure-target flow, runtime fills field and clicks |
| 8-9 | Works but GetText target slightly off |
| 6-7 | TypeInto + Click work but no result extraction |
| 4-5 | NApplicationCard present but selectors hardcoded |
| 2-3 | Wrong UIA approach |
| 0-1 | Didn't follow skill |

---

## T02: UIBank Loan Application (Complex — 5 fields + dropdown + submit)

### Pre-condition
Open browser to `https://uibank.uipath.com/loans/apply`

### User prompt
```
Create a UiPath project "LoanApp" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that fills the loan application form on the UIBank page in my browser:
- Email: test@example.com
- Loan Amount: 25000
- Loan Term: 5 years
- Yearly Income: 75000
- Age: 30
Then click Submit. Run it.
```

### Validation
- `get-errors` returns 0
- `run-file` fills all fields and clicks submit

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, configure-target flow, runtime fills entire form |
| 8-9 | Works but dropdown handled awkwardly (TypeInto vs SelectItem) |
| 6-7 | Hardcoded selectors instead of configure-target |
| 4-5 | Structure right but has validation errors |
| 2-3 | No NApplicationCard scope or classic activities |
| 0-1 | Didn't follow skill |

---

## T03: Notepad Desktop Automation

### Pre-condition
Open Notepad (empty, untitled)

### User prompt
```
Create a UiPath project "NotepadBot" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that types "Hello from UiPath!" into the open Notepad window and saves the file as C:\Users\Alberto\Desktop\test-output.txt. Run it.
```

### Validation
- `get-errors` returns 0
- `run-file` types text and saves file

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, full flow works (type + save), used configure-target |
| 8-9 | Typing works but save dialog handling incomplete |
| 6-7 | Typing works, Ctrl+S flow missing |
| 4-5 | NApplicationCard present but selectors hardcoded |
| 2-3 | Wrong activity types |
| 0-1 | Didn't follow skill |

---

## T04: Web Table Scraping

### Pre-condition
Open browser to a page with a visible HTML table

### User prompt
```
Create a UiPath project "TableScraper" in C:\Users\Alberto\Desktop\SkillTests. The browser has a page with a data table I need. Make a workflow that scrapes the table and saves it to C:\Users\Alberto\Desktop\ScrapedData.xlsx. Run it.
```

### Validation
- `get-errors` returns 0
- `run-file` extracts table data

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, configure-target used, runtime extracts data and writes Excel |
| 8-9 | Works but table selector needs refinement |
| 6-7 | Used GetText instead of ExtractData |
| 4-5 | NApplicationCard present but ExtractData config wrong |
| 2-3 | No UIA flow |
| 0-1 | Didn't follow skill |

---

## Score Sheet

### Test order
T01 → T02 → T03 → T04 (simple web → complex web → desktop → combo)

### Results

| Test | Description | Model | Score | Time | Fix Cycles | CLI Calls | Notes |
|------|-------------|-------|-------|------|------------|-----------|-------|
| T01 | UIBank Loan Lookup | | | | | | |
| T02 | UIBank Loan App | | | | | | |
| T03 | Notepad Desktop | | | | | | |
| T04 | Web Table Scraping | | | | | | |
| | **TOTAL** | | **/40** | | | | |

### Column definitions
- **Time**: Wall-clock minutes from prompt to final validation/run
- **Fix Cycles**: Number of get-errors → edit → get-errors loops
- **CLI Calls**: Total `uip rpa` commands executed (create-project, find-activities, get-default-activity-xaml, get-errors, run-file, install-or-update-packages, configure-target calls)
- **Notes**: Key issues encountered (e.g., "hardcoded selectors", "missed configure-target flow")

### Pass thresholds

| Level | Score |
|-------|-------|
| Excellent | 32+ (80%) |
| Good | 24-31 (60%) |
| Marginal | 16-23 (40%) |
| Failing | <16 |
