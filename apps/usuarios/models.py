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
 
    # Relaciones de usuarios
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
 
    # Datos generales de la solicitud
    empresa = models.CharField(max_length=20, choices=EMPRESAS, default='marsella')
    tipo_solicitud = models.CharField(max_length=20, choices=TIPOS_SOLICITUD, default='nuevo_articulo')
    cotizacion = models.CharField(max_length=20, choices=OPCIONES_COTIZACION, blank=True, null=True)
 
    # Extra para el flujo de Activación
 
    codigo_extra = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Solo se usa en solicitudes de tipo Activación"
    )
 
 
 
    # Estado y control
    titulo = models.CharField(max_length=100, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    mensaje = models.TextField(blank=True, null=True, verbose_name="Mensaje al receptor")
    comentario_estado = models.TextField(blank=True, null=True, verbose_name="Comentario de respuesta")
 
    def __str__(self):
        return f"{self.get_tipo_solicitud_display()} - {self.solicitante.username} → {self.receptor.username}"
 
 
class DetalleCodigo(models.Model):
    ORIGENES = [
        ('sin origen', 'Sin origen'),
        ('nacional', 'Nacional'),
        ('importado', 'Importado'),
        ('mixto', 'Mixto'),
    ]
 
    solicitud = models.ForeignKey(SolicitudCodigo, on_delete=models.CASCADE, related_name='detalles')
    descripcion = models.TextField()
    marca = models.ForeignKey('sap.Marca', on_delete=models.PROTECT)
    udm = models.ForeignKey('sap.UDM', on_delete=models.PROTECT)
 
    origen = models.CharField(max_length=20, choices=ORIGENES, default='sin origen')
    proveedor = models.ForeignKey('sap.Proveedor', on_delete=models.PROTECT, related_name='detalles')
 
    largo = models.DecimalField(max_digits=10, decimal_places=2)
    ancho = models.DecimalField(max_digits=10, decimal_places=2)
    alto = models.DecimalField(max_digits=10, decimal_places=2)
    peso = models.DecimalField(max_digits=10, decimal_places=2)
    costo = models.DecimalField(max_digits=15, decimal_places=2)
    sku_proveedor = models.CharField(max_length=100)
    sku_fabricante = models.CharField(max_length=100)
 
    def __str__(self):
        return f"SKU: {self.sku_proveedor or self.sku_fabricante} - ${self.costo}"
 
 
def ruta_adjuntos(instance, filename):
    carpeta_base = f"solicitudes/{instance.solicitud.id}"
    if instance.tipo == 'documento':
        carpeta = f"{carpeta_base}/archivos"
    else:
        carpeta = f"{carpeta_base}/imagenes"
    return f"{carpeta}/{filename}"
 
 
class SolicitudAdjunto(models.Model):
    TIPO_CHOICES = [
        ('documento', 'Documento'),
        ('imagen', 'Imagen WhatsApp')
    ]
 
    solicitud = models.ForeignKey(
        'SolicitudCodigo',
        on_delete=models.CASCADE,
        related_name='adjuntos'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    archivo = models.FileField(upload_to=ruta_adjuntos)
 
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.archivo.name}"