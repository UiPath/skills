# Discovery Workflow — Detailed Steps

Complete discovery procedure before writing or editing any XAML. Referenced from the main skill when detailed guidance is needed.

---

## Step 1: Project Structure

```
Glob: pattern="**/*.xaml" path="{projectRoot}"       → list all XAML workflow files
Read: file_path="{projectRoot}/project.json"          → read the project definition
```

Analyze: folder conventions, naming patterns, existing workflows, `expressionLanguage` (VB.NET or C#), installed packages (`dependencies`).

---

## Step 2: Consult Activity Reference Docs

Read `references/activity-docs/` for behavioral context (what activities do, gotchas, patterns).

| Situation | Action |
|-----------|--------|
| Know the package | Read `activity-docs/{PackageName}.md` directly |
| Don't know the package | Read `activity-docs/_INDEX.md` to find it |
| Need VB.NET expressions | Read `activity-docs/_PATTERNS.md` |
| Need XAML structure | Read `references/xaml-basics-and-rules.md` |
| Need gotchas | Read `activity-docs/_COMMON-PITFALLS.md` |
| Need InvokeCode patterns | Read `activity-docs/_INVOKE-CODE.md` |
| Working with REFramework | Read `activity-docs/_REFRAMEWORK.md` |
| Working with Document Understanding | Read `activity-docs/_DU-PROCESS.md` |
| Need all activities | Read `activity-docs/AllActivities.md` |

**These docs tell you what and how — NOT exact CLR property names/enum values for XAML. Steps 4 and 5 are mandatory for that.**

---

## Step 3: Search Current Project

```
Glob: pattern="**/*pattern*.xaml" path="{projectRoot}"
Grep: pattern="ActivityName|pattern" path="{projectRoot}"
Read: file_path="{projectRoot}/ExistingWorkflow.xaml"
```

Mature project: prioritize local patterns. Greenfield: skip.

---

## Step 4: Discover Activities (MANDATORY for non-built-in activities)

**Skip find-activities for built-in activities** listed in [_BUILT-IN-ACTIVITIES.md](./activity-docs/_BUILT-IN-ACTIVITIES.md): If, Assign, Sequence, TryCatch, Flowchart, ForEach, While, Switch, Throw, Delay, Parallel, LogMessage, InvokeCode, InvokeWorkflowFile, ForEachRow, AddDataRow. Use the provided XAML snippets directly.

**For all other activities**, run find-activities. Returns exact class names, argument signatures, types, **ready-to-use XAML snippet**, and **xmlns declaration**.

```bash
uip rpa-legacy find-activities "{projectRoot}" --query "send mail" --output json
uip rpa-legacy find-activities "{projectRoot}" --query "invoke code" --include-type-definitions --output json
```

**Use the returned `XamlSnippet` as your starting point** for activity XAML — it has correct element names, namespaces, and property names for the installed package version. Also add the returned `XmlnsDeclaration` to the root `<Activity>` element.

**Query syntax tips:**
- **Multi-word queries work** with relevance scoring: `"Excel Read Range"` splits into words, scores matches, bonuses when all words match
- **CamelCase boundaries detected**: `"SendHotkey"`, `"ExcelReadRange"` match correctly
- **Use `--exact`** when you know the exact activity name: `--query "ReadRange" --exact` — avoids irrelevant results
- Each call takes ~15-30 seconds — use `--exact` for known names to get precise results fast
- If a query returns too many irrelevant results, add `--exact` or use more specific terms

Activity reference docs describe behavior/gotchas but NOT exact CLR class names or argument types. Skipping this step → guessing → wasted validation cycles.

---

## Step 5: Inspect Types (MANDATORY for Enums/Complex Types)

**Run for every enum or complex type.** Gets exact valid values.

```bash
# Example: InvokeCode Language accepts VBNet and CSharp (NOT "VisualBasic" or "VB")
uip rpa-legacy type-definition "{projectRoot}" --type "NetLanguage" --output json

uip rpa-legacy type-definition "{projectRoot}" --type "System.Net.Mail.MailMessage" --output json
```

When to run: any enum property, any complex type argument, any type without listed valid values in docs.

---

## Step 5.5: Search NuGet for Packages (When Needed)

When the known packages in [project-structure.md](./project-structure.md) and `find-activities` don't cover a capability:

```bash
uip rpa-legacy find-package --query "barcode" --limit 10 --output json
```

Searches all configured NuGet feeds by name and description. After finding the right package, add it to `dependencies` in project.json, then `find-activities` will index its activities.

Also works for arbitrary .NET packages (e.g., `CsvHelper`, `HtmlAgilityPack`). Avoid packages already bundled with Studio (e.g., `Newtonsoft.Json`) — version conflicts can cause issues.

---

## Step 6: Search UiPath Documentation (Fallback)

```bash
uip docsai ask "best practices for Excel automation in legacy projects" --output json
uip docsai ask "ExcelApplicationScope ActivityAction body validation error" --output json
```

Use when: bundled docs + CLI tools don't cover the topic, need best practices/guidelines/troubleshooting, unfamiliar error, platform concepts (Orchestrator, queues, triggers).

---

## Step 7: Search the Web (Last Resort)

Use `WebSearch` for UiPath Forum, Stack Overflow, GitHub, Reddit:

```
WebSearch: "UiPath forum ExcelApplicationScope ActivityAction body legacy"
WebSearch: "site:stackoverflow.com UiPath legacy ExcelApplicationScope XAML"
WebSearch: "site:github.com UiPath REFramework legacy XAML example"
```

Use when: all previous steps fail, obscure errors, community workarounds needed. Always verify web-sourced info against project config.

---

## Troubleshooting

### Wrong enum value
**Symptom:** "Cannot create unknown type" or "is not a member of"
**Fix:** `uip rpa-legacy type-definition "{projectRoot}" --type "EnumTypeName" --output json`

### Activity class name not found
**Symptom:** Unknown activity type or missing namespace
**Fix:** `uip rpa-legacy find-activities "{projectRoot}" --query "..." --output json`, add xmlns + assembly ref

### Multiple errors after batch editing
**Symptom:** Many errors at once
**Fix:** Revert to last good state. Re-add one activity at a time, validating after each.

### Activity docs don't match XAML property names
**Symptom:** Properties from docs don't work
**Fix:** `find-activities --include-type-definitions` for exact CLR property names

### Stuck on unfamiliar problem
**Escalation:** `docsai ask` → `WebSearch` → ask user
