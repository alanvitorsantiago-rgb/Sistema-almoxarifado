@echo off
TITLE Servidor de Desenvolvimento - Almoxarifado

echo ======================================================
echo      INICIANDO AMBIENTE DE DESENVOLVIMENTO
echo ======================================================
echo.

REM Navega para o diretorio onde o script .bat esta localizado.
cd /d "%~dp0"

REM --- VERIFICACAO DO AMBIENTE ---

REM Define o caminho para o Python portatil
set PYTHON_PORTABLE_PATH=.\python311\python.exe

REM Verifica se o Python portatil existe
if not exist "%PYTHON_PORTABLE_PATH%" (
    echo [ERRO] Python portatil nao encontrado em '.\python311\'.
    echo Por favor, baixe a versao "embeddable" do Python 3.11 e descompacte na pasta 'python311'.
    pause
    exit /b 1
)

REM --- CRIACAO DO AMBIENTE VIRTUAL ---
REM Para garantir 100% de consistencia, o ambiente virtual sera recriado
REM se um arquivo de 'lock' nao for encontrado.
if not exist .\.venv\Scripts\activate.bat (
    echo [INFO] Ambiente virtual invalido ou nao encontrado.
    
    REM Apaga o ambiente antigo, se existir, para garantir uma recriacao limpa.
    if exist .\.venv (
        echo [INFO] Removendo ambiente virtual antigo...
        rmdir /s /q .venv
    )

    echo [INFO] Criando novo ambiente virtual com Python 3.11...
    echo [INFO] Usando Python de: %PYTHON_PORTABLE_PATH%

    REM O Python 'embeddable' precisa de um arquivo _pth para o venv funcionar corretamente.
    echo import site > .\python311\python311._pth

    %PYTHON_PORTABLE_PATH% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
    echo [INFO] Ambiente virtual criado com sucesso. 

    REM Cria um arquivo de 'lock' para nao recriar o ambiente na proxima execucao.
    echo created > .\.venv\created.lock
)

REM --- EXECUCAO ---

echo [INFO] Ativando o ambiente virtual...
call .\.venv\Scripts\activate

echo [INFO] Instalando/Atualizando dependencias do 'requirements_local.txt'...
pip install -r requirements_local.txt

echo [INFO] Iniciando o servidor de desenvolvimento Flask...
python run.py

pause