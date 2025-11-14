#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Instalando dependências..."
pip install -r requirements.txt

echo "Executando migrações do banco de dados..."
flask db upgrade

echo "Build finalizado."