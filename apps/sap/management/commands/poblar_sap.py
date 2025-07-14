from django.core.management.base import BaseCommand
from apps.sap.models import Proveedor, Marca, UDM

class Command(BaseCommand):
    help = 'Pobla las tablas de Proveedor, Marca y UDM con datos iniciales'

    def handle(self, *args, **options):
        # Proveedores
        proveedores = [
            {"nombre": "Proveedora del Norte", "rut": "76473820-1"},
            {"nombre": "FerreCentro Ltda.", "rut": "76894523-9"},
            {"nombre": "Importadora Sur", "rut": "76983215-0"},
        ]

        for p in proveedores:
            obj, created = Proveedor.objects.get_or_create(rut=p["rut"], defaults={"nombre": p["nombre"]})
            if created:
                self.stdout.write(self.style.SUCCESS(f'✔ Proveedor {p["nombre"]} creado'))
            else:
                self.stdout.write(f'⚠ Proveedor {p["nombre"]} ya existe')

        # Marcas
        marcas = ["Bosch", "Makita", "DeWalt", "3M", "Stanley"]
        for m in marcas:
            obj, created = Marca.objects.get_or_create(nombre=m)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✔ Marca {m} creada'))
            else:
                self.stdout.write(f'⚠ Marca {m} ya existe')

        # UDM
        udms = ["Unidad", "Caja", "Litro", "Metro", "Kilogramo"]
        for u in udms:
            obj, created = UDM.objects.get_or_create(nombre=u)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✔ UDM {u} creada'))
            else:
                self.stdout.write(f'⚠ UDM {u} ya existe')
