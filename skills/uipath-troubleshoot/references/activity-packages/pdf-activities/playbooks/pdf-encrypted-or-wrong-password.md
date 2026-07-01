---
confidence: high
---

# PDF — Encrypted PDF or wrong password

## Context

A PDF activity faults because the input PDF is password-protected and no password (or the wrong password) was supplied, or because `Manage PDF Password` was given an invalid password combination. The file was found; the problem is the encryption / password arguments.

What this looks like:

**Read / Extract activities on an encrypted PDF** (`Read PDF Text`, `Extract PDF Page Range`, …) — the failure comes from the reader (`UiPath.PDF.PdfReader..ctor` → `ReadPDFText.GetFileReader`), so the exception type is `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException`:

- `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException: The password is incorrect.` — the PDF requires a user password and none / the wrong one was supplied (verified verbatim; a missing password reads as "incorrect"). This is the runtime fault you see in a faulted job when reading an encrypted PDF.

**`Manage PDF Password`-specific argument validation** (`System.ArgumentException`, raised by the activity before/around the reader — these strings belong to `Manage PDF Password`, NOT to the read activities):

- `A password for the encrypted PDF file was not supplied` — `Manage PDF Password` was pointed at a user-password-encrypted PDF with no current password provided.
- `The input PDF file is not encrypted with a user password, yet a password was supplied` — a password was supplied for a non-encrypted PDF.
- `At least one password field value is required` — neither a new user nor a new owner password was provided.
- `The supplied password does not grant the permissions (owner rights) to change the password.` — the old password lacks owner rights to change the encryption.
- `The user and owner passwords must not coincide!` — the new user and owner passwords are identical.

What can cause it:
- **Encrypted PDF, no password** — the document requires a user password and `Password` is empty.
- **Wrong password** — the supplied `Password` doesn't match the document's user password.
- **Password set on an unencrypted file** — `Password` was supplied for a PDF that has no user password.
- **Manage-password misconfiguration** — missing new password, insufficient owner rights, or identical user/owner passwords.

What to look for:
- For a **read/extract** activity, the encryption failure is `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException: The password is incorrect.` — set/correct the `Password` argument. The `A password for the encrypted PDF file was not supplied` string is a **Manage PDF Password** validation, not a read-activity message — don't expect it from `Read PDF Text`.

> **Different cause — do not apply this playbook:**
> - `Could not find file` / `does not have a .PDF extension` (`ArgumentException`) means the input path is wrong, before any encryption check → use [pdf-file-not-found-or-not-pdf.md](./pdf-file-not-found-or-not-pdf.md).
> - A `PdfException` with `Invalid input stream` (no inner `PdfIncorrectPasswordException`) means the file is corrupt/not a real PDF → use [pdf-corrupt-or-image-input.md](./pdf-corrupt-or-image-input.md).

## Investigation

1. **Read the message / exception type.** `UiPath.DocumentUnderstanding.Digitizer.Exceptions.PdfException: The password is incorrect.` from a read/extract activity = encrypted PDF, no/wrong `Password`. A `Manage PDF Password` `ArgumentException` (`A password for the encrypted PDF file was not supplied` / `...not encrypted...yet a password was supplied`) = a Manage-PDF-Password argument problem.
2. **Confirm whether the file is actually encrypted** (e.g. opening it in a viewer prompts for a password). This separates "needs a password" from "password supplied on a plain file."
3. **For Manage PDF Password**, capture which field check fired (no new password / owner rights / identical passwords).

## Resolution

- **If a read/extract `PdfException: The password is incorrect.` (encrypted PDF):** set the `Password` argument on the read/extract activity to the document's user password (store it as a secure asset/credential; with explicit user approval, wire it from there). If a password was already set, correct it to the right one for this document.
- **If `Manage PDF Password` → `A password for the encrypted PDF file was not supplied`:** provide the document's current user password to Manage PDF Password.
- **If `Manage PDF Password` → `The input PDF file is not encrypted with a user password, yet a password was supplied`:** clear the supplied password for this (non-encrypted) file.
- **If `At least one password field value is required`:** provide a new user and/or owner password on `Manage PDF Password`.
- **If `The supplied password does not grant the permissions (owner rights) to change the password.`:** supply the owner password (not just the user password) so the change is authorized.
- **If `The user and owner passwords must not coincide!`:** set distinct user and owner passwords.
