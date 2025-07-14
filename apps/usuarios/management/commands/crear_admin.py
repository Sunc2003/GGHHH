from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.organizaciones.models import Area, Cargo

class Command(BaseCommand):
    help = 'Elimina y vuelve a crear usuarios administradores con todos sus campos'

    def handle(self, *args, **options):
        User = get_user_model()

        usuarios = [
            {
                "username": "Gonzalo Neira",
                "email": "gneira@ggh.cl",
                "password": "Manzana",
                "area": "Sistemas",
                "cargo": "LIDER RESPONSABLE ÁREA INFORMÁTICA",
                "usuario_ad": "GNEIRA",
                "usuario_office": "gneira@ggh.cl",
                "usuario_sap": "Gneira",
                "equipo_a_cargo": "Macbook Pro",
                "impresora_a_cargo": "HP TI",
                "movil": "+569 3131 4312"
            },
            {
                "username": "Andres Jimenez",
                "email": "ajimenez@ggh.cl",
                "password": "Manzana",
                "area": "Sistemas",
                "cargo": "JEFE DE INFRAESTRUCTURA Y SOPORTE TI",
                "usuario_ad": "AJIMENEZ",
                "usuario_office": "ajimenez@ggh.cl",
                "usuario_sap": "Sistemas",
                "equipo_a_cargo": "MacBook Pro",
                "impresora_a_cargo": "HP TI",
                "movil": "+569 8765 4321"
            },
            {
                "username": "Millaray Esposito",
                "email": "mesposito@ggh.cl",
                "password": "Manzana",
                "area": "Sistemas",
                "cargo": "ASISTENTE DE INFORMATICA",
                "usuario_ad": "SISTEMAS4",
                "usuario_office": "mesposito@ggh.cl",
                "usuario_sap": "practicante",
                "equipo_a_cargo": "MacBook Air",
                "impresora_a_cargo": "HP TI",
                "movil": "+569 1231 2312"
            },
            {
                "username": "Alexssander Lopez",
                "email": "alopez@ggh.cl",
                "password": "Manzana",
                "area": "Sistemas",
                "cargo": "ASISTENTE DE INFORMATICA",
                "usuario_ad": "SISTEMAS2",
                "usuario_office": "alopez@ggh.cl",
                "usuario_sap": "Sistemas",
                "equipo_a_cargo": "Macbook Pro",
                "impresora_a_cargo": "HP TI",
                "movil": "+569 3213 2132"
            },
        ]

        for u in usuarios:
            # Separar nombre completo
            nombre_split = u["username"].split()
            first_name = nombre_split[0]
            last_name = " ".join(nombre_split[1:]) if len(nombre_split) > 1 else ""

            # Buscar área y cargo
            try:
                area = Area.objects.get(nombre=u["area"])
                cargo = Cargo.objects.get(nombre=u["cargo"], area=area)
            except Area.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Área no encontrada: {u["area"]}'))
                continue
            except Cargo.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Cargo no encontrado: {u["cargo"]}'))
                continue

            # Eliminar usuario si ya existe
            existente = User.objects.filter(username=u["username"])
            if existente.exists():
                existente.delete()
                self.stdout.write(self.style.WARNING(f'✘ Usuario {u["username"]} eliminado'))

            # Crear nuevo usuario con todos los campos
            nuevo = User.objects.create_superuser(
                username=u["username"],
                email=u["email"],
                password=u["password"],
                first_name=first_name,
                last_name=last_name,
                area=area,
                cargo=cargo,
                usuario_ad=u["usuario_ad"],
                usuario_office=u["usuario_office"],
                usuario_sap=u["usuario_sap"],
                equipo_a_cargo=u["equipo_a_cargo"],
                impresora_a_cargo=u["impresora_a_cargo"],
                movil=u["movil"]
            )

            self.stdout.write(self.style.SUCCESS(f'✔ Usuario {u["username"]} creado correctamente'))
