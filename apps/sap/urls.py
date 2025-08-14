from django.urls import path
from .views import buscar_productos_remoto, buscador_productos_view, socios_lista_view, socio_detalle_view, obtener_detalle_producto
 
urlpatterns = [
    path('buscar-productos-externo/', buscar_productos_remoto, name='buscar_productos_remoto'),
    path("buscar-productos-ui/", buscador_productos_view, name="buscar_productos_ui"),
    path("sap/api/productos/<path:itemcode>/", obtener_detalle_producto, name="obtener_detalle_producto"),
    path("socios/", socios_lista_view, name="socios_lista"),
    path("socios/<str:cardcode>/", socio_detalle_view, name="socio_detalle"),
]