#!/usr/bin/env pwsh
# Convert a generated SDD markdown file to a styled Word document.
# PowerShell twin of sdd-to-docx.sh — keep behavior IDENTICAL (change both together).
# Works on Windows PowerShell 5.1 and PowerShell 7+. Requires pandoc on PATH.
# Optional --reference-doc <template.docx> applies a corporate style.
#
# Usage: sdd-to-docx.ps1 <sdd.md> [output.docx] [--reference-doc <template.docx>]
#   output.docx defaults to <input-basename>.docx in the current directory
#
# Known limitation: mermaid code blocks are NOT rendered — they appear as code.
#
# Exit codes: 0 success | 1 usage error | 2 pandoc missing | 3 conversion failed

function Write-Err($msg) { [Console]::Error.WriteLine($msg) }

if ($args.Count -lt 1 -or $args[0] -eq '--help' -or $args[0] -eq '-h') {
  Write-Output "Usage: sdd-to-docx.ps1 <sdd.md> [output.docx] [--reference-doc <template.docx>]"
  Write-Output "Converts an SDD markdown file to .docx via pandoc, with table of contents."
  Write-Output "--reference-doc applies the styles of an existing Word document."
  if ($args.Count -lt 1) { exit 1 } else { exit 0 }
}

if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) {
  Write-Err "ERROR: pandoc is not installed."
  Write-Err "Install it, then re-run:"
  Write-Err "  Windows: winget install JohnMacFarlane.Pandoc"
  Write-Err "  macOS:   brew install pandoc"
  Write-Err "  Linux:   sudo apt-get install pandoc"
  exit 2
}

$inputPath = $args[0]
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) {
  Write-Err "ERROR: input file not found: $inputPath"
  exit 1
}

$base = Split-Path -Path $inputPath -Leaf
$stem = [System.IO.Path]::GetFileNameWithoutExtension($base)
$output = "$stem.docx"
$reference = ""

$i = 1
while ($i -lt $args.Count) {
  if ($args[$i] -eq '--reference-doc') {
    if (($i + 1) -ge $args.Count) { Write-Err "ERROR: --reference-doc needs a path"; exit 1 }
    $reference = $args[$i + 1]
    $i = $i + 2
  } else {
    $output = $args[$i]
    $i = $i + 1
  }
}

$pandocArgs = @($inputPath, '-f', 'gfm', '-t', 'docx', '--toc', '--toc-depth=2', '-o', $output)
if ($reference -ne "") {
  if (-not (Test-Path -LiteralPath $reference -PathType Leaf)) {
    Write-Err "ERROR: reference doc not found: $reference"
    exit 1
  }
  $pandocArgs += "--reference-doc=$reference"
}

& pandoc @pandocArgs
if ($LASTEXITCODE -ne 0) {
  Write-Err "ERROR: pandoc conversion failed for $inputPath"
  exit 3
}

Write-Output "Word document: $output"
if (Select-String -LiteralPath $inputPath -Pattern '```mermaid' -SimpleMatch -Quiet) {
  Write-Err "NOTE: mermaid diagrams are kept as code blocks, not rendered images."
  Write-Err "Render and place images separately if the deliverable needs visuals."
}
