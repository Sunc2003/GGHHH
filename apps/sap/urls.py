# apps/sap/urls.py
from django.urls import path
from . import views
from .views import cotizacion_pdf
from .views import (
    buscar_productos_remoto,
    buscador_productos_view,
    socios_lista_view,
    socio_detalle_view,
    obtener_detalle_producto,
    ov_detalle_view,
    guias_pendientes_view,
    Cotizacion,
    crear_cotizacion,
    
)

urlpatterns = [
    # === PRODUCTOS ===
    path("buscar-productos-externo/", buscar_productos_remoto, name="buscar_productos_remoto"),
    path("buscar-productos-ui/", buscador_productos_view, name="buscar_productos_ui"),
    path("sap/api/productos/<path:itemcode>/", obtener_detalle_producto, name="obtener_detalle_producto"),

    # === SOCIOS ===
    path("socios/", socios_lista_view, name="socios_lista"),
    path("socios/<str:cardcode>/", socio_detalle_view, name="socio_detalle"),
    path("sap/socios/<str:cardcode>/", socio_detalle_view, name="socio_detalle_view"),

    # === ÓRDENES DE VENTA ===
    path("sap/socios/<str:cardcode>/ov/<int:docnum>/", ov_detalle_view, name="ov_detalle"),

    # === GUÍAS ===
    path("guias-pendientes/", guias_pendientes_view, name="guias_pendientes"),

    # === COTIZACIONES ===
    path("cotizaciones/", Cotizacion.as_view(), name="cotizacion_form"),
    path("cotizaciones/nueva/", crear_cotizacion, name="cotizacion_crear"),

    path("buscar_items_inventario/", views.buscar_items_inventario, name="buscar_items_inventario"),
    path("cotizaciones/detalle/<int:doc_entry>/", views.cotizacion_detalle, name="cotizacion_detalle"),
    path("cotizacion/<int:doc_entry>/pdf/", views.cotizacion_pdf, name="cotizacion_pdf"),

]
