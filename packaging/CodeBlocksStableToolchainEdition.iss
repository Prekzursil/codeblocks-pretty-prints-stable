#define AppName "Code::Blocks Stable Toolchain Edition"
#define AppVersion "0.1.0"
#define AppPublisher "Prekzursil"
#define AppURL "https://github.com/Prekzursil/codeblocks-pretty-prints-stable"
#define AppIdGuid "B1B93FD8-5B7B-4A2A-93DB-4A6D5F5D8B15"

#define EditionInstallRoot "{autopf}\CodeBlocks Stable Toolchain Edition"
#define EditionGroupName "Code::Blocks Stable Toolchain Edition"
#define ManagedBackupRoot "{commonappdata}\CodeBlocks Stable Toolchain Edition\Backups"
#define RuntimePayloadRoot "{tmp}\CodeBlocksStableToolchainEdition"
#define RuntimeProfileSeedRoot "{tmp}\CodeBlocksStableToolchainEdition\ProfileSeed"
#define RuntimeOverlayRoot "{tmp}\CodeBlocksStableToolchainEdition\Overlay"

[Setup]
AppId={{#AppIdGuid}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={#EditionInstallRoot}
DefaultGroupName={#EditionGroupName}
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
OutputBaseFilename=codeblocks-pretty-prints-stable-setup
OutputDir=..\dist\installer
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes
MinVersion=10.0
UsePreviousAppDir=no
UsePreviousGroup=no
CloseApplications=no
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\codeblocks.exe
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName}
VersionInfoProductName={#AppName}
VersionInfoProductVersion={#AppVersion}
SetupLogging=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop icon"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: addtopath; Description: "Add the bundled MinGW tools to PATH (not recommended)"; GroupDescription: "Advanced options:"; Flags: unchecked

[Dirs]
Name: "{app}"
Name: "{app}\release"
Name: "{commonappdata}\CodeBlocks Stable Toolchain Edition"
Name: "{commonappdata}\CodeBlocks Stable Toolchain Edition\Backups"

[Files]
; Main application payload. The staged payload is expected to be produced by the
; fetch-and-package lane and copied into the repository build staging area.
Source: "..\dist\payload\CodeBlocks\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Release metadata and notices may be staged alongside the application payload
; so they are available next to the installed edition for support and audits.
Source: "..\dist\release-assets\*"; DestDir: "{app}\release"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; Helper scripts are included for backup/migration handling during install.
Source: "scripts\Backup-LegacyProfile.ps1"; DestDir: "{#RuntimePayloadRoot}"; Flags: ignoreversion
Source: "scripts\Install-ManagedProfile.ps1"; DestDir: "{#RuntimePayloadRoot}"; Flags: ignoreversion

; Seed and overlay inputs are bundled so the installer can seed the profile
; without depending on the build machine layout.
Source: "..\overlay\profile-seed\*"; DestDir: "{#RuntimeProfileSeedRoot}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "..\overlay\profile-replacements.json"; DestDir: "{#RuntimeOverlayRoot}"; Flags: ignoreversion skipifsourcedoesntexist

[Registry]
Root: HKCU; Subkey: "Software\CodeBlocks"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\CodeBlocks\StableToolchainEdition"; ValueType: string; ValueName: "InstallRoot"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\MinGW\bin"; Tasks: addtopath; Flags: preservestringtype

[Icons]
Name: "{group}\Code::Blocks Stable Toolchain Edition"; Filename: "{app}\codeblocks.exe"
Name: "{commondesktop}\Code::Blocks Stable Toolchain Edition"; Filename: "{app}\codeblocks.exe"; Tasks: desktopicon

[Code]
const
  LegacyRegistryKey = 'Software\CodeBlocks';
  LegacyUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\CodeBlocks';
  LegacyProfileRoot = '%APPDATA%\CodeBlocks';

var
  DetectedLegacyInstallPath: string;
  RemoveLegacyInstall: Boolean;
  DetectedLegacyProfilePath: string;

function NormalizePath(const Value: string): string;
begin
  Result := Trim(Value);
  while (Length(Result) > 0) and (Result[Length(Result)] = '\') do
    Delete(Result, Length(Result), 1);
end;

function ReadRegistryString(RootKey: Integer; const SubKey, ValueName: string): string;
begin
  if not RegQueryStringValue(RootKey, SubKey, ValueName, Result) then
    Result := '';
end;

function DetectLegacyInstallPath(): string;
begin
  Result := ReadRegistryString(HKCU, LegacyRegistryKey, 'Path');
  if Result = '' then
    Result := ReadRegistryString(HKLM64, LegacyUninstallKey, 'InstallLocation');
  if Result = '' then
    Result := ReadRegistryString(HKLM, LegacyUninstallKey, 'InstallLocation');
  Result := NormalizePath(Result);
end;

function DetectLegacyProfilePath(): string;
begin
  Result := ExpandConstant(LegacyProfileRoot);
  Result := NormalizePath(Result);
end;

function AppDataBackupRoot(): string;
begin
  Result := ExpandConstant('{#ManagedBackupRoot}');
end;

function InstallToolsRoot(): string;
begin
  Result := ExpandConstant('{#RuntimePayloadRoot}');
end;

function AskAboutLegacyInstall(const LegacyPath: string): Boolean;
begin
  Result := True;
  if LegacyPath = '' then
    Exit;

  Result := MsgBox(
    'An existing official Code::Blocks installation was detected at:'#13#10#13#10 +
    LegacyPath + #13#10#13#10 +
    'Do you want this installer to replace that installation after it backs up your current profile?',
    mbConfirmation, MB_YESNO) = IDYES;
end;

function BackupPreinstallProfile(const SourceProfilePath, BackupRoot: string): Boolean;
var
  ExecResultCode: Integer;
begin
  Result := Exec(
    ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    '-NoProfile -ExecutionPolicy Bypass -File "' + InstallToolsRoot() + '\Backup-LegacyProfile.ps1"' +
    ' -SourceProfilePath "' + SourceProfilePath + '"' +
    ' -BackupRoot "' + BackupRoot + '"' +
    ' -EditionName "' + 'Code::Blocks Stable Toolchain Edition' + '"',
    '', SW_HIDE, ewWaitUntilTerminated, ExecResultCode);
  if Result and (ExecResultCode <> 0) then
    Result := False;
end;

function SeedManagedProfile(const SourceProfilePath, TargetProfilePath, OldInstallRoot, NewInstallRoot: string): Boolean;
var
  ExecResultCode: Integer;
begin
  Result := Exec(
    ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe'),
    '-NoProfile -ExecutionPolicy Bypass -File "' + InstallToolsRoot() + '\Install-ManagedProfile.ps1"' +
    ' -SourceProfilePath "' + SourceProfilePath + '"' +
    ' -TargetProfilePath "' + TargetProfilePath + '"' +
    ' -OldInstallRoot "' + OldInstallRoot + '"' +
    ' -NewInstallRoot "' + NewInstallRoot + '"' +
    ' -BackupRoot "' + AppDataBackupRoot() + '"' +
    ' -OverlayRoot "' + ExpandConstant('{#RuntimeOverlayRoot}') + '"',
    '', SW_HIDE, ewWaitUntilTerminated, ExecResultCode);
  if Result and (ExecResultCode <> 0) then
    Result := False;
end;

procedure InitializeWizard();
begin
  DetectedLegacyInstallPath := DetectLegacyInstallPath();
  DetectedLegacyProfilePath := DetectLegacyProfilePath();
  RemoveLegacyInstall := AskAboutLegacyInstall(DetectedLegacyInstallPath);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  NewProfilePath: string;
  OldInstallRoot: string;
begin
  if CurStep = ssInstall then
  begin
    ForceDirectories(AppDataBackupRoot());
    ForceDirectories(InstallToolsRoot());
  end;

  if CurStep = ssPostInstall then
  begin
    NewProfilePath := ExpandConstant('{userappdata}\CodeBlocks');
    if DetectedLegacyProfilePath <> '' then
      if not BackupPreinstallProfile(DetectedLegacyProfilePath, AppDataBackupRoot()) then
        Log('Legacy profile backup returned a non-zero exit code.');
    if DetectedLegacyInstallPath <> '' then
      OldInstallRoot := DetectedLegacyInstallPath
    else
      OldInstallRoot := ExpandConstant('{app}');
    if not SeedManagedProfile(
      ExpandConstant('{#RuntimeProfileSeedRoot}'),
      NewProfilePath,
      OldInstallRoot,
      ExpandConstant('{app}')) then
      Log('Managed profile seeding returned a non-zero exit code.');

    if RemoveLegacyInstall and (DetectedLegacyInstallPath <> '') and
       (CompareText(NormalizePath(DetectedLegacyInstallPath), NormalizePath(ExpandConstant('{app}'))) <> 0) then
    begin
      if DirExists(DetectedLegacyInstallPath) then
        DelTree(DetectedLegacyInstallPath, True, True, True);
    end;
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

