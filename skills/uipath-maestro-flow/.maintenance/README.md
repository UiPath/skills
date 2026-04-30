# Skill Maintenance

Internal tooling and conventions for maintaining the `uipath-maestro-flow` skill structure. Not loaded by agents during normal use.

## Structure

The skill is organized into three peer capabilities:

```text
SKILL.md                              ← capability router (universal rules + 3-bucket intent)
references/
├── AUTHOR.md                         ← capability index
├── OPERATE.md                        ← capability index
├── DIAGNOSE.md                       ← capability index
├── shared/                           ← cross-capability primitives
│   ├── commands.md                   ← flat CLI lookup
│   ├── cli-conventions.md            ← --output json, login, FOLDER_KEY, etc.
│   ├── file-format.md                ← .flow JSON schema
│   ├── variables-and-expressions.md  ← =js: Jint expressions
│   └── node-output-wiring.md         ← canonical $vars wiring rule
├── author/
│   ├── greenfield.md                 ← create-new-flow journey
│   ├── brownfield.md                 ← edit-existing-flow journey
│   ├── editing-operations.md         ← strategy selection
│   ├── editing-operations-json.md    ← Direct JSON recipes (default)
│   ├── editing-operations-cli.md     ← CLI carve-outs
│   ├── planning-arch.md              ← topology/plugin index
│   ├── planning-impl.md              ← registry/binding/wiring
│   └── plugins/                      ← per-node-type planning + impl
├── operate/
│   ├── ship.md                       ← Studio Web upload + Orchestrator deploy
│   ├── run.md                        ← debug + process run + job status/traces
│   └── manage.md                     ← instance lifecycle (pause/resume/cancel/retry)
└── diagnose/
    ├── troubleshooting-guide.md      ← diagnostic priority ladder
    └── failure-modes.md              ← pattern catalog (MST-9107, MST-9061, etc.)
```

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

Returns `checked=N broken=M`. The known false positive (`./REFACTOR-PROPOSAL.md -> ../AUTHOR.md`) is an example link inside a code block in the design doc — ignore.

## When to run these checkers

- Before committing changes that move files or rewrite link paths
- Before merging a PR that touches `references/`
- After a refactoring phase

The checkers are not currently wired into CI or pre-commit hooks. They are kept as lightweight tooling in this directory so future maintainers can run them on demand.

## Reachability convention

Plugin docs (`references/author/plugins/<name>/{planning,impl}.md`) are linked from `AUTHOR.md` via **folder links** (e.g., `[connector](author/plugins/connector/)`), not individual file links. Agents navigating to the folder discover both `planning.md` and `impl.md` there. This satisfies practical 2-hop reachability from `SKILL.md`.

A strict file-link reachability checker would flag these 29 plugin docs as "unreachable" — that is a false negative against the agent-navigation model. If a future change requires explicit file links (e.g., AUTHOR.md task table needs a specific impl.md anchor), add the file link inline rather than relying on folder discovery.
