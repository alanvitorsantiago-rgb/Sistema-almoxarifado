@echo off
title Gerenciamento de Almoxarifado

echo ======================================================
echo      INICIANDO SERVIDOR DO SISTEMA DE ALMOXARIFADO
echo ======================================================
echo.

echo Ativando o ambiente virtual...
call .\.venv\Scripts\activate

echo O servidor esta sendo iniciado. Aguarde a mensagem com o endereco de acesso...
python run.py

pause