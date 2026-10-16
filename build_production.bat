@echo off
setlocal
pushd "%~dp0"

set "LASER_PYTHON=%~dp0.venv\Scripts\python.exe"
set "PYINSTALLER_CONFIG_DIR=%~dp0build\pyinstaller-config"

if not exist "%LASER_PYTHON%" (
    echo ERROR: Project virtual environment was not found at .venv\Scripts\python.exe
    popd
    exit /b 1
)

"%LASER_PYTHON%" -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed in the project virtual environment.
    echo Install build dependencies with: .venv\Scripts\python.exe -m pip install -r requirements-build.txt
    popd
    exit /b 1
)

echo Running complete test suite before packaging...
"%LASER_PYTHON%" -m pytest -q
if errorlevel 1 (
    echo ERROR: Tests failed. Packaging stopped.
    popd
    exit /b 1
)

echo Building standalone Windows application...
"%LASER_PYTHON%" -m PyInstaller --noconfirm --clean LaserEstimate.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    popd
    exit /b 1
)

if not exist "%~dp0dist\LaserEstimate\LaserEstimate.exe" (
    echo ERROR: Expected executable was not created.
    popd
    exit /b 1
)

echo Build complete:
echo %~dp0dist\LaserEstimate\LaserEstimate.exe
popd
exit /b 0
