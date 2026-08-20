# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=skills-image:latest
FROM ${BASE_IMAGE}

ARG FLOW_SDK_VERSION=latest
ENV PREVIEW_FLOW_SDK_ROOT=/opt/preview-flow-sdk

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
      "@uipath/flow-sdk@$FLOW_SDK_VERSION" && \
    rm -f "$npmrc" && \
    node -e "const p=require('./node_modules/@uipath/flow-sdk/package.json'); console.log('Installed', p.name+'@'+p.version)" && \
    test -x node_modules/.bin/flow-sdk
