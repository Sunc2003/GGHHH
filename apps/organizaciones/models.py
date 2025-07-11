from django.db import models

class Area(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Cargo(models.Model):
    nombre = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='cargos')

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"
