@echo off
rem Threat Tide - browser backglass on the cabinet's back screen.
rem Start this BEFORE Visual Pinball so VPX keeps keyboard focus (or use start_booth.bat).
rem
rem DATA_DIR    the folder the table writes to: TT_DataDir in table\tt_config.vbs
rem SCREEN_POS  top-left corner of the back screen, x,y (check Windows display settings)
rem IDLE_SECS   seconds in attract mode before the ad loop starts
set DATA_DIR=C:\ThreatTide\data
set SCREEN_POS=0,-1080
set IDLE_SECS=60

set PAGE=%~dp0index.html
set DATA=file:///%DATA_DIR:\=/%/

set BROWSER=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set BROWSER=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if "%BROWSER%"=="" if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set BROWSER=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe

if "%BROWSER%"=="" (
  echo Chrome or Edge not found.
  pause
  exit /b 1
)

start "" "%BROWSER%" --kiosk --new-window --user-data-dir="%TEMP%\threattide-backglass" ^
  --window-position=%SCREEN_POS% --allow-file-access-from-files ^
  --autoplay-policy=no-user-gesture-required --disable-features=Translate ^
  "file:///%PAGE:\=/%?data=%DATA%&idle=%IDLE_SECS%"
