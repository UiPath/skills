# File Attachments

CLI syntax, flags, response shapes, and default paths: [Data Fabric CLI docs → `files`](https://github.com/UiPath/cli/blob/main/docs/tools/data-fabric.md#files--file-field-attachments).

## Agent behavior

1. **Never write a FILE column through `records insert` / `records update` / `records import`.** CLI rejects it from `1.199.0+`; on older tools the server silently strips the value and returns Success (Rule 6). Write path: `records insert` without the FILE column → capture `Data.Id` → `files upload <entity-id> <record-id> <field-name> --file <path>`.
2. **`files upload` both attaches and replaces** — no `files delete` first. Use `files delete` to clear the field.
3. **`files delete` is destructive** — irreversible per record/field. Gate with the Destructive Operations block (`--yes` + `--reason`); ask before invoking.
4. **Reading FILE fields**: shape depends on `expansionLevel`. `records get` / `records list` are always `0` (bare UUID). `records query` accepts `expansionLevel` in `--body` — pass `1` to get `{ Id, Name, Size, Type, UpdateTime, ... }`. Full read-shape rules: [`records-query.md` → FILE fields](records-query.md#file-fields--never-write-through-insertupdate).
5. **Do not use the FILE UUID handle to detect content change.** The handle is stable across `files upload` — the bytes change, the UUID does not. Compare bytes or watch `UpdateTime` in the level-`1` shape.
