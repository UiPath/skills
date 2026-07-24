# uipath-ixp discovery mock — delete-document-by-filename fixture

Overlay for [`../mock_template`](../mock_template/README.md); list it **second**
in `template_sources` so its `mocks/uip` overwrites the base fail-all mock
(base still provides `mocks/curl` and the seeded `mocks/calls.log`):

```yaml
sandbox:
  driver: tempdir
  mock_path_dirs: [mocks]
  template_sources:
    - {type: template_dir, path: ../_shared/mock_template}
    - {type: template_dir, path: ../_shared/mock_template_documents}
```

The overlaid `uip` answers the read verb with canned JSON instead of failing, so
the task prompt can name ONLY a document filename and the agent must discover the
DocumentId through the CLI:

| Verb | Canned response |
|------|-----------------|
| `ixp documents list` | three invoices with human-facing `Filename`s and opaque `DocumentId`s (`york_solutions_invoice.png` → `d41f8a90-…-…9f1a`) |
| `ixp documents delete` | `{"Result":"Success"}` — grading catches the resolved-id vs raw-filename choice via `calls.log` |
| anything else | offline auth-style failure, like the base mock |

Because the `Filename` → `DocumentId` mapping lives only in the `documents list`
response, deleting `york_solutions_invoice.png` by name REQUIRES a list lookup —
that resolution is the behavior under test (companion to
[`get_project_by_title`](../../smoke/get_project_by_title.yaml), which resolves a
project Title → Name the same way).

Same logging contract as [`mock_template_ambiguous`](../mock_template_ambiguous/README.md):
every invocation appends `$*` (NO `uip` prefix) to `mocks/calls.log`, so tasks
grade `ixp documents …` lines.
