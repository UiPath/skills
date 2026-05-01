# Skill Maintenance

Internal tooling and conventions for maintaining the `uipath-maestro-flow` skill structure. Not loaded by agents during normal use.

## Structure

The skill is organized into three peer capabilities:

```text
SKILL.md                                ← capability router (universal rules + 3-bucket intent)
references/
├── shared/                             ← cross-capability primitives
│   ├── cli-commands.md                 ← flat CLI lookup
│   ├── cli-conventions.md              ← --output json, login, FOLDER_KEY, etc.
│   ├── file-format.md                  ← .flow JSON schema
│   ├── variables-and-expressions.md    ← =js: Jint expressions
│   └── node-output-wiring.md           ← canonical $vars wiring rule
├── author/
│   ├── CAPABILITY.md                   ← capability index
│   └── references/                     ← author's supporting docs
│       ├── greenfield.md               ← create-new-flow journey
│       ├── brownfield.md               ← edit-existing-flow journey
│       ├── editing-operations.md       ← strategy selection
│       ├── editing-operations-json.md  ← Direct JSON recipes (default)
│       ├── editing-operations-cli.md   ← CLI carve-outs
│       ├── planning-arch.md            ← topology/plugin index
│       ├── planning-impl.md            ← registry/binding/wiring
│       └── plugins/                    ← per-node-type planning + impl
├── operate/
│   ├── CAPABILITY.md                   ← capability index
│   └── references/                     ← operate's supporting docs
│       ├── ship.md                     ← Studio Web upload + Orchestrator deploy
│       ├── run.md                      ← debug + process run + job status/traces
│       └── manage.md                   ← instance lifecycle (pause/resume/cancel/retry)
└── diagnose/
    ├── CAPABILITY.md                   ← capability index
    └── references/                     ← diagnose's supporting docs
        ├── troubleshooting-guide.md    ← diagnostic priority ladder
        └── failure-modes.md            ← pattern catalog (MST-9107, MST-9061, etc.)
```

**Recursive pattern.** Skill = `SKILL.md` + `references/`. Capability = `CAPABILITY.md` + `references/`. The same "index next to its references" shape at two scales. Future capabilities (e.g., `governance/`) get the template for free.

**Convention:** each capability is a self-contained folder. Every file under `<capability>/references/` is implicitly that-capability-scoped — path = provenance. The `CAPABILITY.md` index is always at `<capability>/CAPABILITY.md` (uniform shape across all three).

### Capability boundary

- **Author** = on disk, locally, **without `uip login`** (`flow init`, `validate`, `tidy`, registry, JSON edits)
- **Operate** = touches the cloud, **requires `uip login`** (`solution upload`, `flow debug`, `flow pack`, `process run`, `instance ...`)
- **Diagnose** = postmortem on a failed run, **requires `uip login`** (`instance incidents`, `instance variables`, `instance asset`, `incident get`, `job traces`)

Author terminates at `validate` + `tidy` and hands off to Operate. Operate hands off to Diagnose when a run faults. Diagnose hands off back to Author for the underlying fix.

### Capability-index template

`AUTHOR.md`, `OPERATE.md`, `DIAGNOSE.md` all follow the same 6-section structure:

1. `# <Capability> — <one-line purpose>`
2. `## When to use this capability`
3. `## Critical rules`
4. `## Workflow`
5. `## Common tasks`
6. `## Anti-patterns`
7. `## References`

## Markdown anchor slugs (`[link](file.md#section-name)`)

Anchor links are computed exactly as GitHub does — getting them wrong silently produces a dead link that markdown lint won't catch.

### Slug rule

