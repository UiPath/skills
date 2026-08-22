# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=skills-image:latest
FROM ${BASE_IMAGE}

ARG FLOW_SDK_VERSION
ARG FLOW_BUILDER_SDK_SHA
ENV PREVIEW_FLOW_SDK_ROOT=/opt/preview-flow-sdk
ENV PREVIEW_FLOW_SDK_ASSETS_ROOT=/opt/preview-flow-sdk-assets

RUN apt-get update && apt-get install -y --no-install-recommends unzip \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=secret,id=npm_auth_token \
    set -euo pipefail && \
    token_file=/run/secrets/npm_auth_token && \
    [ -s "$token_file" ] || { echo "npm_auth_token secret is required" >&2; exit 1; } && \
    mkdir -p "$PREVIEW_FLOW_SDK_ROOT" && \
    npmrc="$PREVIEW_FLOW_SDK_ROOT/.npmrc" && \
    printf '%s\n' \
      '@uipath:registry=https://npm.pkg.github.com/' \
      "//npm.pkg.github.com/:_authToken=$(cat "$token_file")" \
      > "$npmrc" && \
    cd "$PREVIEW_FLOW_SDK_ROOT" && \
    printf '%s\n' '{"private":true,"type":"module"}' > package.json && \
    npm install --save-exact --no-audit --no-fund --userconfig "$npmrc" \
      "@uipath/flow-sdk@${FLOW_SDK_VERSION:?FLOW_SDK_VERSION is required}" && \
    rm -f "$npmrc" && \
    node -e "const p=require('./node_modules/@uipath/flow-sdk/package.json'); console.log('Installed', p.name+'@'+p.version)" && \
    printf '%s\n' "$FLOW_SDK_VERSION" > flow-sdk.version && \
    test -x node_modules/.bin/flow-sdk

# Keep connector authoring assets on the same upstream revision as the preview
# skill snapshot. The package itself is the published version pinned by the run.
COPY --from=flow_builder_sdk typescript/sdk/lib/ ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/typescript/sdk/lib/
COPY --from=flow_builder_sdk integrations/ ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/integrations/

RUN FLOW_SDK_ROOT=${PREVIEW_FLOW_SDK_ASSETS_ROOT} \
      bash ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/typescript/sdk/lib/scripts/unpack-library.sh && \
    python3 ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/integrations/scripts/generate_connectors_ts.py \
      --library ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/typescript/sdk/lib/library-json \
      --output ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/connectors \
      --import @uipath/flow-sdk && \
    chmod +x ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/integrations/scripts/prepare_connector.py && \
    printf '#!/bin/sh\nexec python3 %s/integrations/scripts/prepare_connector.py "$@" --import @uipath/flow-sdk\n' \
      "${PREVIEW_FLOW_SDK_ASSETS_ROOT}" > /usr/local/bin/prepare-connector && \
    chmod +x /usr/local/bin/prepare-connector && \
    prepare-connector --help >/dev/null && \
    printf '%s\n' "${FLOW_BUILDER_SDK_SHA:?FLOW_BUILDER_SDK_SHA is required}" \
      > ${PREVIEW_FLOW_SDK_ASSETS_ROOT}/flow-builder-sdk.sha

ENV FLOW_SDK_LIBRARY_JSON=${PREVIEW_FLOW_SDK_ASSETS_ROOT}/typescript/sdk/lib/library-json \
    FLOW_SDK_LIBRARY_MD=${PREVIEW_FLOW_SDK_ASSETS_ROOT}/typescript/sdk/lib/library-md \
    FLOW_SDK_CONNECTORS_DIR=${PREVIEW_FLOW_SDK_ASSETS_ROOT}/connectors
