<#
  Launches `uip rpa debug start` in the background and polls debug.out until the session
  suspends (breakpoint / unhandled exception) or finishes. On a suspend the session stays
  active — drive it with `uip rpa debug continue*` / `step-*` / `execution cancel`, and
  read debug.out for the streamed state (exception details are on the `[Debug] Exception:` line).

  Usage (after copying into the project dir): powershell -ExecutionPolicy Bypass -File debug-run.ps1 <file-path> [extra uip args, e.g. --input-arguments '<json>']
#>
param(
  [Parameter(Mandatory = $true)][string]$FilePath,
  [Parameter(ValueFromRemainingArguments = $true)]$Rest
)
$ErrorActionPreference = 'Stop'
$out = 'debug.out'; '' | Set-Content $out

# Start-Process joins -ArgumentList into one unquoted command line, which the .cmd shim's
# cmd.exe re-parses — quote elements containing whitespace, quotes, or cmd metacharacters
# (MSVCRT convention: double backslashes preceding a quote, escape embedded quotes).
function Format-CmdArg([string]$a) {
  if ($a -notmatch '[\s"&|<>^()]') { return $a }
  $e = $a -replace '(\\*)"', '$1$1\"'
  $e = $e -replace '(\\+)$', '$1$1'
  '"' + $e + '"'
}

# Run uip in a separate process so the helper can return while a suspended session stays alive.
$uip = (Get-Command uip.cmd -ErrorAction Stop).Source
$extra = if ($null -ne $Rest) { @($Rest) } else { @() }   # $Rest is $null without extra args
$uipArgs = @('rpa', 'debug', 'start', '--file-path', (Format-CmdArg $FilePath)) +
           ($extra | ForEach-Object { Format-CmdArg $_ }) + @('--output', 'json')
$p = Start-Process $uip -ArgumentList $uipArgs -NoNewWindow -PassThru `
       -RedirectStandardOutput $out -RedirectStandardError "$out.err"

while (-not (Select-String -Path $out -Pattern '\[Debug\] Suspended|"hasErrors"' -Quiet -ErrorAction SilentlyContinue)) {
  if ($p.HasExited) { break }   # completed or failed early
  Start-Sleep -Seconds 1
}
Get-Content $out -Tail 40
# Environment-level failures land on stderr — surface them.
if ((Test-Path "$out.err") -and (Get-Item "$out.err").Length -gt 0) {
  Write-Output "--- stderr ($out.err) ---"
  Get-Content "$out.err" -Tail 20
}
