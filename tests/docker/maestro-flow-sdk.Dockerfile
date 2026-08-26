# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=skills-image:base

FROM node:22-bookworm-slim AS preview_flow_sdk_package

ARG FLOW_SDK_VERSION
ARG FLOW_BUILDER_SDK_SHA
WORKDIR /src
COPY --from=flow_builder_sdk typescript/sdk/ ./typescript/sdk/
COPY --from=flow_builder_sdk integrations/scripts/ ./integrations/scripts/
RUN mkdir -p /pkg && \
    cd typescript/sdk && \
    npm ci --no-audit --no-fund && \
    npm pkg set \
      version="${FLOW_SDK_VERSION:?FLOW_SDK_VERSION is required}" \
      gitref="${FLOW_BUILDER_SDK_SHA:?FLOW_BUILDER_SDK_SHA is required}" && \
    npm pack --pack-destination /pkg && \
    mv /pkg/uipath-flow-sdk-*.tgz /pkg/uipath-flow-sdk.tgz

FROM ${BASE_IMAGE}

ARG FLOW_SDK_VERSION
ARG FLOW_BUILDER_SDK_SHA
ENV PREVIEW_FLOW_SDK_ROOT=/opt/preview-flow-sdk
ENV PREVIEW_FLOW_SDK_ASSETS_ROOT=/opt/preview-flow-sdk-assets

RUN apt-get update && apt-get install -y --no-install-recommends unzip

# Build and install the SDK from the same pinned source that supplies the
# connector library. This makes an SDK/compiler remediation measurable before
# its next package release without leaving package credentials in the image.
COPY --from=preview_flow_sdk_package \
  /pkg/uipath-flow-sdk.tgz /opt/preview-flow-sdk-pkg/uipath-flow-sdk.tgz
RUN set -euo pipefail && \
    mkdir -p "$PREVIEW_FLOW_SDK_ROOT" && \
    cd "$PREVIEW_FLOW_SDK_ROOT" && \
    printf '%s\n' '{"private":true,"type":"module"}' > package.json && \
    npm install --save-exact --no-audit --no-fund \
      /opt/preview-flow-sdk-pkg/uipath-flow-sdk.tgz && \
    node -e "const p=require('./node_modules/@uipath/flow-sdk/package.json'); console.log('Installed', p.name+'@'+p.version)" && \
    printf '%s\n' "$FLOW_SDK_VERSION" > flow-sdk.version && \
    test -x node_modules/.bin/flow-sdk

# Connector descriptors are kept at the preview skill's provenance pin so
# connector authoring and SDK signatures describe the same source revision.
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

# This assertion runs after the secret-bearing layer has ended. It proves that
# the pinned SDK resolves and the product CLI can check real source without any
# registry credential at runtime.
COPY tests/fixtures/maestro-flow-sdk-smoke/ /opt/maestro-flow-sdk-smoke/
RUN cd /opt/maestro-flow-sdk-smoke && \
    ln -s ${PREVIEW_FLOW_SDK_ROOT}/node_modules node_modules && \
    uip maestro flow check Smoke.flow.ts --source
