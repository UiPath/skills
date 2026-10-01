# Package Doc Errata — TEMPORARY

Delete a package's section once the installed package's own docs carry the corrected text, and this file once no section is left. A package's corrected docs reach a build only with that package's next release; until then the build reads the shipped text.

The owning skill's contract reads the installed package's per-activity doc for every activity kind a build uses ([execution-guide.md § 2.2](execution-guide.md)). **Precedence.** While the installed doc still says what a row's second column quotes, the row wins, because it was checked against the activity's source and a validate or build. Once the doc carries the corrected text, the doc wins and the row is obsolete. Check the installed doc every run: the version a project pins decides which text it ships.

## `UiPath.System.Activities` — docs shipped with 26.8.2 and earlier

| Activity | Installed doc says | The activity does |
|---|---|---|
| Append Line | a newline is added after the existing content; `UseDefaultEncoding` `true` ignores `Encoding` | Writes a line break (`Environment.NewLine`) **before** the text whenever the file is not empty, never after it: two appends to a new file give `a`, a line break, `b`, with no trailing break. A file counts as empty at 0 bytes, or when its size equals the resolved encoding's byte-order mark (3 bytes UTF-8, 2 UTF-16). Creating the file, or appending to an empty one, writes the byte-order mark. A set `Encoding` always wins; `UseDefaultEncoding` applies only when `Encoding` is empty, and then writes UTF-8 without a byte-order mark |
| Copy Folder (`CopyFolderX`) | `To` is the destination path of the copy (`To="C:\archive\reports"`) | `To` is an existing folder the source folder is copied **into**: the copy is `<To>\<source folder name>`. Both folders must exist (`Source or destination folder missing.`), and `To` may be neither the parent of `From` nor a folder inside it |
| Delete File (`DeleteFileX`) | a missing file raises nothing | A missing file fails (`The file was not found at the provided path.`): check with Path Exists first when the file may be absent. `FileResource` (`IResource`) is the overload used when `Path` is empty |
| For Each (`ForEach`) | `Values` is an optional `IEnumerable<T>`; the example binds `scg:IEnumerable(x:String)` | `Values` is required and non-generic: `<InArgument x:TypeArguments="sc:IEnumerable">` with `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"`. `T` is the activity's `x:TypeArguments` and types the iterator variable; a generic type on `Values` fails to load. An optional `Condition` (`Activity<bool>`, no `<InArgument>` wrapper) exists and is undocumented |
| Kill Process | `AppliesTo` members `All`, `User`, `Session`, `Desktop` | Members are `All`, `OnlyCurrentUser`, `OnlyCurrentSession`, `OnlyCurrentDesktop`; any other value (`Session`) fails to load the workflow |
| While (`InterruptibleWhile`) | `Condition` is an optional `InArgument<bool>`; the example wraps it in `<InArgument>` | `Condition` is a required `Activity<bool>`: the expression goes directly inside `<ui:InterruptibleWhile.Condition>`. An `<InArgument>` wrapper fails to load, and a missing condition fails validation |
| Do While (`InterruptibleDoWhile`) | no `Condition` row | As While, inside `<ui:InterruptibleDoWhile.Condition>` |
