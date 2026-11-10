<!--skill-flavor:host-availability-extra:start-->
> **In Studio Web.** Every step runs here through `uip`, with three differences. The host signs you in, so skip each `uip login` command (Rule 7 and step 0 included) and Rule 2's `uip update`: the host's CLI is the one you have. There is no shell, so skip the `curl`, `jq`, `node`, `zip` and `tar` lines, Rule 12, `scripts/run-probes.sh` and the offline hook harness; steps 1, 6, 7, 9 and 10 say what to do instead. And make no REST call of your own: what the terminal does with `curl`, this host does with the `uip` commands those steps name.
<!--skill-flavor:host-availability-extra:end-->

<!--skill-flavor:draft-intro:start-->
The unpublished draft is tested with `uip` too: the user adds its test connection in the Connector Builder, and `uip is resources run create` calls the connector through it at the path the gateway calls. The draft stays unpublished until those calls pass; the product's probes run once, on the published connector's runtime connection, when the configuration is saved.
<!--skill-flavor:draft-intro:end-->

<!--skill-flavor:probe-list:start-->
List what will run by the rules in [references/probes-guide.md](references/probes-guide.md) §"Which files run" (`<SKILL_DIR>` is the folder holding this SKILL.md): read every file in `<SKILL_DIR>/assets/probes/default/` and in `<SKILL_DIR>/assets/probes/<PRODUCT>/`, plus the one `<PROBE_ID>.json` each named probe is, in any folder. Keep a file whose `apiFlavor` is the flavor and whose `match` and `excludeFeatures` fit the feature and the catalog model, drop an `"optIn": true` file no one named, then drop every file a kept file's `replaces` names. Each kept file holds the request body and what the answer must show.
<!--skill-flavor:probe-list:end-->

<!--skill-flavor:draft-test-connection:start-->
This host cannot open the Connector Builder's test connection itself, so ask the user to add it: in Integration Service, open the draft connector (`<CONNECTOR_NAME>`) in the Connector Builder, choose **Add connection**, enter the vendor credentials (a sandbox key is fine), connect, and give you the connection's id. Never ask for the credentials themselves. That connection belongs to the draft and runs whatever was last imported — a fix is one `import` away — and `uip is connections list` does not show it, so its id comes from the user.

If the user cannot find the id, test on the published connector instead: publish (step 8), have them create the runtime connection (step 9), take its `Id` from `uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json`, and run step 7 on it with `<PUBLISHED_KEY>` in place of the draft's key. Each fix then needs a higher `latestVersion`, `import` and `publish --wait` before that connection runs it (Rule 9).
<!--skill-flavor:draft-test-connection:end-->

<!--skill-flavor:draft-calls:start-->
Send each probe file step 1 kept to the test connection, the way the gateway sends it when the configuration is saved:

```bash
uip is resources run create <CONNECTOR_KEY> '<PROBE_PATH>' --connection-id <TEST_CONNECTION_ID> \
  --body '<PROBE_BODY_JSON>' --output json
```

`<CONNECTOR_KEY>` is the draft's key (`Data.Key` from `import`). `<PROBE_PATH>` is the file's `path` without its leading `/`, and `<PROBE_BODY_JSON>` its `body` on one line, with every `{{model}}` in either replaced by the vendor's model id. Ignore the warning that the operation's metadata cannot be resolved: the command then calls that path with the JSON body, which is what the gateway does.

- A `Success` answer carries the vendor's answer, through your hooks, in `Data`. Check it against the file's `checks` in order: each `says` what must hold and its `jq` is the exact test. The first that fails is the gateway's verdict, `INCOMPATIBLE` with that `reason`; none failing is a pass.
- A `Failure` answer is `UNAVAILABLE`: `Message` holds the status (`404 Not Found`), and `Instructions` holds Integration Service's envelope, with the vendor's reason in `providerMessage`. When the status and that text match one of the file's `retries`, apply its `edit` to the body and send it once more, as the gateway does.

The command cannot ask for an event stream, so a streamed call cannot be tested here: if the product streams, tell the user it was not tested.
<!--skill-flavor:draft-calls:end-->

<!--skill-flavor:runtime-connection:start-->
The test connection usually holds the builder's own or a sandbox key. Ask the user which credentials production uses, then have them create the runtime connection from Integration Service in the web UI, on the published connector (`<PUBLISHED_KEY>`), in the shared folder the product will use. `uip is connections create <PUBLISHED_KEY>` opens the same connection page but cannot pick a folder: the connection lands in their Personal workspace, where the gateway can use it but only they can see, edit or rotate it. Find its id:
<!--skill-flavor:runtime-connection:end-->

<!--skill-flavor:config-link-values:start-->
`TenantId` is `Data.TenantId` from `byo-connections get`. `BaseUrl` and `Organization` are the address and organization this Studio Web session runs in (`https://cloud.uipath.com` and the organization's name in its URL, for example); ask the user when you cannot tell them.
<!--skill-flavor:config-link-values:end-->
