#!/usr/bin/env bash
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Archivos estáticos
python manage.py collectstatic --no-input

# Solo crear migraciones si hay cambios
python manage.py makemigrations --check --noinput || python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear usuario admin solo si no existe
python manage.py crear_admin || echo "Admin ya existe o fallo tolerado"
python manage.py poblar_sap || echo "Datos basicos de sap agregados"
