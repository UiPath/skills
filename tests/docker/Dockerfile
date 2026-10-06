# syntax=docker/dockerfile:1.7
# Custom image for UiPath skills smoke tests
# Extends coder-eval-agent with UiPath CLI tools and the Flow SDK pre-installed
ARG CODER_EVAL_IMAGE=coder-eval-agent:latest
FROM ${CODER_EVAL_IMAGE}

ARG NPM_AUTH_TOKEN=
# `dev` = the live prerelease train on GitHub Packages (published on every push
# to cli/main). cli PR #2650 (2026-06-26) renamed the old `alpha` dist-tag →
# `dev`; `alpha` is frozen at the last build (1.197.0-alpha.20260626), so it must
# NOT be used here.
#
# Pinning CLI_VERSION to an exact `-dev.<run>` freezes the CLI shell. Tool plugins
# follow the train of the INSTALLED CLI (dev/preview/latest), never the literal
# version: rpa-tool and friends publish on their own date-stamped
# pipelines, so an exact `-dev.<run>` spec has no matching tool build and
# ETARGETs. Within that train, each tool is pinned to the highest build on the
# INSTALLED CLI's `major.minor` line (tests/docker/tool-line.mjs), not to the
# tool's own dist-tag: the CLI refuses to run a tool from another line, and a
# dist-tag is a per-package pointer that can move to the next line before the
# CLI's does (2026-10-05: cli@dev 1.204.0-dev.9000, maestro-tool@dev
# 1.205.0-dev.9021, every `uip maestro` call failed).
ARG CLI_VERSION=dev

# The builder SDK is released independently from the CLI. Follow its rolling
# release just as CLI_VERSION follows the live CLI train; callers can still
# override this with an exact version for a reproducible comparison.
ARG FLOW_SDK_VERSION=latest

# Which published connectors library the image carries. `latest` follows the
# stable alias download.uipath.com/maestro/registry/library-json.zip, like
# FLOW_SDK_VERSION follows the SDK's rolling release. A build number
# (`connectors-library-2026.09.9`, or `2026.09.9`) pins that build's immutable
# copy under maestro/registry/versions/ instead. The alias is not safe to
# follow blindly: on 2026-09-22 it was overwritten with a 2-connector build and
# every connector task in that day's run authored against it.
#
# The pin applies twice. The build-time pull below fetches the pinned archive,
# and that is the library `flow compile` reads (FLOW_SDK_LIBRARY_JSON). The value
# is also persisted as ENV, so an agent's own bare `uip maestro registry pull`
# stays on the same build: the SDK honours CONNECTORS_LIBRARY_VERSION from the
# release carrying UiPath/flow-builder-sdk#769 (older SDKs ignore it).
ARG CONNECTORS_LIBRARY_VERSION=latest

