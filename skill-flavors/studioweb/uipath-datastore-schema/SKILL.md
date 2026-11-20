<!--skill-flavor:pack-and-deploy:start-->
3. Publish and deploy through the uipath-solution skill (`uip solution publish`, then `uip solution deploy run` or `deploy upgrade`); Studio Web packs the solution on publish, so there is no `pack` step. Data Service validates the changesets at deploy; read its message against the error table in [schema-resource-guide.md](references/schema-resource-guide.md#deploy-errors).
<!--skill-flavor:pack-and-deploy:end-->
