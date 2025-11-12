from django.core.cache import cache
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

@receiver(user_logged_in)
def mark_online(sender, user, request, **kwargs):
    # Guardamos el estado "en línea" sin expiración
    cache.set(f"online:{user.id}", True, None)

@receiver(user_logged_out)
def mark_offline(sender, user, request, **kwargs):
    # Eliminamos el estado al cerrar sesión
    cache.delete(f"online:{user.id}")
