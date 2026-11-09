<!--skill-flavor:field-reference:start-->
Studio Web has no `markdownPath` file to read. Get the operation's field reference with `uip maestro registry describe <nodeType> --output plain` rather than guessing input names.
<!--skill-flavor:field-reference:end-->

<!--skill-flavor:library-pull:start-->
In Studio Web the library of the session is always loaded: `uip maestro registry pull` has no effect.
<!--skill-flavor:library-pull:end-->

<!--skill-flavor:package-metadata-row:start-->
| package metadata | `entry-points.json`, `operate.json`, `package-descriptor.json` | the same `refresh`. Studio Web has no `uip solution resources refresh`: add each connection with `uip solution resources add` ([Validation loop](../SKILL.md#validation-loop)) |
<!--skill-flavor:package-metadata-row:end-->
