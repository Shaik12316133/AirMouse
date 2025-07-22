# AirMouse 🖐️🚀
Control your mouse using just your hand — no touch, no hardware, just your webcam.

AirMouse transforms your webcam into a touch-free mouse controller, using hand gestures powered by computer vision. It runs 100% in the background as a system tray app, giving you seamless control over your computer with simple finger movements.

---

## ✨ Features:
- 🖐️ Index Finger Movement = Mouse Movement
- ✊ Pinch Gesture for Click and Drag
- 📊 Adaptive Movement Speed
- 🛑 Toggle control ON/OFF from system tray
- ⚙️ Runs completely invisible — no OpenCV window
---

## 🚀 How to Use:
1. Install dependencies.
2. Run the Batch file.
3. Check your System tray for the icon.
4. Right click to enable or disable/exit.
   
```bash
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