# The package NAME is a build arg for the same reason the version is: the rename
# split the published history. `@uipath/maestro-builder-sdk` starts at 5.0.0;
# everything at or below 4.0.0 exists only under `@uipath/flow-sdk`. So a
# baseline comparison against a pre-rename build passes both:
#   --build-arg FLOW_SDK_PKG_NAME=@uipath/flow-sdk --build-arg FLOW_SDK_VERSION=4.0.0
# The CLI resolves either name (UiPath/cli#4009), and stage-preview-sdk-workspace.sh
# reads the same variable so the workspace agrees with what the image installed.
ARG FLOW_SDK_PKG_NAME=@uipath/maestro-builder-sdk

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
ENV UIPATH_CLI_DISABLE_VERSION_SYNC=1 \
    PREVIEW_FLOW_SDK_ROOT=/opt/preview-flow-sdk \
    PREVIEW_FLOW_SDK_ASSETS_ROOT=/opt/preview-flow-sdk-assets \
    UIP_MAESTRO_REGISTRY_HOME=/opt/preview-flow-sdk-assets/registry \
    FLOW_SDK_SETUP_STATUS=/opt/preview-flow-sdk-assets/setup-status.json

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
# A tool with nothing to install (not on the registry, or no build on the
# train at or below the CLI's line) is skipped; MIN_TOOLS is the tripwire
# against a wholesale collapse. Every other miss fails the build: a tool whose
# train has builds on an older line but not on the CLI's (a line bump still
# publishing), a failed registry lookup, or a failed install. Any of those
# would leave a tool out and fail its tasks at eval time.
#
# Why raw `npm install -g @uipath/<tool>@<version>` and NOT `uip tools install <tool>`:
# cli PR #2650 made `dev` a publish dist-tag but NOT a release channel (the only
# channels are {stable, preview}). A `-dev` CLI's `uip tools install` resolves
# the channel to `stable`, then looks for a NON-prerelease tool on its `1.199.x`
# line — none exist — and fails with "No compatible version". npm has no such
# logic, so tool-line.mjs does the line-and-train selection and npm installs
# that exact version. The CLI then discovers these on disk by scanning
# `$(npm root -g)/@uipath/*` against the whitelist (toolLoader.ts), so a plain
# global install is found with no registry work at eval time.
#
# The token-bearing npmrc is written and removed inside this single RUN. CI and
# campaign builds provide it through the BuildKit secret so it is absent from
# build output and history. The ARG fallback keeps the external nightly caller
# compatible until that caller can migrate; do not use it for new callers.
COPY tests/docker/tool-line.mjs /opt/uip-tool-line/tool-line.mjs
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
    mkdir -p "$PREVIEW_FLOW_SDK_ROOT" "$PREVIEW_FLOW_SDK_ASSETS_ROOT" && \
    printf '%s\n' '{"private":true,"type":"module"}' \
      > "$PREVIEW_FLOW_SDK_ROOT/package.json" && \
    printf '%s\n' unavailable > "$PREVIEW_FLOW_SDK_ASSETS_ROOT/sdk-install.status" && \
    : > "$PREVIEW_FLOW_SDK_ROOT/flow-sdk.version" && \
    if npm install --prefix "$PREVIEW_FLOW_SDK_ROOT" \
      --save-exact --no-audit --no-fund --userconfig "$npmrc" \
      "${FLOW_SDK_PKG_NAME}@${FLOW_SDK_VERSION}"; then \
      if resolved_sdk_version="$(node -p \
        "require('$PREVIEW_FLOW_SDK_ROOT/node_modules/${FLOW_SDK_PKG_NAME}/package.json').version")" \
        && test -x "$PREVIEW_FLOW_SDK_ROOT/node_modules/.bin/flow-sdk"; then \
        printf '%s\n' "$resolved_sdk_version" > "$PREVIEW_FLOW_SDK_ROOT/flow-sdk.version"; \
        printf '%s\n' available > "$PREVIEW_FLOW_SDK_ASSETS_ROOT/sdk-install.status"; \
        echo "Installed ${FLOW_SDK_PKG_NAME}@${resolved_sdk_version}"; \
      else \
        echo "WARN: ${FLOW_SDK_PKG_NAME}@${FLOW_SDK_VERSION} installed incompletely; Flow tasks will fail at runtime"; \
      fi; \
    else \
      echo "WARN: ${FLOW_SDK_PKG_NAME}@${FLOW_SDK_VERSION} unavailable; Flow tasks will fail at runtime"; \
    fi && \
    cli_version="$(uip --version | tail -n 1)" && \
    tool_line_js=/opt/uip-tool-line/tool-line.mjs && \
    cli_line="$(node "$tool_line_js" line "$cli_version")" && \
    # The tool train comes from the INSTALLED CLI, not the CLI_VERSION string:
    # GitHub Packages `cli@latest` is a dev build, so `latest` there means the
    # dev train.
    tool_tag="$(node "$tool_line_js" train "$cli_version")" && \
    # A public-npm CLI pairs with public-npm tools: stable tool builds are not
    # on GitHub Packages, whose `latest` follows the dev train.
    tool_registry="" && \
    if [ "$public_cli" = true ]; then tool_registry="https://registry.npmjs.org"; fi && \
    echo "CLI ${cli_version} -> tools pinned to the ${cli_line}x line, train @${tool_tag}${tool_registry:+ from $tool_registry}" && \
    uip tools search --output json > /tmp/uip-tools-search.json && \
    tools="$(grep -oE '@uipath/[a-z0-9-]+-tool' /tmp/uip-tools-search.json | sort -u || true)" && \
    installed=0 && \
    for tool in $tools; do \
      pick_rc=0 && \
      tool_version="$(node "$tool_line_js" pick "$tool" "$cli_line" "$tool_tag" $tool_registry)" || pick_rc=$?; \
      case "$pick_rc" in \
        0) echo "Installing ${tool}@${tool_version}" && \
           npm install -g ${tool_registry:+"--@uipath:registry=$tool_registry"} "${tool}@${tool_version}" || \
             { echo "Error: ${tool}@${tool_version} failed to install"; exit 1; }; \
           installed=$((installed + 1)) ;; \
        3) echo "WARN: ${tool} has nothing to install on the @${tool_tag} train at or below ${cli_line}x — skipping" ;; \
        4) echo "Error: ${tool} has @${tool_tag} builds, but none on the CLI's ${cli_line}x line yet. Rebuild once it publishes."; exit 1 ;; \
        *) echo "Error: could not look up ${tool} (tool-line.mjs pick exit ${pick_rc})"; exit 1 ;; \
      esac; \
    done && \
    echo "Installed ${installed} tool plugins (floor ${MIN_TOOLS})" && \
    if [ "$installed" -lt "$MIN_TOOLS" ]; then \
      echo "Error: only ${installed} tools installed (< ${MIN_TOOLS}) — feed outage or wrong dist-tag?"; \
      exit 1; \
    fi && \
    rm -f "$npmrc" && \
    uip tools list && \
    # Gate: every installed tool must be on the CLI's line, or the CLI refuses
    # to run it and every task that needs it fails at eval time.
    uip tools list --output json | node "$tool_line_js" check "$cli_line" "$installed"

