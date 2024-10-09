@echo off
REM Activate the Conda environment
call conda activate openllmvtuber

REM Run the Python script ui.py with Streamlit
streamlit run ui.py

REM Keep the window open after execution
cmd /k
