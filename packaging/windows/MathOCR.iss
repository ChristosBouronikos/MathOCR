; MathOCR Windows installer by Bouronikos Christos <chrisbouronikos@gmail.com>.
; Support development: https://paypal.me/christosbouronikos

#define MyAppName "MathOCR"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Bouronikos Christos"
#define MyAppURL "https://paypal.me/christosbouronikos"
#define MyAppExeName "MathOCR.exe"

[Setup]
AppId={{CC0597D0-412E-49C8-BC45-7AE2C4CA02DD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=mailto:chrisbouronikos@gmail.com
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Resolve every relative path below from the repository root (this .iss lives in
; packaging\windows\), so LicenseFile, [Files] Source, and OutputDir all work
; regardless of the compiler's working directory.
SourceDir={#SourcePath}..\..
LicenseFile=LICENSE
OutputDir=dist
OutputBaseFilename=MathOCR-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\MathOCR\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
