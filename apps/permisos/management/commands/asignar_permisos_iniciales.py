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
        permisos_data =[
            {
                "codigo": "CREACION_USUARIO",
                "nombre": "Creación de Usuarios",
                "descripcion": "Permite registrar nuevos usuarios en el sistema y asignarles permisos correspondientes."
            },
            {
                "codigo": "ENVIAR_SOLICITUD",
                "nombre": "Solicitar Códigos",
                "descripcion": "Permite enviar solicitudes de creación de códigos SAP al área correspondiente."
            },
            {
                "codigo": "GESTIONAR_PERMISOS",
                "nombre": "Gestionar Permisos",
                "descripcion": "Permite crear, asignar, modificar y visualizar todos los permisos definidos en el sistema."
            },
            {
                "codigo": "PANEL_USUARIO",
                "nombre": "Acceso a Panel de Usuario",
                "descripcion": "Permite acceder al dashboard de usuarios."
            },
            {
                "codigo": "PROCESOS",
                "nombre": "Gestión de Procesos",
                "descripcion": "Permite visualizar, cargar y administrar procesos internos en la plataforma."
            },
            {
                "codigo": "SOLICITUD_CODIGO",
                "nombre": "Enviar Solicitudes de Código",
                "descripcion": "Permite a los usuarios enviar solicitudes al Data Master para la creación de nuevos códigos en SAP."
            },
            {
                "codigo": "VER_SOLICITUDES",
                "nombre": "Visualizar Solicitudes Enviadas",
                "descripcion": "Permite consultar el estado y detalle de las solicitudes de código enviadas por el usuario."
            },
            {
                "codigo": "VER_SOLICITUDES_RECIBIDAS",
                "nombre": "Visualizar Solicitudes Recibidas",
                "descripcion": "Permite al receptor revisar las solicitudes de creación de código asignadas a su área o usuario."
            },
            {
                "codigo": "VER_AD",
                "nombre": "Visualizar todos los usuarios del AD",
                "descripcion": "Permite ver la lista de todos los usuarios y poder acceder a su apartado de perfil y permisos."
            },
            {
                "codigo": "TICKETS_ACCESO_MENU",
                "nombre": "Acceso al módulo Tickets",
                "descripcion": "Permite acceder al módulo de Tickets y mostrar la opción en el menú."
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
