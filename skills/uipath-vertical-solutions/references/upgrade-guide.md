# Upgrade or Downgrade a Vertical Solution

An upgrade installs a newer version over an existing deployment, in the same folder. Steps 1 and 2 of the guided deploy in [SKILL.md](../SKILL.md) are the same. Then:

1. **Which deployment.** The dry run in step 3 lists each installed copy with its version and folder. When there is more than one, ask which, and pass its folder key with `--folder-key <FOLDER_KEY>`. When two copies share a folder, the CLI says so: pick one with `--deployment-name <DEPLOYMENT_NAME>` instead.
2. **Which version.** By default the CLI picks the newest version the upgrade rules allow, and the job output shows which. Ask only if the user wants a specific one (`--package-version <VERSION>`). Major versions cannot be skipped: going from 1.x to 3.x while a 2.x exists is refused, and the message names the version to deploy first. A downgrade needs `--action downgrade` and `--package-version <VERSION>`.
3. **Values.** Ask for the package's `--config` values again. The service does not keep them from the last deploy. Per-resource values (`deploy-config.json`) are kept by the deployment: pass the file again only when a new version asks for a value it does not have yet.
4. **Seed CSVs.** Before the upgrade, ask the user to copy any filled-in CSVs out of `./seeding/<PACKAGE_NAME>` (Critical Rule 5).
5. **Access.** Check it as in [Check the Access](../SKILL.md#check-the-access). The target folder is the one that holds the solution folder.
6. **Dry run.** Run it with `--action upgrade` and without `--yes`, then follow steps 5 to 8 of the guided deploy:

   ```bash
   uip vss deploy --package-name <PACKAGE_NAME> --action upgrade \
     --folder-key <FOLDER_KEY> --config <KEY>=<VALUE> --no-seed --no-interactive \
     --output json
   ```

   Leave out `--folder-key` when only one copy is installed.
