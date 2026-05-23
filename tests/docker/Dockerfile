# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
ARG CLI_VERSION=alpha
# Pin @uipath/* to GH Packages — this must persist for both build-time install
# AND the CLI's runtime tool auto-install (`uip maestro flow ...` shells out
# to `npm install @uipath/maestro-tool@<x>`). Earlier this file wrote to
# `npm config get globalconfig` which is the lowest-precedence config file —
# user-level config silently overrode it and resolved @alpha to the npmjs
# version (1.0.0-alpha.20260422, which hardcodes maestro-tool@1.0.4 — a
# stable build that exists on npmjs but not GH Packages). Writing the same
# config to /root/.npmrc (user-level) makes the registry pin actually stick.
RUN set -euo pipefail && \
    if [ -z "$NPM_AUTH_TOKEN" ]; then \
      echo "Error: NPM_AUTH_TOKEN must be passed as build arg"; exit 1; \
    fi && \
    printf '%s\n' \
      '@uipath:registry=https://npm.pkg.github.com/' \
      "//npm.pkg.github.com/:_authToken=${NPM_AUTH_TOKEN}" \
      > /root/.npmrc && \
    chmod 600 /root/.npmrc && \
    npm install -g "@uipath/cli@${CLI_VERSION}" && \
    uip --version

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
