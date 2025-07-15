from django.core.management.base import BaseCommand
from apps.organizaciones.models import Area, Cargo
 
class Command(BaseCommand):
    help = 'Limpia y repuebla las tablas de Área y Cargo con los datos actualizados'
 
    def handle(self, *args, **kwargs):
        # Eliminar todos los cargos primero (por FK a área)
        Cargo.objects.all().delete()
        Area.objects.all().delete()
 
        self.stdout.write(self.style.WARNING("⚠️  Se eliminaron todas las áreas y cargos existentes."))
 
        datos = [
            ("ANALISTA CONTABLE", "Directorio Administración y Finanzas"),
            ("ANALISTA FACTORING", "Directorio Administración y Finanzas"),
            ("ASISTENTE ADMINISTRATIVA SUCURSAL ANTOFAGASTA Y ASISTENTE COMERCIAL NORTE", "Zona Norte"),
            ("ASISTENTE COMERCIAL DE SERVICIOS", "Directorio Comercial"),
            ("ASISTENTE CONTABILIDAD", "Directorio Administración y Finanzas"),
            ("ASISTENTE DE COMPRAS", "Compras e Inventario"),
            ("ASISTENTE DE EJECUTIVOS COMERCIALES", "Directorio Comercial"),
            ("ASISTENTE DE FACTURACIÓN Y OPERACIONES", "Directorio Comercial"),
            ("ASISTENTE DE INFORMATICA", "Sistemas"),
            ("ASISTENTE DE MARKETING", "Sistemas"),
            ("ASISTENTE DE OPERACIONES", "Operaciones"),
            ("ASISTENTE DE RECURSOS HUMANOS", "Directorio Administración y Finanzas"),
            ("ASISTENTE DE VENTAS Y BODEGA", "Zona Norte"),
            ("ASISTENTE SERVICIO AL CLIENTE", "Sistemas"),
            ("ASISTENTE SERVICIO TÉCNICO Y GENERAL", "Directorio Comercial"),
            ("Asistente Soporte TI y Procesos de Negocios", "Sistemas"),
            ("AYUDANTE DE BODEGA", "Operaciones"),
            ("CONDUCTOR", "Operaciones"),
            ("CONTROL INTERNO", "Directorio Administración y Finanzas"),
            ("COORDINADOR DE ADMINISTRACIÓN Y FINANZAS", "Directorio Administración y Finanzas"),
            ("Coordinador de Bodega y Gestión de Pendientes", "Operaciones"),
            ("Data Master", "Sistemas"),
            ("DIRECTOR COMERCIAL", "Directorio Comercial"),
            ("DIRECTOR DE ADMINISTRACION", "Directorio Administración y Finanzas"),
            ("DISEÑADOR GRAFICO", "Sistemas"),
            ("EJECUTIVA PAGO PROVEEDORES", "Directorio Administración y Finanzas"),
            ("EJECUTIVO COMERCIAL", "Directorio Comercial"),
            ("EJECUTIVO COMERCIAL ZONA NORTE", "Zona Norte"),
            ("EJECUTIVO DE COBRANZA", "Directorio Administración y Finanzas"),
            ("EJECUTIVO DE COMPRAS", "Compras e Inventario"),
            ("Encargada de Prevención de Riesgos", "Operaciones"),
            ("ENCARGADA DE RECURSOS HUMANOS", "Directorio Administración y Finanzas"),
            ("Encargado de Control de Gestión y Procesos", "Directorio Administración y Finanzas"),
            ("Encargado de Línea", "Directorio Comercial"),
            ("Encargado de Logística", "Operaciones"),
            ("ENCARGADO DE SERVICIO TECNICO", "Directorio Comercial"),
            ("ENCARGADO DE TESORERIA Y ATENCION A PROVEEDORES", "Directorio Administración y Finanzas"),
            ("Gerente Compras e Inventario", "Compras e Inventario"),
            ("GERENTE DE OPERACIONES", "Operaciones"),
            ("GERENTE DE ZONA NORTE", "Zona Norte"),
            ("JEFE DE INFRAESTRUCTURA Y SOPORTE TI", "Sistemas"),
            ("JUNIOR", "Directorio Administración y Finanzas"),
            ("Lider de Canal Marketplace Ecommerce", "Sistemas"),
            ("LIDER RESPONSABLE ÁREA INFORMÁTICA", "Sistemas"),
            ("OPERADOR DE ASEO", "Directorio Administración y Finanzas"),
            ("OPERADOR DE GRÚA Y AYUDANTE DE BODEGA", "Operaciones"),
            ("OPERARIO DE BODEGA", "Operaciones"),
            ("OPERARIO DE BODEGA RECEPCIÓN", "Operaciones"),
            ("PORTERIA", "Directorio Administración y Finanzas"),
            ("PRODUCT MANAGER", "Sistemas"),
            ("NO APLICA", "NO APLICA"),
        ]
 
        for nombre_cargo, nombre_area in datos:
            area, _ = Area.objects.get_or_create(nombre=nombre_area)
            cargo, created = Cargo.objects.get_or_create(nombre=nombre_cargo, area=area)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✔ Cargo '{nombre_cargo}' creado en área '{nombre_area}'"))
            else:
                self.stdout.write(f"⚠ Cargo '{nombre_cargo}' ya existía")
 
        self.stdout.write(self.style.SUCCESS("✅ Tablas de Área y Cargo repobladas correctamente."))