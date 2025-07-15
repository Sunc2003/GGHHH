from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.organizaciones.models import Area, Cargo
from django.conf import settings
from django.utils import timezone

class CustomUser(AbstractUser):
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True)
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)

    usuario_ad = models.CharField(max_length=100, blank=True, null=True)
    usuario_office = models.CharField(max_length=100, blank=True, null=True)
    usuario_sap = models.CharField(max_length=100, blank=True, null=True)
    equipo_a_cargo = models.TextField(blank=True, null=True)
    impresora_a_cargo = models.CharField(max_length=100, blank=True, null=True)
    movil = models.CharField(max_length=50, blank=True, null=True)
    permisos_directos = models.ManyToManyField('permisos.Permiso', blank=True, related_name='usuarios_con_permiso_directo')

    def __str__(self):
        return self.get_full_name() or self.username

    def obtener_permisos(self):
        return self.permisos_directos.all()

    def tiene_permiso(self, codigo_permiso):
        return self.obtener_permisos().filter(codigo=codigo_permiso).exists()


class SolicitudCodigo(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('creado', 'Código Creado'),
    ]

    EMPRESAS = [
        ('asland', 'Asland'),
        ('marsella', 'Marsella'),
    ]

    TIPOS_SOLICITUD = [
        ('nuevo_articulo', 'Nuevo Artículo'),
        ('produccion', 'Producción'),
        ('activacion', 'Activación'),
        ('modificacion', 'Modificación'),
    ]

    OPCIONES_COTIZACION = [
        ('telefono', 'Por Teléfono'),
        ('documento', 'Por Documento'),
        ('lista_precios', 'Por Lista de Precios'),
        ('whatsapp', 'Por WhatsApp'),
    ]

    ORIGENES = [
        ('sin_origen', 'Sin origen'),
        ('nacional', 'Nacional'),
        ('importado', 'Importado'),
        ('mixto', 'Mixto'),
    ]

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes_enviadas'
    )
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitudes_recibidas'
    )

    # Datos generales
    empresa = models.CharField(max_length=20, choices=EMPRESAS, default='marsella')
    tipo_solicitud = models.CharField(max_length=20, choices=TIPOS_SOLICITUD, default='nuevo_articulo')
    cotizacion = models.CharField(max_length=20, choices=OPCIONES_COTIZACION, blank=True, null=True)
    archivo_cotizacion = models.FileField(upload_to='cotizaciones/', blank=True, null=True)
    imagen_whatsapp = models.ImageField(upload_to='cotizaciones/img/', blank=True, null=True)

    # Datos técnicos
    origen = models.CharField(max_length=20, choices=ORIGENES, default='sin_origen')
    proveedor = models.ForeignKey('sap.Proveedor', on_delete=models.CASCADE, null=True, blank=True)
    rut_proveedor = models.CharField(max_length=12, null=True, blank=True)
    sku_proveedor = models.CharField(max_length=100, null=True, blank=True)
    sku_fabricante = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    marca = models.ForeignKey('sap.Marca', on_delete=models.SET_NULL, null=True)
    udm = models.ForeignKey('sap.UDM', on_delete=models.SET_NULL, null=True)

    # Dimensiones y costo
    largo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ancho = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Control de estado
    titulo = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_tipo_solicitud_display()} - {self.solicitante.username} → {self.receptor.username}"