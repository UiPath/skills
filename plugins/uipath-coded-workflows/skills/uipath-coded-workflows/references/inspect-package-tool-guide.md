# Inspect NuGet Package Tool (On-Demand API Discovery)

Use this when the static reference files (`references/<service>/examples.md`) don't cover an API, when the user has a different package version, or when you need ground-truth method signatures.

## Tool Location

**Relative to skill directory:** `scripts/inspect-package/`

## Before First Use: Build the Tool

The build script auto-detects whether a build is needed:

Resolve `SKILL_DIR` — the absolute path to this skill's root directory (the folder containing `SKILL.md`). Determine it by searching upward from this file or by using the skill's known location in the project (e.g. `.claude/skills/uipath-coded-workflow/`).

**macOS / Linux:**
```bash
bash "$SKILL_DIR/scripts/inspect-package/build.sh"
```

**Windows:**
```powershell
powershell -File "$SKILL_DIR\scripts\inspect-package\build.ps1"
```

## Usage

**Step 1: Set TOOL_DLL variable** (relative to `SKILL_DIR`)

**macOS / Linux:**
```bash
TOOL_DLL="$SKILL_DIR/scripts/inspect-package/bin/Release/net7.0/InspectPackage.dll"
```

**Windows:**
```powershell
$TOOL_DLL="$SKILL_DIR\scripts\inspect-package\bin\Release\net7.0\InspectPackage.dll"
```

**Step 2: Run the tool**
```bash
dotnet <TOOL_DLL> <PackageName> <Version> [FeedUrl]
```

## Examples

```bash
# Inspect Excel activities
dotnet $TOOL_DLL UiPath.Excel.Activities 3.3.1

# Inspect a specific version the user has
dotnet $TOOL_DLL UiPath.System.Activities 25.12.2

# Inspect from a custom feed
dotnet $TOOL_DLL MyPackage 1.0.0 https://my-feed/v3/index.json

# Inspect third-party package from nuget.org
dotnet $TOOL_DLL CsvHelper 33.0.1
```

## Finding the Latest Stable Version

When you don't know the version of a UiPath package, query the UiPath Official NuGet feed to find the latest stable (non-preview) version:

```bash
UIPATH_FEED="https://uipath.pkgs.visualstudio.com/5b98d55c-1b14-4a03-893f-7a59746f1246/_packaging/1c781268-d43d-45ab-9dfc-0151a1c740b7/nuget/v3/flat2" && bun -e "const p=process.argv[1];const r=await fetch(p+'/index.json');const d=await r.json();console.log(d.versions.find(v=>v.indexOf('preview')<0))" "$UIPATH_FEED/<package-name-lowercase>"
```

Replace `<package-name-lowercase>` with the package ID in lowercase (e.g. `uipath.microsoftoffice365.activities`).

**Examples:**
```bash
# Latest stable UiPath.MicrosoftOffice365.Activities → 3.6.10
... "$UIPATH_FEED/uipath.microsoftoffice365.activities"

# Latest stable UiPath.System.Activities → 25.12.2
... "$UIPATH_FEED/uipath.system.activities"
```

**Notes:**
- The feed returns versions in descending order (newest first); the one-liner picks the first non-preview entry
- Package names in the URL **must be lowercase**
- This feed is public for version listing but requires authentication for package downloads (Studio handles this automatically when restoring dependencies)

---

## When to Use

- You encounter an unknown activity/method not in reference files
- The user's `project.json` has a different package version than reference docs
- You need exact method signatures, parameter types, or enum values
- You're unsure about the correct API and want to verify against the actual package
- You need to find and evaluate a third-party NuGet package for use in a coded workflow

## Output

Structured markdown listing all public types, methods, properties, and enums from the package DLLs. Diagnostic messages go to stderr; only the markdown report goes to stdout.

## Requirements & Notes

- Requires `dotnet` SDK 7.0+ on the machine
- Downloads from the UiPath Official feed first, then falls back to nuget.org — so it works with **any** NuGet package, not just UiPath ones
- Some packages are metapackages with no DLLs (e.g. `Humanizer`). If you get "No DLLs found", try the `.Core` sub-package (e.g. `Humanizer.Core`)
- DLLs with missing transitive dependencies will show a load error — this is expected and harmless; the public API assemblies load fine
