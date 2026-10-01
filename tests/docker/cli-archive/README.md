# cli-archive

Build-context slot for a UiPath/cli air-gapped archive. `run-coder-eval.yml`
downloads the `uipath-cli-airgap-*-linux` artifact of the `export-airgapped.yml`
run named by `cli_archive_run_id` into this directory, and the image built with
`--build-arg CLI_SOURCE=archive` installs `@uipath/cli`, every tool and
`@uipath/skills` from it offline (`install.js`). Empty except for this file and
`.gitignore` in the repository; the Dockerfile's `COPY` needs the directory to
exist either way.
