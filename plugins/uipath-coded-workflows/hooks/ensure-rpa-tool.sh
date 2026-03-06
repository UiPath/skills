#!/bin/bash
# Ensures @uipath/uipcli is installed globally.
# Runs once per session via the SessionStart plugin hook.
# If npm is missing, attempts to install Node.js first.
# Supports Windows, macOS, and Linux.

# Already installed — nothing to do
if command -v rpa-tool &> /dev/null; then
  exit 0
fi

# Detect OS
OS="$(uname -s 2>/dev/null || echo "Windows")"
case "$OS" in
  Linux*)  PLATFORM="linux" ;;
  Darwin*) PLATFORM="mac" ;;
  MINGW*|MSYS*|CYGWIN*|Windows*) PLATFORM="windows" ;;
  *)       PLATFORM="unknown" ;;
esac

# Ensure npm is available, install Node.js if not
if ! command -v npm &> /dev/null; then
  echo "npm not found, attempting to install Node.js..." >&2

  case "$PLATFORM" in
    windows)
      if command -v winget &> /dev/null; then
        winget install --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements 2>&1
      elif command -v choco &> /dev/null; then
        choco install nodejs-lts -y 2>&1
      elif command -v nvm &> /dev/null; then
        nvm install --lts 2>&1
        nvm use --lts 2>&1
      else
        echo "Cannot install Node.js automatically. No package manager found (winget, choco, or nvm)." >&2
        echo "Please install Node.js from https://nodejs.org and restart your session." >&2
        exit 2
      fi
      export PATH="$PATH:/c/Program Files/nodejs:/c/ProgramData/nvm"
      ;;
    mac)
      if command -v brew &> /dev/null; then
        brew install node 2>&1
      elif command -v nvm &> /dev/null; then
        nvm install --lts 2>&1
        nvm use --lts 2>&1
      else
        echo "Cannot install Node.js automatically. No package manager found (brew or nvm)." >&2
        echo "Please install Node.js from https://nodejs.org and restart your session." >&2
        exit 2
      fi
      ;;
    linux)
      if command -v apt-get &> /dev/null; then
        sudo apt-get update -y && sudo apt-get install -y nodejs npm 2>&1
      elif command -v dnf &> /dev/null; then
        sudo dnf install -y nodejs npm 2>&1
      elif command -v yum &> /dev/null; then
        sudo yum install -y nodejs npm 2>&1
      elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm nodejs npm 2>&1
      elif command -v nvm &> /dev/null; then
        nvm install --lts 2>&1
        nvm use --lts 2>&1
      else
        echo "Cannot install Node.js automatically. No supported package manager found." >&2
        echo "Please install Node.js from https://nodejs.org and restart your session." >&2
        exit 2
      fi
      ;;
    *)
      echo "Unsupported platform. Please install Node.js from https://nodejs.org" >&2
      exit 2
      ;;
  esac

  hash -r 2>/dev/null

  if ! command -v npm &> /dev/null; then
    echo "Node.js was installed but npm is not yet available in this session." >&2
    echo "Please restart your terminal, then run: npm install -g @uipath/uipcli" >&2
    exit 2
  fi
fi

# Install rpa-tool
echo "Installing @uipath/rpa-tool globally..." >&2
if ! npm install -g @uipath/rpa-tool@26.0.0-alpha.22320; then
  echo "Failed to install @uipath/rpa-tool. Please run: npm install -g @uipath/rpa-tool" >&2
  exit 2
fi

exit 0