# .NET 8 SDK — `uip rpa build` shells out to dotnet for the workflow compiler.
# Without it, RPA tasks running under driver: docker fail their build criterion
# with `spawn dotnet ENOENT`. libicu is a runtime dependency of the SDK.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libicu-dev \
        jq \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && bash /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && bash /tmp/dotnet-install.sh --channel 10.0 --install-dir /usr/share/dotnet \
    && ln -sf /usr/share/dotnet/dotnet /usr/local/bin/dotnet \
    && rm /tmp/dotnet-install.sh \
    && dotnet --version

ENV DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1

# Pull the released connector catalog through the product CLI. Flow-specific
# setup is best-effort so an SDK/feed outage does not block every non-Flow eval;
#
# The smoke fixture's import is rewritten to whatever THIS image installed. A
# build arg cannot reach an import statement, so a hard-coded specifier breaks
# one of the two builds: the new name fails an old-name baseline
# (`--build-arg FLOW_SDK_PKG_NAME=@uipath/flow-sdk`) and the old name fails the
# default build on `Cannot find package`. Here that is only a WARN, so it would
# be a silently skipped smoke rather than a build failure — which is why the
# `grep` follows the `sed`: a specifier shape the pattern misses fails on the
# grep, in the same breath, instead of looking like an SDK defect at
# `flow check`.
#
# Flow tasks still fail at runtime when their required surface is unavailable.
# The status file records exactly which rolling dependencies resolved.
#
# Where the pull lands is the CLI's business, and it moved: up to
# maestro-tool 1.202.0-dev.8425 `uip maestro registry pull` unpacked a snapshot
# under $UIP_MAESTRO_REGISTRY_HOME and wrote `current.json` there; from
# dev.8461 (cli#3823) it delegates to the Flow SDK, which caches the library
# under ~/.uipath/cache/flow-sdk/library/<sha256>/ and writes no current.json.
# This step reads BOTH: the old pointer when the CLI still writes it, otherwise
# `uip maestro registry path` (the CLI's own answer to "where is it") — and then
# records the image's provenance pointer itself, so the per-task
# stage-preview-sdk-workspace.sh and the run scripts keep one contract
# ($UIP_MAESTRO_REGISTRY_HOME/current.json: libraryHash + snapshotPath) no matter
# which layout the installed CLI produced. Hard-coding either layout broke the
# 2026-09-01 image build the moment the @dev tool moved, and under best-effort it
# would be worse than a break: the image would go GREEN with no connector
# library, and every connector-backed task would fail at runtime behind a
# warning nobody reads.
#
# `connectors/` is symlinked when present and never gates the library. The
# current layout does not produce it — `registry pull` emits descriptors only
# for connectors a project references, and says so ("no connector referenced by
# this project yet ... 0 TypeScript modules"). Requiring it would have pinned
# registry_status at `failed` forever, taking the library-json/md symlinks down
# with it since they share the chain.
COPY tests/fixtures/maestro-flow-sdk-smoke/ /opt/maestro-flow-sdk-smoke/
RUN set -euo pipefail && \
    sdk_status="$(tr -d '[:space:]' < "$PREVIEW_FLOW_SDK_ASSETS_ROOT/sdk-install.status")" && \
    resolved_sdk_version="$(tr -d '[:space:]' < "$PREVIEW_FLOW_SDK_ROOT/flow-sdk.version")" && \
    registry_status=skipped && \
    source_check_status=skipped && \
    library_hash='' && \
    connectors_library_version="${CONNECTORS_LIBRARY_VERSION:-latest}" && \
    connectors_library_url='' && \
    if [ "$connectors_library_version" != latest ]; then \
      connectors_library_build="$(printf '%s' "$connectors_library_version" | \
        sed -nE 's/^(connectors-library-)?([0-9]{4}\.[0-9]{2}\.[0-9]+)$/\2/p')"; \
      if [ -z "$connectors_library_build" ]; then \
        echo "ERROR: CONNECTORS_LIBRARY_VERSION must be 'latest' or a build number such as connectors-library-2026.09.9, got '$connectors_library_version'" >&2; \
        exit 1; \
      fi; \
      connectors_library_url="https://download.uipath.com/maestro/registry/versions/connectors-library-${connectors_library_build}/library-json.zip"; \
      echo "Pinning the connectors library to $connectors_library_url"; \
    fi && \
    if [ "$sdk_status" = available ]; then \
      registry_status=failed; \
      if registry_output="$(cd "$PREVIEW_FLOW_SDK_ROOT" && \
        uip maestro registry pull --force ${connectors_library_url:+--url "$connectors_library_url"} --output json 2>&1)"; then \
        printf '%s\n' "$registry_output"; \
        registry_snapshot=''; \
        if [ -f "$UIP_MAESTRO_REGISTRY_HOME/current.json" ]; then \
          registry_snapshot="$(jq -er '.snapshotPath' "$UIP_MAESTRO_REGISTRY_HOME/current.json" || true)"; \
          library_hash="$(jq -er '.libraryHash' "$UIP_MAESTRO_REGISTRY_HOME/current.json" || true)"; \
        else \
          library_json="$(cd "$PREVIEW_FLOW_SDK_ROOT" && \
            readlink -f "$(uip maestro registry path --library-json --output plain | tail -1)" || true)"; \
          library_hash="$(cd "$PREVIEW_FLOW_SDK_ROOT" && \
            uip maestro registry path --sha --output plain | tail -1 || true)"; \
          if [ -n "$library_json" ] && [ -d "$library_json" ] && [ -n "$library_hash" ]; then \
            registry_snapshot="$(dirname "$library_json")"; \
            mkdir -p "$UIP_MAESTRO_REGISTRY_HOME"; \
            jq -n --arg libraryHash "$library_hash" --arg snapshotPath "$registry_snapshot" \
              '{libraryHash: $libraryHash, snapshotPath: $snapshotPath}' \
              > "$UIP_MAESTRO_REGISTRY_HOME/current.json"; \
          fi; \
        fi; \
        if [ -n "$registry_snapshot" ] && [ -n "$library_hash" ] \
          && test -f "$registry_snapshot/library-json/index.json" \
          && test -f "$registry_snapshot/library-md/index.json" \
          && ln -s "$registry_snapshot/library-json" "$PREVIEW_FLOW_SDK_ASSETS_ROOT/library-json" \
          && ln -s "$registry_snapshot/library-md" "$PREVIEW_FLOW_SDK_ASSETS_ROOT/library-md"; then \
          registry_status=available; \
          if [ -d "$registry_snapshot/connectors" ]; then \
            ln -s "$registry_snapshot/connectors" "$PREVIEW_FLOW_SDK_ASSETS_ROOT/connectors"; \
          fi; \
        else \
          echo "WARN: Maestro registry snapshot was incomplete; connector-backed Flow tasks will fail at runtime"; \
        fi; \
      else \
        printf 'WARN: Maestro registry pull failed; connector-backed Flow tasks will fail at runtime\n%s\n' "$registry_output"; \
      fi; \
      source_check_status=failed; \
      if (cd /opt/maestro-flow-sdk-smoke \
        && ln -s "$PREVIEW_FLOW_SDK_ROOT/node_modules" node_modules \
        && sed -i "s#from '@uipath/[a-z0-9-]*'#from '${FLOW_SDK_PKG_NAME}'#" Smoke.flow.ts \
        && grep -q "from '${FLOW_SDK_PKG_NAME}'" Smoke.flow.ts \
        && uip maestro flow check Smoke.flow.ts --source); then \
        source_check_status=passed; \
      else \
        echo "WARN: Maestro Flow source smoke check failed; Flow tasks will fail at runtime"; \
      fi; \
    else \
      echo "WARN: Skipping Maestro registry pull and source check because the Flow SDK is unavailable"; \
    fi && \
    jq -n \
      --arg requestedVersion "$FLOW_SDK_VERSION" \
      --arg resolvedVersion "$resolved_sdk_version" \
      --arg sdkStatus "$sdk_status" \
      --arg registryStatus "$registry_status" \
      --arg libraryHash "$library_hash" \
      --arg connectorsLibraryVersion "$connectors_library_version" \
      --arg sourceCheckStatus "$source_check_status" \
      '{sdk: {requestedVersion: $requestedVersion, resolvedVersion: (if $resolvedVersion == "" then null else $resolvedVersion end), status: $sdkStatus}, registry: {requestedVersion: $connectorsLibraryVersion, libraryHash: (if $libraryHash == "" then null else $libraryHash end), status: $registryStatus}, sourceCheck: {status: $sourceCheckStatus}}' \
      > "$FLOW_SDK_SETUP_STATUS" && \
    cat "$FLOW_SDK_SETUP_STATUS"

