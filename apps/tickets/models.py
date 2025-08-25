from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Ticket(models.Model):
    ESTADOS = (
        ('abierto', 'Abierto'),
        ('en_progreso', 'En progreso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    )
    PRIORIDADES = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    )

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierto')
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='media')
    solicitante = models.ForeignKey(
        User, related_name='tickets_creados', on_delete=models.CASCADE
    )
    asignado_a = models.ForeignKey(
        User, related_name='tickets_asignados',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.pk} {self.titulo}"


class TicketMensaje(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='mensajes', on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)
    publico = models.BooleanField(default=True)

    class Meta:
        ordering = ['fecha']


class TicketAdjunto(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='adjuntos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, default='documento')
    ruta = models.CharField(max_length=512)
    nombre = models.CharField(max_length=255, blank=True)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(default=timezone.now)
