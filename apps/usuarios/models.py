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
    movil = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.get_full_name() or self.username

    def obtener_permisos(self):
        from permisos.models import Permiso
        permisos_area = Permiso.objects.filter(permisoarea__area=self.area)
        permisos_cargo = Permiso.objects.filter(permisocargo__cargo=self.cargo)
        return (permisos_area | permisos_cargo).distinct()

    def tiene_permiso(self, codigo_permiso):
        return self.obtener_permisos().filter(codigo=codigo_permiso).exists()


class SolicitudCodigo(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('creado', 'Código Creado'),
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
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Solicitud de {self.solicitante.username} a {self.receptor.username}"