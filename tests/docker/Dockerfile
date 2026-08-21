# syntax=docker/dockerfile:1.7
# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
# `dev` = the live prerelease train on GitHub Packages (published on every push
# to cli/main). cli PR #2650 (2026-06-26) renamed the old `alpha` dist-tag →
# `dev`; `alpha` is frozen at the last build (1.197.0-alpha.20260626), so it must
# NOT be used here.
#
# Pinning CLI_VERSION to an exact `-dev.<run>` freezes the CLI shell. Tool plugins
# are ALWAYS installed at the dist-tag DERIVED from CLI_VERSION (dev/preview/
# latest), never the literal version: rpa-tool and friends publish on their own
# date-stamped pipelines, so an exact `-dev.<run>` spec has no matching tool build
# and ETARGETs. A pin freezes the CLI; the tools ride the train's tag.
ARG CLI_VERSION=dev

# Floor on the number of tool plugins that must install for the image to be
# usable. Discovery returns the CLI's full whitelist; a few may lack a build on
# the current train (e.g. model-hub-tool has no `-dev` build), so individual
# misses are tolerated — but a collapse below this floor (feed outage, wrong
# dist-tag) fails the build loudly instead of silently scoring agents 0.
ARG MIN_TOOLS=25

# Turn OFF the CLI's startup version-sync inside the eval container. On a `-dev`
# CLI, sync would try to re-align tools through the release-channel path (which
# can't resolve `-dev` tool builds — see below) and would undo the plugins baked
# here. Belt-and-suspenders with the eval harness env.
ENV UIPATH_CLI_DISABLE_VERSION_SYNC=1

