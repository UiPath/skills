# Add Comment

`UiPath.Word.Activities.DocumentAddComment` (cross-platform)
`UiPath.Word.Activities.WordAddComment` (Windows)

Adds a comment to a Word document anchored to a text match, a named bookmark, or (Windows only) a tracked change revision.

**Package:** `UiPath.Word.Activities`
**Category:** Word

## Properties

### Cross-Platform (`DocumentAddComment`)

#### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `FilePath` | File path | InArgument | `string` | Conditional | | Full path to the Word document file |
| `PathResource` | File | InArgument | `IResource` | Conditional | | A file resource reference to the Word document |
| `CommentText` | Comment | InArgument | `string` | Yes | | The text content of the comment. |

Mutually exclusive — provide exactly one of `FilePath` or `PathResource` (see Valid Configurations).

#### Options

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AnchorType` | Search by | Property | `CommentAnchorType` | No | `Text` | The type of anchor for the comment. Cross-platform supports `Text` and `Bookmark` only. |
| `AnchorText` | Text to comment | InArgument | `string` | Conditional | | The text to search for in the document. The comment will be anchored to this text. Required when anchor type is Text. |
| `Bookmark` | Bookmark | InArgument | `string` | Conditional | | The name of the bookmark to anchor the comment to. Required when anchor type is Bookmark. |
| `OccurrenceIndex` | Occurrence index | InArgument | `int?` | No | `1` | The occurrence of the anchor text to target. Default is 1 (first occurrence). |
| `Author` | Author | InArgument | `string` | No | | The author name for the comment. If not specified, uses the current system user (cross-platform). |

### Windows (`WordAddComment`)

**Required Scope:** `WordApplicationScope`

#### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `CommentText` | Comment | InArgument | `string` | Yes | | The text content of the comment. |

#### Options

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `AnchorType` | Search by | Property | `CommentAnchorType` | No | `Text` | The type of anchor for the comment. Text anchors to a text match; Bookmark anchors to a named bookmark; Revision anchors to a tracked change. |
| `AnchorText` | Text to comment | InArgument | `string` | Conditional | | The text to search for in the document. Required when anchor type is Text. |
| `AnchorRevision` | Text to search in revisions | InArgument | `string` | Conditional | | The text to search for in the document's revisions. The comment will be anchored to this text. Required when anchor type is Revision. Windows only. |
| `Bookmark` | Bookmark | InArgument | `string` | Conditional | | The name of the bookmark to anchor the comment to. Required when anchor type is Bookmark. |
| `OccurrenceIndex` | Occurrence index | InArgument | `int?` | No | `1` | The occurrence of the anchor text or revision text to target. Default is 1 (first occurrence). |
| `Author` | Author | InArgument | `string` | No | | The author name for the comment. If not specified, uses the current Word user. |

#### CommentAnchorType Enum Values

| Value | Platforms | Description |
|-------|-----------|-------------|
| `Text` | Both | Anchor the comment to a text match in the document. |
| `Bookmark` | Both | Anchor the comment to a named bookmark in the document. |
| `Revision` | Windows only | Anchor the comment to a tracked change (revision) in the document. |

## Valid Configurations

**Cross-platform document input:** Supports two input modes (mutually exclusive via OverloadGroups):

**Mode A — Local Path**: Set `FilePath` to the document path.
**Mode B — Resource**: Set `PathResource` to a file resource reference.

Only one of `FilePath` or `PathResource` should be set.

**Anchor type selection (both platforms):**

| Anchor Type | Required Property | Optional Properties | Leave Empty |
|-------------|-------------------|---------------------|-------------|
| Text (default) | `AnchorText` | `OccurrenceIndex` | `Bookmark`, `AnchorRevision` |
| Bookmark | `Bookmark` | | `AnchorText`, `OccurrenceIndex`, `AnchorRevision` |
| Revision (Windows only) | `AnchorRevision` | `OccurrenceIndex` | `AnchorText`, `Bookmark` |

## XAML Example

**Cross-platform — anchor to text:**

```xml
<ui:DocumentAddComment
    DisplayName="Add Comment"
    FilePath="[documentPath]"
    AnchorType="Text"
    AnchorText="[textToComment]"
    OccurrenceIndex="1"
    CommentText="[commentText]"
    Author="[authorName]" />
```

**Cross-platform — anchor to bookmark:**

```xml
<ui:DocumentAddComment
    DisplayName="Add Comment"
    FilePath="[documentPath]"
    AnchorType="Bookmark"
    Bookmark="[bookmarkName]"
    CommentText="[commentText]" />
```

**Windows — anchor to text (inside Word Application Scope):**

```xml
<ui:WordAddComment
    DisplayName="Add Comment"
    AnchorType="Text"
    AnchorText="[textToComment]"
    OccurrenceIndex="1"
    CommentText="[commentText]"
    Author="[authorName]" />
```

**Windows — anchor to bookmark:**

```xml
<ui:WordAddComment
    DisplayName="Add Comment"
    AnchorType="Bookmark"
    Bookmark="[bookmarkName]"
    CommentText="[commentText]" />
```

**Windows — anchor to a tracked change revision:**

```xml
<ui:WordAddComment
    DisplayName="Add Comment"
    AnchorType="Revision"
    AnchorRevision="[revisedText]"
    OccurrenceIndex="1"
    CommentText="[commentText]"
    Author="[authorName]" />
```

## Notes

- **Windows — Revision anchor:** Uses the separate `AnchorRevision` property (not `AnchorText`) to search within tracked changes. Matches revision text via case-sensitive substring search.
- **Cross-platform:** Supports `Text` and `Bookmark` anchor types only. Setting `AnchorType` to `Revision` throws an exception.
- `OccurrenceIndex` is 1-based. Defaults to 1 (first occurrence). Values less than 1 throw an exception.
- `Author` defaults to the current Word user on Windows, or the current system user (`Environment.UserName`) on cross-platform.
- Must be placed inside a **Word Application Scope** when using the Windows variant.
- The cross-platform variant works on both Windows and Linux robots without requiring Microsoft Word to be installed.
