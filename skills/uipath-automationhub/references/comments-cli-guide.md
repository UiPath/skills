# Read and Post Comments on an Automation — `uip ah` CLI flow

Reads the discussion on an automation — an idea or a Business Process — and posts a comment or a reply to it: the CLI equivalent of the **Comments** section on the automation's profile page.

> **Use this flow only after the preflight in [`cli-commands.md`](cli-commands.md) passed.** All commands: append `--output json`. The endpoint contract (paging, text rules, who the author is, errors) is in [`api-endpoints.md`](api-endpoints.md) → the `/automations/{id}/comments` sections.

## When to use

- The user asks what people said about an automation, or where its discussion stands.
- The user asks to **comment** on an automation, **reply** to a comment, or record something on it (e.g. "note on the idea that the PDD was published").

Editing, deleting or reacting to a comment is **out of scope** — the Open API has no endpoints for it. Tell the user to do it on the automation's profile page; never post a "correction" comment instead of an edit unless they ask for one.

## Step 1: Check the CLI and resolve the automation

```bash
uip ah comments --help    # unknown command → the installed uip is too old; see Not available yet
```

Named by the user? Resolve the id with `uip ah automations list --search <name> --output json`, and confirm with the user when more than one automation matches. Comments work the same on ideas and Business Processes — no flow-specific handling.

## Step 2: Read the thread

```bash
uip ah comments list <automation-id> --output json
```

`Data` holds the **top-level** comments, newest first. Each has `Id`, `Text`, `AuthorEmail`, `CreatedEpoch` (epoch ms), `ReplyCount` and `Replies` (each `{ Id, Text, AuthorEmail, CreatedEpoch }` — their order isn't guaranteed, so sort by `CreatedEpoch` when it matters). `--limit` / `--offset` count top-level comments, and the default limit is 20: read `Pagination.HasMore` and pass a larger `--limit` (or `--offset`) before saying "no one mentioned X". `--all-fields` adds the stored rich text (`TextDraftjs`) and the full author record.

When summarizing, attribute each point to its author, and say which comments are replies.

## Step 3: Post a comment or a reply (a write — confirm first)

Posting notifies the automation's followers, the same as a comment typed in Automation Hub. So **show the user the exact text and get a confirmation before posting**, unless they dictated it word for word.

```bash
uip ah comments create <automation-id> --text "<text>" --output json
uip ah comments create <automation-id> --text "<text>" --reply-to <comment-id> --output json
```

- **Text** is plain text, up to 2000 characters. Line breaks are kept; Markdown is **not** rendered (it shows literally), and there are no @-mentions. Blank text is refused.
- **`--reply-to`** takes the `Id` of a **top-level** comment from Step 2. Replies are one level deep: to answer a reply, reply to its top-level parent (the comment whose `Replies` holds it). A reply to a reply fails with 400.
- **`--submitter <email>`** is only for a token with **no associated user**, and names the AH user who becomes the author. With a normal signed-in or Delegate token, the author is always the caller and the flag is ignored, so leave it out.

## Step 4: Verify

A success returns `Code: AhCommentsCreate` with `Data: { Id, ParentId, Text, AuthorEmail, CreatedEpoch }`. Report the comment's `Id`, and for a reply its `ParentId`.

**Never re-post on a timeout or 5xx.** The comment may have landed, and a second post notifies followers twice. Run `uip ah comments list <automation-id>` first, and post again only if the text isn't there.

## Errors

| Response | Meaning | What to do |
|---|---|---|
| `ValidationError` (exit 3) | Blank text, text over 2000 characters, or a non-numeric `--reply-to` — caught before sending | Fix the input |
| 400 `Parent comment not found, or it is not a top-level comment…` | `--reply-to` is a reply, or belongs to another automation | Re-read the thread; reply to the top-level parent |
| 403 | The caller can't view this automation | Say so; don't retry |
| 404 `The process with given id/slug was not found` | Unknown automation id | Re-resolve the id (Step 1) |
| 404 `Route Not found.` | This Automation Hub predates the comments endpoints | See [Not available yet](#not-available-yet) |

## Not available yet

- **`uip ah comments` is an unknown command** → the installed `uip` is older than the comments commands. Tell the user to update `uip` and stop. Don't fall back to raw API calls or the UI.
- **The server answers `404 Route Not found.`** → this tenant's Automation Hub doesn't have the comments endpoints yet (UiPath/Automation-Hub#13165, #13166). Say so and stop.