# Persist the built-with name into the image. `ARG` is build-time only, and
# `stage-preview-sdk-workspace.sh` reads this at TASK time — without it a
# non-default build (an old-name baseline) would install one name and have the
# stager look for the other.
ENV FLOW_SDK_PKG_NAME=${FLOW_SDK_PKG_NAME}

# Persisted for the same reason: task-time pulls must resolve to the library the
# image was built with (see the ARG above).
ENV CONNECTORS_LIBRARY_VERSION=${CONNECTORS_LIBRARY_VERSION}

ENV FLOW_SDK_LIBRARY_JSON=/opt/preview-flow-sdk-assets/library-json \
    FLOW_SDK_LIBRARY_MD=/opt/preview-flow-sdk-assets/library-md \
    FLOW_SDK_CONNECTORS_DIR=/opt/preview-flow-sdk-assets/connectors

# Pre-install Python packages needed by coded-agent sandbox fixtures so agents
# don't trigger a live uv-sync download (which takes 1-2 min and causes retry
# loops in the turn timeline). uipath-langchain is declared in the
# SimpleCodedAgent fixture's pyproject.toml but has no pre-built venv.
RUN pip install --no-cache-dir "uipath-langchain>=0.9.26"

# a2a-sdk, pulled in above, caps protobuf below 7, which leaves google-antigravity
# unable to load its gencode-7.35 stubs. a2a's own stubs are 5.29.3, so 7.x serves both.
RUN pip install --no-cache-dir "protobuf>=7.35,<8"
