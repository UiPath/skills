# uipath-ixp runtime-extraction mock — `extract_runtime` fixture

Overlay for [`../mock_template`](../mock_template/README.md); list it **second**
in `template_sources` so its `mocks/uip` overwrites the base fail-all mock
(base still provides `mocks/curl` and the seeded `mocks/calls.log`):

```yaml
sandbox:
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/extraction_mock_template}
```

## Why it exists

Runtime extraction is an **async two-step flow**: `extraction start` returns an
`operationId`, then `extraction get-result <project-id> <operation-id>` fetches
the fields. The base mock fails every command, so `start` returns no id and step
two is unreachable — a correct agent has nothing to pass to `get-result`. This
overlay answers the three verbs of that flow with canned JSON so the flow is
actually executable and gradable.

| Verb | Canned response |
|------|-----------------|
| `ixp projects list` | paged envelope with `my_invoices-f1afa9ef-ixp` (Id `3f2a7c58-…`) + one decoy project — the agent must pick the Id |
| `ixp extraction start` | `Data: { operationId: "d94e1b70-…" }` |
| `ixp extraction get-result` | terminal **finished** shape — `Data` is the field-group array, values matching `invoice.png` |
| anything else | offline auth-style failure, like the base mock |

`get-result` is terminal on the **first** call: no state file, no timing flake.
A `Running` → `Succeeded` sequence would exercise the poll loop but buys little
signal for the flake it adds.

`invoice.png` (root, copied from [`../fixtures`](../fixtures)) is the document
the prompt names, so the agent is not extracting from a file that does not
exist. `.png` is on the [supported-extension
whitelist](../../../../skills/uipath-ixp/references/cli-reference.md#supported-document-files).

## Logging contract — do not diverge

`mocks/uip` appends one line per invocation to `mocks/calls.log` in the **base
mock's exact format**: `uip ` prefix, embedded newlines squashed to spaces.
`extract_runtime.yaml` grades with **anchored** regexes (`(?m)^uip\s+ixp\s+…`),
so dropping the prefix silently fails every criterion. (The sibling
[`mock_template_ambiguous`](../mock_template_ambiguous/README.md) logs bare
`$*`; its task grades by substring, so do not copy that line from it.)

Response shapes follow the skill's [CLI
reference](../../../../skills/uipath-ixp/references/cli-reference.md#runtime-extraction)
— note `projects list` returns the paged envelope `Data: { Projects[], Total,
Offset, Limit }`, not a bare array.
