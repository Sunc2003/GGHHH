from django.core.management.base import BaseCommand
from apps.usuarios.models import SolicitudCodigo, DetalleCodigo, SolicitudAdjunto
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Elimina todas las solicitudes, adjuntos y detalles'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⚠️ Borrando solicitudes y datos asociados..."))

        # 1️⃣ Borrar en orden seguro
        SolicitudAdjunto.objects.all().delete()
        DetalleCodigo.objects.all().delete()
        SolicitudCodigo.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("✅ Todas las solicitudes y datos fueron eliminados."))

        # 2️⃣ (Opcional) Poblar usuarios de prueba
        User = get_user_model()
        if not User.objects.exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin123"
            )
            self.stdout.write(self.style.SUCCESS("👤 Usuario admin creado: admin@example.com / admin123"))