# Install the UiPath CLI shell from its public npm release and pre-bake EVERY
# whitelisted tool plugin from GitHub Packages. Stable CLI releases such as the
# campaign's 1.198.0 pin are not mirrored to GitHub Packages; installing the
# shell before writing the scoped GitHub npmrc keeps the shell byte-aligned with
# the SDK image while the private tool plugins still come from their real feed.
# Pre-installing every tool also means the on-demand auto-install path (which
# only fires for a NOT-installed verb) never triggers.
#
# The tool set is DISCOVERED at build time via `uip tools search` — NOT a
# hand-copied list — so it can't drift behind the CLI's TOOLS_WHITELIST (a tool
# the image misses silently scores 0 on every task that needs its verbs).
# Unpublished tools drop out on their own (install fails → skipped); MIN_TOOLS is
# the tripwire against a wholesale collapse.
#
# Why raw `npm install -g @uipath/<tool>@<tag>` and NOT `uip tools install <tool>`:
# cli PR #2650 made `dev` a publish dist-tag but NOT a release channel (the only
# channels are {stable, preview}). A `-dev` CLI's `uip tools install` resolves
# the channel to `stable`, then looks for a NON-prerelease tool on its `1.199.x`
# line — none exist — and fails with "No compatible version". npm has no such
# logic: `@dev` resolves the dist-tag straight to the latest `-dev` build. The
# CLI then discovers these on disk by scanning `$(npm root -g)/@uipath/*` against
# the whitelist (toolLoader.ts), so a plain global install is found with no
# registry work at eval time.
#
# The token-bearing npmrc is written and removed inside this single RUN. CI and
# campaign builds provide it through the BuildKit secret so it is absent from
# build output and history. The ARG fallback keeps the external nightly caller
# compatible until that caller can migrate; do not use it for new callers.
RUN --mount=type=secret,id=npm_auth_token \
    set -euo pipefail && \
    npm_auth_token="" && \
    if [ -s /run/secrets/npm_auth_token ]; then \
      npm_auth_token="$(cat /run/secrets/npm_auth_token)"; \
    elif [ -n "$NPM_AUTH_TOKEN" ]; then \
      npm_auth_token="$NPM_AUTH_TOKEN"; \
      echo "WARN: NPM_AUTH_TOKEN build-arg fallback is deprecated"; \
    else \
      echo "Error: npm_auth_token secret or NPM_AUTH_TOKEN build arg is required"; exit 1; \
    fi && \
    # Derive the tool dist-tag from CLI_VERSION: an exact prerelease pin
    # (1.199.0-dev.7923) → its train tag (dev); a bare stable semver → latest;
    # a plain dist-tag (dev/preview) → itself.
    case "$CLI_VERSION" in \
      *-*)    tool_tag="${CLI_VERSION#*-}"; tool_tag="${tool_tag%%.*}" ;; \
      [0-9]*) tool_tag="latest" ;; \
      *)      tool_tag="$CLI_VERSION" ;; \
    esac && \
    echo "CLI_VERSION=$CLI_VERSION -> tool dist-tag @$tool_tag" && \
    case "$CLI_VERSION" in \
      [0-9]*-*) public_cli=false ;; \
      [0-9]*)   public_cli=true ;; \
      *)        public_cli=false ;; \
    esac && \
    if [ "$public_cli" = true ]; then \
      npm install -g --registry=https://registry.npmjs.org "@uipath/cli@${CLI_VERSION}"; \
    fi && \
    npmrc="$(npm config get globalconfig)" && \
    mkdir -p "$(dirname "$npmrc")" && \
    printf '%s\n' \
      '@uipath:registry=https://npm.pkg.github.com/' \
      "//npm.pkg.github.com/:_authToken=${npm_auth_token}" \
      > "$npmrc" && \
    if [ "$public_cli" = false ]; then \
      npm install -g "@uipath/cli@${CLI_VERSION}"; \
    fi && \
    uip --version && \
    uip tools search --output json > /tmp/uip-tools-search.json && \
    tools="$(grep -oE '@uipath/[a-z0-9-]+-tool' /tmp/uip-tools-search.json | sort -u || true)" && \
    installed=0 && \
    for tool in $tools; do \
      echo "Installing ${tool}@${tool_tag}" && \
      if npm install -g "${tool}@${tool_tag}"; then \
        installed=$((installed + 1)); \
      else \
        echo "WARN: ${tool}@${tool_tag} not installed (no build on this train?) — skipping"; \
      fi; \
    done && \
    echo "Installed ${installed} tool plugins (floor ${MIN_TOOLS})" && \
    if [ "$installed" -lt "$MIN_TOOLS" ]; then \
      echo "Error: only ${installed} tools installed (< ${MIN_TOOLS}) — feed outage or wrong dist-tag?"; \
      exit 1; \
    fi && \
    rm -f "$npmrc" && \
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

# Runtime npm auth for the @uipath scope, needed by any task whose skill tells
# the agent to `npm install @uipath/...` -- the Maestro builder SDK
# (`@uipath/flow-sdk`) is the live case, and it is published ONLY to GitHub
# Packages.
#
# The build-time npmrc above is written to `npm config get globalconfig` and
# deleted in the same RUN, on purpose: it carries the literal token. This layer
# writes a token-LESS npmrc instead, referencing ${NODE_AUTH_TOKEN}, which npm
# expands at read time. Nothing secret enters the image; the eval harness
# forwards the variable (env_passthrough_extra: NODE_AUTH_TOKEN).
#
# NPM_CONFIG_USERCONFIG is the half that actually decides whether this works,
# and the reason is not obvious. npm resolves `userconfig` to $HOME/.npmrc, and the docker runner
# forwards --env HOME with the HOST value by design (coder_eval
# models/sandbox.py: "HOME is intentional in default"), which overrides this
# image's /root. So npm looks for /home/<hostuser>/.npmrc, finds nothing, never
# maps the @uipath scope to GitHub Packages, and falls through to the public
# registry -- where the package 404s. Pinning userconfig makes npm's view of
# the npmrc independent of whatever HOME the harness forwards.
RUN printf '%s\n' \
      '@uipath:registry=https://npm.pkg.github.com/' \
      '//npm.pkg.github.com/:_authToken=${NODE_AUTH_TOKEN}' \
      > /root/.npmrc
ENV NPM_CONFIG_USERCONFIG=/root/.npmrc
