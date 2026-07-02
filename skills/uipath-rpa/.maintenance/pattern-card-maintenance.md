# Pattern Card Maintenance

Regeneration procedure for [references/common-pattern-card.md](../references/common-pattern-card.md). Run when: a stamped package ships a new minor/major, a staleness report arrives (`/uipath-feedback` or repo issue), or a new pattern is added.

## Procedure

1. Scratch project (never committed): `uip rpa init --name PatternCard --location <TEMP_DIR> --template-id BlankTemplate --expression-language VisualBasic --target-framework Portable --output json`. On macOS/Linux the Helm host cannot open `Windows`-target projects — `Portable` is mandatory there.
2. Install every card-stamped package at the target versions: `uip rpa packages versions --package-id <Id> --include-prerelease ...` to pick, then `uip rpa packages install` (flag shape drifts across CLI builds — confirm with `--help`; current builds take a JSON array `[{"id":"...","version":"..."}]`).
3. One probe workflow per card entry: paste the entry's snippet inside a complete `<Activity>` root cloned from the scaffolded `Main.xaml` (namespaces + `TextExpression` blocks), adding the entry's listed prefixes.
4. Gate: per-file `uip rpa validate --file-path "<RELATIVE_FILE>" --project-dir "<DIR>" --output json` to 0 errors (relative path — absolute falsely fails), then `uip rpa build "<DIR>" --output json` clean. `validate` clean is NOT sufficient — namespace-registration and member-name errors surface only at `build`.
5. Failing entry → fix from `{PROJECT_DIR}/.local/docs/packages/<PackageId>/activities/<Activity>.md` (post-install, authoritative for the installed version), re-gate. `Cannot create unknown type` / `TypeLoadException` on a cross-platform gate usually means Windows-only activity → move the entry to the card's "Not on this card" list or validate on a Windows machine before stamping.
6. Update every entry's version stamp + the header package-anchor line. Entries never carry a version they were not gated against.
7. New pattern candidates qualify by frequency: appears in ≥2 `tests/tasks/uipath-rpa/` tasks or is a documented top user ask. Keep the card ≤ ~15 entries — it is a hot-path read, not a catalog.

## Rules

- CLI-gate before stamp — no exceptions, no "obviously fine" edits.
- UIA activities never enter this card (`skills/uipath-rpa/CLAUDE.md` boundary).
- Windows-only families (Excel X, SMTP SendMail) require a Windows-target gate; until one runs, they stay off the card with an explicit "Not on this card" note.
- Prose follows `.claude/rules/token-optimization.md`.
