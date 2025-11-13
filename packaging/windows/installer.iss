; Inno Setup script for Bank CSV Extractor
; Requires: Inno Setup 6.x (iscc.exe)

#define AppName "Bank CSV Extractor"
#define AppVersion "0.1.0"
#define AppPublisher "Bank CSV"
#define AppExe "BankCSV.exe"

[Setup]
AppId={{6C6B9F29-62C8-4B62-8F65-6F2A87E0B9E0}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=release\windows
OutputBaseFilename=BankCSV-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Install the PyInstaller output directory into {app}
Source: "..\..\dist\BankCSV\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
