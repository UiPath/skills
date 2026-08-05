<!-- skill-flavor:shipping-lifecycle:start -->
## Publish from Studio Web

The solution and Flow are already hosted by Studio Web. Do not refresh a filesystem-backed solution, upload it, or build a local package.

1. Confirm the user wants to publish and whether they specified a location or version.
2. Inspect the live browser-bundle publish surface. Use `uip solution publish` when advertised, supplying only supported options such as version, location, description, or release notes.
3. Do not pass a `.zip`, `.nupkg`, project directory, or `.uipx` path. Studio Web supplies the active solution and project identity.
4. Report that acceptance is asynchronous and direct the user to Studio Web Publish history for packaging/upload completion.

Publishing to a personal workspace may auto-deploy. Other Orchestrator deployment or activation work requires an advertised host capability, the Studio Web/Orchestrator UI, or an external local environment. Never substitute `uip solution deploy` in the browser.

## Anti-patterns

- Do not call `uip solution upload`; the solution is already open in Studio Web.
- Do not run Flow pack; Studio Web publishing packages the project.
- Do not claim publication completed merely because the request was accepted.
<!-- skill-flavor:shipping-lifecycle:end -->
