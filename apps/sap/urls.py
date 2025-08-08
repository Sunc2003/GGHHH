from django.urls import path
from .views import buscar_productos_remoto

urlpatterns = [
    path('buscar-productos-externo/', buscar_productos_remoto, name='buscar_productos_remoto'),
]
