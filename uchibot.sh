#!/bin/bash

VENV_PATH="./venv"

if [ -d "$VENV_PATH" ]; then
    echo "Virtual environment found. Activating..."
    source "$VENV_PATH/bin/activate"
else
    echo "Virtual environment not found. Creating a new one..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"
    echo "Virtual environment created and activated."
fi

pip install -r requirements.txt
python3 bot.py