@echo off
REM Activates the Conda environment
call conda activate iavtuber

REM Runs the Python script server.py
python server.py

REM Keeps the window open after execution
pause
