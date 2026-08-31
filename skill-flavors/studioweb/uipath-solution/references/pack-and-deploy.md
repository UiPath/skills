<!--skill-flavor:publish-feed-discovery:start-->
### Choosing the publish destination in Studio Web

The feed-listing command is absent from the browser bundle, and so is
`publish --feed`. Studio Web intercepts publish and takes `--location`, and the
destination list comes from the command itself: run `uip solution publish` with
no destination flag and it prints every destination it accepts, with the exact
flag for each, without publishing anything.

Two destinations are offered here — your personal workspace and the tenant
location — because the chat bridge receives the v1 publish-location list.
Orchestrator folder feeds exist but are not offered, so a folder feed cannot be
targeted from chat.

```bash
uip solution publish                              # lists destinations, publishes nothing
uip solution publish --personal-workspace         # your own workspace
uip solution publish --location "<key or name>"   # the shared/tenant location
```

The tenant location's display name is whatever the host returns for it (often
`Orchestrator Tenant`, not the word "Shared" that the Publish dialog shows), so
match it against the printed list rather than guessing. `--location` accepts the
key or the name; an unmatched value fails and lists the valid ones.
<!--skill-flavor:publish-feed-discovery:end-->
<!--skill-flavor:publish-feed-scope-row:start-->
| `uip solution publish --location` | Which destination the package is published to (`--feed` is not available in Studio Web) |
<!--skill-flavor:publish-feed-scope-row:end-->
