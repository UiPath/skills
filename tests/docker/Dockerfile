# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
ARG CLI_VERSION=alpha
# Install the UiPath CLI shell AND pre-bake the tool plugins the eval CHECKERS
# invoke (`uip or` → orchestrator-tool, `uip is` → integrationservice-tool,
# `uip maestro` → maestro-tool).
#
# Why pre-bake (do NOT rely on the CLI's on-demand auto-install at eval time):
# the @uipath tool plugins ship CLI-compatible builds only as `-alpha` on the
# private GitHub Packages feed (public npm has stable releases only, no alpha
# channel). At eval time the sandbox pins NPM_CONFIG_PREFIX to a task-local
# `.npm-prefix` (coder_eval sandbox.py, MST-9674), so the CLI's npmrc lookup
# misses this @uipath:registry config and on-demand auto-install falls back to
# public npm, failing with "No compatible alpha version of '<tool>' found for
# CLI". Installing the plugins here lands them in the global @uipath dir
# (PLUGIN_TOOLS_DIR) so they are discovered on disk — no eval-time registry
# resolution, and a feed/registry outage fails THIS build loudly instead of
# silently scoring agents 0 on every orchestrator/IS-dependent checker.
# `set -euo pipefail` makes any failed tool install abort the build.
# (Fixes the recurring `check_folder_id_fresh` "No compatible alpha version of
# '@uipath/orchestrator-tool'" failures in skill-flow-outlook-trigger-inbox.)
RUN set -euo pipefail && \
    if [ -z "$NPM_AUTH_TOKEN" ]; then \
      echo "Error: NPM_AUTH_TOKEN must be passed as build arg"; exit 1; \
    fi && \
    npmrc="$(npm config get globalconfig)" && \
    mkdir -p "$(dirname "$npmrc")" && \
    printf '%s\n' \
      '@uipath:registry=https://npm.pkg.github.com/' \
      "//npm.pkg.github.com/:_authToken=${NPM_AUTH_TOKEN}" \
      > "$npmrc" && \
    npm install -g "@uipath/cli@${CLI_VERSION}" && \
    uip --version && \
    uip tools install @uipath/orchestrator-tool && \
    uip tools install @uipath/integrationservice-tool && \
    uip tools install @uipath/maestro-tool && \
    uip tools list

# .NET 8 SDK — `uip rpa build` shells out to dotnet for the workflow compiler.
# Without it, RPA tasks running under driver: docker fail their build criterion
# with `spawn dotnet ENOENT`. libicu is a runtime dependency of the SDK.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libicu-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && bash /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -sf /usr/share/dotnet/dotnet /usr/local/bin/dotnet \
    && rm /tmp/dotnet-install.sh \
    && dotnet --version

ENV DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1
