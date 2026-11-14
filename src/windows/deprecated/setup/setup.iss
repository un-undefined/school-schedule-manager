[Setup]
AppName=WHS School Schedule Manager
AppVersion=1.0
DefaultDirName={autopf}\WHSSchoolScheduleManager
DefaultGroupName=WHS School Schedule Manager
OutputDir=useroutput
OutputBaseFilename=WHSSchoolScheduleManagerSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Create a shortcut to launch the app on computer startup"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Copy the main executable
Source: "app.whsssm\WHSSchoolScheduleManager.exe"; DestDir: "{app}"; Flags: ignoreversion

; Copy all internal files, including the default config
Source: "app.whsssm\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Copy default.config.json to %localappdata%\WHSSchoolScheduleManager
Source: "app.whsssm\_internal\default.config.json"; DestDir: "{localappdata}\WHSSchoolScheduleManager"; Flags: ignoreversion

; Create config.json by copying and renaming default.config.json in the same destination directory
Source: "app.whsssm\_internal\default.config.json"; DestName: "config.json"; DestDir: "{localappdata}\WHSSchoolScheduleManager"; Flags: ignoreversion

[Icons]
; Desktop Shortcut
Name: "{userdesktop}\WHS School Schedule Manager"; Filename: "{app}\WHSSchoolScheduleManager.exe"; Tasks: desktopicon

; Startup Shortcut
Name: "{userstartup}\WHS School Schedule Manager"; Filename: "{app}\WHSSchoolScheduleManager.exe"; Tasks: startup

[UninstallDelete]
; This tells the built-in uninstaller to clean up the %localappdata% files
Type: files; Name: "{localappdata}\WHSSchoolScheduleManager\default.config.json"
Type: files; Name: "{localappdata}\WHSSchoolScheduleManager\config.json"
Type: dirifempty; Name: "{localappdata}\WHSSchoolScheduleManager"