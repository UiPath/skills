<!--skill-flavor:publish-feed-discovery:start-->
### Choosing the publish destination in Studio Web

Do not use `uip solution feeds list` to pick a publish destination here, and do
not pass `publish --feed`. Studio Web intercepts `solution publish` before it
reaches the CLI: the intercepted command takes `--location`, gets its
destination list from the host rather than from the feed API, and rejects
unknown flags without publishing. `--feed` therefore never applies to a publish
in Studio Web, whatever the CLI's own surface offers.

The destination list comes from the command itself — run `uip solution publish`
with no destination flag and it prints every destination it accepts, with the
exact flag for each, without publishing anything:

```bash
uip solution publish                              # lists destinations, publishes nothing
uip solution publish --personal-workspace         # your own workspace
uip solution publish --location "<key or name>"   # the shared/tenant location
```

Two destinations are offered — your personal workspace and the tenant location
— because the host hands the chat surface the v1 publish-location list.
Orchestrator folder feeds exist but are not on that list, so a folder feed
cannot be targeted from chat even when the CLI elsewhere accepts `--feed`.

The tenant location's display name is whatever the host returns for it (often
`Orchestrator Tenant`, not the word "Shared" that the Publish dialog shows), so
match it against the printed list rather than guessing. `--location` accepts the
key or the name; an unmatched value fails and lists the valid ones.

`uip solution feeds list` itself is a CLI command gated to preview builds, so
whether it answers at all depends on which CLI build the host embeds. It
describes Orchestrator feeds, not the host's publish destinations — so a
non-answer from it says nothing about where you can publish. Use the bare
`publish` listing above instead.
<!--skill-flavor:publish-feed-discovery:end-->

<!--skill-flavor:publish-feed-scope-row:start-->
| `uip solution publish --location` | Which destination the package is published to. Studio Web intercepts publish, so `--feed` does not apply to it |
<!--skill-flavor:publish-feed-scope-row:end-->

<!--skill-flavor:upload-tabs:start-->
`upload` always lands the solution in Studio Web's **Cloud workspace** tab, not the Local tab. SW's Local tab is a separate registration for solutions whose source of truth is a tracked local folder — populated by SW-initiated flows (creating a solution from the SW UI, or downloading a cloud solution to local) or by Studio Desktop signing into the same tenant. `uip solution upload` does not address the Local tab. A locally authored solution pushed with `upload` becomes a Cloud-tab solution; the local folder on disk has no live link to either tab afterward — edits in one place do not propagate to the other without a re-upload (Cloud) or a download (Local).
<!--skill-flavor:upload-tabs:end-->
