#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

FLASK_APP=run.py flask db upgrade
