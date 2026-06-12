Resolve the `uip` binary — npm global installs may not be on PATH (e.g. nvm environments):

```bash
UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
$UIP --version
```

Use `$UIP` in place of `uip` for all subsequent commands if the plain `uip` command isn't found.

If `uip` is not installed:

```bash
npm install -g --@uipath:registry=https://registry.npmjs.org/ @uipath/cli@latest
```

The `--@uipath:registry` flag pins the `@uipath` scope to public npm — guards against corporate default-registry mirrors that don't host `@uipath`. If `npm install -g` fails with a permission error, prompt the user to re-run with appropriate privileges (e.g., `sudo`) — do not retry automatically.
