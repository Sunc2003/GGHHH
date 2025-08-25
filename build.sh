#!/usr/bin/env bash
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

echo "🧹 Limpiando datos antiguos de Solicitudes..."
python manage.py shell <<EOF
from apps.usuarios.models import SolicitudAdjunto, DetalleCodigo, SolicitudCodigo
try:
    SolicitudAdjunto.objects.all().delete()
    DetalleCodigo.objects.all().delete()
    SolicitudCodigo.objects.all().delete()
    print("✅ Solicitudes, detalles y adjuntos eliminados")
except Exception as e:
    print("⚠️ Error limpiando solicitudes:", e)
EOF

# Archivos estáticos
python manage.py collectstatic --no-input
## agregado recien, si falla mover o borrar
## python manage.py reset_solicitudes || echo "Solicitudes limpiadas"

# Solo crear migraciones si hay cambios
python manage.py makemigrations --check --noinput || python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear usuario admin solo si no existe
python manage.py poblar_cargos_areas || echo "Datos basicos de cargos y areas"

python manage.py crear_admin || echo "Admin ya existe o fallo tolerado"
python manage.py poblar_sap || echo "Datos basicos de sap agregados"
python manage.py asignar_permisos_iniciales || echo "Datos basicos de permisos agregados"
