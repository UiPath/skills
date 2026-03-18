# Inspect NuGet Package Tool (On-Demand API Discovery)

Use this when the static reference files (`references/<service>/examples.md`) don't cover an API, when the user has a different package version, or when you need ground-truth method signatures.

## How to Run

The inspect-package tool is built into the UiPath CLI. No separate build step is needed.

### Inspect a package from a NuGet feed
```bash
uip rpa inspect-package --package-name <PackageName> --package-version <Version> [--feed-url <NuGetV3FeedUrl>]
```

When `--feed-url` is omitted, the tool downloads from the UiPath Official feed first and falls back to nuget.org.

### Inspect a local .nupkg file
```bash
uip rpa inspect-package --nupkg-path <path/to/package.nupkg>
```

Use this when the package is already cached locally (e.g. from a private feed) or when you have a `.nupkg` file on disk.

## Examples

```bash
# Inspect Excel activities from UiPath feed
uip rpa inspect-package --package-name UiPath.Excel.Activities --package-version 3.3.1

# Inspect a specific version the user has
uip rpa inspect-package --package-name UiPath.System.Activities --package-version 25.12.2

# Inspect from a custom feed
uip rpa inspect-package --package-name MyPackage --package-version 1.0.0 --feed-url https://my-feed/v3/index.json

# Inspect third-party package from nuget.org
uip rpa inspect-package --package-name CsvHelper --package-version 33.0.1

# Inspect a local .nupkg file directly
uip rpa inspect-package --nupkg-path ~/.nuget/packages/csvhelper/33.0.1/csvhelper.33.0.1.nupkg
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

Structured markdown listing all public types, methods, properties, enums, delegates, and events from the package DLLs. The tool performs framework-aware DLL selection and recursive dependency resolution (up to depth 2).

## Requirements & Notes

- Requires `uip` to be available on PATH
- Downloads from the UiPath Official feed first, then falls back to nuget.org — so it works with **any** NuGet package, not just UiPath ones
- The tool automatically checks the local NuGet cache at `~/.nuget/packages/` when a package cannot be downloaded
- For local `.nupkg` files (e.g. packages from private feeds already cached locally), use `--nupkg-path` to skip the download entirely
- Some packages are metapackages with no DLLs (e.g. `Humanizer`). If you get "No DLLs found", try the `.Core` sub-package (e.g. `Humanizer.Core`)
