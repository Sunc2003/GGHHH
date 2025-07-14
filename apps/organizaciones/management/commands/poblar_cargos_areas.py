from django.core.management.base import BaseCommand
from apps.organizaciones.models import Area, Cargo

class Command(BaseCommand):
    help = 'Pobla la base de datos con las áreas y cargos definidos'

    def handle(self, *args, **options):
        datos = [
            ("ASISTENTE DE COMPRAS", "Compras e Inventario"),
            ("EJECUTIVO DE COMPRAS", "Compras e Inventario"),
            ("ANALISTA CONTABLE", "Directorio Administración y Finanzas"),
            ("ANALISTA FACTORING", "Directorio Administración y Finanzas"),
            ("ASISTENTE CONTABILIDAD", "Directorio Administración y Finanzas"),
            ("ASISTENTE DE RECURSOS HUMANOS", "Directorio Administración y Finanzas"),
            ("ASISTENTE SERVICIO AL CLIENTE", "Sistemas"),
            ("ASISTENTE DE FACTURACIÓN Y OPERACIONES", "Directorio Comercial"),
            ("ASISTENTE DE INFORMATICA", "Sistemas"),
            ("ASISTENTE DE MARKETING", "Sistemas"),
            ("ASISTENTE DE OPERACIONES", "Operaciones"),
            ("ASISTENTE DE VENTAS Y BODEGA", "Zona Norte"),
            ("ASISTENTE DE EJECUTIVOS COMERCIALES", "Directorio Comercial"),
            ("ASISTENTE SERVICIO TÉCNICO Y GENERAL", "Directorio Comercial"),
            ("ASISTENTE COMERCIAL DE SERVICIOS", "Directorio Comercial"),
            ("AYUDANTE DE BODEGA", "Operaciones"),
            ("CONDUCTOR", "Operaciones"),
            ("COORDINADOR DE ADMINISTRACIÓN Y FINANZAS", "Directorio Administración y Finanzas"),
            ("CONTROL INTERNO", "Directorio Administración y Finanzas"),
            ("DATA MASTER", "Sistemas"),
            ("DISEÑADOR GRAFICO", "Sistemas"),
            ("DIRECTOR COMERCIAL", "Directorio Comercial"),
            ("DIRECTOR DE ADMINISTRACION", "Directorio Administración y Finanzas"),
            ("EJECUTIVA PAGO PROVEEDORES", "Directorio Administración y Finanzas"),
            ("EJECUTIVO COMERCIAL", "Directorio Comercial"),
            ("EJECUTIVO COMERCIAL ZONA NORTE", "Zona Norte"),
            ("EJECUTIVO DE COBRANZA", "Directorio Administración y Finanzas"),
            ("ENCARGADO DE LOGÍSTICA", "Operaciones"),
            ("ENCARGADA DE RECURSOS HUMANOS", "Directorio Administración y Finanzas"),
            ("ENCARGADA DE PREVENCIÓN DE RIESGOS", "Operaciones"),
            ("ENCARGADO DE SERVICIO TECNICO", "Directorio Comercial"),
            ("ENCARGADO DE TESORERIA Y ATENCION A PROVEEDORES", "Directorio Administración y Finanzas"),
            ("GERENTE DE OPERACIONES", "Operaciones"),
            ("GERENTE DE ZONA NORTE", "Zona Norte"),
            ("GERENTE COMPRAS E INVENTARIO", "Compras e Inventario"),
            ("JEFE DE INFRAESTRUCTURA Y SOPORTE TI", "Sistemas"),
            ("JUNIOR", "Directorio Administración y Finanzas"),
            ("LIDER RESPONSABLE ÁREA INFORMÁTICA", "Sistemas"),
            ("LIDER DE CANAL MARKETPLACE ECOMMERCE", "Sistemas"),
            ("OPERADOR DE ASEO", "Directorio Administración y Finanzas"),
            ("OPERADOR DE GRÚA Y AYUDANTE DE BODEGA", "Operaciones"),
            ("OPERARIO DE BODEGA", "Operaciones"),
            ("OPERARIO DE BODEGA RECEPCIÓN", "Operaciones"),
            ("PORTERIA", "Directorio Administración y Finanzas"),
            ("PRODUCT MANAGER", "Sistemas"),
            ("COORDINADOR DE BODEGA Y GESTIÓN DE PENDIENTES", "Operaciones"),
            ("ENCARGADO DE CONTROL DE GESTIÓN Y PROCESOS", "Directorio Administración y Finanzas"),
            ("ENCARGADO DE LÍNEA", "Directorio Comercial"),
        ]

        for nombre_cargo, nombre_area in datos:
            area, _ = Area.objects.get_or_create(nombre=nombre_area)
            cargo, created = Cargo.objects.get_or_create(nombre=nombre_cargo, area=area)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Cargo '{nombre_cargo}' creado en área '{nombre_area}'"))
            else:
                self.stdout.write(f"⚠ Cargo '{nombre_cargo}' ya existía")
