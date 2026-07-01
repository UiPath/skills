# Data Fabric Reserved-Name Validators

Two independent server-side validators reject reserved names. They live on different code paths and behave differently — a name legal in one place can be illegal in the other. Look up the target validator here instead of hand-checking.

## Which validator fires

| Target | Validator | Error string |
|---|---|---|
| Entity name (`entities create <name>`) | Entity/field-name validator | `cannot be a reserved word in C# or VB` / `RESERVED_LANGUAGE_KEYWORDS` |
| Field name (`fields[].fieldName` on create; `removeFields[].fieldName` on delete) | Entity/field-name validator | same as above |
| Choice-set value `Name` (`choice-set-values create --name <name>`) | Choice-value `Name` validator | `Choiceset member name must only contain alphanumeric characters, start with alphabetic characters and not be C# keyword` |

## Shared alphabet rules (both validators)

- Must start with a letter (`[a-zA-Z]`).
- Must contain only letters, digits, and underscores (`[a-zA-Z0-9_]`). No hyphens, spaces, or punctuation.
- Length 3–100 characters.

## Reserved system field names

These always error on `entities create` / `addFields`, regardless of casing: `Id`, `CreatedBy`, `CreateTime`, `UpdatedBy`, `UpdateTime`. Every entity gets them auto-created — do not redefine.

## Entity / field-name validator

| Aspect | Behavior |
|---|---|
| Case match | **Case-insensitive.** `Class`, `class`, `CLASS` all rejected. |
| Language scope | **C# and VB reserved keywords only.** SQL keywords are NOT part of this list. |
| Rejected (partial, non-exhaustive) | `Case`, `Class`, `If`, `Then`, `Else`, `New`, `Object`, `Public`, `Private`, `Return`, `Select`, `Internal`, `Static`, `Void`, `Event`, `Lock`, `String`, `Int` |
| Accepted (SQL keywords are fine) | `Status`, `Order`, `Key`, `User`, `Role`, `Type`, `Group`, `Index`, `From`, `Where`, `Table` — use these as-is; don't rename defensively |
| Canonical renames on rejection | `Case` → `WorkItem` / `Matter` · `Class` → `Category` · `New` → `IsNew` |

## Choice-value `Name` validator

| Aspect | Behavior |
|---|---|
| Case match | **Case-sensitive.** `class` rejected; `Class` may pass (empirically verified — `New` accepted while `new` rejected). |
| Language scope | **Partial C# keyword list — incomplete.** `select` slips through here even though `Select` is rejected as a field name. |
| Rejected (partial, non-exhaustive lowercase set) | `internal`, `public`, `private`, `class`, `case`, `new`, `default`, `static`, `void`, `event`, `lock`, `object`, `string`, `int` |
| Portable convention | Lowercase snake_case, namespaced: `internal_audit`, `new_lead`, `class_a`. Human label goes on `DisplayName` — dropdown shows `Internal`, validator sees `internal_audit`. |

## Do NOT assume portability

A name legal for a field is not automatically legal as a choice-value `Name`, and vice versa. `Select` passes the choice-value validator (case mismatch on its list) but fails the field-name validator. `New` passes the choice-value validator but fails the field-name one. Always look up the target validator above.

## API is authoritative

The rejection matrix here is empirical, not exhaustive. When the API rejects a name not on this list, surface the error to the user verbatim and pick a domain-specific rename — do not silently substitute (data-fabric.md Rule 18). Report additions back to this file when you find them.
