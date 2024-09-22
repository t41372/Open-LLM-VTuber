@echo off
REM Ativa o ambiente Conda
call conda activate iavtuber

REM Executa o script Python server.py
python server.py

REM Mantém a janela aberta após a execução
pause
