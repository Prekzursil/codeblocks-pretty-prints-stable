[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceProfilePath,

    [Parameter(Mandatory = $true)]
    [string]$BackupRoot,

    [Parameter(Mandatory = $true)]
    [string]$EditionName
)

$ErrorActionPreference = 'Stop'

function New-Timestamp {
    Get-Date -Format 'yyyyMMdd-HHmmss'
}

function Copy-ItemSafely {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return
    }

    $parent = Split-Path -Parent $Destination
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

$timestamp = New-Timestamp
$backupPath = Join-Path $BackupRoot (Join-Path $timestamp ($EditionName -replace '[\\/:*?"<>|]', '_'))
$files = @(
    'default.conf',
    'default.cbKeyBinder20.conf',
    'codesnippets.ini',
    'DragScroll.ini',
    'en_US_personaldictionary.dic'
)

New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

foreach ($file in $files) {
    $source = Join-Path $SourceProfilePath $file
    $destination = Join-Path $backupPath $file
    Copy-ItemSafely -Source $source -Destination $destination
}

$shareSource = Join-Path $SourceProfilePath 'share'
if (Test-Path -LiteralPath $shareSource) {
    $shareDestination = Join-Path $backupPath 'share'
    Copy-Item -LiteralPath $shareSource -Destination $shareDestination -Recurse -Force
}

@{
    edition = $EditionName
    source_profile = $SourceProfilePath
    backup_path = $backupPath
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backupPath 'backup-manifest.json') -Encoding UTF8

Write-Host "Backed up legacy Code::Blocks profile to $backupPath"


