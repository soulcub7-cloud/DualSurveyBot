@echo off
setlocal
cd /d "%~dp0"

set "LMS_PORT=8000"
:check_port
netstat -ano | findstr /R /C:":%LMS_PORT% .*LISTENING" >nul
if errorlevel 1 goto port_ready
set /a LMS_PORT+=1
goto check_port

:port_ready
echo Starting CT Assembly Learning Hub on port %LMS_PORT%...

where py >nul 2>nul
if not errorlevel 1 goto run_py

where python >nul 2>nul
if not errorlevel 1 goto run_python

echo Python 3 was not found.
echo Install Python and enable Add python.exe to PATH.
pause
exit /b 1

:run_py
start "CT Assembly Learning Hub Server - port %LMS_PORT%" cmd /k py -3 app.py --port=%LMS_PORT%
goto open_site

:run_python
start "CT Assembly Learning Hub Server - port %LMS_PORT%" cmd /k python app.py --port=%LMS_PORT%

:open_site
timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:%LMS_PORT%
endlocal
