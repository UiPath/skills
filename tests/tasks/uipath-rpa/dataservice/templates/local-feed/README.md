# Local NuGet feed (test fixture)

This template ships a `NuGet.Config` that declares `./local-feed/` as a NuGet
source. At test time, `template_sources` copies both into the sandbox tempdir
so the agent's `uip rpa init` + restore inherits the local feed via NuGet's
parent-directory config walk.

## What's gitignored

The `.nupkg` files under `local-feed/` are gitignored (see `/.gitignore`:
`**/**.nupkg`). Each runner needs to place the package(s) on disk locally
before running the tests:

```
templates/local-feed/local-feed/UiPath.DataService.Activities.23.1.4-dev.nupkg
```

Source: the dev build output of the `Entities-Desktop` repo.

## Why not ship the .nupkg

Approach is exploratory; this template will not be merged in its current
shape. Long-term plan is to publish the package to an internal UiPath NuGet
feed and drop the local-feed fixture entirely.
