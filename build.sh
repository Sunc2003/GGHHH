#!/usr/bin/env bash
# Exit on error
set -o errexit

# Instala dependencias
pip install -r requirements.txt

# Archivos estáticos
python manage.py collectstatic --no-input

# Crea migraciones si no existen
python manage.py makemigrations

# Aplica migraciones
python manage.py migrate

# Crea usuario admin predefinido (si tienes ese comando)
python manage.py crear_admin
