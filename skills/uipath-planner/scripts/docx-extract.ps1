#!/usr/bin/env pwsh
# Extract a .docx (typically a PDD) to GitHub-flavored Markdown.
# PowerShell twin of docx-extract.sh — keep behavior IDENTICAL (change both together).
# Works on Windows PowerShell 5.1 and PowerShell 7+. Requires pandoc on PATH.
#
# Usage: docx-extract.ps1 <input.docx> [output.md]
#   output.md defaults to <input-basename>.md in the current directory
#   embedded media lands in <output-basename>-media/
#
# Exit codes: 0 success | 1 usage error | 2 pandoc missing | 3 conversion failed

function Write-Err($msg) { [Console]::Error.WriteLine($msg) }

if ($args.Count -lt 1 -or $args[0] -eq '--help' -or $args[0] -eq '-h') {
  Write-Output "Usage: docx-extract.ps1 <input.docx> [output.md]"
  Write-Output "Converts a .docx to GitHub-flavored Markdown via pandoc."
  Write-Output "Embedded images are extracted to <output-basename>-media/."
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
if ($args.Count -ge 2) { $output = $args[1] } else { $output = "$stem.md" }
if ($output -match '\.md$') { $mediaDir = ($output -replace '\.md$', '-media') } else { $mediaDir = "$output-media" }

$pandocArgs = @($inputPath, '-f', 'docx', '-t', 'gfm', '--wrap=none', "--extract-media=$mediaDir", '-o', $output)
& pandoc @pandocArgs
if ($LASTEXITCODE -ne 0) {
  Write-Err "ERROR: pandoc conversion failed for $inputPath"
  exit 3
}

Write-Output "Markdown: $output"
if (Test-Path -LiteralPath $mediaDir -PathType Container) {
  $files = @(Get-ChildItem -LiteralPath $mediaDir -Recurse -File)
  Write-Output ("Media:    {0}/ ({1} file(s))" -f $mediaDir, $files.Count)
  $unreadable = @($files | Where-Object { $_.Extension -match '(?i)\.(emf|wmf)$' } | ForEach-Object { $_.FullName })
  if ($unreadable.Count -gt 0) {
    Write-Err ("WARNING: EMF/WMF media cannot be rendered by the Read tool: " + ($unreadable -join ' '))
    Write-Err "Ask the user for PNG exports of those figures, or mark dependent extractions [SME REVIEW]."
  }
} else {
  Write-Output "Media:    none embedded"
}
