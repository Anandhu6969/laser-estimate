@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "SPEC=%ROOT%installer\LaserEstimate.iss"
set "OUTPUT=%ROOT%installer\LaserEstimate_Setup.exe"

if not exist "%PYTHON%" (
    echo ERROR: Project Python environment not found: "%PYTHON%"
    exit /b 1
)
if not exist "%ROOT%dist\LaserEstimate\LaserEstimate.exe" (
    echo ERROR: PyInstaller distribution is missing. Build it first.
    exit /b 1
)

echo Running complete test suite...
"%PYTHON%" -m pytest -q
if errorlevel 1 (
    echo ERROR: Tests failed; installer was not built.
    exit /b 1
)

set "ISCC=%INNO_SETUP_ISCC%"
if not defined ISCC if exist "%ROOT%tools\InnoSetup\ISCC.exe" set "ISCC=%ROOT%tools\InnoSetup\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
    echo ERROR: Inno Setup compiler not found.
    echo Set INNO_SETUP_ISCC or install Inno Setup under tools\InnoSetup.
    exit /b 1
)

echo Building Windows installer...
"%ISCC%" "%SPEC%"
if errorlevel 1 exit /b 1
if not exist "%OUTPUT%" (
    echo ERROR: Expected installer output was not created: "%OUTPUT%"
    exit /b 1
)

echo Installer created: "%OUTPUT%"
exit /b 0
