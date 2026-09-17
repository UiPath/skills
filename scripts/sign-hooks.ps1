<#
.SYNOPSIS
Authenticode-sign the plugin's PowerShell hook scripts.

.DESCRIPTION
Signs every `hooks/*.ps1` in the repository and verifies each signature before
returning. Run on Windows only: `Set-AuthenticodeSignature` is not implemented
on the PowerShell 7 builds for macOS and Linux.

This is NOT the publish path. Released packages are signed by the Azure DevOps
release gate (`.pipelines/release-gate.yml`), which calls UiPath's signing
template: since the DigiCert delivery change the official certificate is never
exported, so it can only be used through an Azure DevOps service connection.
This script exists to exercise the packing and verification plumbing locally --
typically with `-SelfSigned` -- and as the fallback if a PFX-based backend is
ever reintroduced.

Signing happens at publish time and is never committed. The scripts in git stay
unsigned, so an editor never has to re-sign and a reviewer never sees a
signature block in a diff.

An Authenticode signature covers a file's exact bytes, which is why
.gitattributes marks hooks/* as -text: a checkout that rewrote LF to CRLF before
signing would produce a signature covering content no consumer receives.

Certificate resolution, in order of precedence:

  -PfxPath        A PFX/P12 file plus -PfxPassword. The portable option: works
                  with a certificate exported from Key Vault, issued by an
                  internal CA, or produced by ESRP.
  -Thumbprint     A certificate already present in the machine or user store,
                  for a runner where a prior step installed one.
  -SelfSigned     Generates a throwaway certificate and signs with it. FOR
                  PIPELINE TESTING ONLY — the resulting signature chains to
                  nothing and no consumer will trust it. Refuses to run unless
                  -AllowUntrusted is also passed, so it can never be reached by
                  a publish job that merely forgot to configure a credential.

.PARAMETER TimestampServer
RFC 3161 timestamp authority. Timestamping is what keeps a signature valid
after the signing certificate expires; without it every published package stops
verifying on the certificate's expiry date.

.EXAMPLE
./scripts/sign-hooks.ps1 -PfxPath cert.pfx -PfxPassword $env:CERT_PASSWORD

.EXAMPLE
./scripts/sign-hooks.ps1 -SelfSigned -AllowUntrusted
#>
[CmdletBinding(DefaultParameterSetName = 'Pfx')]
param(
    [Parameter(ParameterSetName = 'Pfx', Mandatory = $true)]
    [string]$PfxPath,

    [Parameter(ParameterSetName = 'Pfx')]
    [string]$PfxPassword,

    [Parameter(ParameterSetName = 'Store', Mandatory = $true)]
    [string]$Thumbprint,

    [Parameter(ParameterSetName = 'SelfSigned', Mandatory = $true)]
    [switch]$SelfSigned,

    [Parameter(ParameterSetName = 'SelfSigned')]
    [switch]$AllowUntrusted,

    [string]$TimestampServer = 'http://timestamp.digicert.com',

    [string]$HooksDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-HooksDirectory {
    if ($HooksDirectory) { return $HooksDirectory }
    $repoRoot = Split-Path -Parent $PSScriptRoot
    return (Join-Path $repoRoot 'hooks')
}

# A throwaway certificate, for proving the pipeline works before a real one is
# provisioned. Deliberately awkward to reach: the caller must ask for it AND
# acknowledge that the output is untrusted.
function New-TestCertificate {
    if (-not $AllowUntrusted) {
        throw '-SelfSigned produces a signature no consumer will trust. Pass -AllowUntrusted to confirm this is a pipeline test, not a publish.'
    }
    Write-Warning 'Signing with a SELF-SIGNED certificate. The result is valid for pipeline testing only and must never be published.'
    return New-SelfSignedCertificate `
        -Subject 'CN=UiPath Skills Hook Signing (TEST - DO NOT TRUST)' `
        -Type CodeSigningCert `
        -CertStoreLocation 'Cert:\CurrentUser\My' `
        -KeyUsage DigitalSignature `
        -KeyAlgorithm RSA `
        -KeyLength 2048
}

function Resolve-SigningCertificate {
    if ($PSCmdlet.ParameterSetName -eq 'SelfSigned') {
        return New-TestCertificate
    }

    if ($PSCmdlet.ParameterSetName -eq 'Store') {
        $found = Get-ChildItem -Path 'Cert:\' -Recurse -CodeSigningCert |
            Where-Object { $_.Thumbprint -eq $Thumbprint } |
            Select-Object -First 1
        if (-not $found) {
            throw "No code-signing certificate with thumbprint $Thumbprint found in the certificate store."
        }
        return $found
    }

    if (-not (Test-Path -LiteralPath $PfxPath)) {
        throw "Certificate file not found: $PfxPath"
    }
    # The X509Certificate2 constructor rather than `Get-PfxCertificate
    # -Password`: that parameter does not exist in Windows PowerShell 5.1, and
    # this script is documented to run under both hosts.
    #
    # PersistKeySet, not EphemeralKeySet: an ephemeral CNG key is not reachable
    # through the CryptoAPI path `Set-AuthenticodeSignature` uses, and signing
    # fails with "Keyset does not exist". The key lands in the runner's
    # per-user store, which is discarded with the runner; the PFX itself is
    # deleted by the caller either way.
    #
    # Exportable is deliberately NOT set — the private key signs and is never
    # written back out by this process.
    $resolved = (Resolve-Path -LiteralPath $PfxPath).ProviderPath
    return New-Object System.Security.Cryptography.X509Certificates.X509Certificate2(
        $resolved,
        $PfxPassword,
        [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::PersistKeySet)
}

function Assert-SignatureValid {
    param(
        [string]$Path,
        [bool]$TrustExpected
    )
    $signature = Get-AuthenticodeSignature -LiteralPath $Path

    if ($signature.Status -eq 'Valid') {
        return $signature
    }

    # A self-signed certificate chains to nothing, so the signature is present
    # and internally consistent but reports UnknownError/NotTrusted. That is the
    # expected outcome of a pipeline test and must not fail the run; every other
    # status is a real signing failure.
    if (-not $TrustExpected -and $signature.Status -eq 'UnknownError') {
        return $signature
    }

    throw "Signature verification failed for $Path : $($signature.Status) - $($signature.StatusMessage)"
}

function Invoke-Main {
    $hooksDir = Get-HooksDirectory
    if (-not (Test-Path -LiteralPath $hooksDir)) {
        throw "Hooks directory not found: $hooksDir"
    }

    $scripts = @(Get-ChildItem -LiteralPath $hooksDir -Filter '*.ps1' -File | Sort-Object Name)
    if ($scripts.Count -eq 0) {
        throw "No .ps1 files found in $hooksDir. Refusing to report success for a run that signed nothing."
    }

    $certificate = Resolve-SigningCertificate
    $trustExpected = $PSCmdlet.ParameterSetName -ne 'SelfSigned'
    Write-Host "Signing $($scripts.Count) hook script(s) with $($certificate.Subject)"
    Write-Host "Thumbprint: $($certificate.Thumbprint)"

    foreach ($script in $scripts) {
        $result = Set-AuthenticodeSignature `
            -LiteralPath $script.FullName `
            -Certificate $certificate `
            -HashAlgorithm SHA256 `
            -TimestampServer $TimestampServer `
            -IncludeChain All

        if ($result.Status -ne 'Valid' -and $trustExpected) {
            throw "Signing failed for $($script.Name): $($result.Status) - $($result.StatusMessage)"
        }

        $verified = Assert-SignatureValid -Path $script.FullName -TrustExpected $trustExpected
        Write-Host "  $($script.Name): $($verified.Status)"
    }

    Write-Host "Signed and verified $($scripts.Count) hook script(s)."
}

Invoke-Main
