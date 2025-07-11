from django.urls import path
from .views import RegistroUsuarioView, IniciarSesionView, CerrarSesionView, panel_admin_usuarios
from .views import (
    SolicitudCreateView,
    SolicitudesRecibidasView,
    SolicitudDetailView,
    CambiarEstadoView,
)

urlpatterns = [
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('login/', IniciarSesionView.as_view(), name='login'),
    path('logout/', CerrarSesionView.as_view(), name='logout'),
    path('panel/', panel_admin_usuarios, name='panel_admin_usuarios'),
    path('solicitud/nueva/', SolicitudCreateView.as_view(), name='nueva_solicitud'),
    path('solicitudes/recibidas/', SolicitudesRecibidasView.as_view(), name='solicitudes_recibidas'),
    path('solicitud/<int:pk>/', SolicitudDetailView.as_view(), name='detalle_solicitud'),
    path('solicitud/<int:pk>/cambiar-estado/', CambiarEstadoView.as_view(), name='cambiar_estado'),
    
]
