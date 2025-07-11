from django.contrib.auth.models import AbstractUser
from django.db import models
from organizaciones.models import Area, Cargo

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
