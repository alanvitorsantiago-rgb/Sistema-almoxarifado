@echo off
chcp 65001 > nul

REM Navega para o diretorio onde o script .bat esta localizado para garantir que os caminhos relativos funcionem.
cd /d "%~dp0"

echo =========================================
echo    INICIANDO SCRIPT DE BACKUP AUTOMATICO
echo =========================================

set "BACKUP_DIR=.\backups"
set "DB_FILE=.\database.db"

REM --- Verifica se a pasta de backups existe ---
if not exist "%BACKUP_DIR%" (
    echo.
    echo Pasta 'backups' nao encontrada.
    echo Criando pasta em: %BACKUP_DIR%
    mkdir "%BACKUP_DIR%"
    if errorlevel 1 (
        echo.
        echo X ERRO: Nao foi possivel criar a pasta de backups. >> backup_log.txt
        exit /b 1
    )
    echo Pasta 'backups' criada com sucesso.
)

REM --- Verifica se o arquivo do banco de dados existe ---
if not exist "%DB_FILE%" (
    echo.
    echo X ERRO: Arquivo do banco de dados (database.db) nao encontrado. >> backup_log.txt
    exit /b 1
)

echo.
echo Arquivo do banco de dados encontrado.

REM --- Gera o nome do arquivo de backup com data e hora ---
REM Formato: YYYY-MM-DD_HH-MM-SS
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set DATETIME_STR=%%I
set "TIMESTAMP=%DATETIME_STR:~0,4%-%DATETIME_STR:~4,2%-%DATETIME_STR:~6,2%_%DATETIME_STR:~8,2%-%DATETIME_STR:~10,2%-%DATETIME_STR:~12,2%"

REM --- Verifica se o comando wmic funcionou ---
if not defined DATETIME_STR (
    echo.
    echo X ERRO: Nao foi possivel obter a data e hora do sistema via WMIC. >> backup_log.txt
    exit /b 1
)

set "BACKUP_FILENAME=database_backup_%TIMESTAMP%.db"
set "BACKUP_PATH=%BACKUP_DIR%\%BACKUP_FILENAME%"

echo Gerando backup com o nome: %BACKUP_FILENAME%

REM --- Copia o arquivo do banco de dados ---
copy "%DB_FILE%" "%BACKUP_PATH%"

if errorlevel 1 (
    echo.
    echo X ERRO: Falha ao copiar o arquivo do banco de dados. >> backup_log.txt
) else (
    echo.
    echo ====================================================
    echo   BACKUP REALIZADO COM SUCESSO!
    echo   Arquivo salvo em: %BACKUP_PATH%
    echo ====================================================
)

exit /b 0