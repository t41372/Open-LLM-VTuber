@echo off
REM Check if the Conda environment openllmvtuber exists
conda env list | findstr "openllmvtuber" >nul
IF %ERRORLEVEL% EQU 0 (
    REM Environment exists, activate it
    echo Environment openllmvtuber already exists. Activating it...
) ELSE (
    REM Create a Conda environment named openllmvtuber
    echo Creating Conda environment openllmvtuber...
    conda create --name openllmvtuber python=3.10 -y
)

REM Activate the environment
call conda activate openllmvtuber

REM Change to the requirements directory
cd requirements

REM Install the dependencies listed in requirements.txt
pip install -r requirements.txt

REM Go back to the previous directory
cd ..

REM Execute the ui.bat file
start ui.bat
