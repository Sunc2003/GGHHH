# apps/sap/urls.py
from django.urls import path
from . import views
from .views import cotizacion_pdf
from apps.sap import views as sap_views
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
    MenuVentasView,
    BuscarCotizacionesView,
    api_cotizaciones,
    api_cotizacion_action,
    OrdenVenta, 
    crear_orden_venta
    
    
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
    path('menu/', MenuVentasView.as_view(), name='menu_ventas'),
    path("api/cotizaciones/", api_cotizaciones, name="api_cotizaciones"),
    path("cotizaciones/buscar/", BuscarCotizacionesView.as_view(), name="buscar_cotizacion"),
    path("buscar_socios_por_nombre/", sap_views.buscar_socios_por_nombre, name="buscar_socios_por_nombre"),
    path("api/cotizaciones/<int:doc_entry>/action/", api_cotizacion_action, name="api_cotizacion_action"),
    path("ventas/ov/nueva/", OrdenVenta.as_view(), name="ov_nueva"),
    path("api/ventas/ov/crear/", crear_orden_venta, name="ov_crear"),
]
