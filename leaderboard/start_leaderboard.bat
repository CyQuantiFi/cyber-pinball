@echo off
rem Threat Tide - open the live leaderboard full screen on the second monitor.
rem
rem DATA_DIR must be the folder the table writes to: TT_DataDir in
rem table\tt_config.vbs, or VPX's User folder if TT_DataDir is "".
set DATA_DIR=C:\ThreatTide\data
rem Screen position of the second monitor (x,y). 1920,0 = right of a 1080p main screen.
set SCREEN_POS=1920,0

set PAGE=%~dp0index.html
set DATA=file:///%DATA_DIR:\=/%/ThreatTide_leaderboard.js

set BROWSER=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set BROWSER=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set BROWSER=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if "%BROWSER%"=="" if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set BROWSER=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe

if "%BROWSER%"=="" (
  echo Chrome or Edge not found. Open this in any browser, full screen:
  echo   %PAGE%?data=%DATA%
  pause
  exit /b 1
)

start "" "%BROWSER%" --kiosk --new-window --user-data-dir="%TEMP%\threattide-board" --window-position=%SCREEN_POS% --allow-file-access-from-files "file:///%PAGE:\=/%?data=%DATA%"
