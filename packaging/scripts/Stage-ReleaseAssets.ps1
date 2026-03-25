[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallerPath,

    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,

    [Parameter(Mandatory = $true)]
    [string]$NoticesPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputRoot,

    [string]$SbomPath,
    [string]$AttestationPath,
    [string]$ReleaseNotesPath,
    [string]$NoticeDirectory
)

$ErrorActionPreference = 'Stop'

function Copy-RequiredFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Required release asset missing: $Source"
    }

    $parent = Split-Path -Parent $Destination
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

$assets = @(
    @{ Source = $InstallerPath; Destination = (Join-Path $OutputRoot (Split-Path -Leaf $InstallerPath)) },
    @{ Source = $ManifestPath; Destination = (Join-Path $OutputRoot (Split-Path -Leaf $ManifestPath)) },
    @{ Source = $NoticesPath; Destination = (Join-Path $OutputRoot (Split-Path -Leaf $NoticesPath)) }
)

foreach ($asset in $assets) {
    Copy-RequiredFile -Source $asset.Source -Destination $asset.Destination
}

if ($SbomPath) {
    if (Test-Path -LiteralPath $SbomPath) {
        Copy-Item -LiteralPath $SbomPath -Destination (Join-Path $OutputRoot (Split-Path -Leaf $SbomPath)) -Force
    }
}

if ($AttestationPath) {
    if (Test-Path -LiteralPath $AttestationPath) {
        Copy-Item -LiteralPath $AttestationPath -Destination (Join-Path $OutputRoot (Split-Path -Leaf $AttestationPath)) -Force
    }
}

if ($ReleaseNotesPath) {
    if (Test-Path -LiteralPath $ReleaseNotesPath) {
        Copy-Item -LiteralPath $ReleaseNotesPath -Destination (Join-Path $OutputRoot (Split-Path -Leaf $ReleaseNotesPath)) -Force
    }
}

if ($NoticeDirectory) {
    if (Test-Path -LiteralPath $NoticeDirectory) {
        Copy-Item -LiteralPath $NoticeDirectory -Destination (Join-Path $OutputRoot 'notices') -Recurse -Force
    }
}

$hashes = Get-ChildItem -LiteralPath $OutputRoot -Recurse -File | Sort-Object FullName | ForEach-Object {
    $hash = Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256
    [pscustomobject]@{
        file = $_.FullName.Substring($OutputRoot.Length).TrimStart('\', '/').Replace('\', '/')
        sha256 = $hash.Hash.ToLowerInvariant()
    }
}

$hashes | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OutputRoot 'sha256-manifest.json') -Encoding UTF8

$lines = foreach ($item in $hashes) {
    "{0} *{1}" -f $item.sha256, $item.file
}
$lines | Set-Content -LiteralPath (Join-Path $OutputRoot 'SHA256SUMS.txt') -Encoding ASCII

Write-Host "Staged release assets to $OutputRoot"

