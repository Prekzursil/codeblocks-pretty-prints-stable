[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot,

    [string]$Version = '0.1.0',

    [string]$SourceInstallRoot = 'C:\Program Files\CodeBlocks',

    [switch]$InstallInnoSetupIfMissing,

    [switch]$CreateGitHubRelease
)

$ErrorActionPreference = 'Stop'

function Resolve-Python {
    $candidates = @('python', 'python3', 'py')
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            if ($candidate -eq 'py') {
                return [pscustomobject]@{
                    Command = $command.Source
                    PrefixArgs = @('-3')
                }
            }
            return [pscustomobject]@{
                Command = $command.Source
                PrefixArgs = @()
            }
        }
    }
    throw 'No Python launcher was found on PATH.'
}

$repo = Resolve-Path -LiteralPath $RepositoryRoot
$python = Resolve-Python
$distRoot = Join-Path $repo 'dist'

Push-Location $repo
try {
    & $python.Command @($python.PrefixArgs) -m scripts.codeblocks_release prepare-local-release `
        --repo-root $repo `
        --source-install-root $SourceInstallRoot `
        --version "v$Version" `
        --output-root $distRoot
}
finally {
    Pop-Location
}

$installerPath = & (Join-Path $repo 'packaging\scripts\Build-Installer.ps1') `
    -RepositoryRoot $repo `
    -Version $Version `
    -InstallIfMissing:$InstallInnoSetupIfMissing

$releaseAssetsRoot = Join-Path $distRoot 'release-assets'
$publishRoot = Join-Path $distRoot 'publish'

& (Join-Path $repo 'packaging\scripts\Stage-ReleaseAssets.ps1') `
    -InstallerPath $installerPath `
    -ManifestPath (Join-Path $releaseAssetsRoot 'release-manifest.json') `
    -NoticesPath (Join-Path $releaseAssetsRoot 'THIRD_PARTY_NOTICES.md') `
    -OutputRoot $publishRoot `
    -SbomPath (Join-Path $releaseAssetsRoot 'sbom.json') `
    -AttestationPath (Join-Path $releaseAssetsRoot 'provenance.json') `
    -ReleaseNotesPath (Join-Path $releaseAssetsRoot "RELEASE_NOTES_v$Version.md") `
    -NoticeDirectory (Join-Path $releaseAssetsRoot 'notices')

if ($CreateGitHubRelease) {
    $tag = "v$Version"
    $existingTag = git -C $repo tag --list $tag
    if (-not $existingTag) {
        git -C $repo tag -a $tag -m "Release $tag`n`nCo-authored-by: Codex <noreply@openai.com>"
        git -C $repo push origin $tag
    }

    $releaseAssets = Get-ChildItem -LiteralPath $publishRoot -Recurse -File | ForEach-Object { $_.FullName }
    gh release create $tag @releaseAssets --repo Prekzursil/codeblocks-pretty-prints-stable `
        --title "Code::Blocks Stable Toolchain Edition $tag" `
        --notes-file (Join-Path $releaseAssetsRoot "RELEASE_NOTES_v$Version.md")
}

Write-Output $publishRoot
