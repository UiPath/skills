<!--skill-flavor:df-tool-install:start-->
1. **The tool comes with the host.** In Studio Web the host bundles the CLI and its tools, so there is nothing to install. If `uip df` returns `unknown command 'df'`, report the error to the user and stop.
<!--skill-flavor:df-tool-install:end-->
<!--skill-flavor:df-cli-install-rows:start-->
| `unknown command 'df'` | The host's CLI has no Data Fabric tool | Report the error to the user and stop |
<!--skill-flavor:df-cli-install-rows:end-->
<!--skill-flavor:df-outdated-tool-row:start-->
| `unknown option '--folder-key'` / `unknown option '--include-folders'` | The host's tool is older than the option | Report the error to the user and stop: the host's CLI does not have that option |
<!--skill-flavor:df-outdated-tool-row:end-->
