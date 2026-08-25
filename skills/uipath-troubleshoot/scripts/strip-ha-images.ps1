<#
.SYNOPSIS
    Strips base64 image content from healing agent JSON files to reduce file size.
.DESCRIPTION
    Processes all JSON files in the specified directory (or current directory).
    Replaces AnalysisResult[].Images[].Content with a placeholder string.
    Original files are overwritten in place.
    Compatible with Windows PowerShell 5.1+ (ships with Windows 10/11).
.PARAMETER Path
    Directory containing healing agent JSON files. Defaults to current directory.
#>
param(
    [string]$Path = "."
)

$files = Get-ChildItem -Path $Path -Filter "*.json" -File

if ($files.Count -eq 0) {
    Write-Host "No JSON files found in $Path"
    exit 0
}

foreach ($file in $files) {
    try {
        $raw = Get-Content -Path $file.FullName -Raw
        $json = $raw | ConvertFrom-Json

        $modified = $false

        if ($json.Content -and $json.Content.AnalysisResult) {
            foreach ($result in $json.Content.AnalysisResult) {
                if ($result.Images) {
                    foreach ($image in $result.Images) {
                        if ($image.Content) {
                            $image.Content = "[base64 image removed]"
                            $modified = $true
                        }
                    }
                }
            }
        }

        if ($modified) {
            $depth = 100
            # Windows PowerShell 5.1 does not support -Depth on ConvertTo-Json; use default (no flag)
            if ($PSVersionTable.PSVersion.Major -ge 7) {
                $output = $json | ConvertTo-Json -Depth $depth
            } else {
                $output = $json | ConvertTo-Json -Depth $depth -ErrorAction SilentlyContinue
                if (-not $output) {
                    $output = $json | ConvertTo-Json
                }
            }
            [System.IO.File]::WriteAllText($file.FullName, $output, [System.Text.Encoding]::UTF8)
            Write-Host "Stripped images from $($file.Name)"
        }
    }
    catch {
        Write-Warning "Failed to process $($file.Name): $_"
    }
}
