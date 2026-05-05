[Setup]
AppId={{C625C7B4-4EAD-4F11-BDC3-86335E34CD91}
AppName=Quartz
AppVersion=1.0.0
AppPublisher=GoldKit
DefaultDirName={localappdata}\Programs\GoldKit\Quartz
DefaultGroupName=GoldKit\Quartz
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=Quartz-Setup-v1.0.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\Quartz.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\Quartz\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\GoldKit\Quartz"; Filename: "{app}\Quartz.exe"
Name: "{autodesktop}\Quartz"; Filename: "{app}\Quartz.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Quartz.exe"; Description: "Launch Quartz"; Flags: nowait postinstall skipifsilent