from django.db import models
from organizaciones.models import Area, Cargo

class Permiso(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return f"[{self.codigo}] {self.nombre}"

class PermisoArea(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('area', 'permiso')

class PermisoCargo(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('cargo', 'permiso')
