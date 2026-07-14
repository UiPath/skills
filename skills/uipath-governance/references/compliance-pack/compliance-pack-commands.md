# uip gov compliance-pack — CLI Command Reference

Single source of truth for every `uip gov compliance-pack` subcommand. All commands require **tenant-scoped login**: `uip login --tenant <TENANT_NAME>`.

Two types of packs:
- **Prebuilt** — UiPath-shipped bundles (ISO 42001, HIPAA, SOC 2, ISO 27001). Use `enable`/`disable`.
- **Custom** — generated from a compliance PDF via the three-step authoring flow. Use `analyze → review → bundle`, then `enable`/`disable`/`delete`.

---

## uip gov compliance-pack list

List all available packs for the tenant (prebuilt and custom), with their current activation status.

```bash
uip gov compliance-pack list --output json
```

**Output:**

```json
{
  "prebuilt": [
    { "packId": "uipath-iso42001", "name": "ISO 42001", "version": "1.0", "active": true }
  ],
  "custom": [
    { "packId": "3f2504e0-...", "name": "My Compliance Pack", "version": "1.0", "active": false, "createdAt": "..." }
  ]
}
```

Present to the user as a plain-English table — do not show raw JSON or UUIDs as the main output.

**Prebuilt pack ID lookup:**

| User says | packId |
|---|---|
| "ISO 42001" / "ISO/IEC 42001" / "AI Management System" | `uipath-iso42001` |
| Unrecognised standard | Run `list`, present options, ask user to choose |

---

## uip gov compliance-pack enable

Enable a pack for the current tenant. First-time enable creates the underlying policies in AOps and activates Rego runtime assignments. Idempotent — safe to call again if partially applied.

```bash
uip gov compliance-pack enable <PACK_ID> --output json
```

**Output:** Confirmation with `packId` and `active: true`.

---

## uip gov compliance-pack disable

Remove the tenant binding for a pack. Policies remain in AOps for other tenants. Idempotent.

```bash
uip gov compliance-pack disable <PACK_ID> --output json
```

Running agents are not interrupted mid-run. Change takes effect at the next run boundary.

---

## uip gov compliance-pack delete

Hard-delete a **custom** compliance pack. Only applies to custom packs — use `disable` to deactivate prebuilt packs.

```bash
uip gov compliance-pack delete <PACK_ID> --output json
```

**Destructive — cannot be undone.** Always confirm the pack name and active status with `list` before deleting.

---

## Debug

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or missing | Run `uip login --tenant <TENANT_NAME>` and retry |
| `403 Forbidden` | User-scoped login | Run `uip login --tenant <TENANT_NAME>` |
| `pack not found` | Invalid `packId` | Run `list` to confirm available pack IDs |
| `cannot delete prebuilt pack` | Tried to `delete` a UiPath-shipped pack | Use `disable` instead |
