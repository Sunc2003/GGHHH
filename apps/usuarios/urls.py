from django.urls import path
from .views import RegistroUsuarioView, IniciarSesionView, CerrarSesionView, panel_admin_usuarios

urlpatterns = [
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('login/', IniciarSesionView.as_view(), name='login'),
    path('logout/', CerrarSesionView.as_view(), name='logout'),
    path('panel/', panel_admin_usuarios, name='panel_admin_usuarios'),
]
