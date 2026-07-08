# Ensures @uipath/cli and @uipath/rpa-tool are installed globally.
# Runs once per session via the SessionStart plugin hook.
# If npm is missing, attempts to install Node.js first.
# Runs under Windows PowerShell 5.1 and PowerShell 7+ (pwsh).
#
# TWIN SCRIPT: hooks/ensure-uip.sh is the bash twin of this file — any
# behavioral change here MUST be mirrored there in the same PR (see CLAUDE.md).

$ErrorActionPreference = 'Continue'

# $IsWindows exists only on PowerShell 6+; 5.1 is always Windows.
$script:OnWindows = ($PSVersionTable.PSVersion.Major -lt 6) -or $IsWindows

# ── helpers ──────────────────────────────────────────────────────────
function Fail([string]$Message) {
  [Console]::Error.WriteLine($Message)
  [Console]::Error.WriteLine('Please install Node.js from https://nodejs.org and restart your session.')
  exit 2
}

function Test-CommandAvailable([string]$Name) {
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# Run a native installer command and echo its merged output as plain
# strings (avoids Windows PowerShell 5.1 wrapping stderr lines in
# NativeCommandError records).
function Invoke-Installer([scriptblock]$Command) {
  & $Command 2>&1 | ForEach-Object { "$_" }
}

function Confirm-Npm {
  if (Test-CommandAvailable npm) { return }

  [Console]::Error.WriteLine('npm not found, attempting to install Node.js...')

  if ($script:OnWindows) {
    if (Test-CommandAvailable winget) {
      Invoke-Installer { winget install --id OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements }
    }
    elseif (Test-CommandAvailable choco) { Invoke-Installer { choco install nodejs-lts -y } }
    elseif (Test-CommandAvailable nvm)   { Invoke-Installer { nvm install lts }; Invoke-Installer { nvm use lts } }
    else { Fail 'No package manager found (winget, choco, or nvm).' }
    $env:PATH = "$env:PATH;$env:ProgramFiles\nodejs;$env:ProgramData\nvm"
  }
  elseif ($IsMacOS) {
    if (Test-CommandAvailable brew) { Invoke-Installer { brew install node } }
    else { Fail 'No package manager found (brew).' }
  }
  elseif ($IsLinux) {
    if     (Test-CommandAvailable apt-get) { Invoke-Installer { sudo apt-get update -y }; Invoke-Installer { sudo apt-get install -y nodejs npm } }
    elseif (Test-CommandAvailable dnf)     { Invoke-Installer { sudo dnf install -y nodejs npm } }
    elseif (Test-CommandAvailable yum)     { Invoke-Installer { sudo yum install -y nodejs npm } }
    elseif (Test-CommandAvailable pacman)  { Invoke-Installer { sudo pacman -Sy --noconfirm nodejs npm } }
    else { Fail 'No supported package manager found.' }
  }
  else { Fail 'Unsupported platform.' }

  if (-not (Test-CommandAvailable npm)) {
    [Console]::Error.WriteLine('Node.js was installed but npm is not yet available in this session.')
    [Console]::Error.WriteLine('Please restart your terminal, then run: npm install -g @uipath/cli')
    exit 2
  }
}

# Force `@uipath` to public npm. Narrowly guards users who set a custom
# default `registry=...` in `~/.npmrc` (e.g., a corporate proxy/mirror)
# but no `@uipath:registry=...` scope override — without this flag,
# `outdated`, `view`, and `install` route through their default mirror,
# which may not host `@uipath` or may serve a different `latest`.
# `--registry=` does NOT bypass scope mappings; only the scope-specific
# override does. Apply to `outdated` / `view` (registry lookup) and
# `install`; `ls` reads disk and doesn't need it.
#
# Users WITH a non-public `@uipath:registry=...` scope mapping (UiPath
# devs on the GitHub Packages prerelease line, private mirrors aliasing
# the scope) are skipped earlier by `Test-FromOtherFeed`, so this flag
# never clobbers a deliberate non-public install — it only protects the
# narrow "custom default registry, no scope mapping" path.
$script:UipathRegistryFlag = '--@uipath:registry=https://registry.npmjs.org/'

# True if $Path is a symlink OR a Windows directory junction. .NET's
# ReparsePoint attribute covers both on Windows — junctions are the
# default fallback `npm link` uses on Windows when run without developer
# mode or admin rights — and PowerShell 7 maps POSIX symlinks to the
# same attribute on macOS/Linux.
function Test-SymlinkOrJunction([string]$Path) {
  try {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    return (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
  }
  catch { return $false }
}

# Detect a local-source install via `npm link` / `bun link` (see the CLI
# repo README, "Building from Source"). Linked installs point at a
# working tree that is, by definition, ahead of the published `latest`
# tag — upgrading would clobber the developer's local build with an
# older registry version.
function Test-LinkedPackage([string]$Pkg) {
  $npmRoot = (& npm root -g 2>$null | Select-Object -First 1)
  if ($npmRoot -and (Test-SymlinkOrJunction (Join-Path $npmRoot $Pkg))) { return $true }
  return (Test-SymlinkOrJunction (Join-Path $HOME ".bun/install/global/node_modules/$Pkg"))
}

# Detect a scope mapped to a non-public feed (GitHub Packages, an internal
# Artifactory, etc.). Such builds typically carry prerelease versions ahead
# of the public `latest` tag — forcing an upgrade against the public
# registry would downgrade the developer's chosen feed. Signal is the
# merged npm config for `@<scope>:registry`: if the user's `.npmrc` (any
# level) maps the package's scope to something other than the public
# registry, leave the install alone. Reads merged config so project/user/
# global/env overrides are all honored. Unscoped packages → never skip.
function Test-FromOtherFeed([string]$Pkg) {
  if ($Pkg -notmatch '^@[^/]+/') { return $false }
  $scope = $Pkg.Split('/')[0]
  $cfg = (& npm config get "${scope}:registry" 2>$null | Select-Object -First 1)
  if (-not $cfg -or $cfg -eq 'undefined') { return $false }
  return ("$cfg".TrimEnd('/') -ne 'https://registry.npmjs.org')
}

# npm install -g always re-downloads and re-installs, even if the same version
# is already present. This is slow for a synchronous session hook and also
# re-triggers package lifecycle scripts. Check first, install only when needed.
# Stay silent on the happy path: Claude Code surfaces ANY stderr from an
# exit-0 SessionStart hook as "Failed with non-blocking status code",
# which is misleading. Capture install output and only emit on failure.
function Confirm-NpmPackage([string]$Pkg) {
  if ((Test-LinkedPackage $Pkg) -or (Test-FromOtherFeed $Pkg)) { return }

  & npm ls -g $Pkg --depth=0 *> $null
  if ($LASTEXITCODE -eq 0) {
    $outdated = (& npm outdated -g $Pkg $script:UipathRegistryFlag 2>$null | Out-String).Trim()
    if (-not $outdated) { return }
  }

  $output = (& npm install -g $script:UipathRegistryFlag $Pkg 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine("Failed to install ${Pkg}:")
    [Console]::Error.WriteLine($output)
    [Console]::Error.WriteLine("Please run manually: npm install -g $($script:UipathRegistryFlag) $Pkg")
    exit 2
  }
}

# ── main ─────────────────────────────────────────────────────────────
Confirm-Npm
Confirm-NpmPackage '@uipath/cli'
Confirm-NpmPackage '@uipath/rpa-tool'
exit 0
