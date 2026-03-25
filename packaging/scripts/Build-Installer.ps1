[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot,

    [string]$Version = '0.1.0',

    [switch]$InstallIfMissing
)

$ErrorActionPreference = 'Stop'

function Resolve-Iscc {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $knownPaths = @(
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($path in $knownPaths) {
        if (Test-Path -LiteralPath $path) {
            return $path
        }
    }

    return $null
}

function Ensure-Iscc {
    $resolved = Resolve-Iscc
    if ($resolved) {
        return $resolved
    }

    if (-not $InstallIfMissing) {
        throw 'Inno Setup compiler (iscc.exe) was not found. Re-run with -InstallIfMissing or install JRSoftware.InnoSetup.'
    }

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'winget is not available to install Inno Setup automatically.'
    }

    winget install --id JRSoftware.InnoSetup --exact --silent --accept-package-agreements --accept-source-agreements

    $resolved = Resolve-Iscc
    if (-not $resolved) {
        throw 'Inno Setup installation completed but iscc.exe is still unavailable.'
    }
    return $resolved
}

$repo = Resolve-Path -LiteralPath $RepositoryRoot
$iscc = Ensure-Iscc
$scriptPath = Join-Path $repo 'packaging\CodeBlocksStableToolchainEdition.iss'

Push-Location (Join-Path $repo 'packaging')
try {
    & $iscc "/DAppVersion=$Version" $scriptPath
}
finally {
    Pop-Location
}

$installerPath = Join-Path $repo "dist\installer\codeblocks-pretty-prints-stable-$Version-setup.exe"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Expected installer output was not created: $installerPath"
}

Write-Output $installerPath
