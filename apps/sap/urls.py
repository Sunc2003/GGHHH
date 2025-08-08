from django.urls import path
from .views import buscar_productos_remoto, buscador_productos_view

urlpatterns = [
    path('buscar-productos-externo/', buscar_productos_remoto, name='buscar_productos_remoto'),
    path("buscar-productos-ui/", buscador_productos_view, name="buscar_productos_ui"),
]

