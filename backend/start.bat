@echo off

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Create HLS output directory
if not exist "hls_output\" mkdir hls_output

REM Start the server
python main.py

pause
