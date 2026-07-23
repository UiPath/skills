# uipath-ixp discovery mock — rename-ambiguity fixture

Overlay for [`../mock_template`](../mock_template/README.md); list it **second**
in `template_sources` so its `mocks/uip` overwrites the base fail-all mock
(base still provides `mocks/curl` and the seeded `mocks/calls.log`):

```yaml
sandbox:
  driver: tempdir
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_ambiguous}
```

The overlaid `uip` answers read verbs with canned JSON instead of failing, so
the task prompt can state ONLY the goal and the agent must discover the
fixture through the CLI:

| Verb | Canned response |
|------|-----------------|
| `ixp projects list` | project `subscriptions-4c1d9e2a-ixp` TITLED "subscriptions" + one decoy project |
| `ixp projects get` | the subscriptions project's metadata |
| `ixp projects get-taxonomy` | field group `subscriptions` containing field `subscriptions` (+ decoy group/field) |
| rename / delete mutations | `{"Result":"Success"}` — grading catches them via `calls.log` |
| anything else | offline auth-style failure, like the base mock |

Same logging contract as the base mock: every invocation appends `$*` to
`mocks/calls.log` — tasks grade that log and MUST keep the harness-integrity
criterion asserting the sink line is present in this script.
