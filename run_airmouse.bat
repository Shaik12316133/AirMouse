@echo off
setlocal

REM === Check if Python is installed ===
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python not found! Installing Python...
    powershell -Command "Start-Process 'https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe' -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait"
    echo Python installed. Please restart this script.
    pause
    exit /b
)

REM === Check if pip is installed ===
python -m pip --version >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Pip not found! Installing pip...
    python -m ensurepip --default-pip
)

REM === Upgrade pip ===
python -m pip install --upgrade pip

REM === Install project dependencies ===
echo Installing required Python packages...
pip install opencv-python mediapipe pyautogui pystray pillow numpy

REM === Launch AirMouse ===
echo Starting AirMouse...
python app.py

pause
