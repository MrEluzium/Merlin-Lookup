@echo off

set VENV_PATH=.venv

if exist "%VENV_PATH%" (
    echo Virtual environment found. Activating...
    call "%VENV_PATH%\Scripts\activate"
) else (
    echo Virtual environment not found. Creating a new one...
    python -m venv "%VENV_PATH%"
    call "%VENV_PATH%\Scripts\activate"
    echo Virtual environment created and activated.
)

pip install -r requirements.txt
start python bot.py