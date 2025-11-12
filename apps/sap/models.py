from django.db import models

class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    rut = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return f"{self.nombre} - {self.rut}"


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class UDM(models.Model):  # Unidad de Medida
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre