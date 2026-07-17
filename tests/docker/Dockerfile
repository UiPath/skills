# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
# `dev` = the live prerelease train on GitHub Packages (published on every push
# to cli/main). cli PR #2650 (2026-06-26) renamed the old `alpha` dist-tag →
# `dev`; `alpha` is frozen at the last build (1.197.0-alpha.20260626), so it must
# NOT be used here. Pin to an exact `-dev.<run>` to freeze the image.
ARG CLI_VERSION=dev

# Turn OFF the CLI's startup version-sync inside the eval container. On a `-dev`
# CLI, sync would try to re-align tools through the release-channel path (which
# can't resolve `-dev` tool builds — see below) and would undo the plugins baked
# here. Belt-and-suspenders with the eval harness env.
ENV UIPATH_CLI_DISABLE_VERSION_SYNC=1

# Install the UiPath CLI shell AND pre-bake EVERY whitelisted tool plugin, all
# from the SAME `@dev` feed on GitHub Packages, so the eval never depends on the
# CLI's on-demand auto-install or channel resolution at task time. Pre-installing
# every tool also means the on-demand auto-install path (which only fires for a
# NOT-installed verb) never triggers.
#
# Why raw `npm install -g @uipath/<tool>@dev` and NOT `uip tools install <tool>`:
# cli PR #2650 made `dev` a publish dist-tag but NOT a release channel (the only
# channels are {stable, preview}). A `-dev` CLI's `uip tools install` resolves
# the channel to `stable`, then looks for a NON-prerelease tool on its `1.199.x`
# line — none exist — and fails with "No compatible version". npm has no such
# logic: `@dev` resolves the dist-tag straight to the latest `-dev` build. The
# CLI then discovers these on disk by scanning `$(npm root -g)/@uipath/*` against
# the whitelist (toolLoader.ts), so a plain global install is found with no
# registry work at eval time. A feed outage fails THIS build loudly instead of
# silently scoring agents 0 on every tool-dependent checker.
#
# The tool list mirrors the CLI's TOOLS_WHITELIST. `set -euo pipefail` aborts the
# build on any failed install. `model-hub-tool` is intentionally omitted — it has
# no `-dev` build published; add it here once it does.
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
    for tool in \
      solution-tool agent-tool agenthub-tool conversational-tool \
      codedagent-tool context-grounding-tool functions-tool codedapp-tool \
      integrationservice-tool orchestrator-tool rpa-tool test-manager-tool \
      api-workflow-tool maestro-tool docsai-tool vertical-solutions-tool \
      rpa-legacy-tool traces-tool gov-tool admin-tool data-fabric-tool \
      insights-tool tasks-tool aops-tool llmgw-tool platform-tool \
      ixp-tool pm-tool; do \
      echo "Installing @uipath/${tool}@${CLI_VERSION}" && \
      npm install -g "@uipath/${tool}@${CLI_VERSION}"; \
    done && \
    uip tools list

# .NET 8 SDK — `uip rpa build` shells out to dotnet for the workflow compiler.
# Without it, RPA tasks running under driver: docker fail their build criterion
# with `spawn dotnet ENOENT`. libicu is a runtime dependency of the SDK.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libicu-dev \
        jq \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && bash /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -sf /usr/share/dotnet/dotnet /usr/local/bin/dotnet \
    && rm /tmp/dotnet-install.sh \
    && dotnet --version

ENV DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

# Pre-install Python packages needed by coded-agent sandbox fixtures so agents
# don't trigger a live uv-sync download (which takes 1-2 min and causes retry
# loops in the turn timeline). uipath-langchain is declared in the
# SimpleCodedAgent fixture's pyproject.toml but has no pre-built venv.
RUN pip install --no-cache-dir "uipath-langchain>=0.9.26"
