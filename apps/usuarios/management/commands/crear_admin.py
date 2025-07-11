from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea usuarios administradores predeterminados si no existen'
    def handle(self, *args, **options):
        User = get_user_model()

        usuarios = [
            {"username": "Gonzalo Neira", "email": "gneira@ggh.cl", "password": "Manzana"},
            {"username": "Andres Jimenez", "email": "ajimenez@ggh.cl", "password": "Manzana"},
            {"username": "Millaray Esposito", "email": "mesposito@ggh.cl", "password": "Manzana"},
            {"username": "Alexssander Lopez", "email": "alopez@ggh.cl", "password": "Manzana"},
        ]

        for usuario in usuarios:
            if not User.objects.filter(username=usuario["username"]).exists():
                User.objects.create_superuser(
                    username=usuario["username"],
                    email=usuario["email"],
                    password=usuario["password"]
                )
                self.stdout.write(self.style.SUCCESS(f'✔ Usuario {usuario["username"]} creado'))
            else:
                self.stdout.write(f'⚠ Usuario {usuario["username"]} ya existe')
