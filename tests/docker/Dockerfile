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
    # `uip agent …` (e.g. `agent review`) is provided by agent-tool. Pre-install
    # from the @alpha feed so the eval-time on-demand resolver doesn't fall back
    # to public npm (stable only) — stable lacks the alpha-only guardrail-format
    # review rules, which silently scores guardrail review tasks 0.
    uip tools install @uipath/agent-tool && \
    # `uip codedagent …` (e.g. `codedagent review`) is provided by codedagent-tool.
    # Pre-install from the @alpha feed so the eval-time resolver doesn't fall back
    # to public npm — stable lacks the alpha-only coded guardrail review rules
    # (CODED_GUARDRAIL_WRONG_IMPORT / _TOOL_SCOPE_NO_TOOLS / _INVALID_CONTRACT),
    # which silently scores coded guardrail review tasks 0.
    uip tools install @uipath/codedagent-tool && \
    # IXP command group (`uip ixp …`) ships as a separate plugin on the @alpha
    # feed. Required so the live ixp e2e (full_lifecycle) can actually execute
    # `uip ixp` — without it the command is unknown and the e2e thrashes to
    # MAX_TURNS. (Smoke ixp tasks pass regardless, since they grade command shape.)
    uip tools install @uipath/ixp-tool && \
    # AgentHub command group ships as a separate plugin (CLI fetches it lazily).
    # Pre-install from the same @alpha feed so live `uip agenthub …` MCP e2e
    # tasks don't hit a missing-plugin 401.
    uip tools install @uipath/agenthub-tool && \
    # Data Fabric command group (`uip df …`) — required by every
    # tests/tasks/uipath-platform/data-fabric/* task. Without this,
    # `uip df entities …` / `records …` / `choice-sets …` / `files …` all
    # return "unknown command 'df'" and pre_run seed scripts + agent calls
    # both fail.
    uip tools install @uipath/data-fabric-tool && \
    # Governance tool — provides `uip gov aops-policy`, `uip gov access-policy`,
    # and `uip gov compliance-packs` commands used by uipath-governance skill tests.
    uip tools install @uipath/gov-tool && \
    # Test Manager command group (`uip tm …`) — required by uipath-test tasks
    uip tools install @uipath/test-manager-tool && \
    # Solution command group (`uip solution …`) — required by uipath-solution
    # tasks (e.g. skill-solution-deploy-list)
    uip tools install @uipath/solution-tool && \
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