1. Lowercase the heading
2. Strip these characters entirely: `` ` ``, `*`, `_`, and any non-alphanumeric/non-space/non-dash character
3. Replace each remaining space with `-`
4. **Separator characters do not collapse** — each space (or em-dash that became a space-pair) becomes its own dash

### Common gotchas

| Heading | Wrong slug | Correct slug | Why |
| --- | --- | --- | --- |
| `## 5. \`--folder-key\` requirement` | `#5--folder-key-requirement` | `#5---folder-key-requirement` | After `.` strips and backticks strip: `5 --folder-key requirement`. The space between `5` and `--` becomes a dash, joining the two literal dashes from `--folder-key` → 3 dashes |
| `## Reused reference ID — cross-connection ID leakage` | `#reused-reference-id-cross-connection-id-leakage` | `#reused-reference-id--cross-connection-id-leakage` | The em-dash (`—`) is stripped (non-alphanumeric/space/dash), but the spaces on either side of it survive and both become dashes → 2 dashes |
| `## MST-9107 — \`=js:\` prefix missing` | `#mst-9107-js-prefix-missing` | `#mst-9107--js-prefix-missing` | Backticks strip from around `=js:`, then the em-dash, `=`, and `:` strip (non-alphanumeric/space/dash). The space before and after the em-dash both survive → 2 consecutive dashes between `9107` and `js` |

### Verifying anchor links

Run the anchor-checker script before committing changes that add or edit anchor links:

```bash
bash .maintenance/check-anchors.sh
```

Returns `anchors_checked=N anchors_bad=0` on success. Any non-zero `anchors_bad` lists which file → which target slug failed to resolve.

## Verifying file-path links

Run the link-checker script to catch broken `[text](path)` links:

```bash
bash .maintenance/check-links.sh
```

Returns `checked=N broken=M`. Both checkers skip links inside fenced code blocks and inline code spans, so example links in this README and in REFACTOR-PROPOSAL.md don't trigger false positives.

## Verifying link text agrees with link URL

Run the link-text checker to catch links whose **text looks like a file** but whose **URL points elsewhere**:

```bash
bash .maintenance/check-link-text.sh
```

Returns `checked=N broken=M`. Exits non-zero on any mismatch. Three failure modes, all hard failures:

- **basename-mismatch** — text basename ≠ URL basename (e.g., text `AUTHOR.md`, URL `../CAPABILITY.md`).
- **prefix-mismatch** — basenames agree but the directory hint in the text contradicts the URL's directory (e.g., text `operate/manage.md`, URL `references/manage.md`). Tolerated when the text directory is a suffix of the URL directory (e.g., text `author/greenfield.md`, URL `references/author/greenfield.md`).
- **folder-url-but-text-is-file** — URL ends with `/` but text claims a file.

Only links whose text contains a file-like token (extension `.md`, `.sh`, `.json`, `.js`, `.ts`, `.py`, `.cs`, `.xaml`, `.flow`, `.yaml`, `.yml`) are evaluated; descriptive text like `[JSON: Variable Operations](...)` is skipped. Same skip rules as `check-links.sh` (fenced code, inline code, http(s), slash commands, anchor-only).

## Verifying reachability depth

Run the depth-checker script to verify every file under `references/` is reachable from `SKILL.md` within the configured max hops (default 2):

```bash
bash .maintenance/check-depth.sh
```

Pass a custom max-hops value as the first argument:

```bash
bash .maintenance/check-depth.sh 3
```

Returns `total_files=N reachable_within=R unreachable=U exceeds_depth=E`. Folder links count as reachability for every file in the folder (per the agent-navigation convention below). Exits non-zero if any file is unreachable or exceeds the configured depth.

## Verifying capability-index template conformance

Run the template-checker script to verify each `CAPABILITY.md` follows the canonical 6-section structure (When to use / Critical rules / Workflow / Common tasks / Anti-patterns / References):

```bash
bash .maintenance/check-template.sh
```

Returns `capabilities_checked=N missing_sections=M`. Exits non-zero if any `CAPABILITY.md` is missing a required section. Catches drift if a future edit removes or renames a canonical section.

## Verifying no orphaned files

Run the orphan-checker script to find `.md` files under `references/` that no other `.md` file links to:

```bash
bash .maintenance/check-orphans.sh
```

Returns `files_checked=N orphans=M`. Exits non-zero if any orphans are found. `CAPABILITY.md` files are excluded (they are entry points linked from SKILL.md and peer indexes; SKILL.md itself is excluded as the root entry point).

Orphans typically appear after a refactor that removed inbound links but didn't delete the now-unreferenced file. Folder links count as inbound for every `.md` inside the folder, matching the agent-navigation convention used by `check-depth.sh`.

