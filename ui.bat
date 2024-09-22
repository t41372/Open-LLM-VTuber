@echo off
REM Ativa o ambiente Conda
call conda activate iavtuber

REM Executa o script Python ui.py com Streamlit
streamlit run ui.py

REM Mantém a janela aberta após a execução
cmd /k
