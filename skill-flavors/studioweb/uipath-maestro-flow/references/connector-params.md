<!--skill-flavor:check-source:start-->
3. **Check**: `uip maestro flow check .flow-sdk/new.flow.ts --source` (a new flow). It names each
<!--skill-flavor:check-source:end-->

<!--skill-flavor:not-in-library-pull:start-->
     If the session has a library and the operation is newer than it, tell the user: Studio Web cannot refresh the library of the session.
     With no session library (Automation Suite), `check` and `compile` have already asked the tenant through `uip`, and the message's last sentence says what it answered: "does not serve it" means the name is wrong or the connector is not on this tenant; for any other reason, report it to the user and stop.
<!--skill-flavor:not-in-library-pull:end-->

<!--skill-flavor:library-discovery:start-->
In Studio Web on cloud the connector library comes with the session.
There is no local cache and no library path: `uip maestro registry pull` writes nothing here, and `registry path` is not available.
With no session library (Automation Suite), `check` and `compile` fetch a missing operation through `uip`, so re-run `check`, and `registry search` searches the tenant's live catalog.
Read the library with three verbs, run from the project folder:

```bash
uip maestro registry search '<words>' --output json              # the operation and its node type
uip maestro registry describe <node-type> --output plain         # one operation's page: inputs, outputs, lookups, code
uip maestro registry prepare <connector-key> --action <action>   # the live schema, into .flow-sdk/connectors-local/
```
<!--skill-flavor:library-discovery:end-->

<!--skill-flavor:library-search:start-->
Search that library for static contracts with `uip maestro registry search`,
then read the page of a hit with
`uip maestro registry describe <node-type> --output plain`.
<!--skill-flavor:library-search:end-->

<!--skill-flavor:descriptor-imports:start-->
Import a prepared descriptor with its real `.ts` extension — a `.js` specifier
does not resolve, because these are sources rather than compiled output. The
path is relative to the source in `.flow-sdk/`. Studio Web writes no
`./connectors/` tree, so import only from `./connectors-local/`:

```ts
import { CreateInvoiceShare } from './connectors-local/uipath-salesforce-sfdc.ts';
```
<!--skill-flavor:descriptor-imports:end-->

<!--skill-flavor:connection-user:start-->
**When the task names nobody for a person-shaped required field** (`reporter`,
`requester`, `owner`), the value is the connection's own user. Ask the user for
the display name of that account, and resolve by **display name**. Search only
by the names the field's "matches on" list declares — do not improvise queries
against raw collections. Jira in particular hides e-mail addresses from user
search, so an `emailAddress=` query returns nothing for a user that plainly
exists, while `displayName=` finds them; the field's spec (`matches on
displayName | accountId`) already told you e-mail was not searchable.
<!--skill-flavor:connection-user:end-->

<!--skill-flavor:output-names:start-->
Output field names are case-sensitive and `check` does not verify them:
`out('upload', 'WebUrl')` compiles and reads `null` at run time when the field is
`webUrl`. Copy each name from the operation's `## Outputs`, which
`uip maestro registry describe <node-type>` prints.
<!--skill-flavor:output-names:end-->
