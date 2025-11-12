# apps/tickets/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    solicitante = models.ForeignKey(User, related_name='tickets_creados', on_delete=models.CASCADE)
    asignado_a = models.ForeignKey(User, related_name='tickets_asignados',
                                   on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.pk} {self.titulo}"

    @property
    def esta_cerrado(self) -> bool:
        return self.estado == 'cerrado'

    @property
    def esta_bloqueado(self) -> bool:
        # Trata 'resuelto' como bloqueado igual que 'cerrado'
        return self.estado in ('resuelto', 'cerrado')

    @property
    def puede_responder(self) -> bool:
        return not self.esta_bloqueado


class TicketMensaje(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='mensajes', on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)
    publico = models.BooleanField(default=True)

    class Meta:
        ordering = ['fecha']

    def clean(self):
       
        tid = getattr(self, "ticket_id", None)
        if not tid:
            return
        estado = Ticket.objects.filter(pk=tid).values_list("estado", flat=True).first()
        if estado in ("resuelto", "cerrado"):
            raise ValidationError("El ticket está bloqueado (resuelto/cerrado); no se pueden agregar mensajes.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class TicketAdjunto(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='adjuntos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, default='documento')
    ruta = models.CharField(max_length=512)
    nombre = models.CharField(max_length=255, blank=True)
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(default=timezone.now)

    def clean(self):
        tid = getattr(self, "ticket_id", None)
        if not tid:
            return
        estado = Ticket.objects.filter(pk=tid).values_list("estado", flat=True).first()
        if estado in ("resuelto", "cerrado"):
            raise ValidationError("El ticket está bloqueado (resuelto/cerrado); no se pueden subir adjuntos.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
