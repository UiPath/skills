<!--skill-flavor:unknown-rules-command:start-->
| `error: unknown command 'rules'` | The host bundles the CLI, and this one has no `uip rules`. Show the user the error and stop. |
<!--skill-flavor:unknown-rules-command:end-->
<!--skill-flavor:deployed-rules-login:start-->
| `The Business Rules service did not accept this login (401).` | Studio Web owns the sign-in. Show the user the error and stop. |
<!--skill-flavor:deployed-rules-login:end-->
<!--skill-flavor:rule-not-found:start-->
| `Business rule '<NAME>' was not found in folder '<FOLDER_PATH>'.` | Run `uip rules list --folder-path "<FOLDER_PATH>"` to see the rules in that folder. |
<!--skill-flavor:rule-not-found:end-->
