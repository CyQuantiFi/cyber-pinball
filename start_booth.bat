@echo off
rem Threat Tide - start the whole booth in the right order.
rem Back screen and leaderboard first, the table last, so Visual Pinball has
rem keyboard focus and the flippers work without clicking anything.
rem
rem VPX_EXE  path to Visual Pinball X (64-bit)
rem TABLE    path to ThreatTide.vpx
rem USE_LEADERBOARD  1 if a separate leaderboard monitor is attached
set VPX_EXE=C:\vPinball\VisualPinball\VPinballX64.exe
set TABLE=C:\vPinball\VisualPinball\Tables\ThreatTide.vpx
set USE_LEADERBOARD=0

call "%~dp0backglass\start_backglass.bat"
if "%USE_LEADERBOARD%"=="1" call "%~dp0leaderboard\start_leaderboard.bat"
rem give the browser windows a moment to open before VPX takes focus
timeout /t 4 /nobreak >nul
start "" "%VPX_EXE%" -play "%TABLE%"
