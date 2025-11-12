# apps/usuarios/management/commands/seed_users.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.organizaciones.models import Area, Cargo

NO_EMAIL_VALUES = {"NO APLICA", "DISPONIBLE", ""}

# ⚠️ Pega aquí tu lista completa exactamente como la tienes:
#    OJO: el orden determina quiénes serán superusers (los primeros 4).
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
                "cargo": "Asistente Soporte TI y Procesos de Negocios",
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
                {
        "username": "Valentina Osorio",
        "email": "vosorio@ggh.cl",
        "password": "Osorio.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ANALISTA CONTABLE",
        "usuario_ad": "FINAN9",
        "usuario_office": "vosorio@ggh.cl",
        "usuario_sap": "finan9",
        "equipo_a_cargo": "SAMSUNG",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "+569 52167864"
    },
    {
        "username": "Claudia Sanhueza",
        "email": "csanhueza@ggh.cl",
        "password": "Sanhueza.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ANALISTA CONTABLE",
        "usuario_ad": "FINAN4",
        "usuario_office": "csanhueza@ggh.cl",
        "usuario_sap": "finan4",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Sebastián Calderón",
        "email": "scalderon@ggh.cl",
        "password": "Calderon.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ANALISTA FACTORING",
        "usuario_ad": "FINAN10",
        "usuario_office": "scalderon@ggh.cl",
        "usuario_sap": "scalderon",
        "equipo_a_cargo": "MACBOOKPRO",
        "impresora_a_cargo": "NO APLICA",
        "movil": "No APLICA"
    },
    {
        "username": "Jacqueline Pizarro",
        "email": "jpizarro@ggh.cl",
        "password": "Pizarro.2025",
        "area": "Zona Norte",
        "cargo": "ASISTENTE ADMINISTRATIVA SUCURSAL ANTOFAGASTA Y ASISTENTE COMERCIAL NORTE",
        "usuario_ad": "VENTAS25",
        "usuario_office": "jpizarro@ggh.cl",
        "usuario_sap": "ventas24",
        "equipo_a_cargo": "",
        "impresora_a_cargo": "RICCO SB3710",
        "movil": "No APLICA"
    },
    {
        "username": "Rebecca Retamales",
        "email": "retamales@ggh.cl",
        "password": "Retamales.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE COMERCIAL DE SERVICIOS",
        "usuario_ad": "COMPRAS3",
        "usuario_office": "retamales@ggh.cl",
        "usuario_sap": "retamales",
        "equipo_a_cargo": "MACBOOK AIR",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "MOTOROLA + 56 9 62491731"
    },
    {
        "username": "Luis Cisternas",
        "email": "lcisternas@ggh.cl",
        "password": "Cisternas.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ASISTENTE CONTABILIDAD",
        "usuario_ad": "FINAN8",
        "usuario_office": "lcisternas@ggh.cl",
        "usuario_sap": "finan8",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Paula Faúndez",
        "email": "finanzas5@ggh.cl",
        "password": "Faúndez.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ASISTENTE CONTABILIDAD",
        "usuario_ad": "FINAN5",
        "usuario_office": "finanzas5@ggh.cl",
        "usuario_sap": "finan5",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "+569 5216 7823"
    },
    {
        "username": "Stefhanie Ramirez",
        "email": "Sramirez@ggh.cl",
        "password": "Ramirez.2025",
        "area": "Compras e Inventario",
        "cargo": "ASISTENTE DE COMPRAS",
        "usuario_ad": "COMPRAS1",
        "usuario_office": "Sramirez@ggh.cl",
        "usuario_sap": "mesparza",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "BROTHER  C2/ HP/ BROTHER A COLOR",
        "movil": "No APLICA"
    },
    {
        "username": "Carolina Herrera",
        "email": "cherrera@ggh.cl",
        "password": "Herrera.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE DE EJECUTIVOS COMERCIALES",
        "usuario_ad": "VENTAS10",
        "usuario_office": "cherrera@ggh.cl",
        "usuario_sap": "cherrera",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Paola Chiguay",
        "email": "pchiguay@ggh.cl",
        "password": "Chiguay.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE DE EJECUTIVOS COMERCIALES",
        "usuario_ad": "VENTAS1",
        "usuario_office": "pchiguay@ggh.cl",
        "usuario_sap": "ventas1",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
        {
        "username": "Judith Lucero",
        "email": "jlucero@ggh.cl",
        "password": "Lucero.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE DE EJECUTIVOS COMERCIALES",
        "usuario_ad": "VENTAS4",
        "usuario_office": "jlucero@ggh.cl",
        "usuario_sap": "Ventas4",
        "equipo_a_cargo": "HP LAPTOP15",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Sebastian Mella",
        "email": "smella@ggh.cl",
        "password": "Mella.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE DE EJECUTIVOS COMERCIALES",
        "usuario_ad": "VENTAS22",
        "usuario_office": "smella@ggh.cl",
        "usuario_sap": "smella",
        "equipo_a_cargo": "MACBOOK AIR",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Javiera Quezada",
        "email": "jquezada@ggh.cl",
        "password": "Quezada.2025",
        "area": "Directorio Comercial",
        "cargo": "ASISTENTE DE FACTURACIÓN Y OPERACIONES",
        "usuario_ad": "BOD5",
        "usuario_office": "jquezada@ggh.cl",
        "usuario_sap": "mhidalgo+pchiguay",
        "equipo_a_cargo": "LENOVO",
        "impresora_a_cargo": "KYOCERA",
        "movil": "No APLICA"
    },
    {
        "username": "Elvis Lopez",
        "email": "elopez@ggh.cl",
        "password": "Lopez.2025",
        "area": "Operaciones",
        "cargo": "ASISTENTE DE OPERACIONES",
        "usuario_ad": "BOD2",
        "usuario_office": "elopez@ggh.cl",
        "usuario_sap": "bod2",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER  C2/ HP/ BROTHER A COLOR",
        "movil": "+569 34313889"
    },
    {
        "username": "Sabrina Arce",
        "email": "sarce@ggh.cl",
        "password": "Arce.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ASISTENTE DE RECURSOS HUMANOS",
        "usuario_ad": "NO APLICA",
        "usuario_office": "sarce@ggh.cl",
        "usuario_sap": "aerices",
        "equipo_a_cargo": "Samsung",
        "impresora_a_cargo": "HP",
        "movil": "+569 5 216 7830"
    },
    {
        "username": "Byron Marambio",
        "email": "bmarambio@ggh.cl",
        "password": "Marambio.2025",
        "area": "Zona Norte",
        "cargo": "ASISTENTE DE VENTAS Y BODEGA",
        "usuario_ad": "BOD3",
        "usuario_office": "bmarambio@ggh.cl",
        "usuario_sap": "Bodega13",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "RICOH SB3710",
        "movil": "No APLICA"
    },
    {
        "username": "Valeria Godoy",
        "email": "CONTACTO@GGH.CL",
        "password": "Godoy.2025",
        "area": "Sistemas",
        "cargo": "ASISTENTE SERVICIO AL CLIENTE",
        "usuario_ad": "VENTAS24",
        "usuario_office": "CONTACTO@GGH.CL",
        "usuario_sap": "ventas27",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Jaime Garrido",
        "email": "Jaime.seguridad@ggh.cl",
        "password": "Garrido.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "CONTROL INTERNO",
        "usuario_ad": "NO APLICA",
        "usuario_office": "Jaime.seguridad@ggh.cl",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Isrrael Castro",
        "email": "icastro@ggh.cl",
        "password": "Castro.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "COORDINADOR DE ADMINISTRACIÓN Y FINANZAS",
        "usuario_ad": "FINAN6",
        "usuario_office": "icastro@ggh.cl",
        "usuario_sap": "FINAN6",
        "equipo_a_cargo": "MACBOOKPRO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "569 64331881"
    },
    {
        "username": "Pedro Rojas",
        "email": "projas@ggh.cl",
        "password": "Rojas.2025",
        "area": "Operaciones",
        "cargo": "Coordinador de Bodega y Gestión de Pendientes",
        "usuario_ad": "BOD12",
        "usuario_office": "projas@ggh.cl",
        "usuario_sap": "bod3",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "BROTHER CONTAINER",
        "movil": "No APLICA"
    },
        {
        "username": "Marcelo Cabezas",
        "email": "mcabezas@ggh.cl",
        "password": "Cabezas.2025",
        "area": "Sistemas",
        "cargo": "Data Master",
        "usuario_ad": "SISTEMAS3",
        "usuario_office": "mcabezas@ggh.cl",
        "usuario_sap": "soporte",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "LASER JET PRO",
        "movil": "No APLICA"
    },
    {
        "username": "Rodrigo Gomez",
        "email": "rgomez@ggh.cl",
        "password": "Gomez.2025",
        "area": "Directorio Comercial",
        "cargo": "DIRECTOR COMERCIAL",
        "usuario_ad": "RGOMEZ",
        "usuario_office": "rgomez@ggh.cl",
        "usuario_sap": "rgomez",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "HP",
        "movil": "No APLICA"
    },
    {
        "username": "Alfredo Gomez",
        "email": "agomez@ggh.cl",
        "password": "Gomez.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "DIRECTOR DE ADMINISTRACION",
        "usuario_ad": "AGOMEZ",
        "usuario_office": "agomez@ggh.cl",
        "usuario_sap": "agomez",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "HP",
        "movil": "No APLICA"
    },
    {
        "username": "Felipe Leiva",
        "email": "design@ggh.cl",
        "password": "Leiva.2025",
        "area": "Sistemas",
        "cargo": "DISEÑADOR GRAFICO",
        "usuario_ad": "NO APLICA",
        "usuario_office": "design@ggh.cl",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "iMAC",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Débora Astudillo",
        "email": "dastudillo@ggh.cl",
        "password": "Astudillo.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "EJECUTIVA PAGO PROVEEDORES",
        "usuario_ad": "FINAN11",
        "usuario_office": "dastudillo@ggh.cl",
        "usuario_sap": "finan11",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "HPT LASER JET P3015",
        "movil": "+569 52167834"
    },
    {
        "username": "María Serey",
        "email": "mserey@ggh.cl",
        "password": "Serey.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "EJECUTIVA PAGO PROVEEDORES",
        "usuario_ad": "FINAN3",
        "usuario_office": "mserey@ggh.cl",
        "usuario_sap": "finan3",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Silvina Araya",
        "email": "saraya@ggh.cl",
        "password": "Araya.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS23",
        "usuario_office": "saraya@ggh.cl",
        "usuario_sap": "saraya",
        "equipo_a_cargo": "",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Cecilia Rodriguez",
        "email": "crodriguez@ggh.cl",
        "password": "Rodriguez.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS12",
        "usuario_office": "crodriguez@ggh.cl",
        "usuario_sap": "crodriguez",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Dorka Molina",
        "email": "dmolina@ggh.cl",
        "password": "Molina.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS26",
        "usuario_office": "dmolina@ggh.cl",
        "usuario_sap": "dmolina",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Israel Vergara",
        "email": "ivergara@ggh.cl",
        "password": "Vergara.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS19",
        "usuario_office": "ivergara@ggh.cl",
        "usuario_sap": "ivergara",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "SOLO NUMERO +56 9 51167840"
    },
        {
        "username": "Andres Rojas",
        "email": "arojas@ggh.cl",
        "password": "Rojas.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS5",
        "usuario_office": "arojas@ggh.cl",
        "usuario_sap": "arojasm",
        "equipo_a_cargo": "EQUIPO PROPIO",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Alfredo Garreton",
        "email": "agarreton@ggh.cl",
        "password": "Garreton.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS3",
        "usuario_office": "agarreton@ggh.cl",
        "usuario_sap": "agarreton",
        "equipo_a_cargo": "TABLET Samsung",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "Mariana Cortes",
        "email": "mcortes@ggh.cl",
        "password": "Cortes.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS17",
        "usuario_office": "mcortes@ggh.cl",
        "usuario_sap": "mcortes",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Grecia Castro",
        "email": "gcastro@ggh.cl",
        "password": "Castro.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS15",
        "usuario_office": "gcastro@ggh.cl",
        "usuario_sap": "gcastro",
        "equipo_a_cargo": "PROPIO",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Carlos Pinto",
        "email": "cpinto@ggh.cl",
        "password": "Nm4Dyp6V",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS7",
        "usuario_office": "cpinto@ggh.cl",
        "usuario_sap": "cpinto",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Karen Oporto",
        "email": "koporto@ggh.cl",
        "password": "Zx9Kmv4P",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS27",
        "usuario_office": "koporto@ggh.cl",
        "usuario_sap": "ventas25",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "NOKIA +56 9  88345541"
    },
    {
        "username": "Patricio Toro",
        "email": "ptoro@ggh.cl",
        "password": "Toro.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS21",
        "usuario_office": "ptoro@ggh.cl",
        "usuario_sap": "ptoro",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Sebastian Valdivia",
        "email": "svaldivia@ggh.cl",
        "password": "Valdivia.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS8",
        "usuario_office": "svaldivia@ggh.cl",
        "usuario_sap": "ventas8",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "+569 3 431 3883"
    },
    {
        "username": "Jorge Bustamante",
        "email": "abustamante@ggh.cl",
        "password": "Bustamante.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS6",
        "usuario_office": "abustamante@ggh.cl",
        "usuario_sap": "abustamante",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Ivan Toro",
        "email": "itoro@ggh.cl",
        "password": "Toro.2025",
        "area": "Directorio Comercial",
        "cargo": "EJECUTIVO COMERCIAL",
        "usuario_ad": "VENTAS28",
        "usuario_office": "itoro@ggh.cl",
        "usuario_sap": "ventas28",
        "equipo_a_cargo": "HP LAPTOP15",
        "impresora_a_cargo": "No APLICA",
        "movil": "No APLICA"
    },
        {
        "username": "Paola Rivera",
        "email": "privera@ggh.cl",
        "password": "Rivera.2025",
        "area": "Zona Norte",
        "cargo": "EJECUTIVO COMERCIAL ZONA NORTE",
        "usuario_ad": "VENTAS20",
        "usuario_office": "privera@ggh.cl",
        "usuario_sap": "privera",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "RICCO SB3710",
        "movil": "No APLICA"
    },
    {
        "username": "Lorena Jiménez",
        "email": "finanzas13@ggh.cl",
        "password": "Jimenez.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "EJECUTIVO DE COBRANZA",
        "usuario_ad": "FINAN13",
        "usuario_office": "finanzas13@ggh.cl",
        "usuario_sap": "finanzas13",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "+569 5216 7829"
    },
    {
        "username": "Carolina Diaz",
        "email": "cdiaz@ggh.cl",
        "password": "Diaz.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "EJECUTIVO DE COBRANZA",
        "usuario_ad": "cdiaz",
        "usuario_office": "cdiaz@ggh.cl",
        "usuario_sap": "pdelcampo",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "MOTOROLA 9 7887 2844"
    },
    {
        "username": "Maribel Esparza",
        "email": "mesparza@ggh.cl",
        "password": "Esparza.2025",
        "area": "Compras e Inventario",
        "cargo": "EJECUTIVO DE COMPRAS",
        "usuario_ad": "LICENCIA",
        "usuario_office": "mesparza@ggh.cl",
        "usuario_sap": "LICENCIA",
        "equipo_a_cargo": "LICENCIA",
        "impresora_a_cargo": "LICENCIA",
        "movil": "No APLICA"
    },
    {
        "username": "Pedro Carreño",
        "email": "pcarreno@ggh.cl",
        "password": "Carreño.2025",
        "area": "Compras e Inventario",
        "cargo": "EJECUTIVO DE COMPRAS",
        "usuario_ad": "COMPRAS2",
        "usuario_office": "pcarreno@ggh.cl",
        "usuario_sap": "pcarreno",
        "equipo_a_cargo": "lenovo",
        "impresora_a_cargo": "BROTHER  C2/ HP/ BROTHER A COLOR",
        "movil": "No APLICA"
    },
    {
        "username": "Elba Díaz",
        "email": "Prevencion@ggh.cl",
        "password": "Diaz.2025",
        "area": "Operaciones",
        "cargo": "Encargada de Prevención de Riesgos",
        "usuario_ad": "no aplica",
        "usuario_office": "Prevencion@ggh.cl",
        "usuario_sap": "no aplica",
        "equipo_a_cargo": "Hp Laptop",
        "impresora_a_cargo": "Brother Finanzas",
        "movil": "569 3201 3732"
    },
    {
        "username": "Angelica Erices",
        "email": "aerices@ggh.cl",
        "password": "Erices.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "ENCARGADA DE RECURSOS HUMANOS",
        "usuario_ad": "FINAN2",
        "usuario_office": "aerices@ggh.cl",
        "usuario_sap": "aerices",
        "equipo_a_cargo": "MACBOOK AIR",
        "impresora_a_cargo": "HP",
        "movil": "+569 5216 7830"
    },
    {
        "username": "Emerson Vera",
        "email": "evera@ggh.cl",
        "password": "Vera.2025",
        "area": "Directorio Administración y Finanzas",
        "cargo": "Encargado de Control de Gestión y Procesos",
        "usuario_ad": "FINAN12",
        "usuario_office": "evera@ggh.cl",
        "usuario_sap": "finan12",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "KYOCERA TK-3182",
        "movil": "No APLICA"
    },
    {
        "username": "Ariel Martínez",
        "email": "amartinez@ggh.cl",
        "password": "Martinez.2025",
        "area": "Directorio Comercial",
        "cargo": "Encargado de Línea",
        "usuario_ad": "VENTAS9",
        "usuario_office": "amartinez@ggh.cl",
        "usuario_sap": "ventas9",
        "equipo_a_cargo": "Lenovo ideapad s340",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Luis Bravo",
        "email": "lbravo@ggh.cl",
        "password": "Bravo.2025",
        "area": "Operaciones",
        "cargo": "Encargado de Logística",
        "usuario_ad": "BOD4",
        "usuario_office": "lbravo@ggh.cl",
        "usuario_sap": "bod4",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "BROTHER CONTAINER",
        "movil": "+56 9 34313884"
    },
        {
        "username": "Hernan Ahumada",
        "email": "serviciotecnico@ggh.cl",
        "password": "Uhumada.2025",
        "area": "Directorio Comercial",
        "cargo": "ENCARGADO DE SERVICIO TECNICO",
        "usuario_ad": "VENTAS16",
        "usuario_office": "serviciotecnico@ggh.cl",
        "usuario_sap": "hahumada",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Mauricio Ricke",
        "email": "mricke@ggh.cl",
        "password": "Ricke.2025",
        "area": "Compras e Inventario",
        "cargo": "Gerente Compras e Inventario",
        "usuario_ad": "BOD9",
        "usuario_office": "mricke@ggh.cl",
        "usuario_sap": "Mricke",
        "equipo_a_cargo": "LENOVO",
        "impresora_a_cargo": "BROTHER  C2/ HP/ BROTHER A COLOR",
        "movil": "No APLICA"
    },
    {
        "username": "Ricardo Añual",
        "email": "ranual@ggh.cl",
        "password": "Anual.2025",
        "area": "Operaciones",
        "cargo": "GERENTE DE OPERACIONES",
        "usuario_ad": "RANUAL",
        "usuario_office": "ranual@ggh.cl",
        "usuario_sap": "ranual",
        "equipo_a_cargo": "PROPIO",
        "impresora_a_cargo": "HP BODEGA",
        "movil": "No APLICA"
    },
    {
        "username": "Daniel Canto",
        "email": "dcanto@ggh.cl",
        "password": "Canto.2025",
        "area": "Zona Norte",
        "cargo": "GERENTE DE ZONA NORTE",
        "usuario_ad": "VENTAS13",
        "usuario_office": "dcanto@ggh.cl",
        "usuario_sap": "dcanto",
        "equipo_a_cargo": "ACER",
        "impresora_a_cargo": "RICCO SB3710",
        "movil": "+569 664 7935 LG"
    },
    {
        "username": "Iván Henríquez",
        "email": "ihenriquez@ggh.cl",
        "password": "Henriquez.2025",
        "area": "Sistemas",
        "cargo": "Lider de Canal Marketplace Ecommerce",
        "usuario_ad": "VENTAS2",
        "usuario_office": "ihenriquez@ggh.cl",
        "usuario_sap": "ventas2",
        "equipo_a_cargo": "LENOVO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "+569 7710 6231"
    },
    {
        "username": "FE2 DISPONIBLE",
        "email": "",
        "password": "Disponible123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "FE2",
        "usuario_office": "NO APLICA",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "NO APLICA",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "FE4 DISPONIBLE",
        "email": "",
        "password": "Disponible123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "FE4",
        "usuario_office": "NO APLICA",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "NO APLICA",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "Raul Olivares",
        "email": "rolivares@ggh.cl",
        "password": "Olivares.2025",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "FINAN7",
        "usuario_office": "rolivares@ggh.cl",
        "usuario_sap": "rolivares",
        "equipo_a_cargo": "ASSUS",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "VENTAS9 DISPONIBLE",
        "email": "",
        "password": "Disponible123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "VENTAS9",
        "usuario_office": "DISPONIBLE",
        "usuario_sap": "DISPONIBLE",
        "equipo_a_cargo": "",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
        "username": "TV INDICADORES BODEGA",
        "email": "",
        "password": "TVBodega123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "NO APLICA",
        "usuario_office": "NO APLICA",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "NO APLICA",
        "impresora_a_cargo": "",
        "movil": "No APLICA"
    },
    {
    "username": "Poligonix",
    "email": "NO APLICA",
    "password": "Poligonix123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "poligonix",
    "usuario_office": "NO APLICA",
    "usuario_sap": "manager",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "COBRANZAS FE1",
    "email": "NO APLICA",
    "password": "Cobranza123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "FE1",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE VENTAS18",
    "email": "DISPONIBLE",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "VENTAS18",
    "usuario_office": "DISPONIBLE",
    "usuario_sap": "DISPONIBLE",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE RRHH2",
    "email": "NO APLICA",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "RRHH2",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE FE3",
    "email": "NO APLICA",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "FE3",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE FE5",
    "email": "NO APLICA",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "FE5",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE COMPRAS4",
    "email": "Disponible",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "COMPRAS4",
    "usuario_office": "Disponible",
    "usuario_sap": "compras4",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE RRHH1",
    "email": "NO APLICA",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "RRHH1",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE VENTAS28",
    "email": "dDISPONIBLE",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "VENTAS28",
    "usuario_office": "dDISPONIBLE",
    "usuario_sap": "ventas28",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "Arturo León",
    "email": "NO APLICA",
    "password": "Leon.2025",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "aleon",
    "usuario_office": "marketing@ggh.cl",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "MACBOOK PRO",
    "impresora_a_cargo": "BROTHER MFCL6900W",
    "movil": "No APLICA"
},
{
    "username": "Bodega Antofagasta",
    "email": "NO APLICA",
    "password": "Bodega123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "BOD14",
    "usuario_office": "NO APLICA",
    "usuario_sap": "bodega14",
    "equipo_a_cargo": "HP",
    "impresora_a_cargo": "RICOH SB3710",
    "movil": "No APLICA"
},
{
    "username": "Inxap",
    "email": "NO APLICA",
    "password": "Inxap2025",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "Inxap",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "DISPONIBLE BOD13",
    "email": "NO APLICA",
    "password": "Disponible123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "BOD13",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "Inxap2",
    "email": "NO APLICA",
    "password": "Inxap2025",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "inxap2",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
{
    "username": "ITHelper",
    "email": "NO APLICA",
    "password": "IThelper123",
    "area": "NO APLICA",
    "cargo": "NO APLICA",
    "usuario_ad": "SISTEMAS1",
    "usuario_office": "NO APLICA",
    "usuario_sap": "NO APLICA",
    "equipo_a_cargo": "NO APLICA",
    "impresora_a_cargo": "NO APLICA",
    "movil": "No APLICA"
},
    {
        "username": "Juan Leiva",
        "email": "marketing@ggh.cl",
        "password": "Leiva.2025",
        "area": "Sistemas",
        "cargo": "ASISTENTE DE MARKETING",
        "usuario_ad": "NO APLICA",
        "usuario_office": "marketing@ggh.cl",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "No APLICA"
    },
    {
        "username": "DISPONIBLE FINAN1",
        "email": "NO APLICA",
        "password": "Disponible123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "FINAN1",
        "usuario_office": "NO APLICA",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "NO APLICA",
        "impresora_a_cargo": "NO APLICA",
        "movil": "No APLICA"
    },
    {
        "username": "DISPONIBLE BOD8",
        "email": "NO APLICA",
        "password": "Disponible123",
        "area": "NO APLICA",
        "cargo": "NO APLICA",
        "usuario_ad": "BOD8",
        "usuario_office": "NO APLICA",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "NO APLICA",
        "impresora_a_cargo": "NO APLICA",
        "movil": "No APLICA"
    },
    {
        "username": "Marco Pinto",
        "email": "packing@ggh.cl",
        "password": "Pinto.2025",
        "area": "Operaciones",
        "cargo": "OPERARIO DE BODEGA",
        "usuario_ad": "NO APLICA",
        "usuario_office": "packing@ggh.cl",
        "usuario_sap": "NO APLICA",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "ZEBRA 420T",
        "movil": "No APLICA"
    },
    {
        "username": "Eliseo Ancan",
        "email": "eancan@ggh.cl",
        "password": "Ancan.2025",
        "area": "Operaciones",
        "cargo": "OPERARIO DE BODEGA",
        "usuario_ad": "BOD11",
        "usuario_office": "eancan@ggh.cl",
        "usuario_sap": "bod11",
        "equipo_a_cargo": "ASUS VIVOBOOK",
        "impresora_a_cargo": "ZEBRA GK420T",
        "movil": "No APLICA"
    },
    {
        "username": "Maximiliano Jara",
        "email": "mjara@ggh.cl",
        "password": "Jara.2025",
        "area": "Operaciones",
        "cargo": "OPERARIO DE BODEGA",
        "usuario_ad": "BOD10",
        "usuario_office": "mjara@ggh.cl",
        "usuario_sap": "bod10",
        "equipo_a_cargo": "ASUS",
        "impresora_a_cargo": "ZEBRA ZD 220",
        "movil": "No APLICA"
    },
    {
        "username": "Luis Ortega",
        "email": "lortega@ggh.cl",
        "password": "Ortega.2025",
        "area": "Operaciones",
        "cargo": "OPERARIO DE BODEGA RECEPCIÓN",
        "usuario_ad": "BOD6",
        "usuario_office": "lortega@ggh.cl",
        "usuario_sap": "bod6",
        "equipo_a_cargo": "HP",
        "impresora_a_cargo": "BROTHER CONTAINER",
        "movil": "+569 52167822"
    },
    {
        "username": "Gustavo Zuñiga",
        "email": "recepcion@ggh.cl",
        "password": "Zuniga.2025",
        "area": "Operaciones",
        "cargo": "OPERARIO DE BODEGA RECEPCIÓN",
        "usuario_ad": "BOD7",
        "usuario_office": "recepcion@ggh.cl",
        "usuario_sap": "lortega",
        "equipo_a_cargo": "ACER",
        "impresora_a_cargo": "ZEBRA GK420T",
        "movil": "No APLICA"
    },
    {
        "username": "Valentina Pérez",
        "email": "vperez@ggh.cl",
        "password": "Perez.2025",
        "area": "Sistemas",
        "cargo": "PRODUCT MANAGER",
        "usuario_ad": "VENTAS14",
        "usuario_office": "vperez@ggh.cl",
        "usuario_sap": "ventas14",
        "equipo_a_cargo": "MACBOOK PRO",
        "impresora_a_cargo": "BROTHER MFCL6900W",
        "movil": "+569 5 216 7864"
    }
]

class Command(BaseCommand):
    help = "Elimina todos los usuarios y los recrea desde una lista. Los primeros N quedan como superusers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="No pedir confirmación para borrar todos los usuarios.",
        )
        parser.add_argument(
            "--super-count",
            type=int,
            default=4,
            help="Cantidad de usuarios iniciales a marcar como superusers (default: 4).",
        )

    def _split_names(self, nombre_completo: str):
        partes = (nombre_completo or "").strip().split()
        if not partes:
            return "", ""
        first = partes[0]
        last = " ".join(partes[1:]) if len(partes) > 1 else ""
        return first, last

    def handle(self, *args, **opts):
        User = get_user_model()
        super_count = int(opts["super_count"])

        if not usuarios:
            raise CommandError("La lista 'usuarios' está vacía. Pega tu data antes de ejecutar.")


        with transaction.atomic():
            # 1) Borrar todos los usuarios
            total_prev = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"✘ Eliminados {total_prev} usuarios."))

            # 2) Crear de nuevo en orden
            creados, saltados = 0, 0
            for idx, u in enumerate(usuarios, start=1):
                username = (u.get("username") or "").strip()
                email_raw = (u.get("email") or "").strip()
                email = "" if email_raw.upper() in NO_EMAIL_VALUES else email_raw
                pwd = u.get("password") or "Cambiar123!"  # fallback decente
                area_nombre = (u.get("area") or "").strip()
                cargo_nombre = (u.get("cargo") or "").strip()

                if not username:
                    self.stdout.write(self.style.ERROR("Usuario sin 'username' → saltado."))
                    saltados += 1
                    continue

                # Resuelve Area y Cargo
                area = Area.objects.filter(nombre=area_nombre).first()
                if not area:
                    self.stdout.write(self.style.ERROR(f"Área no encontrada: {area_nombre} → {username} saltado"))
                    saltados += 1
                    continue

                cargo = Cargo.objects.filter(nombre=cargo_nombre, area=area).first()
                if not cargo:
                    self.stdout.write(self.style.ERROR(f"Cargo '{cargo_nombre}' no encontrado en área '{area_nombre}' → {username} saltado"))
                    saltados += 1
                    continue

                first_name, last_name = self._split_names(username)

                # Flags: primeros N superusers
                es_super = idx <= super_count
                es_staff = es_super  # si quieres, puedes dejar staff=True para otros también

                # Crear usuario
                obj = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    area=area,
                    cargo=cargo,
                    usuario_ad=u.get("usuario_ad") or "",
                    usuario_office=u.get("usuario_office") or "",
                    usuario_sap=u.get("usuario_sap") or "",
                    equipo_a_cargo=u.get("equipo_a_cargo") or "",
                    impresora_a_cargo=u.get("impresora_a_cargo") or "",
                    movil=u.get("movil") or "",
                    is_superuser=es_super,
                    is_staff=es_staff,
                    is_active=True,
                )
                obj.set_password(pwd)
                obj.save()
                creados += 1

                if es_super:
                    self.stdout.write(self.style.SUCCESS(f"✔ {idx}. {username} (SUPERUSER) creado"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✔ {idx}. {username} creado"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Listo. Creados: {creados} | Saltados: {saltados}"))
        self.stdout.write(self.style.HTTP_INFO("Recuerda: sólo los primeros N quedaron como superusers."))