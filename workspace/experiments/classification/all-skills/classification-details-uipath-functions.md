# Classification Details — uipath-functions

**Classification: Partial**

---

## What the Skill Teaches

Scaffolding, implementing, and deploying UiPath Python Coded Functions — deterministic Python units built via `uip function` (new/init/pack/publish) with typed Pydantic I/O, `uipath.json` functions map, and full UiPath SDK access.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| 1 | Scaffold with `uip function new -l py` | Marginal | Single command; post-scaffold fix-up if framework deps are present adds some logic but is too small for a standalone script |
| 2 | Define function schema (Pydantic Input/Output models) | No | Judgment; field names, types, and error fields depend on the function's business domain |
| 3 | Implement business logic (Python code) | No | Judgment; core of the skill — writing the deterministic logic the function encapsulates |
| 4 | Register entrypoint in `uipath.json` (`functions` map) | Marginal | Single-field edit; mechanical but too small for standalone script |
| 5 | Declare dependencies in `pyproject.toml` | Marginal | Small template fill; well-defined but one-liner edit |
| 6 | **Generate entry points (`uip function init`)** | **Yes — VALIDATE/CHECK** | Must run after every Input/Output or entrypoint change; deterministic — generates `entry-points.json`, `bindings.json`, `project.uiproj` |
| 7 | SDK capabilities (assets, buckets, queues, connections, Integration Service) | No | Judgment; which services to call, how to handle errors, what business rules to apply |
| 8 | **Pack and publish lifecycle (`uip function pack` → `uip function publish`)** | **Yes — TRANSFORM-PIPELINE** | Fixed ordered sequence with no judgment between steps; prerequisite is that `init` has been run |

---

## Codifiable Procedures (not yet scripted)

### 1. Entry Point Generation — VALIDATE/CHECK

**Source:** `skills/uipath-functions/SKILL.md` §Step 6: Generate Entry Points

**What it does:** Runs `uip function init` to discover all entrypoints declared in `uipath.json` and generate `entry-points.json`, `bindings.json`, and `project.uiproj`. Must be run before `pack` or `push`, and re-run whenever Input/Output schemas or the entrypoint registration in `uipath.json` changes. If the command fails, the project structure is invalid and cannot be packed. Line 191: `"Python only. Discovers entrypoints and generates entry-points.json, bindings.json, and project.uiproj. Must run before pack or push. Re-run whenever Input/Output schemas or the entrypoint registration in uipath.json changes."`

**Why it's mechanical:** The command is a single deterministic CLI call with a fixed trigger condition (any schema or entrypoint change); success/failure is binary.

**Turn savings:** Without a script, the agent must remember to run `init` and verify the generated files each time schemas change; a check script can detect schema drift and prompt re-generation automatically.

---

### 2. Pack and Publish Pipeline — TRANSFORM-PIPELINE

**Source:** `skills/uipath-functions/SKILL.md` §Step 8: Pack and Publish

**What it does:** Executes the function publication sequence: `uip function pack` (creates `.nupkg` from the project), then `uip function publish` (uploads `.nupkg` to Orchestrator, either interactively or with `--feed-id` for CI). For Studio Web sync, substitutes `uip function push`. Inputs: project directory, optional feed ID. Outputs: `.nupkg` file, published package in Orchestrator. Line 244: `"uip function pack    # creates .nupkg" / "uip function publish  # upload to Orchestrator (interactive feed picker)" / "uip function publish --feed-id <FEED_ID>  # CI/non-interactive"`

**Why it's mechanical:** The two steps run sequentially with no branching or judgment; the only variation is whether `--feed-id` is supplied for headless execution.

**Turn savings:** Without a script, the agent runs each command separately and checks output between them across 2–3 turns; a pipeline script completes both steps in one.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The implementation step (Step 3: writing the Python business logic) is the central and heaviest part of what the skill teaches — it is entirely judgment-based (what logic to write, how to handle errors, which SDK services to call). Schema definition (Step 2) and SDK integration (Step 7) are also judgment-driven. These judgment areas account for the majority of the skill's teaching weight; the codifiable lifecycle steps (init, pack, publish) are supporting mechanics.

**Why not None:** Entry point generation (`uip function init`) is a well-defined VALIDATE/CHECK trigger with explicit re-run conditions, and the pack→publish sequence is a TRANSFORM-PIPELINE with no judgment between steps.

**Evidence locations:**
- Entry point generation mandate: `skills/uipath-functions/SKILL.md` §Step 6: Generate Entry Points (lines 186–191)
- Pack/publish sequence: `skills/uipath-functions/SKILL.md` §Step 8: Pack and Publish (lines 244–255)
- Implementation judgment: `skills/uipath-functions/SKILL.md` §Step 3: Implement Business Logic (lines 102–148) — explicit "do not make LLM calls" guidance signals judgment is the agent's responsibility
