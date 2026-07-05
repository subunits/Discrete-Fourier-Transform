@echo off
REM DFT Audio Visualizer - PyQt6 Installation Script (Windows)
REM Automates the migration from PyQt5 to PyQt6

setlocal enabledelayedexpansion

echo ==================================
echo DFT Visualizer Qt6 Installation
echo ==================================
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Step 1: Uninstall PyQt5
echo [Step 1] Removing PyQt5 (if installed)...
pip uninstall PyQt5 PyQt5-sip -y >nul 2>&1
if errorlevel 0 (
    echo [OK] PyQt5 removal complete
) else (
    echo [INFO] PyQt5 was not installed or already removed
)
echo.

REM Step 2: Install PyQt6 and dependencies
echo [Step 2] Installing PyQt6 and dependencies...
pip install -r requirements_qt6.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [OK] PyQt6 and dependencies installed
echo.

REM Step 3: Verify installation
echo [Step 3] Verifying installation...

REM Check PyQt6
python -c "from PyQt6 import QtCore; print('PyQt6 OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] PyQt6 imported successfully
) else (
    echo [ERROR] Failed to import PyQt6
    exit /b 1
)

REM Check PyQtGraph
python -c "import pyqtgraph; print('PyQtGraph OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] PyQtGraph imported successfully
) else (
    echo [ERROR] Failed to import PyQtGraph
    exit /b 1
)

REM Check numpy
python -c "import numpy; print('NumPy OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] NumPy imported successfully
) else (
    echo [ERROR] Failed to import NumPy
    exit /b 1
)

REM Check scipy
python -c "import scipy; print('SciPy OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] SciPy imported successfully
) else (
    echo [ERROR] Failed to import SciPy
    exit /b 1
)

REM Check sounddevice
python -c "import sounddevice; print('SoundDevice OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] SoundDevice imported successfully
) else (
    echo [ERROR] Failed to import SoundDevice
    exit /b 1
)

REM Check soundfile
python -c "import soundfile; print('SoundFile OK')" >nul 2>&1
if errorlevel 0 (
    echo [OK] SoundFile imported successfully
) else (
    echo [ERROR] Failed to import SoundFile
    exit /b 1
)

echo.
echo ==================================
echo Installation Successful!
echo ==================================
echo.
echo Next steps:
echo 1. Run tests: python test_dft_visualizer.py
echo 2. Start visualizer: python dft_visualizer_production_qt6.py
echo 3. Read guide: QT6_MIGRATION_GUIDE.md
echo.
echo For audio input, ensure:
echo - Microphone is connected and enabled
echo - Audio drivers are installed
echo - No other apps are using the microphone
echo.
pause
