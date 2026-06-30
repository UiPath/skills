---
confidence: high
---

# PDF — Encrypted PDF or wrong password

## Context

A PDF activity faults because the input PDF is password-protected and no password (or the wrong password) was supplied, or because `Manage PDF Password` was given an invalid password combination. The file was found; the problem is the encryption / password arguments.

What this looks like:

- `A password for the encrypted PDF file was not supplied` (`System.ArgumentException`) — the PDF is user-password-encrypted and the activity's `Password` argument is empty. Activity-level check, before the reader opens it.
- A `UiPath.PDF.PdfException` whose inner exception is a `PdfIncorrectPasswordException` — a password **was** supplied but is wrong for this file (the reader re-throws the incorrect-password error as `PdfException` with the same message).
- `The input PDF file is not encrypted with a user password, yet a password was supplied` (`System.ArgumentException`) — a `Password` was set on a non-encrypted PDF.

`Manage PDF Password` argument errors:
- `At least one password field value is required` — neither a new user nor a new owner password was provided.
- `The supplied password does not grant the permissions (owner rights) to change the password.` — the old password lacks owner rights to change the encryption.
- `The user and owner passwords must not coincide!` — the new user and owner passwords are identical.

What can cause it:
- **Encrypted PDF, no password** — the document requires a user password and `Password` is empty.
- **Wrong password** — the supplied `Password` doesn't match the document's user password.
- **Password set on an unencrypted file** — `Password` was supplied for a PDF that has no user password.
- **Manage-password misconfiguration** — missing new password, insufficient owner rights, or identical user/owner passwords.

What to look for:
- `A password for the encrypted PDF file was not supplied` = no password set; a `PdfException`/`PdfIncorrectPasswordException` = wrong password set. These have different fixes — distinguish them.

> **Different cause — do not apply this playbook:**
> - `Could not find file` / `does not have a .PDF extension` (`ArgumentException`) means the input path is wrong, before any encryption check → use [pdf-file-not-found-or-not-pdf.md](./pdf-file-not-found-or-not-pdf.md).
> - A `PdfException` with `Invalid input stream` (no inner `PdfIncorrectPasswordException`) means the file is corrupt/not a real PDF → use [pdf-corrupt-or-image-input.md](./pdf-corrupt-or-image-input.md).

## Investigation

1. **Read the message / exception type.** `A password for the encrypted PDF file was not supplied` (no password) vs `PdfException` with inner `PdfIncorrectPasswordException` (wrong password) vs `The input PDF file is not encrypted...yet a password was supplied` (password on plain PDF).
2. **Confirm whether the file is actually encrypted** (e.g. opening it in a viewer prompts for a password). This separates "needs a password" from "password supplied on a plain file."
3. **For Manage PDF Password**, capture which field check fired (no new password / owner rights / identical passwords).

## Resolution

- **If `A password for the encrypted PDF file was not supplied`:** set the `Password` argument on the read/extract activity to the document's user password (store it as a secure asset/credential; with explicit user approval, wire it from there).
- **If a wrong-password `PdfException` / `PdfIncorrectPasswordException`:** correct the `Password` value to the right one for this document.
- **If `The input PDF file is not encrypted with a user password, yet a password was supplied`:** clear the `Password` argument for this (non-encrypted) file.
- **If `At least one password field value is required`:** provide a new user and/or owner password on `Manage PDF Password`.
- **If `The supplied password does not grant the permissions (owner rights) to change the password.`:** supply the owner password (not just the user password) so the change is authorized.
- **If `The user and owner passwords must not coincide!`:** set distinct user and owner passwords.
