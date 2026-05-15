# Audit `uip` Verb References

Verify that every `uip <verb>` mentioned in task YAMLs and skill docs corresponds to a real verb in the installed `uip` CLI. Produces two markdown audit reports under `tests/reports/`.

**Input:** `$ARGUMENTS`
- Empty (default) — audit both tests and skills.
- `tests` — only `tests/tasks/`. Writes `tests/reports/cli-verb-audit.md`.
- `skills` — only `skills/`. Writes `tests/reports/skill-verb-audit.md`.
- `--refresh` — force a catalog rebuild before running, even if a snapshot already exists.

**Output:** One or both of:
- `tests/reports/cli-verb-audit.md` — task-YAML reachability (High/Medium/Info severities, sourced from `command_executed` patterns).
- `tests/reports/skill-verb-audit.md` — skill-doc verb references (Stale/Uncertain severities, sourced from prose, code blocks, and tables).

Plus a chat summary with the top counts and the worst-offender files.

---

## Phase 1 — Ensure Catalog

The catalog at `assets/uip-catalog-snapshot.json` is the source of truth for "which verbs exist". Without it the checkers cannot run.

1. If `--refresh` was passed, or `assets/uip-catalog-snapshot.json` does not exist, run:
   ```bash
   python3 scripts/build-uip-catalog.py
   ```
   The builder requires `uip` on PATH. If the user has `uip 1.1.0+` and is missing plugin tools (`admin`, `platform`, etc.), warn that coverage will be incomplete — the report will surface those as Stale findings even when the verbs are valid in a fully-installed environment. Suggest `python3 scripts/build-uip-catalog.py --install-tools` if GH Packages auth is available.

2. If the snapshot exists and `--refresh` was NOT passed, read its `generated_at` field. If older than 24 hours, print a one-line note suggesting `/audit-verbs --refresh` and continue with the stale snapshot.

3. Read the snapshot to know:
   - `cli_version`, `verbs` count, `unwalkable_groups` — surface all three in the chat summary.

## Phase 2 — Run the Audits

Run whichever sides the user asked for. Each checker emits its own report via `--report PATH`.

### Tests audit (when `$ARGUMENTS` is empty or `tests`)

```bash
find tests/tasks -name "*.yaml" \
  -not -path "*/activation/*" -not -path "*/_shared/*" \
  | xargs python3 scripts/check-cli-verbs.py \
      --report tests/reports/cli-verb-audit.md
```

Severity legend (mirror `.claude/commands/lint-task.md`):
- **High** — verb path does not exist in the catalog. The criterion can never fire; the task scores zero on a passing run.
- **Medium** — pattern matches only retired verbs listed in `.claude/rules/cli-renames.md`. Suggest the canonical replacement.
- **Info** — pattern is too dynamic to enumerate (`.*`, character classes, unbounded quantifiers). Advisory only; not counted in the verdict.

### Skills audit (when `$ARGUMENTS` is empty or `skills`)

```bash
python3 scripts/check-skill-verbs.py \
  --report tests/reports/skill-verb-audit.md skills/
```

Severity legend:
- **Stale** — verb path does not match any catalog entry, and no part of the path falls under an unwalkable group. Agents copy-pasting from the skill will hit `unknown command`.
- **Uncertain** — verb path starts with an unwalkable-group prefix (the tool failed to enumerate its subcommands, e.g. via missing `--output json` support or a broken `npm install`). Cannot be verified statically; do not treat as a true positive.

## Phase 3 — Summarize in Chat

After both runs (or the one the user requested) complete, post a single message with:

1. **Catalog header** — `uip <version>`, verb count, list of unwalkable groups.
2. **Tests row** — `<H> High, <M> Medium, <I> Info`. Name the report path.
3. **Skills row** — `<Stale> Stale, <Uncertain> Uncertain`. Name the report path.
4. **Top offenders** — for each side that ran, list the top 3 verb paths by count and the top 3 files by count, drawn from the report's leading tables. Each line ≤ one row.
5. **Suggested next steps** — pick from this menu based on the findings:
   - Stale `solution init` → suggest a `git grep -l "solution init" skills/` sweep, replace with `solution new`.
   - Many Uncertain under a single group (e.g. `codedagent`) → suggest filing an upstream bug for `--output json` support so the group can be walked.
   - High count concentrated in one plugin group (e.g. `rpa`) → suggest `uip tools install @uipath/<group>-tool` to enrich the catalog, then `/audit-verbs --refresh`.

Keep the summary under 15 lines. Link to the report files for detail. Do **not** inline every finding.

## Phase 4 — Exit Code

- 0 if no Stale/High findings on either side that ran.
- 1 otherwise. (For CI consumers; the user sees the summary regardless.)

---

## Rules

1. **Never modify task YAMLs or skill docs.** This command produces reports only. Suggested fixes belong in the chat summary, never as edits.
2. **Always write to `tests/reports/`** — same location as `/test-coverage` reports so all generated audits live together.
3. **Never skip Phase 1.** If the catalog is missing, the checker will exit with an error; the user wants the report, not the error.
4. **If running on a fresh checkout** (no `tests/.venv`, no catalog), do Phase 1 first and surface the catalog-build timing — it can take ~2 minutes serially. Suggest `--install-tools` only when `npm.pkg.github.com` auth is known to be available (env var `NPM_TOKEN` set or `~/.npmrc` configured for `@uipath:`).
5. **Cite line numbers** in the chat summary only when calling out a single broken finding worth fixing immediately; otherwise leave drilldown to the report file.