## Verifying plugin folder pairs

Run the plugin-pairs checker to verify every plugin folder has both `planning.md` and `impl.md` (the per-plugin convention):

```bash
bash .maintenance/check-plugin-pairs.sh
```

Returns `plugins_checked=N missing_files=M`. Exits non-zero if any plugin folder is missing a required file. Catches half-deleted plugins or new plugin folders that haven't been completed.

## Verifying `uip` command references

Run the uip-command checker to verify every `uip ...` invocation resolves to a real command in the installed CLI:

```bash
bash .maintenance/check-uip-commands.sh
```

Returns `commands_checked=N unknown=M`. Exits non-zero if any referenced command path is unknown to `uip`. Verification is **help-only** — the checker walks each command path with `uip <prefix> --help`, confirms the requested segment appears in the parent's `Subcommands` list, and never executes the command for real. Help responses are cached per prefix.

The checker:

- Scans `SKILL.md` and `references/**/*.md`. Skips `.maintenance/` and root-level scratch files (`PLAN.md`, `PR_BODY.md`).
- Scans both **fenced code blocks** tagged `bash`, `sh`, `shell`, `zsh`, `console`, or unlabelled, **and inline backtick spans** like `` `uip maestro flow init` ``. Inline scanning catches doc-narrative drift that fenced-only scanning misses.
- Stops the path at the first flag, placeholder (`<...>`), shell metachar, comment (`#`), path-literal, or non-kebab-case token — so positional args like `uip maestro flow registry search outlook` don't get mistreated as subcommands.
- Treats trailing tokens after a leaf-with-positional-args (e.g. `uip maestro flow registry search <keyword>`) as arguments, not missing subcommands.
- Falls back gracefully if `uip` is not installed: warns and exits 0. Pass `--strict` to fail in CI.

Pass specific files to scan only those (e.g. for pre-commit on staged files):

```bash
bash .maintenance/check-uip-commands.sh references/shared/cli-commands.md
```

### Skipping intentional historical references

Some docs reference removed commands on purpose — for example, a CLI version-comparison table that documents a pre-restructure prefix. Add `<!-- uip-check-skip -->` anywhere on the line to suppress checking for that line:

```markdown
> Replace `uip maestro flow` with `uip flow` if version < 0.3.4. <!-- uip-check-skip -->
```

For table rows, place the marker **inside a cell** so it doesn't break table structure (HTML comments render as nothing):

```markdown
| **< 0.3.4** | `uip flow` | `uip flow init MyProject` <!-- uip-check-skip --> |
```

## Running the full suite

Run all eight checkers in one invocation:

```bash
bash .maintenance/check-all.sh
```

Continues running all checkers even when one fails — the goal is to surface every issue in a single pass. Exits non-zero if any checker fails.

## When to run these checkers

- Before committing changes that move files or rewrite link paths — `check-all.sh` covers everything in one pass
- Before merging a PR that touches `references/`
- After a refactoring phase
- After deleting a doc — run `check-orphans.sh` to confirm nothing else became orphaned
- Before adding a new capability — run `check-template.sh` against the new `CAPABILITY.md`
- After adding a new plugin — run `check-plugin-pairs.sh` to confirm both `planning.md` and `impl.md` are present
- After a `uip` CLI version bump — run `check-uip-commands.sh` to catch any commands that were renamed or removed

The checkers are not currently wired into CI or pre-commit hooks. They are kept as lightweight tooling in this directory so future maintainers can run them on demand.

## Reachability convention

Plugin docs (`references/author/references/plugins/<name>/{planning,impl}.md`) are linked from `author/CAPABILITY.md` via **folder links** (e.g., `[connector](references/plugins/connector/)`), not individual file links. Agents navigating to the folder discover both `planning.md` and `impl.md` there. This satisfies practical 2-hop reachability from `SKILL.md`.

The depth checker (`check-depth.sh`) treats folder links as reachability for every `.md` file inside the folder, matching this agent-navigation model. A strict file-link-only reachability check would flag plugin docs as "unreachable" — that's a false negative.

If a future change requires explicit file links (e.g., a task table needs a specific `impl.md` anchor), add the file link inline rather than relying on folder discovery.
