# Skill Maintenance

Lightweight checkers for the `uipath-maestro-bpmn` skill. Not loaded by agents
during normal use.

The skill is a single `SKILL.md` plus a small set of behavioral references under
`references/shared/` (`cli-conventions.md`, `expression-authoring.md`,
`public-safety.md`). All structural authoring (element shapes, bindings,
script/variables payloads) comes from the `uip maestro bpmn registry` CLI, not
from docs in this skill — so the maintenance surface is intentionally small.

## Run everything

```bash
bash .maintenance/check-all.sh
```

Runs each checker and exits non-zero if any fails.

## Checkers

| Script | Purpose |
| --- | --- |
| `check-links.sh` | Every relative markdown link in SKILL.md / references resolves to a real file. |
| `check-anchors.sh` | Every in-page `#anchor` link resolves to a heading. |
| `check-uip-commands.sh` | Every `uip ...` command referenced in SKILL.md / references exists in the installed CLI (help-output walk; no command is executed). Use `<!-- uip-check-skip -->` on a line to opt out — e.g. for the intentional "there is no `uip maestro bpmn validate` command" note, or for `uip is ...` commands the help-walk cannot resolve. |
| `check-validation-fixtures.sh` / `.py` | The static `fixtures/validation/` corpus is well-formed and structurally consistent. |
| `check-real-pack.sh` | The fixture corpus packs locally with the `uip` CLI. |

## When to run

- After editing SKILL.md or a reference — `check-links.sh`, `check-anchors.sh`, `check-uip-commands.sh`.
- After adding or editing a validation fixture — `check-validation-fixtures.sh`.

CI should run `check-all.sh` before evals so link / command / fixture drift fails fast.
