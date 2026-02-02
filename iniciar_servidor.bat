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
call .\.venv\Scripts\activate || ( 
    echo ERRO: Nao foi possivel ativar o ambiente virtual. Verifique o caminho. 
    echo ERRO: Detalhes >> errorlog.txt
    echo ERRO: Nao foi possivel ativar o ambiente virtual. Verifique o caminho.
    pause
    exit /b 1
)

echo Iniciando o servidor de desenvolvimento (Flask)...
echo.
echo O navegador sera aberto automaticamente em http://127.0.0.1:5000
echo Para acessar de outro computador na mesma rede, use o IP: http://192.168.1.62:5000

REM Aguarda 3 segundos para dar tempo ao servidor iniciar antes de abrir o navegador.
timeout /t 3 /nobreak > nul
start http://127.0.0.1:5000

REM Inicia o ngrok em uma nova janela para criar o tunel publico.
echo Iniciando o tunel ngrok...
start "ngrok" ngrok http 5000

REM Inicia a aplicacao Flask diretamente com Python para garantir que o bloco __main__ seja executado.
python app.py

echo.
echo Servidor encerrado. Pressione qualquer tecla para fechar.
pause