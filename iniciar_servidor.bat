@echo off
REM Define o titulo da janela do console para facil identificacao.
TITLE Servidor do Sistema de Almoxarifado

echo ======================================================
echo  INICIANDO SERVIDOR DO SISTEMA DE ALMOXARIFADO
echo ======================================================
echo.

REM Navega para o diretorio onde o script .bat esta localizado.
cd /d "%~dp0"

echo Ativando o ambiente virtual (.venv)...
call .\.venv\Scripts\activate

echo Iniciando o servidor de desenvolvimento (Flask)...

REM Inicia a aplicacao Python. O servidor ficara ativo nesta janela.
REM O comando abaixo usa o Gunicorn, um servidor de produção.
REM O Render usará um comando parecido.
echo Servidor iniciado em http://127.0.0.1:8080
gunicorn --bind 0.0.0.0:8080 run:app

echo.
echo Servidor encerrado. Pressione qualquer tecla para fechar.
pause