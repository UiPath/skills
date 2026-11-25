#!/bin/sh
# Give this task container its own copy of the run's UiPath login.
#
# The host's ~/.uipath is mounted read-only at SRC (smoke.yaml). Every container
# copies it to DST (/.uipath, which `uip` finds by walking up from the task's
# cwd) before the agent starts. The copy belongs to the container's root user,
# so whatever `uip` does to it — tighten /.uipath to 0700 on a credentials save,
# rewrite .auth on a token refresh — stays inside this container. Before this,
# all containers shared one read-write mount of the host-owned directory: one
# container's save set it to 0700, and every other container (root without
# DAC_OVERRIDE/DAC_READ_SEARCH) could no longer see .auth.
#
# Usage: seed-uipath-auth [SRC] [DST]   (defaults: /.uipath-host /.uipath)
set -eu

src="${1:-/.uipath-host}"
dst="${2:-/.uipath}"

if [ ! -f "$src/.auth" ]; then
  echo "seed-uipath-auth: no login at $src/.auth (is ~/.uipath mounted there?)" >&2
  exit 1
fi
if [ -e "$dst" ]; then
  echo "seed-uipath-auth: $dst already exists; refusing to overwrite it" >&2
  exit 1
fi

# Owner-only, like the CLI's own credentials file and directory.
umask 077
mkdir -p "$dst"
cp -R "$src/." "$dst/"
