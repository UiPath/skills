# Get Asset Failure — External Credential Store Failure

This scenario reproduces a runtime `Get Credential` failure caused by
an **external credential store** (CyberArk, Azure Key Vault, Thycotic,
or other vault) being unreachable or misconfigured. The asset itself
is correctly defined in Orchestrator — its value just lives in a
remote vault that Orchestrator can't reach. Orchestrator returns
**error code 2304** / "Failed to read from Credential Store type
'CyberArk'".

## What this scenario uncovers

**Root Cause:** The `Get Credential` activity targets a Credential
asset (`MyCyberArkSecret`) whose value is stored in an external
CyberArk vault. The asset's `CredentialStoreId` points at a non-default
store named "Production CyberArk Store" of type `CyberArk`. The vault
endpoint is currently unreachable from Orchestrator (network issue,
endpoint moved, or configuration drift on the Orchestrator side).
Orchestrator therefore rejects the read with error code 2304.

This maps to:
`references/activity-packages/system-activities/playbooks/get-asset-external-vault-failure.md`
(medium-confidence playbook).

> **Why "medium-confidence":** error codes 2303 / 2304 are unique to
> external-vault failures but the underlying cause has many
> sub-branches per the playbook — network unreachable, CyberArk FIPS
> mode mismatch, Azure Key Vault IP not whitelisted, Thycotic
> integration URL wrong, plugin configuration incomplete. The agent
> must identify the vault type from the error message and recommend
> the right diagnosis path.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | synthesized UiPath project — Get Credential activity correctly configured at every workflow layer |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the documented playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

The decisive evidence:

1. The error log: `Failed to read from Credential Store type 'CyberArk'. Error code: 2304`.
2. The asset list shows `MyCyberArkSecret` with a non-null `CredentialStoreId` and `ExternalName` — proof the asset's value is stored externally.
3. The credential-stores list (`uip orch credential-stores list`) returns "Production CyberArk Store" with `Type: "CyberArk"` matching the asset's binding.

## How this differs from sibling scenarios

| Dimension | `name-mismatch` | `folder-scope-mismatch` | `permission-denied` | `wrong-activity-type` | `per-robot-no-value` | `robot-not-authenticated` | `external-vault-failure` (this) |
|---|---|---|---|---|---|---|---|
| Asset present? | no (typo) | n/a | yes | yes (wrong type) | yes | yes | yes |
| Folder present? | yes | no | yes | yes | yes | yes | yes |
| Permissions correct? | n/a | n/a | no | n/a | n/a | n/a | yes |
| Robot licensed? | n/a | n/a | n/a | n/a | n/a | no | yes |
| External vault backing? | n/a | n/a | n/a | n/a | n/a | n/a | **yes — CyberArk (unreachable)** |
| Error code anchor | 1002 | 1100 | 0 (HTTP 403) | "Invalid asset type" | n/a | 0 (HTTP 401) | **2304** |
| Matched playbook | not-found | folder-scope-mismatch | permission-denied | wrong-activity-type | per-robot-no-value | robot-not-authenticated | external-vault-failure |

This scenario is the first where the failing layer is **outside
Orchestrator entirely** — it's the external vault product. The agent
must recommend connectivity / configuration checks on the vault side,
not changes to the asset, the folder, the robot, or the workflow.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Conclusion must (a) name the vault type (`CyberArk`), (b) recognize the asset is backed by an external store, and (c) recommend checking vault connectivity / configuration on the Orchestrator-to-vault path

## Regenerating from a real session

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path-to-.local/investigations> \
    --project <path-to-failing-project> \
    --transcript <path-to-session-jsonl> \
    --scenario-name getasset-external-vault-failure --apply
```
