# Licenses Guide

Inspect and manage license assignments via `uip or licenses`.

## Concepts

Licenses control concurrent robot capacity at the tenant level.

**Runtime types** (per machine): `Unattended`, `NonProduction`, `Headless`, `TestAutomation`

**Named User types** (per user): `Attended`, `Development`, `Studio`, `StudioX`, `RpaDeveloper`, `CitizenDeveloper`

---

## Commands

### 1. License Summary

```bash
uip or licenses info --output json
```

Returns tenant overview: allowed vs used counts per type, expiration, licensed features. **Run this first** before making allocation changes.

---

### 2. List License Assignments

```bash
uip or licenses list --type <TYPE> --output json
```

| Option | Required | Description |
|---|---|---|
| `--type <TYPE>` | Yes | Any type from above |
| `--licensed` / `--unlicensed` | No | Filter by enabled/disabled state |
| `--limit <N>` | No | Default: `50` |
| `--offset <N>` | No | Default: `0` |
| `--order-by "<FIELD> <DIR>"` | No | e.g., `"Key asc"` |

---

### 3. Toggle Machine Licensing

```bash
uip or licenses toggle <MACHINE_KEY> --type <TYPE> --enable --output json
```

| Option | Required | Description |
|---|---|---|
| `--type <TYPE>` | Yes | Runtime types only: `Unattended`, `NonProduction`, `Headless`, `TestAutomation` |
| `--enable` / `--disable` | Yes (one of) | Enable or disable |

> Named User types cannot be toggled via CLI — use Orchestrator UI.

---

## Anti-Patterns

- **Do not toggle without checking `licenses info` first.** Enabling when `usedCount == allowedCount` fails.
- **Do not use `toggle` for Named User types.** CLI supports runtime types only.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `toggle` fails "license limit reached" | No available slots | Check `licenses info`; reduce usage or increase subscription |
| `toggle` fails on Named User type | Not supported by CLI | Use Orchestrator UI |
