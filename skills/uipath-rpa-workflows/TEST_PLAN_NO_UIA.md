# Test Plan: No-UIA Scenarios

Each test starts from scratch. Fresh conversation, no pre-existing project.

**Scoring:** 0-10 per test.

## Pre-test checklist

1. Studio Desktop is running
2. Create folder `C:\Users\Alberto\Desktop\SkillTests` (if it doesn't exist)
3. Delete leftover project folders inside `SkillTests` from previous run
4. Fresh conversation — no prior context

---

## T01: Create Project + Log Message

### User prompt
```
Create a new UiPath project called "HelloWorld" in C:\Users\Alberto\Desktop\SkillTests, VisualBasic, Windows framework. Add a workflow that logs "Hello from UiPath!" and run it.
```

### Validation
- `get-errors` returns 0
- `run-file` log output contains `"Hello from UiPath!"`

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | Project created, 0 errors, runtime logs message |
| 8-9 | Works but tried `uip rpa new` first, recovered |
| 6-7 | Project created, needed fix cycles on the XAML |
| 4-5 | Project created but workflow doesn't validate |
| 2-3 | Couldn't create the project |
| 0-1 | Didn't follow skill at all |

---

## T02: ForEach Loop + String Building

### User prompt
```
Make me a UiPath project called "CityLoop" in C:\Users\Alberto\Desktop\SkillTests. I want a workflow that has a list of cities — New York, London, Tokyo, Paris, Sydney — loops through them and builds a comma-separated string, then logs "Cities: New York, London, Tokyo, Paris, Sydney". Run it.
```

### Validation
- `run-file` log output contains `"Cities: New York, London, Tokyo, Paris, Sydney"`

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, correct output on first or second try |
| 8-9 | Works but trailing comma or extra space |
| 6-7 | Used String.Join instead of loop (valid but different approach) |
| 4-5 | ForEach present but broken (wrong type, variable scoping) |
| 2-3 | Completely wrong ForEach syntax |
| 0-1 | Didn't follow skill |

---

## T03: Sub-Workflow with Arguments + Invoke

### User prompt
```
Create a UiPath project "DiscountCalc" in C:\Users\Alberto\Desktop\SkillTests. I need two workflows:
1. Workflows/CalculateDiscount.xaml — takes a price (Double) and a membership flag (Boolean), returns the final price. Members get 20% off, non-members 5% off. Log which discount was applied.
2. Main.xaml — calls CalculateDiscount with price 100 and member=true, logs the result.
Run Main.xaml.
```

### Validation
- Both files: `get-errors` returns 0
- `run-file` logs show final price = 80

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | Both files 0 errors, runtime outputs 80, correct x:Class naming |
| 8-9 | Works but needed a fix cycle on argument binding |
| 6-7 | Sub-workflow works but invocation broken |
| 4-5 | x:Class naming wrong or arguments broken |
| 2-3 | Didn't create separate workflow |
| 0-1 | Didn't follow skill |

---

## T04: REST API + JSON Parse

### User prompt
```
Create a UiPath project "ApiUsers" in C:\Users\Alberto\Desktop\SkillTests. I want a workflow that calls https://jsonplaceholder.typicode.com/users, parses the JSON, and logs the name and email of the first 3 users. Run it.
```

### Validation
- `run-file` logs show 3 lines with real user names and emails

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, 3 correct log entries on first try |
| 8-9 | Works but needed 1-2 fix cycles |
| 6-7 | Used string parsing instead of JSON deserialization |
| 4-5 | HTTP works but JSON parsing or loop fails |
| 2-3 | Wrong activity or completely broken |
| 0-1 | Didn't follow skill |

---

## T05: Try-Catch with HTTP Error

### User prompt
```
Create a UiPath project "SafeHttp" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that calls https://httpstat.us/500 — it always returns a server error. Wrap it in a try-catch so the workflow doesn't crash. Log the error in the catch block, and after the try-catch log "Workflow completed". Run it.
```

### Validation
- `run-file` logs show an error message AND "Workflow completed" after it

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, error caught, "Workflow completed" logged |
| 8-9 | Works but catch variable naming slightly off |
| 6-7 | Catch block empty or wrong exception type |
| 4-5 | TryCatch structure broken |
| 2-3 | No TryCatch at all |
| 0-1 | Didn't follow skill |

---

## T06: Send Email with Attachment

### User prompt
```
Create a UiPath project "EmailSender" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that sends an email via SMTP to test@example.com with subject "Monthly Report", body "Please find the attached monthly report.", and attach C:\Users\Alberto\Desktop\report.pdf. Use smtp.gmail.com port 587 with SSL. Don't hardcode credentials, use variables. Just validate it, don't run.
```

### Validation
- `get-errors` returns 0

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, all properties correct, attachment configured, creds as variables |
| 8-9 | 0 errors but attachment slightly off |
| 6-7 | Used Outlook activity instead of SMTP |
| 4-5 | Missing required properties (port, SSL) |
| 2-3 | Wrong activity class |
| 0-1 | Didn't follow skill |

---

## T07: Install Package + Read PDF

### User prompt
```
Create a UiPath project "PdfReader" in C:\Users\Alberto\Desktop\SkillTests. I need to read a PDF file at C:\Users\Alberto\Desktop\sample.pdf and log its text content. Figure out what package I need. Just validate, don't run.
```

### Validation
- `get-errors` returns 0
- PDF package is installed in project.json

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | Identified missing package, installed it, 0 errors |
| 8-9 | Works but extra search cycles |
| 6-7 | Installed but used wrong activity |
| 4-5 | Tried to use activity without installing package |
| 2-3 | Installed wrong package |
| 0-1 | Didn't follow skill |

---

## T08: Excel Read, Filter, Write

### User prompt
```
Create a UiPath project "ExcelFilter" in C:\Users\Alberto\Desktop\SkillTests. Make a workflow that reads TestData/Employees.xlsx (sheet "Data" with Name, Department, Salary columns), filters employees earning above 60000, writes the results to a new sheet "HighEarners" in the same file, and logs how many were filtered. Just validate, don't run.
```

### Validation
- `get-errors` returns 0

### Scoring
| Score | Criteria |
|-------|----------|
| 10 | 0 errors, correct scope nesting, filter logic, count logged |
| 8-9 | 0 errors but filter suboptimal |
| 6-7 | Needed multiple fix cycles for scope/Range type issues |
| 4-5 | Scope nesting wrong or DataTable type issues |
| 2-3 | Wrong activity class names |
| 0-1 | Didn't follow skill |

---

## Score Sheet

### Test order
T01 → T02 → T03 → T04 → T05 → T06 → T07 → T08

### Column definitions
- **Time**: Wall-clock minutes from prompt to final validation/run
- **Fix Cycles**: Number of get-errors → edit → get-errors loops
- **CLI Calls**: Total `uip rpa` commands executed (create-project, find-activities, get-default-activity-xaml, get-errors, run-file, install-or-update-packages)
- **Notes**: Key issues encountered (e.g., "forgot WebAPI package", "wrong property name")

### Pass thresholds

| Level | Score |
|-------|-------|
| Excellent | 64+ (80%) |
| Good | 48-63 (60%) |
| Marginal | 32-47 (40%) |
| Failing | <32 |

Results are recorded in [TEST_RESULTS_NO_UIA.md](./TEST_RESULTS_NO_UIA.md).
