# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
ARG CLI_VERSION=alpha
# github-packages: install @uipath/cli@<CLI_VERSION> from GH Packages
#   (tracks @alpha — published every cli/main merge).
# npmjs: install from default public npm registry (tracks GH releases).
ARG CLI_REGISTRY=github-packages
RUN set -euo pipefail && \
    case "$CLI_REGISTRY" in \
      github-packages) \
        if [ -z "$NPM_AUTH_TOKEN" ]; then \
          echo "Error: NPM_AUTH_TOKEN required for github-packages registry"; exit 1; \
        fi; \
        npmrc="$(npm config get globalconfig)"; \
        mkdir -p "$(dirname "$npmrc")"; \
        printf '%s\n' \
          '@uipath:registry=https://npm.pkg.github.com/' \
          "//npm.pkg.github.com/:_authToken=${NPM_AUTH_TOKEN}" \
          > "$npmrc" ;; \
      npmjs) \
        : ;; \
      *) \
        echo "Error: CLI_REGISTRY must be 'github-packages' or 'npmjs', got: $CLI_REGISTRY"; exit 1 ;; \
    esac && \
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
