when: using a `uip function` subcommand or flag not shown in Quick Start (serve port/runtime, pack --nolock, publish --feed-id, push, runtime-install)

## CLI Reference

Use singular `uip function`; retired plural `functions` is unavailable.

```bash
uip function new <NAME> -l py|ts|js [--empty]   # scaffold; TypeScript default; --empty only for JS/TS
uip function init                                # Python only — creates entry-points.json, project.uiproj, and empty bindings.json
uip function serve [--port 7070] [--runtime node|deno]   # JS/TS only — local HTTP server with hot reload
uip function run                                 # both languages — one-shot local execution
uip function pack [--nolock]                     # build the .nupkg
uip function publish [--feed-id <FEED_ID>]      # upload package to a process feed
uip function push --project-id <PROJECT_ID> [--ignore-resources]   # sync sources to Studio Web and import bindings.json resources
uip function runtime-install                    # JS/TS only — one-time runtime pre-install; otherwise downloaded on first serve/run
```