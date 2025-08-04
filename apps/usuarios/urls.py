from django.urls import path
from . import views  # Asegúrate de importar views si usas views.cargos_por_area
from .views import (
    RegistroUsuarioView,
    IniciarSesionView,
    CerrarSesionView,
    panel_admin_usuarios,
    SolicitudConDetallesCreateView,
    SolicitudesRecibidasView,
    SolicitudDetailView,
    CambiarEstadoView,
    UsuariosADListView,
    perfil_usuario,
    solicitudes_enviadas_view,
  
    
    
)
from apps.organizaciones.views import cargos_por_area
from .views import procesos_view





urlpatterns = [
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('login/', IniciarSesionView.as_view(), name='login'),
    path('logout/', CerrarSesionView.as_view(), name='logout'),
    path('panel/', panel_admin_usuarios, name='panel_admin_usuarios'),
    path('solicitud/nueva/', SolicitudConDetallesCreateView.as_view(), name='nueva_solicitud'),
    path('solicitudes/recibidas/', SolicitudesRecibidasView.as_view(), name='solicitudes_recibidas'),
    path('solicitud/<int:pk>/', SolicitudDetailView.as_view(), name='detalle_solicitud'),
    path('solicitud/<int:pk>/cambiar-estado/', CambiarEstadoView.as_view(), name='cambiar_estado'),
    path('usuarios_ad/', UsuariosADListView.as_view(), name='usuarios_ad'),
    path('perfil/', perfil_usuario, name='perfil_usuario'),
    path('solicitudes/enviadas/', solicitudes_enviadas_view, name='solicitudes_enviadas'),
    path('procesos/', procesos_view, name='procesos'),
    

    # API para carga dinámica de cargos
 
    path('api/cargos_por_area/<int:area_id>/', cargos_por_area, name='cargos_por_area'),
]

