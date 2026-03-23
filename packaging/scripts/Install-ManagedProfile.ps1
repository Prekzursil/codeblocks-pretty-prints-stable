[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceProfilePath,

    [Parameter(Mandatory = $true)]
    [string]$TargetProfilePath,

    [Parameter(Mandatory = $true)]
    [string]$OldInstallRoot,

    [Parameter(Mandatory = $true)]
    [string]$NewInstallRoot,

    [Parameter(Mandatory = $true)]
    [string]$BackupRoot,

    [Parameter(Mandatory = $true)]
    [string]$OverlayRoot
)

$ErrorActionPreference = 'Stop'

$textExtensions = @(
    '.conf', '.ini', '.json', '.md', '.txt', '.xml', '.script', '.gdb', '.yml', '.yaml', '.iss'
)

function Get-SafePathText {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($OldInstallRoot) -or [string]::IsNullOrWhiteSpace($NewInstallRoot)) {
        return $Text
    }

    $normalizedOld = $OldInstallRoot.TrimEnd('\')
    $normalizedNew = $NewInstallRoot.TrimEnd('\')
    $normalizedText = $Text.Replace($normalizedOld, $normalizedNew)
    return $normalizedText.Replace($normalizedOld.ToUpperInvariant(), $normalizedNew).Replace($normalizedOld.ToLowerInvariant(), $normalizedNew)
}

function Ensure-ParentDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
}

function Backup-ExistingProfile {
    if (-not (Test-Path -LiteralPath $TargetProfilePath)) {
        return $null
    }

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $safeStamp = $stamp + '-existing-profile'
    $backupPath = Join-Path $BackupRoot $safeStamp
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

    Copy-Item -LiteralPath $TargetProfilePath -Destination $backupPath -Recurse -Force
    return $backupPath
}

function Copy-SeedTree {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing managed profile seed root: $Source"
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    Get-ChildItem -LiteralPath $Source -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($Source.Length).TrimStart('\')
        $target = Join-Path $Destination $relative
        Ensure-ParentDirectory -Path $target

        if ($textExtensions -contains $_.Extension.ToLowerInvariant()) {
            $content = Get-Content -LiteralPath $_.FullName -Raw
            $content = $content -replace [regex]::Escape($OldInstallRoot), $NewInstallRoot
            $content = Get-SafePathText -Text $content
            Set-Content -LiteralPath $target -Value $content -Encoding UTF8
        }
        else {
            Copy-Item -LiteralPath $_.FullName -Destination $target -Force
        }
    }
}

function Apply-OverlayReplacements {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Root
    )

    $replacementMap = Join-Path $OverlayRoot 'profile-replacements.json'
    if (-not (Test-Path -LiteralPath $replacementMap)) {
        return
    }

    $map = Get-Content -LiteralPath $replacementMap -Raw | ConvertFrom-Json
    foreach ($entry in @($map.replacements)) {
        $relative = [string]$entry.path
        $search = [string]$entry.search
        $replace = [string]$entry.replace
        if ([string]::IsNullOrWhiteSpace($relative) -or [string]::IsNullOrWhiteSpace($search)) {
            continue
        }

        $target = Join-Path $Root $relative
        if (-not (Test-Path -LiteralPath $target)) {
            continue
        }

        $content = Get-Content -LiteralPath $target -Raw
        $content = $content.Replace($search, $replace)
        Set-Content -LiteralPath $target -Value $content -Encoding UTF8
    }
}

$backupPath = Backup-ExistingProfile
Remove-Item -LiteralPath $TargetProfilePath -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $TargetProfilePath -Force | Out-Null

Copy-SeedTree -Source $SourceProfilePath -Destination $TargetProfilePath
Apply-OverlayReplacements -Root $TargetProfilePath

@{
    edition = 'Code::Blocks Stable Toolchain Edition'
    source_profile_seed = $SourceProfilePath
    target_profile = $TargetProfilePath
    old_install_root = $OldInstallRoot
    new_install_root = $NewInstallRoot
    previous_profile_backup = $backupPath
    overlay_root = $OverlayRoot
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $TargetProfilePath 'managed-profile-manifest.json') -Encoding UTF8

Write-Host "Installed managed Code::Blocks profile to $TargetProfilePath"

