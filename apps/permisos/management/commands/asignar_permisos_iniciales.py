from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.permisos.models import Permiso

class Command(BaseCommand):
    help = 'Crea los permisos iniciales y los asigna a usuarios específicos'

    def handle(self, *args, **options):
        User = get_user_model()

        # Usuarios a los que se asignarán los permisos
        usuarios_nombres = [
            "Alexssander Lopez",
            "Andres Jimenez",
            "Gonzalo Neira",
            "Millaray Esposito",
        ]

        # Permisos a crear/asignar
        permisos_data = [
            {
                "codigo": "GESTIONAR_PERMISOS",
                "nombre": "Gestionar Permisos",
                "descripcion": "Permite crear, asignar y visualizar todos los permisos"
            },
            {
                "codigo": "SOLICITUD_CODIGO",
                "nombre": "Enviar solicitudes de creación de códigos",
                "descripcion": "Permite a los vendedores enviar solicitudes al data master para la creación de nuevos códigos en SAP."
            }
        ]

        permisos_creados = []
        for data in permisos_data:
            permiso, creado = Permiso.objects.get_or_create(
                codigo=data["codigo"],
                defaults={"nombre": data["nombre"], "descripcion": data["descripcion"]}
            )
            permisos_creados.append(permiso)
            if creado:
                self.stdout.write(self.style.SUCCESS(f"✔ Permiso '{data['codigo']}' creado"))
            else:
                self.stdout.write(f"✓ Permiso '{data['codigo']}' ya existía")

        # Asignar permisos a usuarios
        for nombre in usuarios_nombres:
            try:
                usuario = User.objects.get(username=nombre)
                usuario.permisos_directos.add(*permisos_creados)
                self.stdout.write(self.style.SUCCESS(f"✅ Permisos asignados a {nombre}"))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Usuario '{nombre}' no encontrado"))
